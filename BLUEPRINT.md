# OTI Tolerance Simulation Blueprint

Repository name: `optical-truss-ifo-sim`

## 1. Purpose

This repository will implement a cleaned, reproducible simulation workflow for tolerance analysis of a compact fiber-injected Optical Truss Interferometer (OTI) cavity. The workflow combines:

- Zemax OpticStudio accessed through the ZOS-API via ZOSPy for optical design, tolerancing, compensation, and Gaussian beam export.
- FINESSE 3 for resonant Fabry-Perot cavity modeling, Hermite-Gaussian mode coupling, mirror/cavity misalignment sensitivity, and computation of TEM00 visibility.
- Python for orchestration, configuration, data validation, batch execution, statistics, plotting, and reproducible reporting.

The goal is to preserve the physical clarity of a hybrid optical-design plus interferometer-simulation workflow while replacing ad hoc handoffs with a maintainable, version-controlled, testable pipeline.

## 2. Physical system being modeled

The modeled system is a compact, fiber-coupled Fabry-Perot cavity intended to measure dimensional changes of a stable structure. It consists of an input stage and a return stage separated by a cavity baseline.

### 2.1 Input stage

The OTI input stage contains:

- A single-mode polarization-maintaining fiber delivering 1064 nm light.
- An adjustable fiber collimator that defines the injected Gaussian beam.
- A compact two-lens mode-matching telescope.
- A high-reflectivity cavity input mirror integrated on the final optic of the input stage.
- A mechanical housing intended to maintain alignment and minimize thermally induced motion of the input optics and cavity mirror.

The input stage transforms the fiber-collimator output beam into the target cavity eigenmode. Manufacturing and assembly tolerances in this stage introduce mode mismatch, angular misalignment, lateral beam offset, astigmatism, and imperfect coupling to the cavity TEM00 mode.

### 2.2 Return stage

The return stage contains the second high-reflectivity cavity mirror. It may be represented either as an ideal mirror with controlled alignment perturbations or as a toleranced mechanical/optical element if a more detailed design is available.

### 2.3 Fabry-Perot cavity

The input and return mirrors form a two-mirror Fabry-Perot cavity. The primary simulated observable is the reflected-power visibility of the fundamental Gaussian cavity resonance:

```math
V_{00} = \frac{P_{\max} - P_{\min}}{P_{\max} + P_{\min}}.
```

Here, `P_max` is the reflected power away from resonance and `P_min` is the reflected power at the TEM00 resonance. A perfectly mode-matched, impedance-matched, lossless cavity would approach `V_00 = 1`. Realistic tolerances reduce this value by coupling power into non-resonant or higher-order spatial modes.

### 2.4 Compensation concept

The adjustable fiber collimator provides lateral and angular degrees of freedom for input-beam compensation. In the simulation, compensation is modeled as a constrained optimization problem:

- The input beam is adjusted to minimize mismatch and misalignment at the cavity input.
- Adjustment range and resolution are finite and should be configurable.
- The compensated and uncompensated Monte Carlo distributions are compared to quantify the value of the alignment degrees of freedom.

## 3. Simulation goals

The repository should support the following primary goals.

### 3.1 Monte Carlo tolerance analysis

Run Monte Carlo campaigns over manufacturing, assembly, and alignment tolerances to estimate the statistical distribution of TEM00 cavity visibility.

The core result should be a pair of distributions:

- Visibility without input-beam compensation.
- Visibility with input-beam compensation.

Typical summary statistics should include mean, median, standard deviation, percentiles, worst-case samples, and yield above user-defined visibility thresholds.

### 3.2 Sensitivity studies

Support deterministic sweeps of individual parameters, including:

- Lens radius or focal-length error.
- Lens thickness error.
- Lens separation error.
- Lens tilt.
- Lens decenter.
- Fiber-collimator lateral offset.
- Fiber-collimator angular offset.
- Cavity mirror tilt.
- Cavity mirror decenter.
- Cavity baseline length.
- Mirror radius of curvature.
- Input waist size and waist location.

These sweeps should be used to identify dominant tolerance drivers and validate Monte Carlo behavior.

### 3.3 Compensation-performance analysis

Quantify how collimator alignment range and resolution affect the final visibility distribution. The pipeline should support sweeps over actuator resolution and dynamic range, making it possible to specify practical alignment requirements for hardware.

