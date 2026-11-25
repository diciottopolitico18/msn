"""Single MSN neuron: synaptic kernels (Eq. 10) and rheobase.

Expected values: jump = w and decay time constant = tau of the receptor (single_neuron.py,
E002); rheobase measured with injected current on a 5-pA grid (E002, confirmed with the spike
at V_th = 40 mV on 2026-11-25).
"""
import numpy as np
import nest
import pytest

from single_neuron import CELLS, RECEPTORS, create_msn
from utils.kernel import setup_kernel

DT = 0.1


@pytest.mark.parametrize("cell", CELLS)
@pytest.mark.parametrize("name, rport, w, var, tau_key", RECEPTORS, ids=[r[0] for r in RECEPTORS])
def test_synaptic_jump_and_decay(cell, name, rport, w, var, tau_key):
    t_spike, delay = 200.0, 1.0
    setup_kernel(dt=DT)
    n = create_msn(CELLS[cell])
    sg = nest.Create("spike_generator", params={"spike_times": [t_spike]})
    nest.Connect(sg, n, syn_spec={"weight": w, "delay": delay, "receptor_type": rport})
    mm = nest.Create("multimeter", params={"record_from": [var], "interval": DT})
    nest.Connect(mm, n)
    nest.Simulate(1200.0)

    t, h = mm.events["times"], mm.events[var]
    tau, t_arr = CELLS[cell][tau_key], t_spike + delay
    # the first sample after arrival lies between w*exp(-dt/tau) and w
    assert w * np.exp(-1.01 * DT / tau) <= h.max() <= w * (1 + 1e-9)
    mask = (t > t_arr + DT) & (h > h.max() * 1e-3) & (t < t_arr + 3 * tau)
    tau_fit = -1.0 / np.polyfit(t[mask], np.log(h[mask]), 1)[0]
    assert tau_fit == pytest.approx(tau, rel=0.01)


@pytest.mark.parametrize("cell, da, expected_pA", [("D1", 0.0, 240.0), ("D2", 0.0, 240.0),
                                                   ("D1", 1.0, 280.0), ("D2", 1.0, 225.0)])
def test_rheobase(cell, da, expected_pA):
    currents = np.arange(0.0, 405.0, 5.0)
    setup_kernel(dt=DT)
    n = create_msn(CELLS[cell], len(currents), da=da)
    n.I_e = currents
    sr = nest.Create("spike_recorder", params={"start": 300.0})
    nest.Connect(n, sr)
    nest.Simulate(1300.0)
    counts = np.bincount(np.asarray(sr.events["senders"]) - n.tolist()[0], minlength=len(currents))
    assert currents[np.nonzero(counts)[0][0]] == expected_pA
