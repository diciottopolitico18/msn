#!/usr/bin/env python3
"""
Single MSN neuron test (D1 and D2).

A) Synaptic response: one spike on AMPA, NMDA and GABA with the paper's weights.
   Checks that the synaptic variable h jumps by w (Eq. 10) and decays with tau.
B) f-I curve: firing rate vs injected current I_e, for several DA levels.

Usage (from the "MSN code" folder, with nestmlmodule already compiled):
    python analysis/single_neuron.py [--dt 0.1] [--out results/single_neuron]
"""

import argparse
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import nest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from msn_params import params  # noqa: E402
from utils.kernel import setup_kernel  # noqa: E402

# Synaptic weights used by msn.py (paper, Tables 2 and 3)
SYN_AMPA = params.syn.ctx_msn.syn_spec_ampa
SYN_NMDA = params.syn.ctx_msn.syn_spec_nmda
SYN_GABA = params.syn.msn_msn.syn_spec_random

RECEPTORS = [  # name, receptor_type, weight, recordable variable, tau parameter
    ("AMPA", SYN_AMPA.receptor_type, SYN_AMPA.weight, "kernel_ampa__X__spikes_ampa", "tau_decay_AMPA"),
    ("NMDA", SYN_NMDA.receptor_type, SYN_NMDA.weight, "kernel_nmda__X__spikes_nmda", "tau_decay_NMDA"),
    ("GABA", SYN_GABA.receptor_type, SYN_GABA.weight, "kernel_gaba__X__spikes_gaba", "tau_decay_GABA_A"),
]
CELLS = {"D1": params.neuron.msn_d1, "D2": params.neuron.msn_d2}


def create_msn(cell_params, n=1, da=None):
    p = dict(cell_params)
    if da is not None:
        p["phi_1"] = da
        p["phi_2"] = da
    neurons = nest.Create("msn_neuron", n, params=p)
    neurons.V_m = cell_params["vp"]  # same initial condition as msn.py
    return neurons


