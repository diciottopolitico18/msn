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

```bash
cd "MSN code"
python run_simulation.py           # compiles msn.nestml, runs the ramp experiment, saves the figure
python analysis/single_neuron.py   # single-neuron tests: synaptic response and D1/D2 f-I curves
```
