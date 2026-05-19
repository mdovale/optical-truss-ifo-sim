# Handoff: Milestone 3 — Zemax beam export (headless, Mac + Parallels VM)

## Scope

Implement **BLUEPRINT Milestone 3** (ZOSPy connection, nominal beam export, SI-normalized
`BeamState` table, CLI `zemax-export`) following the **headless, GUI-minimal** workflow
documented in [docs/zemax_headless.md](../zemax_headless.md).

**In scope:** nominal single-sample export, validation against existing FINESSE reference
beams, Mac-orchestrated / Windows-executed Zemax, unit tests that run without OpticStudio on
macOS.

**Out of scope (later milestones):** Monte Carlo tolerancing, compensation optimization,
deterministic sweeps, `run-full`, `analyze`, `make-report`.

---

## Feature / goal

Deliver a reproducible Zemax → Python handoff so `oti-pipeline finesse-run` can consume
machine-generated beam states instead of only `tests/reference_data/beam_states_nominal.csv`.

**User-facing workflow (desired):**

1. Develop on **macOS** (Cursor, git, FINESSE, pytest for non-Zemax tests).
2. Run Zemax export in **Windows 11 Parallels VM** (Apple Silicon host) via SSH or
   `prlctl exec`, without opening the Zemax GUI for routine work.
3. Use **ZOSPy standalone** (invisible OpticStudio) for all automated export.
4. Prefer **spec-driven or checked-in `.zmx`** for the optical model; optional
   `zemax/build_oti_input_stage.py` builder from REFERENCE nominal table — not ad-hoc GUI
   edits for each change.
5. Chain on Mac: exported `beam_states.parquet` → `oti-pipeline finesse-run`.

**Non-goals for this handoff:**

- Running ZOSPy from the macOS `.venv` against OpticStudio in the VM (unsupported).
- Full replication of dissertation Monte Carlo in Zemax (Milestones 4–5).
- Replacing optical review; first nominal model still needs physics validation.

---

## Current status

| Area | Status |
|------|--------|
| Milestone 2 (FINESSE) | **Done** — `finesse_runner.py`, `finesse-run`, reference CSV, tests |
| Milestone 3 stubs | `zemax_api.py`, `beam_export.py` are one-line placeholders |
| CLI `zemax-export` | Stub (exit 2) in `cli.py` |
| `zemax/models/oti_input_stage.zmx` | **Missing** — path referenced in `configs/nominal.yaml` only |
| `docs/zemax_interface.md` | Not written (listed in BLUEPRINT §15) |
| `docs/zemax_headless.md` | **Written** — architecture and VM workflow |
| Windows VM + ZOSPy | **User environment** — Parallels Win11 Pro ARM, Zemax installed; implementer must verify `zospy` in Windows `.venv` |
| Prior conversation | Agreed Mac-brain / Windows-muscle split; LLM assists builders/specs, not optical invention |

**Reproducible bug:** N/A (greenfield feature).

---

## Context

### Repository modules to implement

| Module | Responsibility |
|--------|----------------|
| `zemax_api.py` | `zemax_available()`, `connect_standalone()`, context manager, load `.zmx` |
| `beam_export.py` | Run analysis at `cavity_input`, map Zemax columns → `BeamState`, write parquet/CSV |
| `cli.py` | Wire `zemax-export` like `finesse-run` (load config, call export, write outputs) |
| `scripts/zemax-export-vm.sh` | Mac wrapper: validate-config → VM command → optional local `finesse-run` |

### Existing contracts

- **`BeamState`** — `schemas.py`; minimum fields in BLUEPRINT §6.1.
- **`ZemaxConfig`** — `model_path`, `reference_plane: cavity_input`, `wavelength_m`.
- **`load_beam_states`** — `finesse_runner.py` reads CSV/Parquet into `BeamState` (reuse for round-trip tests).
- **Reference targets** — `tests/reference_data/beam_states_nominal.csv` row `nominal`:
  waists `2.79e-4` m, `zx=zy=0.35` m, zero offset/angle.
