#!/usr/bin/env python3
"""
run_simulation.py — Standalone script to reproduce the MSN general behaviour.

Replicates the workflow of '01 - General behaviour.ipynb':
  1. Loads the compiled NESTML MSN model (run compile_module.py first)
  2. Runs the cortical ramp experiment (ExperimentDAHD)
  3. Generates the composite raster + firing rate figure

Usage:
    conda run -n env_nest python run_simulation.py [--dt 0.1] [--seed 1] [--threads 8] [--da 0.3]
"""

import argparse
import sys
import os

from msn_params import params
from msn import MSN
from experiment import ExperimentDAHD

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("--dt", type=float, default=params.sim.step, help="simulation resolution in ms")
ap.add_argument("--seed", type=int, default=params.sim.seed, help="NEST rng_seed")
ap.add_argument("--threads", type=int, default=params.sim.n_threads, help="NEST local_num_threads")
ap.add_argument("--da", type=float, default=0.3, help="dopamine level")
args = ap.parse_args()

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

print(f"dt = {args.dt} ms · seed = {args.seed} · threads = {args.threads} · DA = {args.da}")


# ─── Step 1: Load the compiled module into NEST ──────────────────────────────
print("\n" + "=" * 60)
print("Step 1: Setting up the NEST kernel and loading nestmlmodule")
print("=" * 60)

# Warn if msn.nestml was edited after the module was last compiled
nestml_input = os.path.join(os.path.dirname(os.path.abspath(__file__)), "nest_module", "msn.nestml")
module_path = os.path.join(NEST_INSTALL, "lib", "nest", "nestmlmodule.so")
if os.path.exists(module_path) and os.path.getmtime(nestml_input) > os.path.getmtime(module_path):
    print("⚠ msn.nestml is newer than the installed nestmlmodule: run compile_module.py to rebuild it.")

try:
    from utils.kernel import setup_kernel
    setup_kernel(dt=args.dt, seed=args.seed, threads=args.threads, verbosity="M_WARNING")
    print("✓ Kernel ready, module loaded successfully!")
except Exception as e:
    print(f"✗ Module loading failed: {e}")
    print("Compile and install it first with: python compile_module.py")
    import traceback
    traceback.print_exc()
    sys.exit(1)


# ─── Step 2: Run the simulation ──────────────────────────────────────────────
print("\n" + "=" * 60)
print("Step 2: Running MSN simulation")
print("=" * 60)

msn = MSN(curr=0)
e_normal = ExperimentDAHD(dopamine_level=args.da, msn=msn)

print("Simulating (warm-up 1500ms + ramp 50ms + steady 1000ms = 2550ms total)...")
e_normal.run()
print("✓ Simulation complete!")


# ─── Step 3: Generate the figure ─────────────────────────────────────────────
print("\n" + "=" * 60)
print("Step 3: Generating figures")
print("=" * 60)

e = e_normal

# Colours used consistently across the project figures:
#   D1 = blue, D2 = orange (as in analysis/single_neuron.py)
#   channel 1 (selected) = violet, channel 2 (non-selected) = green
# The original notebook used blue / orange for the channels, which clashed with D1 / D2.
CHANNEL_COLORS = ['#E47AFF', '#5D8500']
POP_COLORS = {'D1': '#1f77b4', 'D2': '#ff7f0e'}
ONSET_LINE = dict(color='#2ca02c', linestyle='--')   # stimulus onset, same green as the original figure


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

        ax.plot(times, rates, color=CHANNEL_COLORS[ch_idx], linewidth=1.5)

    ax.axvline(x=1500, **ONSET_LINE)  # stimulus onset, as in the MSN panel
    ax.set_ylabel('Ctx input\n(Hz per afferent)', fontsize=14)
    ax.set_xlim(0, 2550)
    ax.set_xticks([])


