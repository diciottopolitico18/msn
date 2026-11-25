"""
Rate and selectivity metrics of the cortical ramp experiment (ExperimentDAHD).

Used by network_validation.py; kept here so that tests, sweeps and the closed loop can
reuse them. Firing rates are normalised by the total number of neurons in each channel
(not only by the neurons that spiked).
"""

import os
import sys

import numpy as np
from scipy.signal.windows import gaussian

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils import transient_selectivity, steadystate_selectivity  # noqa: E402

T_RAMP = 1500.0           # end of the warm-up / start of the ramp (ms)
T_RAMP_END = 1550.0       # end of the ramp (ms)
T_END = 2550.0            # total simulated time (ms)


def binned_rate(times, n_neurons, bin_ms, t0=0.0, t1=T_END):
    edges = np.arange(t0, t1 + bin_ms, bin_ms)
    counts, _ = np.histogram(times, bins=edges)
    return edges[:-1], counts / (n_neurons * bin_ms / 1000.0)


def window_rate(times, n_neurons, t0, t1):
    return np.sum((times >= t0) & (times < t1)) / (n_neurons * (t1 - t0) / 1000.0)


def smoothed_signal(times, n_neurons):
    """1-ms rate convolved with a normalised Gaussian (as in MSN._compute_signals)."""
    _, r = binned_rate(times, n_neurons, 1.0)
    win = gaussian(M=50, std=7.5)
    return np.convolve(r, win / win.sum(), mode="same")


def metrics(spikes):
    (t_s, _, n_s), (t_n, _, n_n) = spikes[0], spikes[1]
    m = {}

    # first 50-ms bin in which both channels exceed 0.1 Hz
    centers, r_s = binned_rate(t_s, n_s, 50.0)
    _, r_n = binned_rate(t_n, n_n, 50.0)
    active = np.nonzero((r_s > 0.1) & (r_n > 0.1))[0]
    m["first_activity_ms"] = float(centers[active[0]]) if len(active) else np.nan

    m["rate_end_warmup_selected_Hz"] = window_rate(t_s, n_s, T_RAMP - 100, T_RAMP)
    m["rate_end_warmup_nonselected_Hz"] = window_rate(t_n, n_n, T_RAMP - 100, T_RAMP)
    m["rate_first25ms_selected_Hz"] = window_rate(t_s, n_s, T_RAMP, T_RAMP + 25)
    m["rate_first25ms_nonselected_Hz"] = window_rate(t_n, n_n, T_RAMP, T_RAMP + 25)
    m["rate_steady_selected_Hz"] = window_rate(t_s, n_s, 2000.0, T_END)
    m["rate_steady_nonselected_Hz"] = window_rate(t_n, n_n, 2000.0, T_END)

    _, r_n25 = binned_rate(t_n, n_n, 25.0)
    c25 = np.arange(0.0, T_END, 25.0)
    after = (c25 >= T_RAMP_END) & (c25 < T_RAMP_END + 200)
    m["min_nonselected_after_ramp_Hz"] = float(r_n25[after].min())

    # time after the ramp at which the selected channel reaches 90% of its steady-state rate
    target = 0.9 * m["rate_steady_selected_Hz"]
    post = np.nonzero((centers >= T_RAMP_END) & (r_s >= target))[0]
    m["convergence_selected_ms"] = float(centers[post[0]] + 50.0 - T_RAMP_END) if len(post) else np.nan

    # González-Redondo selectivity metrics (same windows as Experiment.* in experiment.py)
    sig_s, sig_n = smoothed_signal(t_s, n_s), smoothed_signal(t_n, n_n)
    m["transient_selectivity"] = float(transient_selectivity(sig_s, sig_n, t_stable=(2000, 2500), t_transit=(1500, 1700)))
    m["steadystate_selectivity_%"] = float(steadystate_selectivity(sig_n, t_pre=(1250, 1500), t_stable=(2000, 2500)))
    return m
