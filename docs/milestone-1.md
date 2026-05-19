# Milestone 1: Skeleton repository

This document records what was delivered for [BLUEPRINT.md](../BLUEPRINT.md) Milestone 1
and how to use it.

## Deliverables

| Item | Location |
|------|----------|
| Python package | `src/optical_truss_ifo_sim/` (`import optical_truss_ifo_sim`) |
| Project metadata and CLI entry point | `pyproject.toml` → `oti-pipeline` |
| Configuration YAML | `configs/*.yaml` with `includes` merging |
| Configuration schema | `schemas.py`, loader in `config.py` |
| CLI skeleton | `cli.py` — `validate-config` fully wired; other commands exit with code 2 |
| Placeholder FINESSE models | `finesse/models/*.kat`, `finesse/templates/cavity_scan.kat.j2` |
| Visibility extraction | `visibility.py` — $V_{00}$ from detuning scans |
| Unit tests | `tests/test_config.py`, `tests/test_beam_schema.py`, `tests/test_visibility.py` |
| Coordinate conventions | `docs/coordinate_conventions.md` |

Stub modules (`zemax_api`, `finesse_runner`, `monte_carlo`, …) exist as package
placeholders for later milestones.

## Setup

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Install **FINESSE 3** and **ZOSPy** in the same venv when you reach Milestones 2–3
(see `AGENTS.md`). Milestone 1 tests do not require them.

Verify the environment:

```bash
.venv/bin/python -m pytest
oti-pipeline validate-config configs/monte_carlo.yaml
oti-pipeline --version
```

## Configuration

- **`configs/nominal.yaml`** — run metadata and Zemax paths.
- **`configs/finesse.yaml`** — detuning grid and placeholder `.kat` path.
- **`configs/compensation.yaml`** — collimator compensation bounds.
- **`configs/tolerances.yaml`** — tolerance parameter definitions.
- **`configs/monte_carlo.yaml`** — merges the above via `includes` and sets campaign defaults.

`oti-pipeline validate-config <path>` loads YAML, resolves `includes`, validates with
Pydantic, and prints a summary table.

## Visibility

`compute_visibility_00(detuning_hz, reflected_power)` implements BLUEPRINT section 9:

1. Estimate $P_{\max}$ from edge-sample medians.
2. Take $P_{\min}$ as the scan minimum.
3. Compute $V_{00} = (P_{\max} - P_{\min}) / (P_{\max} + P_{\min})$.
4. Attach QC flags when the resonance is missing, the baseline is unstable, etc.

## CLI commands (Milestone 1)

| Command | Status |
|---------|--------|
| `validate-config` | Implemented |
| `zemax-export` | Skeleton (exit 2) |
| `finesse-run` | Implemented in Milestone 2 |
| `analyze` | Skeleton (exit 2) |
| `run-full` | Skeleton (exit 2) |
| `make-report` | Skeleton (exit 2) |

## Next milestone

**Milestone 2** — FINESSE-only visibility engine: runnable `.kat` model, cavity runner,
manual beam injection, and physics regression tests against reference cases.
