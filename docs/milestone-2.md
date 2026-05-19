# Milestone 2: FINESSE-only visibility engine

Delivered scope from [BLUEPRINT.md](../BLUEPRINT.md) Milestone 2.

## Deliverables

| Item | Location |
|------|----------|
| FINESSE 3 runner | `src/optical_truss_ifo_sim/finesse_runner.py` |
| Kat template | `finesse/templates/cavity_scan.kat.j2` |
| Reference cavity | `finesse/models/test_cavity.kat` |
| Validation config | `configs/finesse_validation.yaml` |
| Reference beam table | `tests/reference_data/beam_states_nominal.csv` |
| CLI `finesse-run` | `src/optical_truss_ifo_sim/cli.py` |
| Tests | `tests/test_finesse_runner.py`, `tests/test_finesse_import.py` |
| Interface docs | `docs/finesse_interface.md`, `docs/validation.md` |
| Demo notebook | `notebooks/01_validate_nominal_design.ipynb` |

## Prerequisites

```bash
conda install -c conda-forge finesse
pip install -e ".[dev]"
```

Verify:

```bash
.venv/bin/python -c "from optical_truss_ifo_sim.finesse_runner import finesse_available; print(finesse_available())"
.venv/bin/python -m pytest tests/test_finesse_import.py tests/test_visibility.py -q
```

With FINESSE installed:

```bash
.venv/bin/python -m pytest tests/test_finesse_runner.py -q
oti-pipeline finesse-run tests/reference_data/beam_states_nominal.csv configs/finesse_validation.yaml
```

## Workflow

1. Define beam states manually (CSV/Parquet) or, in later milestones, export from Zemax.
2. Render `cavity_scan.kat.j2` per sample with waists, steering tilts, and detuning grid.
3. Run FINESSE `xaxis(L0.f, …)` and read reflected power `pd refl`.
4. Compute $V_{00} = (P_{\max} - P_{\min}) / (P_{\max} + P_{\min})$ via `visibility.py`.

## Demo notebook

Open `notebooks/01_validate_nominal_design.ipynb` for an interactive nominal scan, visibility
extraction, and comparison of offset / angle / waist-mismatch cases.

## Next milestone

**Milestone 3** — ZOSPy connection, nominal Zemax model, and beam-state export into the
same `BeamState` schema.