def rasterplot(ax, nucleus_name='msn', channels=0, n_neurons=40, time_bin=50.0,
               time_axis=True, alpha_spike=0.5, alpha_background=0.125):
    """Custom raster plot matching the notebook's inline implementation."""
    ax1 = ax
    ax1.set_ylabel(f'{nucleus_name} raster\n({n_neurons} neurons per channel)', fontsize=16)
    nucleus_name_lower = nucleus_name.lower()

    if type(channels) is not list:
        channels = [channels]

    spikes = []
    for i, channel in enumerate(channels):
        # Background shading
        ax1.axhspan(i * n_neurons, (i + 1) * n_neurons,
                    facecolor=CHANNEL_COLORS[channel], alpha=alpha_background)

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
                    '.', markersize=2.5, color='black', alpha=alpha_spike)

        spikes.append((events, channel))

    # Firing rate on twin axis
    ax2 = ax1.twinx()
    ax2.set_ylabel('Firing rate (Hz)')

    total_time = nest.GetKernelStatus('biological_time')
    n_bins = int(total_time / time_bin)

    for events, channel in spikes:
        spike_times = events['times']
        n_channel = len(e.msn.msn_channels[channel])  # all neurons of the channel, not only those that spiked

        counts, bin_edges = np.histogram(spike_times, bins=n_bins, range=(0, total_time))
        rates = counts / (n_channel * (time_bin / 1000.0))
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

        ax2.step(bin_centers, rates, color=CHANNEL_COLORS[channel], linewidth=1.5,
                where='mid')

    ax2.set_ylim(0, 22)
    ax2.grid(True, axis='y', alpha=0.3)   # horizontal lines on the firing-rate scale
    ax1.grid(True, axis='x', alpha=0.3)   # vertical lines on the time axis
    ax1.set_ylim(0, n_neurons * len(channels))
    ax1.set_xlim(0, total_time)
    # left axis: one band of n_neurons sampled neurons per channel
    ax1.set_yticks([(i + 0.5) * n_neurons for i in range(len(channels))])
    ax1.set_yticklabels([f'Ch {c + 1}' for c in channels])

    # Stimulus onset line
    ax1.axvline(x=1500, **ONSET_LINE)

    if time_axis:
        ax1.set_xlabel('Time (ms)')
    else:
        ax1.set_xticks([])


# Create composite figure
plt.rcParams['figure.figsize'] = [16.0, 8.0]
plt.rcParams['font.size'] = 20

# Layout, from top to bottom: title of the Ctx panel, shared legend, Ctx panel,
# title of the MSN panel, MSN panel (positions set by hand, no tight_layout)
fig = plt.figure(figsize=(16.0, 10.0))
gs = fig.add_gridspec(2, 1, height_ratios=[2, 7], hspace=0.45, top=0.87, bottom=0.08)
ax_ctx = fig.add_subplot(gs[0])
ax_msn = fig.add_subplot(gs[1])

plot_input_from_cortex(ax_ctx)
rasterplot(ax_msn, 'MSN', channels=[0, 1])

fig.text(0.5, 0.975, 'Cortical input: firing rate of each cortical afferent to the two action channels',
         ha='center', va='top', fontsize=20)
legend_handles = [
    plt.Line2D([], [], color=CHANNEL_COLORS[0], linewidth=2.5),
    plt.Line2D([], [], color=CHANNEL_COLORS[1], linewidth=2.5),
    plt.Line2D([], [], color='black', marker='.', linestyle='none', markersize=8, alpha=0.6),
    plt.Line2D([], [], **ONSET_LINE),
]
legend_labels = ['Channel 1 (selected)', 'Channel 2 (non-selected)',
                 'raster: 1 dot = 1 spike', 'ramp onset (1500 ms)']
fig.legend(legend_handles, legend_labels, loc='upper center', bbox_to_anchor=(0.5, 0.935),
           ncol=4, frameon=False, fontsize=16)
ax_msn.set_title('MSN response: raster of 40 sampled neurons per channel (bands, left axis) and\n'
                 'mean firing rate of all 916 neurons of each channel (lines, right axis)',
                 fontsize=20, pad=15)

# Save
output_dir = os.path.dirname(__file__)
png_path = os.path.join(output_dir, "general_behaviour_reproduced.png")  # transparent background
jpg_path = os.path.join(output_dir, "general_behaviour_reproduced.jpg")  # white background
svg_path = os.path.join(output_dir, "general_behaviour_reproduced.svg")

fig.savefig(png_path, dpi=150, bbox_inches='tight', transparent=True)
fig.savefig(jpg_path, dpi=150, bbox_inches='tight', facecolor='white', pil_kwargs={'quality': 95})
fig.savefig(svg_path, bbox_inches='tight')
for path in (png_path, jpg_path, svg_path):
    print(f"✓ Saved: {path}")


# ─── Step 3b: D1 vs D2 figure ────────────────────────────────────────────────
# Each channel contains both D1 and D2 MSNs: here their firing rates are shown
# separately, using the per-population recorders created by msn.py.
POP_STYLE = {'D1': dict(color=POP_COLORS['D1'], linestyle='-'),    # blue
             'D2': dict(color=POP_COLORS['D2'], linestyle='-')}    # orange


def population_rate(detector, n_pop, time_bin=50.0):
    """Firing rate (Hz per neuron) of one population, in bins of time_bin ms."""
    total_time = nest.GetKernelStatus('biological_time')
    n_bins = int(total_time / time_bin)
    spike_times = nest.GetStatus(detector, 'events')[0]['times']
    counts, edges = np.histogram(spike_times, bins=n_bins, range=(0, total_time))
    return (edges[:-1] + edges[1:]) / 2, counts / (n_pop * time_bin / 1000.0)


