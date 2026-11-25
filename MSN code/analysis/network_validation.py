#!/usr/bin/env python3
"""
Statistical validation of the MSN network against Rusiecka (2022) and
González-Redondo et al. (2020).

Runs the cortical ramp experiment (ExperimentDAHD) for several seeds and reports
mean ± sd of the acceptance metrics. Firing rates are normalised by the total
number of neurons in each channel (not only by the neurons that spiked).

Usage (from the "MSN code" folder, with nestmlmodule already compiled):
    python analysis/network_validation.py [--seeds 10] [--dt 0.1] [--threads 8] [--da 0.3]
"""

import argparse
import json
import os
import sys
import time

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import nest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from msn import MSN  # noqa: E402
from experiment import ExperimentDAHD  # noqa: E402
from msn_params import params  # noqa: E402
from utils.kernel import setup_kernel  # noqa: E402
from metrics import T_RAMP, T_RAMP_END, T_END, binned_rate, metrics  # noqa: E402

CHANNELS = {0: "selected", 1: "non-selected"}

# Reference values (Rusiecka 2022, Fig. 3 and text; González-Redondo 2020)
REFERENCE = {
    "first_activity_ms": "~250",
    "rate_end_warmup_Hz": "~3 (G-R: >5)",
    "rate_steady_selected_Hz": "~18.5 (17.5-20)",
    "rate_steady_nonselected_Hz": "~2 (G-R: ~2.5)",
    "min_nonselected_after_ramp_Hz": "<1",
    "convergence_selected_ms": "~250 after ramp",
}


def run_one(seed, dt, threads, da):
    setup_kernel(dt=dt, seed=seed, threads=threads)

    msn = MSN(curr=0)
    exp = ExperimentDAHD(dopamine_level=da, msn=msn)
    exp.run()

    spikes = {}
    for ch in CHANNELS:
        ev = msn.spikedetector_msn_channels[ch].events
        spikes[ch] = (np.asarray(ev["times"]), np.asarray(ev["senders"]), len(msn.msn_channels[ch]))
    return spikes


def plot_mean_rates(all_spikes, out_path, bin_ms=50.0):
    fig, ax = plt.subplots(figsize=(10, 4.5))
    for ch, label in CHANNELS.items():
        rates = []
        for spikes in all_spikes:
            t, _, n = spikes[ch]
            centers, r = binned_rate(t, n, bin_ms)
            rates.append(r)
        rates = np.array(rates)
        mu, sd = rates.mean(0), rates.std(0)
        x = centers + bin_ms / 2
        ax.plot(x, mu, drawstyle="steps-mid", label=f"{label} (mean of {len(rates)} seeds)")
        ax.fill_between(x, mu - sd, mu + sd, step="mid", alpha=0.25)
    ax.axvline(T_RAMP, color="green", ls="--", lw=1)
    ax.axvline(T_RAMP_END, color="green", ls=":", lw=1)
    ax.set_xlabel("time (ms)")
    ax.set_ylabel(f"firing rate (Hz, {bin_ms:.0f} ms bins)")
    ax.set_xlim(0, T_END)
    ax.legend(loc="upper left")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seeds", type=int, default=10, help="number of seeds (1..N)")
    ap.add_argument("--dt", type=float, default=params.sim.step, help="simulation resolution in ms")
    ap.add_argument("--threads", type=int, default=params.sim.n_threads, help="NEST local_num_threads")
    ap.add_argument("--da", type=float, default=0.3, help="dopamine level (phi_1 = phi_2)")
    ap.add_argument("--out", default="results/network_validation", help="output folder")
    args = ap.parse_args()

    out_dir = os.path.join(args.out, f"dt{args.dt}_da{args.da}_seeds{args.seeds}_thr{args.threads}")
    os.makedirs(out_dir, exist_ok=True)
    print(f"NEST {nest.__version__} · dt = {args.dt} ms · DA = {args.da} · "
          f"threads = {args.threads} · output: {out_dir}")

    all_spikes, all_metrics = [], []
    for seed in range(1, args.seeds + 1):
        t0 = time.time()
        spikes = run_one(seed, args.dt, args.threads, args.da)
        m = metrics(spikes)
        all_spikes.append(spikes)
        all_metrics.append(m)
        np.savez_compressed(os.path.join(out_dir, f"spikes_seed{seed}.npz"),
                            **{f"ch{ch}_{k}": v for ch, (t, s, n) in spikes.items()
                               for k, v in (("times", t), ("senders", s), ("n", n))})
        print(f"seed {seed:2d} ({time.time() - t0:5.1f} s): "
              f"sel {m['rate_steady_selected_Hz']:5.2f} Hz · non-sel {m['rate_steady_nonselected_Hz']:4.2f} Hz",
              flush=True)

    keys = list(all_metrics[0])
    summary = {k: {"mean": float(np.nanmean([m[k] for m in all_metrics])),
                   "sd": float(np.nanstd([m[k] for m in all_metrics]))} for k in keys}

    print(f"\nSummary over {args.seeds} seeds (mean ± sd)")
    print(f"{'metric':34} {'value':>18}   reference")
    for k in keys:
        ref = REFERENCE.get(k) or REFERENCE.get(k.replace("_selected", "").replace("_nonselected", ""), "")
        print(f"{k:34} {summary[k]['mean']:9.2f} ± {summary[k]['sd']:5.2f}   {ref}")

    with open(os.path.join(out_dir, "summary.json"), "w") as f:
        json.dump({"args": vars(args), "nest_version": nest.__version__,
                   "per_seed": all_metrics, "summary": summary}, f, indent=2)
    plot_mean_rates(all_spikes, os.path.join(out_dir, "mean_rates.png"))
    print(f"\nResults saved in {out_dir}/")


if __name__ == "__main__":
    main()