# ----------------------------------------------------------------------------
# A) Synaptic response
# ----------------------------------------------------------------------------
def synaptic_test(dt, out_dir):
    t_spike, delay, t_end = 200.0, 1.0, 1200.0
    rows = []
    fig, axes = plt.subplots(2, 3, figsize=(14, 8), sharex="col")

    for col, (name, rport, w, var, tau_key) in enumerate(RECEPTORS):
        taus = {}
        for cell, cp in CELLS.items():
            setup_kernel(dt=dt)
            n = create_msn(cp)
            sg = nest.Create("spike_generator", params={"spike_times": [t_spike]})
            nest.Connect(sg, n, syn_spec={"weight": w, "delay": delay, "receptor_type": rport})
            mm = nest.Create("multimeter", params={"record_from": [var, "V_m"], "interval": dt})
            nest.Connect(mm, n)
            nest.Simulate(t_end)

            ev = mm.events
            t, h, v = ev["times"], ev[var], ev["V_m"]
            tau = cp[tau_key]
            t_arr = t_spike + delay

            # jump: the first sample after arrival lies between w*exp(-dt/tau) and w
            h_max = h.max()
            jump_ok = w * np.exp(-1.01 * dt / tau) <= h_max <= w * (1 + 1e-9)

            # tau from the slope of log(h) (independent of the exact jump time)
            mask = (t > t_arr + dt) & (h > h_max * 1e-3) & (t < t_arr + 3 * tau)
            slope = np.polyfit(t[mask], np.log(h[mask]), 1)[0]
            tau_fit = -1.0 / slope

            # PSP: change of V_m relative to the value just before the spike
            v0 = v[np.searchsorted(t, t_arr) - 1]
            dv = v - v0
            psp = dv[np.argmax(np.abs(dv[t >= t_arr])) + np.searchsorted(t, t_arr)]

            rows.append((name, cell, w, h_max, jump_ok, tau, tau_fit, psp))

            sel = (t > t_arr - 10) & (t < t_arr + min(5 * tau, 900))
            line, = axes[0, col].plot(t[sel] - t_arr, h[sel], label=cell)
            axes[1, col].plot(t[sel] - t_arr, dv[sel], label=cell)
            # mark t = tau, where h has decayed to w/e (about 37 % of the peak)
            axes[0, col].plot([tau, tau], [0, w / np.e], color=line.get_color(), ls="--", lw=1)
            axes[0, col].plot(tau, w / np.e, "o", color=line.get_color(), ms=4)
            taus[cell] = tau

        if len(set(taus.values())) == 1:
            tau_txt = f"τ = {taus['D1']:g} ms"
        else:
            tau_txt = "τ = " + " / ".join(f"{v:g} ms ({c})" for c, v in taus.items())
        axes[0, col].set_title(f"{name}\nw = {w:.4g} nS, {tau_txt}")
        axes[0, col].axhline(w, color="gray", ls=":", lw=1)
        axes[1, col].set_xlabel("time from spike arrival (ms)")
        axes[0, col].tick_params(labelbottom=True)  # sharex hides the numbers on the top row

    for ax in axes.flat:
        ax.grid(True, alpha=0.3)
    axes[0, 0].set_ylabel("conductance h (nS)")
    axes[1, 0].set_ylabel("ΔV_m (mV)")
    fig.suptitle("Response to a single spike: exponential decay of the synaptic "
                 "conductance (top) and PSP (bottom)\n"
                 f"dt = {dt} ms, DA = {CELLS['D1']['phi_1']}")
    # one legend for all six panels, below the title: cells + markers of the top row
    handles, labels = axes[0, 0].get_legend_handles_labels()
    handles += [plt.Line2D([], [], color="gray", ls=":", lw=1),
                plt.Line2D([], [], color="black", ls="--", lw=1, marker="o", ms=4)]
    labels += ["peak w (top row)", "t = τ, where h = w/e ≈ 0.37 w (top row)"]
    fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, 0.915),
               ncol=len(labels), frameon=False)
    fig.tight_layout()
    fig.subplots_adjust(top=0.80, hspace=0.3)  # room for title and legend
    fig.savefig(os.path.join(out_dir, "A_synaptic_response.png"), dpi=150)
    plt.close(fig)

    print("\nA) Synaptic response (single spike)")
    print(f"{'rec':5} {'cell':4} {'w':>9} {'h_max':>9} {'jump':>6} {'tau':>7} {'tau_fit':>8} {'PSP (mV)':>9}")
    for name, cell, w, h_max, ok, tau, tau_fit, psp in rows:
        print(f"{name:5} {cell:4} {w:9.5f} {h_max:9.5f} {'OK' if ok else 'FAIL':>6} "
              f"{tau:7.1f} {tau_fit:8.2f} {psp:9.4f}")
    all_ok = all(r[4] for r in rows) and all(abs(r[6] - r[5]) / r[5] < 0.01 for r in rows)
    print("Result A:", "PASSED" if all_ok else "FAILED")
    return all_ok


