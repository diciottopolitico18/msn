"""Seed-by-seed comparison of two network_validation.py runs.

Usage: python analysis/compare_runs.py <run_dir_a> <run_dir_b>

Each folder must contain the summary.json written by network_validation.py.
Prints IDENTICAL (exit code 0) or the list of differing values (exit code 1).
"""
import json
import math
import os
import sys


def load(run_dir):
    with open(os.path.join(run_dir, "summary.json")) as f:
        return json.load(f)


def differences(a, b):
    """List of (seed, metric, value_a, value_b) for every metric that is not exactly equal."""
    diffs = []
    if len(a) != len(b):
        diffs.append(("-", "number_of_seeds", len(a), len(b)))
    for seed, (ma, mb) in enumerate(zip(a, b), start=1):
        for key in sorted(set(ma) | set(mb)):
            va, vb = ma.get(key), mb.get(key)
            both_nan = isinstance(va, float) and isinstance(vb, float) and math.isnan(va) and math.isnan(vb)
            if va != vb and not both_nan:
                diffs.append((seed, key, va, vb))
    return diffs


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    a, b = load(sys.argv[1]), load(sys.argv[2])

    # seeds, dt, threads and DA must match for the comparison to mean anything
    for key in ("seeds", "dt", "threads", "da"):
        if a["args"].get(key) != b["args"].get(key):
            print(f"note: runs differ in --{key}: {a['args'].get(key)} vs {b['args'].get(key)}")

    diffs = differences(a["per_seed"], b["per_seed"])
    if not diffs:
        print(f"IDENTICAL ({len(a['per_seed'])} seeds, {len(a['per_seed'][0])} metrics each)")
        return
    for seed, key, va, vb in diffs:
        print(f"seed {seed}: {key}: {va} != {vb}")
    seeds = {d[0] for d in diffs}
    sys.exit(f"DIFFERENT: {len(diffs)} values in {len(seeds)} seeds")


if __name__ == "__main__":
    # self-check: equal runs give no differences, NaN equals NaN, a changed value is reported
    nan = float("nan")
    assert differences([{"x": 1.0, "y": nan}], [{"x": 1.0, "y": nan}]) == []
    assert differences([{"x": 1.0}], [{"x": 1.5}]) == [(1, "x", 1.0, 1.5)]
    main()
