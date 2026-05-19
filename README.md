# optical-truss-ifo-sim

Reproducible tolerance simulation for a compact fiber-injected Optical Truss
Interferometer (OTI) Fabry–Perot cavity. Zemax OpticStudio (via ZOSPy) exports Gaussian
beam states; FINESSE 3 models the cavity and TEM00 visibility $V_{00}$.

Design and roadmap: [BLUEPRINT.md](BLUEPRINT.md).

## Status

**Milestone 1 (skeleton)** is implemented: package layout, YAML configuration schema,
CLI skeleton, placeholder FINESSE models, visibility extraction, and unit tests. See
[docs/milestone-1.md](docs/milestone-1.md).

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

Install **finesse** and **zospy** in `.venv` before running optical simulations
(Milestones 2–3); they are not required for Milestone 1 unit tests.

## Repository layout

```text
configs/           YAML run and tolerance configuration
finesse/models/    FINESSE .kat models (placeholder in M1)
src/optical_truss_ifo_sim/   Python package (`import optical_truss_ifo_sim`)
tests/             pytest suite
docs/              Conventions and milestone notes
```

## License

Proprietary — internal OTI simulation project.
