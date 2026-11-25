"""Single MSN neuron: synaptic kernels (Eq. 10) and rheobase.

The measurements are the functions of analysis/single_neuron.py (the same ones that draw its
figures); here only the expected values are checked. Expected values: jump = w and decay time
constant = tau of the receptor (E002); rheobase on a 5-pA grid (E002, confirmed with the spike
at V_th = 40 mV on 2026-11-25).
"""
import numpy as np
import pytest

from single_neuron import CELLS, RECEPTORS, fi_curves, kernel_jump_and_tau, rheobase, spike_response

DT = 0.1


@pytest.mark.parametrize("cell", CELLS)
@pytest.mark.parametrize("name, rport, w, var, tau_key", RECEPTORS, ids=[r[0] for r in RECEPTORS])
def test_synaptic_jump_and_decay(cell, name, rport, w, var, tau_key):
    t, h, _, t_arr = spike_response(DT, cell, rport, w, var)
    tau = CELLS[cell][tau_key]
    _, jump_ok, tau_fit = kernel_jump_and_tau(t, h, w, tau, t_arr, DT)
    assert jump_ok
    assert tau_fit == pytest.approx(tau, rel=0.01)


@pytest.mark.parametrize("cell, da, expected_pA", [("D1", 0.0, 240.0), ("D2", 0.0, 240.0),
                                                   ("D1", 1.0, 280.0), ("D2", 1.0, 225.0)])
def test_rheobase(cell, da, expected_pA):
    currents = np.arange(0.0, 405.0, 5.0)
    rate = fi_curves(DT, [(cell, da)], currents)[(cell, da)]
    assert rheobase(currents, rate) == expected_pA