# ----------------------------------------------------------------------------
# B) f-I curve
# ----------------------------------------------------------------------------
def fi_test(dt, out_dir, da_levels=(0.0, 0.3, 0.6, 1.0), i_max=600.0, i_step=5.0,
            t_settle=300.0, t_meas=1000.0):
    currents = np.arange(0.0, i_max + i_step, i_step)
    setup_kernel(dt=dt)

    groups = {}
    for cell, cp in CELLS.items():
        for da in da_levels:
            n = create_msn(cp, len(currents), da=da)
            n.I_e = currents
            sr = nest.Create("spike_recorder", params={"start": t_settle})
            nest.Connect(n, sr)
            groups[(cell, da)] = (n, sr)

    nest.Simulate(t_settle + t_meas)

    fig, axes = plt.subplots(1, 2, figsize=(12, 5.5), sharey=True)
    # DA is ordered: light gray (DA = 0) -> black (DA = 1)
    colors = plt.cm.Greys(np.linspace(0.4, 1.0, len(da_levels)))
    da_effect = {"D1": "DA acts on v_r (resting potential)\n"
                       "and d (after-spike reset of the recovery variable u)",
                 "D2": "DA acts on k (gain of the quadratic term,\n"
                       "i.e. how fast V_m accelerates towards the spike)"}
    zoom_i, zoom_f = (200.0, 320.0), (-1.0, 20.0)   # region around the rheobase
    print("\nB) f-I curve  (rate in Hz over %.0f ms after %.0f ms of settling)" % (t_meas, t_settle))
    print(f"{'cell':4} {'DA':>4} {'rheobase (pA)':>14} {'f@300pA':>8} {'f@400pA':>8} {'f@600pA':>8}")
    results = {}
    for ax, cell in zip(axes, CELLS):
        # D2 curves leave the upper-left corner empty: legend on the right, bigger zoom
        inset_box = [0.07, 0.30, 0.40, 0.38] if cell == "D1" else [0.08, 0.40, 0.50, 0.50]
        inset = ax.inset_axes(inset_box)
        for da, color in zip(da_levels, colors):
            n, sr = groups[(cell, da)]
            senders = sr.events["senders"]
            first = n.global_id if len(n) == 1 else n[0].global_id
            counts = np.bincount(senders - first, minlength=len(n))
            rate = counts / (t_meas / 1000.0)
            results[(cell, da)] = rate
            idx = np.nonzero(rate > 0)[0]
            rheo = currents[idx[0]] if len(idx) else np.nan
            for a in (ax, inset):
                a.plot(currents, rate, color=color, label=f"DA = {da}  (rheobase {rheo:.0f} pA)")
                # rheobase marker: first current that produces spikes
                a.plot(rheo, rate[idx[0]], "o", color=color, ms=5, zorder=3)
            f_at = lambda i: rate[np.argmin(np.abs(currents - i))]
            print(f"{cell:4} {da:4.1f} {rheo:14.0f} {f_at(300):8.1f} {f_at(400):8.1f} {f_at(600):8.1f}")
        ax.set_title(f"MSN {cell}", fontsize=12, pad=34)
        ax.text(0.5, 1.01, da_effect[cell], transform=ax.transAxes, ha="center",
                va="bottom", fontsize=9, style="italic")
        ax.set_xlabel("injected current I_e (pA)")
        ax.grid(True, alpha=0.3)
        ax.legend(loc="upper left" if cell == "D1" else "upper right", fontsize=8)
        inset.set_xlim(*zoom_i)
        inset.set_ylim(*zoom_f)
        inset.set_yticks(np.arange(0, zoom_f[1] + 1, 5))
        inset.grid(True, alpha=0.3)
        inset.tick_params(labelsize=7)
        inset.set_title("zoom on the rheobase", fontsize=8)
        ax.indicate_inset_zoom(inset, edgecolor="gray")
    axes[0].set_ylabel("firing rate (Hz)")
    fig.suptitle("f–I curve: firing rate vs injected current at different dopamine levels\n"
                 "each point: one neuron with a constant injected current, steady-state firing rate\n"
                 f"integration step dt = {dt} ms",
                 fontsize=12)
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, "B_fI_curve.png"), dpi=150)
    plt.close(fig)

    np.savez(os.path.join(out_dir, "B_fI_curve.npz"), currents=currents,
             **{f"{c}_DA{d}": r for (c, d), r in results.items()})
    return results


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dt", type=float, default=params.sim.step, help="simulation resolution in ms")
    ap.add_argument("--out", default="results/single_neuron", help="output folder")
    args = ap.parse_args()

    out_dir = os.path.join(args.out, f"dt{args.dt}")
    os.makedirs(out_dir, exist_ok=True)

    print(f"NEST {nest.__version__} · dt = {args.dt} ms · output: {out_dir}")

    synaptic_test(args.dt, out_dir)
    fi_test(args.dt, out_dir)
    print(f"\nFigures saved in {out_dir}/")


if __name__ == "__main__":
    main()
