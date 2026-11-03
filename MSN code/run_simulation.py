#!/usr/bin/env python3
"""
run_simulation.py — Standalone script to reproduce the MSN general behaviour.

Replicates the workflow of '01 - General behaviour.ipynb':
  1. Compiles the NESTML MSN model for the local NEST installation
  2. Runs the cortical ramp experiment (ExperimentDAHD)
  3. Generates the composite raster + firing rate figure

Usage:
    conda run -n env_nest python run_simulation.py
"""

import sys
import os
import shutil

# ─── Step 0: Print environment info ───────────────────────────────────────────
print("=" * 60)
print("MSN Simulation — Environment Check")
print("=" * 60)
print(f"Python: {sys.version}")

import nest
print(f"NEST:   {nest.__version__}")

NEST_INSTALL = nest.ll_api.sli_func("statusdict/prefix ::")
print(f"NEST install location: {NEST_INSTALL}")

import numpy as np
print(f"NumPy:  {np.__version__}")

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for headless rendering
import matplotlib.pyplot as plt

try:
    import pynestml
    print(f"NESTML: {pynestml.__version__}")
except Exception:
    print("NESTML: version unknown")

from pynestml.frontend.pynestml_frontend import generate_nest_target


# ─── Step 1: Compile the NESTML module ────────────────────────────────────────
print("\n" + "=" * 60)
print("Step 1: Compiling NESTML MSN module")
print("=" * 60)

nestml_input = os.path.join(os.path.dirname(__file__), "nest_module", "msn.nestml")
nestml_target = os.path.join(os.path.dirname(__file__), "nest_module", "nestml_target")

# Clean old build artifacts from macOS
if os.path.exists(nestml_target):
    print(f"Cleaning old build dir: {nestml_target}")
    shutil.rmtree(nestml_target)

print(f"Input:  {nestml_input}")
print(f"Target: {nestml_target}")
print("Generating NEST target (this may take a minute)...")

try:
    generate_nest_target(
        input_path=nestml_input,
        target_path=nestml_target,
        logging_level="WARNING",
    )
    print("✓ NESTML compilation successful!")
except Exception as e:
    print(f"✗ NESTML compilation failed: {e}")
    print("\nFull traceback:")
    import traceback
    traceback.print_exc()
    sys.exit(1)


# ─── Step 2: Load the compiled module into NEST ──────────────────────────────
print("\n" + "=" * 60)
print("Step 2: Setting up the NEST kernel and loading nestmlmodule")
print("=" * 60)

try:
    from utils.kernel import setup_kernel
    setup_kernel(verbosity="M_WARNING")
    print("✓ Kernel ready, module loaded successfully!")
except Exception as e:
    print(f"✗ Module loading failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)


# ─── Step 3: Run the simulation ──────────────────────────────────────────────
print("\n" + "=" * 60)
print("Step 3: Running MSN simulation")
print("=" * 60)

from msn import MSN
from experiment import ExperimentDAHD

msn = MSN(curr=0)
e_normal = ExperimentDAHD(dopamine_level=0.3, msn=msn)

print("Simulating (warm-up 1500ms + ramp 50ms + steady 1000ms = 2550ms total)...")
e_normal.run()
print("✓ Simulation complete!")


# ─── Step 4: Generate the figure ─────────────────────────────────────────────
print("\n" + "=" * 60)
print("Step 4: Generating figures")
print("=" * 60)

e = e_normal

# Colors matching the original notebook
new_colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b',
              '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']


def plot_input_from_cortex(ax, channels=[0, 1]):
    """Plot cortical input frequency ramp for each channel."""
    cortex_low_freq = 2.2
    cortex_high_freq = 3.6
    ctx_afferents = e.msn.params.net.ctx_afferents_per_neuron
    m = cortex_low_freq * ctx_afferents
    M = cortex_high_freq * ctx_afferents

    for ch_idx in channels:
        rates = []
        times = []

        # Warm-up
        rates.append(m / ctx_afferents)
        times.append(0)
        rates.append(m / ctx_afferents)
        times.append(1500)

        # First ramp (25 ms)
        for i in range(25):
            fi = i / 50.0
            t = 1500 + i
            if ch_idx == 0:
                r = m + (M - m) * fi
            else:
                r = m + (M - m) * fi
            rates.append(r / ctx_afferents)
            times.append(t)

        # Second ramp (25 ms)
        for i in range(25):
            fi = i / 50.0
            t = 1525 + i
            if ch_idx == 0:
                r = (m + M) * 0.5 + (M - m) * fi
            else:
                r = (m + M) * 0.5 - (M - m) * fi
            rates.append(r / ctx_afferents)
            times.append(t)

        # Steady
        rates.append(rates[-1])
        times.append(2550)

        ax.plot(times, rates, color=new_colors[ch_idx], linewidth=1.5)

    ax.set_ylabel('Ctx')
    ax.set_xlim(0, 2550)
    ax.set_xticks([])


