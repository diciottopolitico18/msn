"""Network baseline (DA 0.3, dt 0.1 ms) against analysis/reference/baseline_v2.

- fast: seeds 1-2 at 8 threads must be identical, value by value, to the reference;
- slow (pytest --full): seeds 1-10 at 4 threads. Other thread counts give different spikes, so
  only the means are compared, with a tolerance.
"""
import json
import os

import numpy as np
import pytest

from metrics import metrics
from network_validation import run_one

REF = json.load(open(os.path.join(os.path.dirname(__file__), "..", "analysis", "reference",
                                  "baseline_v2", "summary.json")))
# chosen 2026-11-25: about 5 sd of the seed-to-seed spread (0.06 / 0.05 Hz), loose enough for
# another thread count, tight enough to catch a real model change (e.g. beta split: -0.45 / +0.43 Hz)
TOL_HZ = {"rate_steady_selected_Hz": 0.3, "rate_steady_nonselected_Hz": 0.15}


@pytest.mark.parametrize("seed", [1, 2])
def test_baseline_exact(seed):
    m = metrics(run_one(seed, 0.1, 8, 0.3))
    ref = REF["per_seed"][seed - 1]
    for k, v in ref.items():
        assert m[k] == v or (np.isnan(m[k]) and np.isnan(v)), k


@pytest.mark.slow
def test_baseline_mean_other_threads():
    runs = [metrics(run_one(seed, 0.1, 4, 0.3)) for seed in range(1, 11)]
    for k, tol in TOL_HZ.items():
        mean = np.mean([m[k] for m in runs])
        assert mean == pytest.approx(REF["summary"][k]["mean"], abs=tol), (k, mean)
