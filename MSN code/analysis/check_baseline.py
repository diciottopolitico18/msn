"""One-command regression check against baseline v2 (betas split by population, spike cutoff at V_th = 40 mV; v0 and v1 kept in reference/).

Usage (from the code folder, in env_nest): python analysis/check_baseline.py

Runs network_validation.py with the baseline conditions (dt 0.1 ms, seeds 1-10,
8 threads, DA 0.3; ~45 s) and compares the result seed by seed with
analysis/reference/baseline_v2/summary.json.
Prints IDENTICAL (exit code 0) or the differing values (exit code 1).
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CODE_DIR = os.path.dirname(HERE)
REFERENCE = os.path.join(HERE, "reference", "baseline_v2")
OUT = os.path.join("results", "_check")
RUN_DIR = os.path.join(OUT, "dt0.1_da0.3_seeds10_thr8")  # folder name built by network_validation.py

# explicit conditions: the check must not follow a change of the defaults in msn_params.py
subprocess.run([sys.executable, os.path.join(HERE, "network_validation.py"), "--seeds", "10", "--dt", "0.1",
                "--threads", "8", "--da", "0.3", "--out", OUT], cwd=CODE_DIR, check=True, stdout=subprocess.DEVNULL)
sys.exit(subprocess.run([sys.executable, os.path.join(HERE, "compare_runs.py"), REFERENCE, RUN_DIR],
                        cwd=CODE_DIR).returncode)