- **Coordinates** — [docs/coordinate_conventions.md](../coordinate_conventions.md).
- **Legacy pitfalls** — REFERENCE §5.3 (`zy` duplicated in old macro); explicit named columns in parser.

### Environment

- **macOS `.venv`:** project package + FINESSE; `zospy` optional; default `pytest` must pass without Zemax.
- **Windows VM `.venv`:** same repo via shared folder; **must** install `zospy` + licensed OpticStudio.
- **Python:** `>=3.11` per `pyproject.toml`; confirm ZOSPy/OpticStudio version compatibility on Windows ARM.

### Nominal optics source

`.cursor/read-only-references/REFERENCE.md` §2.3 — fiber, collimator, Lens 1/2, cavity
parameters. Lens 2 back surface = HR input mirror.

---

## Design decisions (locked)

1. **Zemax runs only on Windows VM**; macOS never hosts ZOS-API calls for production export.
2. **Standalone ZOSPy connection** for automation; extension/GUI mode only for rare debug.
3. **SI units at export boundary** — convert immediately in `beam_export.py`; raw Zemax
   dump under `data/raw/zemax/` if retained.
4. **Same `BeamState` schema** as FINESSE path — no parallel column naming.
5. **`zemax-export` writes** at minimum:
   - `data/intermediate/beam_states.parquet` (or path derived from `run.output_dir` in config)
   - optional raw export under `data/raw/zemax/<run_name>/`
6. **Split `run-full`** (Milestone 3): document two-step `zemax-export` (VM) then
   `finesse-run` (Mac); do not block M3 on single-process `run-full`.
7. **Optional spec-driven builder** (`zemax/build_oti_input_stage.py` + `configs/oti_optics.yaml`)
   is encouraged but **not required** if a validated `oti_input_stage.zmx` is checked in first.

---

## Success criteria / acceptance

- [ ] `zemax_available()` returns `False` on macOS without OpticStudio; `True` in Windows VM with Zemax.
- [ ] `oti-pipeline zemax-export configs/nominal.yaml` runs in VM standalone mode **without opening Zemax GUI**.
- [ ] Output Parquet/CSV validates as list of `BeamState`; `load_beam_states` succeeds.
- [ ] Nominal exported row matches `beam_states_nominal.csv` `nominal` within documented tolerances (suggest relative waist 1%, offsets/angles absolute thresholds TBD in test).
- [ ] `oti-pipeline finesse-run <exported.parquet> configs/finesse_validation.yaml` succeeds on Mac when FINESSE installed.
- [ ] Unit tests on Mac cover: column mapping, SI conversion, schema validation (synthetic Zemax-like tables); no OpticStudio required.
- [ ] Optional `pytest -m zemax` (or env-gated) runs nominal export test on VM.
- [ ] `docs/zemax_interface.md` documents required `.zmx` analyses, reference plane, surface naming.
- [ ] `scripts/zemax-export-vm.sh` documented in `zemax_headless.md` with env vars for VM name/paths.
- [ ] `docs/milestone-3.md` added mirroring `docs/milestone-2.md` structure.

---

## Implementation plan / remaining work

### Phase A — Bootstrap optical model (VM)

1. Create nominal `.zmx` **or** `configs/oti_optics.yaml` + `zemax/build_oti_input_stage.py`
   from REFERENCE §2.3.
2. One-time validation (GUI or scripted checks): beam at cavity input vs expected waist/position.
3. Commit `zemax/models/oti_input_stage.zmx` (and builder script if used).

### Phase B — `zemax_api.py`

1. `zemax_available() -> bool` (try import + optional lightweight connect).
2. `ZemaxSession` context manager: connect standalone, `load_file(model_path)`, `close`.
3. Clear errors when OpticStudio missing (mirror `finesse_available()` pattern).