### 3.4 Design comparison

Support comparison between candidate optical designs, for example:

- Different mirror radii of curvature.
- Different cavity lengths.
- Different mode-matching lens prescriptions.
- Different fiber-collimator output waists.
- Different tolerance allocations.
- Different compensation strategies.

### 3.5 Reproducibility and traceability

Every simulation run should be reproducible from a saved configuration. Outputs should include enough metadata to reconstruct:

- Git commit hash.
- Software versions.
- Zemax model file path and checksum.
- FINESSE model file path and checksum.
- Random seed.
- Tolerance configuration.
- Compensation configuration.
- Number of Monte Carlo trials.
- Date/time of execution.

## 4. Recommended repository structure

```text
optical-truss-ifo-sim/
├── README.md
├── BLUEPRINT.md
├── pyproject.toml
├── .gitignore
├── .venv/                  # local virtualenv (gitignored)
├── configs/
│   ├── nominal.yaml
│   ├── tolerances.yaml
│   ├── compensation.yaml
│   ├── monte_carlo.yaml
│   └── finesse.yaml
├── zemax/
│   ├── models/
│   │   └── README.md
│   ├── merit_functions/
│   │   └── README.md
│   └── zos_extensions/
│       └── README.md
├── finesse/
│   ├── models/
│   │   ├── oti_cavity.kat
│   │   └── test_cavity.kat
│   └── templates/
│       └── cavity_scan.kat.j2
├── src/
│   └── oti_tolerance_pipeline/
│       ├── __init__.py
│       ├── config.py
│       ├── schemas.py
│       ├── zemax_api.py
│       ├── beam_export.py
│       ├── compensation.py
│       ├── finesse_runner.py
│       ├── visibility.py
│       ├── monte_carlo.py
│       ├── sensitivity.py
│       ├── plotting.py
│       ├── reporting.py
│       └── cli.py
├── notebooks/
│   ├── 01_validate_nominal_design.ipynb
│   ├── 02_single_parameter_sweeps.ipynb
│   ├── 03_monte_carlo_visibility.ipynb
│   └── 04_compensation_trade_study.ipynb
├── tests/
│   ├── test_config.py
│   ├── test_beam_schema.py
│   ├── test_visibility.py
│   ├── test_compensation.py
│   └── reference_data/
├── scripts/
│   ├── run_zemax_monte_carlo.py
│   ├── run_finesse_batch.py
│   ├── run_full_pipeline.py
│   └── make_report.py
├── data/
│   ├── raw/
│   ├── intermediate/
│   └── processed/
└── reports/
    ├── figures/
    └── tables/
```

## 5. Simulation environment

### 5.1 Python environment

Orchestration and analysis run in a **repository-local `.venv`** at the project root. That environment is the single source of truth for the interpreter, **FINESSE 3**, **ZOSPy**, and pip-installed project dependencies. Do not use system `python`/`pip` for this repo. Prefer `.venv` over Conda or a shared external venv unless explicitly requested.

| Item | Location |
|------|----------|
| Virtual environment | `.venv/` (gitignored) |
| Agent / editor conventions | `AGENTS.md`, `.cursor/rules/python-venv.mdc` |
| Package metadata and pip deps | `pyproject.toml` |
| Worktree sanity check | `.cursor/scripts/ensure-venv.sh` |

**Setup (once per machine or after cloning):**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Install **finesse** and **zospy** into `.venv` as required (via `pyproject.toml` or documented pins). Use `.venv/bin/python` and `.venv/bin/pip` directly when activation is inconvenient (see `AGENTS.md`).

**`pyproject.toml`** declares this package (`oti_tolerance_pipeline`), its version-pinned dependencies, optional extras (e.g. `dev` for pytest and linters), and the `oti-pipeline` CLI entry point. If ZOSPy import fails, fix the host .NET/Mono and Zemax setup per `.cursor/rules/python-venv.mdc`; do not switch to system Python or another environment.

**Heavy simulation stack** (must be present in `.venv`):

- `finesse` (FINESSE 3)
- `zospy` (Zemax OpticStudio via ZOS-API)

**Declared in `pyproject.toml`** (typical core set):