def rasterplot(ax, nucleus_name='msn', channels=0, n_neurons=40, time_bin=50.0,
               time_axis=True, alpha_spike=0.2, alpha_background=0.125):
    """Custom raster plot matching the notebook's inline implementation."""
    ax1 = ax
    ax1.set_ylabel(nucleus_name)
    nucleus_name_lower = nucleus_name.lower()

    if type(channels) is not list:
        channels = [channels]

    spikes = []
    for i, channel in enumerate(channels):
        # Background shading
        ax1.axhspan(i * n_neurons, (i + 1) * n_neurons,
                    facecolor=new_colors[channel], alpha=alpha_background)

        # Get spike data for this channel
        detector = e.msn.spikedetector_msn_channels[channel]
        events = nest.GetStatus(detector, 'events')[0]
        senders = events['senders']
        times = events['times']

        # Get unique neuron IDs and subsample
        unique_senders = np.unique(senders)
        if len(unique_senders) > n_neurons:
            selected = np.sort(np.random.choice(unique_senders, n_neurons, replace=False))
        else:
            selected = unique_senders

        # Map sender IDs to plot positions
        for j, nid in enumerate(selected):
            mask = senders == nid
            spike_times = times[mask]
            ax1.plot(spike_times, np.full_like(spike_times, i * n_neurons + j),
                    '.', markersize=1, color='gray', alpha=alpha_spike)

        spikes.append((events, channel))

    # Firing rate on twin axis
    ax2 = ax1.twinx()
    ax2.set_ylabel('Firing rate (Hz)')

    total_time = nest.GetKernelStatus('biological_time')
    n_bins = int(total_time / time_bin)

    for events, channel in spikes:
        spike_times = events['times']
        n_senders = len(np.unique(events['senders']))

        counts, bin_edges = np.histogram(spike_times, bins=n_bins, range=(0, total_time))
        rates = counts / (n_senders * (time_bin / 1000.0))
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

        ax2.step(bin_centers, rates, color=new_colors[channel], linewidth=1.5,
                where='mid')

    ax2.set_ylim(0, 22)
    ax1.set_ylim(0, n_neurons * len(channels))
    ax1.set_xlim(0, total_time)

    # Stimulus onset line
    ax1.axvline(x=1500, color='green', linestyle='--', alpha=0.7)

    if time_axis:
        ax1.set_xlabel('Time (ms)')
    else:
        ax1.set_xticks([])


# Create composite figure
plt.rcParams['figure.figsize'] = [16.0, 8.0]
plt.rcParams['font.size'] = 20

fig = plt.figure()
ax_ctx = plt.subplot2grid((9, 1), (0, 0), rowspan=2)
ax_msn = plt.subplot2grid((9, 1), (2, 0), rowspan=7)

plot_input_from_cortex(ax_ctx)
rasterplot(ax_msn, 'MSN', channels=[0, 1])

ax1 = fig.add_subplot(111, frameon=False)
ax1.tick_params(labelcolor='none', top=False, bottom=False, left=False, right=False)
ax1.set_xlabel('Time (ms)')
ax1.set_ylabel('Nucleus')

ax2 = ax1.twinx()
ax2.tick_params(labelcolor='none', top=False, bottom=False, left=False, right=False)
ax2.set_ylabel('Firing rate (Hz)')

plt.tight_layout()

# Save
output_dir = os.path.dirname(__file__)
png_path = os.path.join(output_dir, "general_behaviour_reproduced.png")
svg_path = os.path.join(output_dir, "general_behaviour_reproduced.svg")

fig.savefig(png_path, dpi=150, bbox_inches='tight')
fig.savefig(svg_path, bbox_inches='tight')
print(f"✓ Saved: {png_path}")
print(f"✓ Saved: {svg_path}")


# ─── Step 5: Print firing rate summary ───────────────────────────────────────
print("\n" + "=" * 60)
print("Step 5: Firing rate analysis")
print("=" * 60)

time_bin_analysis = 50.0
total_time = nest.GetKernelStatus('biological_time')
n_bins = int(total_time / time_bin_analysis)

for ch_idx in [0, 1]:
    detector = e.msn.spikedetector_msn_channels[ch_idx]
    events = nest.GetStatus(detector, 'events')[0]
    spike_times = events['times']
    n_senders = len(np.unique(events['senders']))

    # Steady-state period (last 500ms)
    steady_mask = spike_times >= 2000
    steady_spikes = spike_times[steady_mask]
    steady_duration_s = (total_time - 2000) / 1000.0
    steady_rate = len(steady_spikes) / (n_senders * steady_duration_s) if n_senders > 0 else 0

    ch_name = "SELECTED" if ch_idx == 0 else "NON-SELECTED"
    print(f"Channel {ch_idx + 1} ({ch_name}):")
    print(f"  Neurons: {n_senders}")
    print(f"  Steady-state firing rate (t>2000ms): {steady_rate:.2f} Hz")
    print(f"  Target: {'~18.5 Hz' if ch_idx == 0 else '~2 Hz'}")
    print()

print("=" * 60)
print("DONE! Compare general_behaviour_reproduced.png with general_behaviour.png")
print("=" * 60)
