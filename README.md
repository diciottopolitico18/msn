# msn

Spiking model of striatal medium spiny neurons (MSNs) with D1/D2 dopaminergic modulation, lateral inhibition and three parallel channels, implemented in NEST/NESTML.
Starting point: code by E. Rusiecka (DTU, 2022), derived from González-Redondo et al. (2020). The original code is available at the `original` tag.

## Versions

| | Original (2022) | Current |
|---|---|---|
| Python | 3.9 / 3.10 | 3.11 |
| NEST | 3.x | 3.8 |
| NESTML | 5.0.0-rc2 | 9.0.1 |

## Installation

```bash
conda env create -f environment.yml
conda activate env_nest
```

## Usage

All commands run from the code folder, with the environment active:

```bash
conda activate env_nest
cd "MSN code"
python compile_module.py                 # compile msn.nestml and install it in NEST (once, and after every change to it)
python run_simulation.py                 # one run of the ramp experiment + figures (options: --dt --seed --threads --da)
python analysis/network_validation.py    # 10 seeds, mean ± sd of rates and selectivity (options: --seeds --dt --threads --da --out)
python analysis/single_neuron.py         # single neuron: synaptic response and D1/D2 f-I curves (figures)
```

The ramp protocol (rates and durations) is in `msn_params.py`, section `params.exp`.

## Tests

The tests check the single neuron (synaptic kernels, rheobase) and the network baseline in `analysis/reference/baseline_v2/`.

```bash
pytest                    # fast tests (~10 s); the slow one is skipped
pytest --full             # also the slow test: 10 seeds with 4 threads, means within a tolerance (~80 s)
pytest -v                 # one line per test, PASSED / FAILED
pytest -rs                # show why a test was skipped
pytest -k rheobase        # only the tests whose name contains "rheobase"
python analysis/check_baseline.py   # full seed-by-seed regression check (10 seeds, ~45 s): IDENTICAL or the list of differences
```

Run `pytest` after every code change and after recompiling `msn.nestml`. A change that is not meant to alter the results must also give `IDENTICAL` with `check_baseline.py`.

Code of the original model that is not used, or does not run with NEST 3.8, is kept unchanged in `MSN code/legacy/` (not imported by anything).