with plt.rc_context({'font.size': 16}):
    fig2 = plt.figure(figsize=(16.0, 10.0))
    ax_ctx2 = plt.subplot2grid((10, 1), (0, 0), rowspan=2)
    ax_ch = [plt.subplot2grid((10, 1), (2 + 4 * k, 0), rowspan=4) for k in range(2)]

    plot_input_from_cortex(ax_ctx2)
    fig2.suptitle('Firing rate of D1 and D2 MSNs within each action channel')

    total_time = nest.GetKernelStatus('biological_time')
    for k, ax in enumerate(ax_ch):
        ax.axvspan(0, total_time, facecolor=CHANNEL_COLORS[k], alpha=0.125, zorder=0)  # channel colour, as in the raster
        for pop, detectors, groups in (('D1', e.msn.spikedetector_msn_d1_channels, e.msn.msn_d1_channels),
                                       ('D2', e.msn.spikedetector_msn_d2_channels, e.msn.msn_d2_channels)):
            t, rate = population_rate(detectors[k], len(groups[k]))
            ax.step(t, rate, where='mid', linewidth=2, label=f'{pop} ({len(groups[k])} neurons)', **POP_STYLE[pop])
        ax.axvline(x=1500, **ONSET_LINE)
        ax.set_ylabel('Firing rate (Hz)')
        ax.set_ylim(0, 25)
        ax.set_xlim(0, total_time)
        ax.grid(True, alpha=0.3)
        ax.text(0.01, 0.92, f'Channel {k + 1} ({"selected" if k == 0 else "non-selected"})',
                transform=ax.transAxes, va='top', fontweight='bold')
    ax_ch[0].tick_params(labelbottom=False)
    ax_ch[1].set_xlabel('Time (ms)')
    # one legend for both channel panels, below the title (each channel has 458 D1 + 458 D2 neurons)
    handles, labels = ax_ch[0].get_legend_handles_labels()
    fig2.legend(handles, labels, loc='upper center', bbox_to_anchor=(0.5, 0.955), ncol=2, frameon=False)
    fig2.tight_layout()
    fig2.subplots_adjust(top=0.88)

    base = os.path.join(output_dir, "general_behaviour_D1_D2_reproduced")
    fig2.savefig(base + ".png", dpi=150, bbox_inches='tight', transparent=True)
    fig2.savefig(base + ".jpg", dpi=150, bbox_inches='tight', facecolor='white', pil_kwargs={'quality': 95})
    fig2.savefig(base + ".svg", bbox_inches='tight')
    for ext in (".png", ".jpg", ".svg"):
        print(f"✓ Saved: {base}{ext}")


# ─── Step 4: Print firing rate summary ───────────────────────────────────────
print("\n" + "=" * 60)
print("Step 4: Firing rate analysis")
print("=" * 60)

time_bin_analysis = 50.0
total_time = nest.GetKernelStatus('biological_time')
n_bins = int(total_time / time_bin_analysis)

for ch_idx in [0, 1]:
    detector = e.msn.spikedetector_msn_channels[ch_idx]
    events = nest.GetStatus(detector, 'events')[0]
    spike_times = events['times']
    n_neurons = len(e.msn.msn_channels[ch_idx])  # all neurons of the channel, not only those that spiked
    n_active = len(np.unique(events['senders']))

    # Steady-state period (last 500ms)
    steady_mask = spike_times >= 2000
    steady_spikes = spike_times[steady_mask]
    steady_duration_s = (total_time - 2000) / 1000.0
    steady_rate = len(steady_spikes) / (n_neurons * steady_duration_s)

    ch_name = "SELECTED" if ch_idx == 0 else "NON-SELECTED"
    print(f"Channel {ch_idx + 1} ({ch_name}):")
    print(f"  Neurons: {n_neurons} ({n_active} spiked at least once)")
    print(f"  Steady-state firing rate (t>2000ms): {steady_rate:.2f} Hz")
    for pop, detectors, groups in (('D1', e.msn.spikedetector_msn_d1_channels, e.msn.msn_d1_channels),
                                   ('D2', e.msn.spikedetector_msn_d2_channels, e.msn.msn_d2_channels)):
        t_pop = nest.GetStatus(detectors[ch_idx], 'events')[0]['times']
        rate_pop = np.sum(t_pop >= 2000) / (len(groups[ch_idx]) * steady_duration_s)
        print(f"    of which {pop} ({len(groups[ch_idx])} neurons): {rate_pop:.2f} Hz")
    print(f"  Target: {'~18.5 Hz' if ch_idx == 0 else '~2 Hz'}")
    print()

print("=" * 60)
print("DONE! Compare general_behaviour_reproduced.png with general_behaviour.png")
print("=" * 60)
