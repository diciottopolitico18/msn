#!/usr/bin/env python3
"""Test NESTML compilation in isolation."""
import tempfile, os, shutil, sys

sys.stdout.flush()

from pynestml.frontend.pynestml_frontend import generate_nest_target

tmpdir = tempfile.mkdtemp()
target_dir = os.path.join(tmpdir, 'target')

input_path = os.path.join(os.path.dirname(__file__), 'nest_module', 'msn.nestml')
print(f'Input: {input_path}')
print(f'Target: {target_dir}')
sys.stdout.flush()

generate_nest_target(
    input_path=input_path,
    target_path=target_dir,
    logging_level='WARNING',
)

sys.stdout.flush()

# Check if the model C++ was generated
all_files = os.listdir(target_dir)
cpp_files = [f for f in all_files if f.endswith('.cpp')]
print(f'Generated C++ files: {cpp_files}')

if 'msn_neuron.cpp' in cpp_files:
    print('SUCCESS: msn_neuron.cpp was generated!')
else:
    print('FAILURE: msn_neuron.cpp was NOT generated')
    print(f'All files in target dir: {all_files}')

shutil.rmtree(tmpdir)
