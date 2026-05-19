# optical-truss-ifo-sim

Reproducible tolerance simulation for a compact fiber-injected Optical Truss
Interferometer (OTI) Fabry–Perot cavity. Zemax OpticStudio (via ZOSPy) exports Gaussian
beam states; FINESSE 3 models the cavity and TEM00 visibility $V_{00}$.

Design and roadmap: [BLUEPRINT.md](BLUEPRINT.md).

## Status

**Milestone 2 (FINESSE visibility engine)** is implemented: cavity runner, manual beam
injection, detuning scans, $V_{00}$ extraction, `finesse-run` CLI, validation tests, and
demo notebook. See [docs/milestone-2.md](docs/milestone-2.md).

**Milestone 1 (skeleton)** — [docs/milestone-1.md](docs/milestone-1.md).

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

python -m pytest
oti-pipeline validate-config configs/monte_carlo.yaml
```

Use `.venv/bin/python` and `.venv/bin/pip` if you prefer not to activate the venv
(see [AGENTS.md](AGENTS.md)).

Install **FINESSE 3** for cavity simulations (`conda install -c conda-forge finesse`).
Unit tests that do not call FINESSE still pass without it. Install **zospy** for Zemax
export (Milestone 3+).

## Repository layout

```text
configs/           YAML run and tolerance configuration
finesse/           FINESSE .kat models and Jinja templates
notebooks/         Demo notebooks (start with 01_validate_nominal_design.ipynb)
src/optical_truss_ifo_sim/   Python package (`import optical_truss_ifo_sim`)
tests/             pytest suite
docs/              Conventions, FINESSE interface, milestone notes
```

### FINESSE quick check

```bash
oti-pipeline finesse-run tests/reference_data/beam_states_nominal.csv \
  configs/finesse_validation.yaml
```

## License

Proprietary — internal OTI simulation project.
