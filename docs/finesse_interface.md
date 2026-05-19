# FINESSE interface

This document describes how the OTI pipeline uses [FINESSE 3](https://finesse.ifosim.org/)
for Fabry–Perot cavity modelling and TEM00 visibility extraction (Milestone 2).

## Installation

FINESSE 3 is distributed on **conda-forge**, not PyPI:

```bash
conda install -c conda-forge finesse
```

Install into the same environment as this project (or export that env’s Python into
`.venv` per your site policy). The runner checks importability with
`optical_truss_ifo_sim.finesse_runner.finesse_available()`.

### Namespace clash with `finesse/models/`

This repository stores Kat files under `finesse/models/`. If the current working
directory is the repo root, Python may import that folder instead of the FINESSE
library. The runner’s `_import_finesse()` filters `sys.path` to avoid that shadow.
Prefer running scripts with `src/` on `PYTHONPATH` only (as pytest does), or call
the public API which performs the scrub before import.

## Model structure

| Artifact | Purpose |
|----------|---------|
| `finesse/templates/cavity_scan.kat.j2` | Jinja2 template rendered per beam state |
| `finesse/models/test_cavity.kat` | Static reference model (same geometry) |
| `finesse/models/oti_cavity.kat` | Production cavity (future milestones) |

The test cavity is a two-mirror Fabry–Perot resonator with:

- Input steering mirror `m_steer` (maps beam offset/angle to `xbeta`/`ybeta`)
- High-reflectivity mirrors `m1`, `m2` with radius of curvature ±0.5 m
- Cavity length 0.1 m
- Reflected-power detector `pd refl` on the input port
- Hermite–Gaussian basis `modes(maxtem=…)` from configuration

Laser frequency is swept with `xaxis(L0.f, lin, …)` over the detuning grid defined
in `configs/finesse.yaml`.

## Beam-state injection

Each row of the beam-state table (`BeamState` in `schemas.py`) supplies SI parameters
at the cavity input reference plane (see `docs/coordinate_conventions.md`):

- Waists `wx_m`, `wy_m` and waist positions `zx_m`, `zy_m` → `gauss` at the laser node
- Lateral offsets and propagation angles → steering mirror tilts:

  - `xbeta ≈ x_angle_rad / 2 + x_offset_m / (2 * steer_arm_m)` (and similarly for *y*)

This is a compact single-mirror steerer one `steer_arm_m` (default 10 mm) before the
input mirror. It is adequate for Milestone 2 sensitivity checks; paired-mirror steering
may replace it when Zemax handoff validation requires independent actuator control.

## Python API

```python
from optical_truss_ifo_sim.config import load_config, resolve_repo_paths
from optical_truss_ifo_sim.finesse_runner import load_beam_states, run_cavity_scan

repo = Path(".")
cfg = resolve_repo_paths(load_config("configs/finesse_validation.yaml", repo_root=repo), repo)
beam = load_beam_states("tests/reference_data/beam_states_nominal.csv")[0]
result = run_cavity_scan(beam, cfg.finesse)
print(result.v_00, result.status)
```

`run_cavity_scan` returns `FinesseScanResult` with detuning trace, `VisibilityResult`,
and `SampleStatus` (`OK`, `FINESSE_FAILED`, `QC_FAILED`, …).

## CLI

```bash
oti-pipeline finesse-run tests/reference_data/beam_states_nominal.csv \
  configs/finesse_validation.yaml
```

Writes `finesse_results.csv` under the run `output_dir` (override with `--output`).

## Visibility extraction

Reflected power versus laser detuning is passed to `visibility.compute_visibility_00`
(BLUEPRINT section 9). Quality-control flags cover missing resonances, unstable
baselines, and out-of-range visibility.