### Phase C — `beam_export.py`

1. Define Zemax analysis settings needed for astigmatic Gaussian parameters at reference plane
   (document in `zemax_interface.md`).
2. `export_beam_states(oss, cfg: ZemaxConfig, n_samples=1) -> list[BeamState]`.
3. `write_beam_states(beams, path)` — Parquet default; CSV supported.
4. Raw artifact writer under `data/raw/zemax/`.

### Phase D — CLI and Mac wrapper

1. Implement `zemax-export` in `cli.py` (replace stub).
2. Add `scripts/zemax-export-vm.sh` with `OTI_ZEMAX_VM_NAME`, `OTI_ZEMAX_VM_REPO`, optional SSH.
3. Write `run_manifest.yaml` snippet (git hash, zospy version, model checksum) — align with BLUEPRINT §3.5.

### Phase E — Tests and docs

1. `tests/test_zemax_export_schema.py` — synthetic rows, column renames, unit conversion.
2. `tests/test_zemax_import.py` — import/`zemax_available` smoke (skip if no zospy).
3. `docs/zemax_interface.md`, `docs/milestone-3.md`.
4. Update `README.md` status section.

### Phase F — End-to-end check (user machine)

1. VM: `oti-pipeline zemax-export configs/nominal.yaml`
2. Mac: `oti-pipeline finesse-run data/intermediate/beam_states.parquet configs/finesse_validation.yaml`
3. Compare `v_00` to Milestone 2 notebook baseline for nominal case.

---

## Recommended next steps

1. Read [docs/zemax_headless.md](../zemax_headless.md) and confirm Parallels share path + VM name with user.
2. Set up Windows `.venv` and verify `import zospy` + standalone connect.
3. Deliver Phase A (`.zmx` or builder) before API export — export tests depend on a real model.
4. Implement Phases B–D in small commits (`feat(zemax): …`) per `.cursor/rules/git-workflow.mdc`.
5. Do not implement Monte Carlo in M3; stub tolerances application for M4.

---

## Test coverage gaps

| Exists | Missing |
|--------|---------|
| `test_finesse_runner.py`, `beam_states_nominal.csv` | Zemax export parser tests |
| `test_config.py` for `ZemaxConfig` | VM integration / `pytest -m zemax` |
| FINESSE nominal visibility path | Zemax→FINESSE round-trip on exported file |

---

## Branch / workspace notes

- Uncommitted WIP may exist on `finesse_runner.py`, FINESSE docs/tests (Milestone 2 polish) — do not revert unrelated changes; stage narrowly per commit.
- `pyproject.toml` does not yet list `zospy` as a dependency; add as optional extra e.g. `[zemax]` or document manual `pip install zospy` in Windows venv only to keep Mac CI lean.

---

## What was tried

Nothing implemented yet for Milestone 3 in code — discussion and `docs/zemax_headless.md` only.

---

## References

- [docs/zemax_headless.md](../zemax_headless.md) — target workflow (this handoff)
- [BLUEPRINT.md](../../BLUEPRINT.md) §5.2, §6, §16 Milestone 3, §11 CLI
- [docs/milestone-2.md](../milestone-2.md) — `load_beam_states`, `finesse-run` pattern
- [docs/coordinate_conventions.md](../coordinate_conventions.md)
- [.cursor/read-only-references/REFERENCE.md](../../.cursor/read-only-references/REFERENCE.md) §2.3, §5
- [ZOSPy connection](https://zospy.readthedocs.io/en/stable/usage/01_connection.html)
- [ZOSPy LDE / building systems](https://zospy.readthedocs.io/en/latest/usage/02_lens_data_editor.html)
- [Zemax community: VM + Python](https://community.zemax.com/zos-api-12/connect-python-api-in-windows-virtual-machine-2078)
- Prior chat context: macOS orchestration, Parallels ARM, GUI avoidance, LLM for spec→builder code only
