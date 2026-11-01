# msn

Modello spiking di neuroni spinosi medi (MSN) dello striato con modulazione dopaminergica D1/D2, inibizione laterale e tre canali paralleli, in NEST/NESTML.
Punto di partenza: codice di E. Rusiecka (DTU, 2022), derivato da González-Redondo et al. (2020). Il codice originale è al tag `original`.
La pianificazione del lavoro è in [MSN code/ROADMAP.md](MSN%20code/ROADMAP.md).

## Versioni

| | Originale (2022) | Attuale |
|---|---|---|
| Python | 3.9 / 3.10 | 3.11 |
| NEST | 3.x | 3.8 |
| NESTML | 5.0.0-rc2 | 9.0.1 |

## Installazione

```bash
conda env create -f environment.yml
conda activate env_nest
```

## Esecuzione

```bash
cd "MSN code"
python run_simulation.py   # compila msn.nestml, esegue l'esperimento a rampa, salva la figura
```