- `numpy`, `scipy`, `pandas`
- `xarray` or `h5py`
- `pydantic`, `pyyaml`
- `matplotlib`
- `click` or `typer`
- `jinja2`

**Optional extras** (e.g. `[parallel]`, `[dev]` in `pyproject.toml`):

- `joblib`, `dask`, or `ray` for parallel execution
- `plotly` for interactive diagnostics
- `rich` for command-line progress reporting
- `pytest`, `ruff`, `black`, and `mypy` for development

### 5.2 Zemax and ZOSPy

Zemax OpticStudio should be controlled through ZOSPy, which provides a Python interface to the Zemax OpticStudio ZOS-API. The repository should isolate all Zemax-specific logic in `zemax_api.py` and `beam_export.py`.

Expected Zemax-side capabilities:

- Load the nominal OTI input-stage optical model.
- Apply tolerances and compensator settings.
- Run Monte Carlo tolerancing or deterministic perturbation cases.
- Run local optimization where needed.
- Extract Gaussian beam parameters at a well-defined reference plane.
- Export a structured beam-parameter table.

The code should avoid burying essential logic inside opaque Zemax files where possible. Configuration should live in YAML or Python dataclasses, with the Zemax file treated as the optical prescription source of truth.

### 5.3 FINESSE 3

FINESSE 3 should be used to model the Fabry-Perot cavity resonance and spatial-mode coupling. All FINESSE models should be stored as version-controlled `.kat` files or templates.

Expected FINESSE-side capabilities:

- Define the two-mirror cavity.
- Define mirror reflectivities, curvatures, spacing, and losses.
- Define spatial-mode order cutoff.
- Inject a Gaussian beam with specified waist, waist position, offset, and angle.
- Represent input-beam misalignment using equivalent steering optics or direct beam parameters.
- Scan laser frequency across the cavity resonance.
- Compute reflected power and extract `P_max`, `P_min`, and `V_00`.

### 5.4 Python/PyKat compatibility note

FINESSE 3 has a Python-native interface. Older workflows may refer to PyKat, which was developed around FINESSE 2. This repository should target FINESSE 3 as the primary backend. If PyKat-style abstractions are still useful, they should be implemented as local compatibility wrappers, not as a hard dependency on obsolete syntax.

Recommended naming:

- Use `finesse_runner.py` for the production FINESSE 3 interface.
- Use `pykat_compat.py` only if legacy PyKat-like APIs are required.

## 6. Data model and handoff contract

The most important design decision is to define a strict contract for the handoff between Zemax and FINESSE. Zemax should export the incident beam state at a reference plane immediately before the cavity input mirror or at another explicitly documented plane.

### 6.1 Beam-state table

Each Monte Carlo sample should produce one row with fields such as:

```text
sample_id
seed
case_type
compensation_enabled
x_offset_m
y_offset_m
x_angle_rad
y_angle_rad
wx_m
wy_m
zx_m
zy_m
q_x_real_m
q_x_imag_m
q_y_real_m
q_y_imag_m
collimator_x_m
collimator_y_m
collimator_theta_x_rad
collimator_theta_y_rad
zemax_status
zemax_merit
```

Not all fields are mandatory if an equivalent representation is used. The required minimum is:

```text
sample_id
x_offset_m
y_offset_m
x_angle_rad
y_angle_rad
wx_m
wy_m
zx_m
zy_m
```

Units must be SI in exported intermediate files. User-facing plots may use convenient units such as microradians, micrometers, millimeters, or percent.

### 6.2 Reference-plane convention

The repository must define a single coordinate convention:

- `z = 0` is the chosen cavity input reference plane.
- Positive `z` points from the input mirror toward the return mirror.
- `x_offset_m` and `y_offset_m` are lateral beam-centroid offsets at the reference plane.
- `x_angle_rad` and `y_angle_rad` are propagation angles relative to the nominal cavity axis.
- `zx_m` and `zy_m` are waist locations relative to the reference plane.
- `wx_m` and `wy_m` are waist radii in the two transverse axes.

This convention should be documented and enforced by schema validation.

### 6.3 File formats

Recommended intermediate formats:

- CSV for quick inspection and compatibility.
- Parquet or HDF5 for large Monte Carlo campaigns.
- YAML or JSON for configuration and run metadata.

Each run should produce:

```text
run_manifest.yaml
beam_states.parquet
finesse_results.parquet
summary_statistics.yaml
figures/
```

## 7. End-to-end workflow

### 7.1 Nominal design validation

1. Load the nominal Zemax model.
2. Extract the nominal Gaussian beam at the cavity input reference plane.
3. Run the nominal FINESSE cavity model.
4. Verify that the injected beam is mode matched to the target cavity eigenmode.
5. Confirm that the nominal `V_00` is close to the expected ideal value.

### 7.2 Deterministic tolerance sweeps

1. Select one tolerance parameter.
2. Sweep it over a configured range.
3. For each value, extract the beam state from Zemax.
4. Run FINESSE and calculate `V_00`.
5. Plot visibility versus tolerance parameter.
6. Store sweep data and metadata.

These sweeps provide sanity checks and help identify dominant tolerance drivers.

### 7.3 Uncompensated Monte Carlo

1. Load the nominal Zemax model.
2. Apply randomized tolerances using a reproducible seed.
3. Do not optimize the input beam.
4. Export the resulting beam state for each sample.
5. Run FINESSE for each sample.
6. Extract `V_00` for each sample.
7. Generate histogram, summary statistics, and threshold yield metrics.

### 7.4 Compensated Monte Carlo

1. Load the same tolerance samples used in the uncompensated case.
2. Enable input-beam compensation.
3. Optimize collimator lateral and angular degrees of freedom within configured range and resolution.
4. Export compensated beam states.
5. Run FINESSE for each compensated sample.
6. Extract `V_00` for each sample.
7. Compare compensated and uncompensated distributions.

Using the same random tolerance samples for both cases is strongly recommended because it enables paired statistical comparisons.

### 7.5 Reporting

The pipeline should automatically generate:

- Visibility histograms.
- Cumulative distribution functions.
- Box plots or violin plots for design comparisons.
- Parameter-correlation plots.
- Worst-case sample reports.
- Compensation actuator usage statistics.
- Summary tables in CSV and Markdown.

## 8. Tool integration architecture

### 8.1 High-level data flow

```text
Configuration YAML
      │
      ▼
Python orchestration layer
      │
      ├──► Zemax via ZOSPy
      │        ├── Load optical prescription
      │        ├── Apply tolerances
      │        ├── Apply compensation
      │        └── Export beam states
      │
      ├──► Beam-state validation
      │        ├── Unit checks
      │        ├── Coordinate convention checks
      │        └── Schema validation
      │
      ├──► FINESSE 3
      │        ├── Build cavity model
      │        ├── Inject beam state
      │        ├── Scan resonance
      │        └── Export reflected power
      │
      └──► Analysis/reporting
               ├── Compute V_00
               ├── Compute statistics
               ├── Generate plots
               └── Save run manifest
```

### 8.2 Responsibility split

Zemax is responsible for the detailed input-stage optics:

- Real lens prescription.
- Optical-material propagation.
- Lens thickness and curvature tolerances.
- Mechanical tilts and decenters.
- Beam propagation through the compact input-stage telescope.
- Practical compensation using fiber-collimator degrees of freedom.

FINESSE is responsible for cavity physics:

- Fabry-Perot resonance.
- Hermite-Gaussian mode decomposition.
- Mirror curvature and cavity eigenmode.
- Higher-order spatial-mode coupling.
- Reflected power as a function of detuning.
- Computation of the TEM00 resonance visibility.

Python is responsible for workflow control:

- Configuration parsing.
- Run orchestration.
- Random sampling.
- Parallel execution.
- Data validation.
- File management.
- Plotting and reporting.
- Testing and reproducibility.

## 9. Visibility extraction

For each FINESSE run, the pipeline should scan laser detuning across the fundamental resonance and compute:

```math
V_{00} = \frac{P_{\max} - P_{\min}}{P_{\max} + P_{\min}}.
```

Recommended algorithm:

1. Evaluate reflected power over a configured detuning range around the expected TEM00 resonance.
2. Estimate `P_max` from the off-resonance baseline, using robust statistics such as the median of edge samples.
3. Estimate `P_min` from the minimum reflected power near the TEM00 resonance.
4. Optionally fit a local resonance model to improve robustness against numerical sampling resolution.
5. Store `V_00`, `P_max`, `P_min`, detuning at minimum, and quality-control flags.

