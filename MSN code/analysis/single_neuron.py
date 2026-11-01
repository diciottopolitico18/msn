#!/usr/bin/env python3
"""
Test del neurone MSN singolo (D1 e D2).

A) Risposta sinaptica: un singolo spike su AMPA, NMDA e GABA con i pesi del paper.
   Verifica che la variabile sinaptica h salti di w (Eq. 10) e decada con tau.
B) Curva f-I: frequenza di scarica contro corrente iniettata I_e, per vari livelli di DA.

Uso (dalla cartella "MSN code", con il modulo nestmlmodule già compilato):
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

# Pesi delle sinapsi come in msn.py (Tab. 2 e 3 del paper)
W_AMPA = 6.1 / params.neuron.msn_d1.tau_decay_AMPA
W_NMDA = 3.05 / params.neuron.msn_d1.tau_decay_NMDA
W_GABA = params.syn.msn_msn.syn_spec_random.weight

RECEPTORS = [  # nome, receptor_type, peso, variabile registrabile, parametro tau
    ("AMPA", 1, W_AMPA, "kernel_ampa__X__spikes_ampa", "tau_decay_AMPA"),
    ("NMDA", 2, W_NMDA, "kernel_nmda__X__spikes_nmda", "tau_decay_NMDA"),
    ("GABA", 3, W_GABA, "kernel_gaba__X__spikes_gaba", "tau_decay_GABA_A"),
]
CELLS = {"D1": params.neuron.msn_d1, "D2": params.neuron.msn_d2}


def reset_kernel(dt):
    nest.ResetKernel()  # in NEST 3.x scarica anche i moduli esterni
    nest.set_verbosity("M_ERROR")
    nest.Install("nestmlmodule")
    nest.resolution = dt
    nest.rng_seed = 1


def create_msn(cell_params, n=1, da=None):
    p = dict(cell_params)
    if da is not None:
        p["y1"] = da
        p["y2"] = da
    neurons = nest.Create("msn_neuron", n, params=p)
    neurons.V_m = cell_params["vp"]  # come in msn.py
    return neurons


# ----------------------------------------------------------------------------
# A) Risposta sinaptica
# ----------------------------------------------------------------------------
def synaptic_test(dt, out_dir):
    t_spike, delay, t_end = 200.0, 1.0, 1200.0
    rows = []
    fig, axes = plt.subplots(2, 3, figsize=(13, 6), sharex="col")

    for col, (name, rport, w, var, tau_key) in enumerate(RECEPTORS):
        for cell, cp in CELLS.items():
            reset_kernel(dt)
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

            # salto: il campione successivo all'arrivo vale tra w*exp(-dt/tau) e w
            h_max = h.max()
            jump_ok = w * np.exp(-1.01 * dt / tau) <= h_max <= w * (1 + 1e-9)

            # tau dalla pendenza di log(h) (non dipende dall'istante esatto del salto)
            mask = (t > t_arr + dt) & (h > h_max * 1e-3) & (t < t_arr + 3 * tau)
            slope = np.polyfit(t[mask], np.log(h[mask]), 1)[0]
            tau_fit = -1.0 / slope

            # PSP: variazione di V_m rispetto al valore appena prima dello spike
            v0 = v[np.searchsorted(t, t_arr) - 1]
            dv = v - v0
            psp = dv[np.argmax(np.abs(dv[t >= t_arr])) + np.searchsorted(t, t_arr)]

            rows.append((name, cell, w, h_max, jump_ok, tau, tau_fit, psp))

            sel = (t > t_arr - 10) & (t < t_arr + min(5 * tau, 900))
            axes[0, col].plot(t[sel] - t_arr, h[sel], label=cell)
            axes[1, col].plot(t[sel] - t_arr, dv[sel], label=cell)

        axes[0, col].set_title(f"{name}  (w = {w:.4g})")
        axes[0, col].axhline(w, color="gray", ls=":", lw=1)
        axes[1, col].set_xlabel("tempo dall'arrivo dello spike (ms)")
        axes[0, col].legend()

    axes[0, 0].set_ylabel("h  (g = h · 1 nS)")
    axes[1, 0].set_ylabel("ΔV_m (mV)")
    fig.suptitle(f"Risposta a un singolo spike — dt = {dt} ms")
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, "A_risposta_sinaptica.png"), dpi=150)
    plt.close(fig)

    print("\nA) Risposta sinaptica (un singolo spike)")
    print(f"{'rec':5} {'cell':4} {'w':>9} {'h_max':>9} {'salto':>6} {'tau':>7} {'tau_fit':>8} {'PSP (mV)':>9}")
    for name, cell, w, h_max, ok, tau, tau_fit, psp in rows:
        print(f"{name:5} {cell:4} {w:9.5f} {h_max:9.5f} {'OK' if ok else 'NO':>6} "
              f"{tau:7.1f} {tau_fit:8.2f} {psp:9.4f}")
    all_ok = all(r[4] for r in rows) and all(abs(r[6] - r[5]) / r[5] < 0.01 for r in rows)
    print("Esito A:", "SUPERATO" if all_ok else "NON SUPERATO")
    return all_ok


# ----------------------------------------------------------------------------
# B) Curva f-I
# ----------------------------------------------------------------------------
def fi_test(dt, out_dir, da_levels=(0.0, 0.3, 0.6, 1.0), i_max=600.0, i_step=5.0,
            t_settle=300.0, t_meas=1000.0):
    currents = np.arange(0.0, i_max + i_step, i_step)
    reset_kernel(dt)

    groups = {}
    for cell, cp in CELLS.items():
        for da in da_levels:
            n = create_msn(cp, len(currents), da=da)
            n.I_e = currents
            sr = nest.Create("spike_recorder", params={"start": t_settle})
            nest.Connect(n, sr)
            groups[(cell, da)] = (n, sr)

    nest.Simulate(t_settle + t_meas)

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5), sharey=True)
    print("\nB) Curva f-I  (rate in Hz su %.0f ms dopo %.0f ms di assestamento)" % (t_meas, t_settle))
    print(f"{'cell':4} {'DA':>4} {'reobase (pA)':>13} {'f@300pA':>8} {'f@400pA':>8} {'f@600pA':>8}")
    results = {}
    for ax, cell in zip(axes, CELLS):
        for da in da_levels:
            n, sr = groups[(cell, da)]
            senders = sr.events["senders"]
            first = n.global_id if len(n) == 1 else n[0].global_id
            counts = np.bincount(senders - first, minlength=len(n))
            rate = counts / (t_meas / 1000.0)
            results[(cell, da)] = rate
            ax.plot(currents, rate, label=f"DA = {da}")
            idx = np.nonzero(rate > 0)[0]
            rheo = currents[idx[0]] if len(idx) else np.nan
            f_at = lambda i: rate[np.argmin(np.abs(currents - i))]
            print(f"{cell:4} {da:4.1f} {rheo:13.0f} {f_at(300):8.1f} {f_at(400):8.1f} {f_at(600):8.1f}")
        ax.set_title(f"MSN {cell}")
        ax.set_xlabel("I_e (pA)")
        ax.legend()
    axes[0].set_ylabel("frequenza (Hz)")
    fig.suptitle(f"Curva f–I — dt = {dt} ms")
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, "B_curva_fI.png"), dpi=150)
    plt.close(fig)

    np.savez(os.path.join(out_dir, "B_curva_fI.npz"), currents=currents,
             **{f"{c}_DA{d}": r for (c, d), r in results.items()})
    return results


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dt", type=float, default=0.1, help="risoluzione della simulazione in ms (default 0.1)")
    ap.add_argument("--out", default="results/single_neuron", help="cartella di output")
    args = ap.parse_args()

    out_dir = os.path.join(args.out, f"dt{args.dt}")
    os.makedirs(out_dir, exist_ok=True)

    print(f"NEST {nest.__version__} · dt = {args.dt} ms · output: {out_dir}")

    synaptic_test(args.dt, out_dir)
    fi_test(args.dt, out_dir)
    print(f"\nFigure salvate in {out_dir}/")


if __name__ == "__main__":
    main()
