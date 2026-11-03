#!/usr/bin/env python3
"""
compile_module.py — Compile nest_module/msn.nestml and install nestmlmodule into NEST.

Run it once after setting up the environment and again after every change to
msn.nestml. The other scripts only load the installed module (nest.Install).

Usage:
    conda run -n env_nest python compile_module.py
"""

import os
import shutil
import sys

from pynestml.frontend.pynestml_frontend import generate_nest_target

nestml_input = os.path.join(os.path.dirname(os.path.abspath(__file__)), "nest_module", "msn.nestml")
nestml_target = os.path.join(os.path.dirname(os.path.abspath(__file__)), "nest_module", "nestml_target")

# Start from a clean build directory
if os.path.exists(nestml_target):
    print(f"Cleaning old build dir: {nestml_target}")
    shutil.rmtree(nestml_target)

print(f"Input:  {nestml_input}")
print(f"Target: {nestml_target}")
print("Generating NEST target (this may take a minute)...")

try:
    generate_nest_target(
        input_path=nestml_input,
        target_path=nestml_target,
        logging_level="WARNING",
    )
    print("✓ NESTML compilation successful!")
except Exception as e:
    print(f"✗ NESTML compilation failed: {e}")
    print("\nFull traceback:")
    import traceback
    traceback.print_exc()
    sys.exit(1)