Quality-control flags should include:

- Resonance not found.
- Multiple competing minima.
- Scan range too narrow.
- Reflected baseline unstable.
- FINESSE run failed.
- Visibility outside physical bounds.

## 10. Configuration examples

### 10.1 Monte Carlo configuration

```yaml
run:
  name: nominal_oti_mc
  random_seed: 12345
  n_samples: 1000
  output_dir: data/processed/nominal_oti_mc

zemax:
  model_path: zemax/models/oti_input_stage.zmx
  reference_plane: cavity_input
  wavelength_m: 1.064e-6

finesse:
  model_template: finesse/templates/cavity_scan.kat.j2
  maxtem: 10
  detuning_start_hz: -10.0e6
  detuning_stop_hz: 10.0e6
  detuning_points: 2001

compensation:
  enabled: true
  x_range_m: [-1.0e-3, 1.0e-3]
  y_range_m: [-1.0e-3, 1.0e-3]
  theta_x_range_rad: [-1.0e-3, 1.0e-3]
  theta_y_range_rad: [-1.0e-3, 1.0e-3]
  x_resolution_m: 1.0e-6
  y_resolution_m: 1.0e-6
  theta_x_resolution_rad: 1.745e-5
  theta_y_resolution_rad: 1.745e-5
```

### 10.2 Tolerance configuration

```yaml
tolerances:
  lens_1_radius:
    distribution: uniform
    nominal_m: 15.979e-3
    half_width_m: 0.034e-3

  lens_1_thickness:
    distribution: uniform
    nominal_m: 4.45e-3
    half_width_m: 50.0e-6

  lens_1_lens_2_separation:
    distribution: uniform
    nominal_m: 17.26e-3
    half_width_m: 50.0e-6

  lens_1_decenter_x:
    distribution: uniform
    nominal_m: 0.0
    half_width_m: 5.0e-6

  lens_1_decenter_y:
    distribution: uniform
    nominal_m: 0.0
    half_width_m: 5.0e-6

  lens_1_tilt_x:
    distribution: uniform
    nominal_rad: 0.0
    half_width_rad: 140.0e-6

  lens_1_tilt_y:
    distribution: uniform
    nominal_rad: 0.0
    half_width_rad: 140.0e-6
```

The exact tolerance list should be expanded to include all relevant input-stage and cavity parameters once the optical prescription is finalized.

## 11. Command-line interface

The repository should expose a command-line interface. Example commands:

```bash
oti-pipeline validate-config configs/monte_carlo.yaml

oti-pipeline zemax-export configs/monte_carlo.yaml

oti-pipeline finesse-run data/intermediate/beam_states.parquet configs/monte_carlo.yaml

oti-pipeline analyze data/processed/nominal_oti_mc

oti-pipeline run-full configs/monte_carlo.yaml

oti-pipeline make-report data/processed/nominal_oti_mc
```

## 12. Testing strategy

### 12.1 Unit tests

Unit tests should cover:

- YAML configuration parsing.
- Unit conversion.
- Beam-state schema validation.
- Visibility calculation from synthetic reflected-power traces.
- Compensation grid rounding.
- Detection of invalid FINESSE outputs.

### 12.2 Physics regression tests

Regression tests should compare against known reference cases:

- Nominal perfectly aligned cavity gives high visibility.
- Pure beam offset reduces visibility symmetrically with sign.
- Pure angular error reduces visibility symmetrically with sign.
- Waist-size mismatch reduces visibility independent of sign convention.
- Waist-position mismatch has the expected symmetry around the cavity waist reference.
- Increasing `maxtem` converges the predicted visibility.

### 12.3 Cross-tool validation tests

The repository should include benchmark cases in which Zemax-exported beam parameters are manually specified and compared against FINESSE-only analytic expectations where available.

Recommended validation cases:

- Ideal Gaussian beam matched to the cavity eigenmode.
- Known lateral offset only.
- Known angular tilt only.
- Known waist-size mismatch only.
- Known waist-location mismatch only.
- Combined offset and tilt.
- Astigmatic beam with independent `x` and `y` waist parameters.

## 13. Parallelization strategy

Monte Carlo campaigns are embarrassingly parallel after beam-state generation. The pipeline should support:

- Serial execution for debugging.
- Local multiprocessing for workstation runs.
- Optional joblib/dask/ray backend for large campaigns.
- Chunked execution to avoid losing progress after failure.

Each sample should be independently reproducible from its `sample_id` and random seed.

## 14. Failure handling

The pipeline should never silently drop failed cases. Each sample should receive a status code.

Recommended status values:

```text
OK
ZEMAX_FAILED
ZEMAX_OPTIMIZATION_FAILED
BEAM_EXPORT_INVALID
FINESSE_FAILED
VISIBILITY_EXTRACTION_FAILED
QC_FAILED
```

Failures should be included in summary reports and optionally re-runnable.

## 15. Documentation plan

The repository should include the following documentation:

- `README.md`: quick-start instructions and project overview.
- `BLUEPRINT.md`: this design document.
- `docs/coordinate_conventions.md`: beam-state and cavity coordinate definitions.
- `docs/zemax_interface.md`: how ZOSPy is used and what is expected from the Zemax model.
- `docs/finesse_interface.md`: FINESSE model structure and visibility extraction.
- `docs/validation.md`: reference cases and physics checks.
- `docs/results_format.md`: output files and metadata schema.

## 16. Initial implementation milestones

### Milestone 1: Skeleton repository

- Create package structure and `pyproject.toml` (install editable into `.venv`).
- Add configuration schema.
- Add CLI skeleton.
- Add placeholder FINESSE model.
- Add unit tests for configuration and visibility calculation.

### Milestone 2: FINESSE-only visibility engine

- Implement FINESSE 3 cavity runner.
- Inject manually specified beam states.
- Extract reflected-power traces.
- Compute `V_00`.
- Validate nominal and simple misalignment cases.

### Milestone 3: Zemax beam export

- Implement ZOSPy connection.
- Load nominal Zemax model.
- Extract nominal beam parameters.
- Export beam-state table.
- Validate coordinate and unit conventions.

### Milestone 4: Deterministic sweeps

- Implement one-parameter Zemax sweeps.
- Pipe sweep beam states into FINESSE.
- Plot visibility versus perturbation.
- Add reference plots and regression data.

### Milestone 5: Monte Carlo campaign

- Implement random tolerance sampling.
- Run uncompensated Monte Carlo.
- Run compensated Monte Carlo.
- Generate summary report and plots.

### Milestone 6: Compensation trade studies

- Sweep collimator range and resolution.
- Quantify visibility yield versus compensation capability.
- Generate alignment-requirement tables.

## 17. Design principles

1. Keep physical conventions explicit.
2. Keep units SI in machine-readable data.
3. Keep Zemax, FINESSE, and Python responsibilities separate.
4. Store configurations, not hidden state.
5. Make every run reproducible.
6. Validate simple physics before trusting Monte Carlo results.
7. Prefer transparent intermediate files over opaque tool-specific state.
8. Treat compensation as a modeled hardware capability, not an ideal mathematical operation.
9. Use paired random samples for compensated and uncompensated comparisons.
10. Make failure modes visible in the final statistics.

## 18. Open technical decisions

The following decisions should be resolved early in the project:

- Exact cavity input reference plane used for beam export.
- Whether FINESSE receives beam state through direct Gaussian-beam parameters or through an equivalent steering/periscope representation.
- Required maximum Hermite-Gaussian mode order for convergence.
- Whether astigmatic beams are represented directly or approximated by independent `x` and `y` Gaussian parameters.
- Whether compensation is performed inside Zemax, in Python using Zemax evaluations, or through a reduced surrogate model.
- Whether large Monte Carlo outputs are stored in Parquet, HDF5, or both.
- Whether the repository should support multiple cavity designs through a plugin-like model registry.

## 19. Minimal viable result

The minimal useful version of this repository should produce one figure and one table:

1. A histogram comparing uncompensated and compensated TEM00 visibility distributions.
2. A summary table containing mean, standard deviation, median, 5th percentile, 95th percentile, minimum, maximum, and yield above selected visibility thresholds.

The result should be generated from a single command:

```bash
oti-pipeline run-full configs/monte_carlo.yaml
```

The output should be reproducible from the saved run directory without requiring manual copying, editing, or interpretation of intermediate files.
