# Headless Zemax workflow (ZOSPy + Parallels)

This document describes how to run OpticStudio **without the Zemax GUI** for day-to-day
work, and how that fits the **macOS host + Windows VM** setup used on Apple Silicon with
Parallels. It complements [BLUEPRINT.md](../BLUEPRINT.md) Milestone 3 and
[docs/coordinate_conventions.md](coordinate_conventions.md).

Implementation handoff: [docs/handoffs/20260519_milestone-3-zemax-headless-workflow.md](handoffs/20260519_milestone-3-zemax-headless-workflow.md).

---

## 1. Hard constraints

| Fact | Implication |
|------|-------------|
| ZOS-API / ZOSPy require **Windows**, .NET, and a licensed OpticStudio install | Zemax code runs in the **Parallels VM**, not in the macOS `.venv` |
| There is **no supported remote ZOS-API** from macOS to a VM | “Command from Mac” means **orchestration on Mac**, **execution in Windows** |
| OpticStudio must still be installed and licensed on the VM | Headless ≠ license-free; it means **no interactive GUI session** |

FINESSE 3 runs natively on macOS. Zemax export and FINESSE analysis are **deliberately
split stages** (see Milestone 2 `finesse-run` with manual or exported beam tables).

---

## 2. Target architecture

```text
┌─────────────────────────────────────────────────────────────┐
│ macOS (authoring, git, FINESSE, analysis)                   │
│  • Edit configs, Python, notebooks                          │
│  • oti-pipeline validate-config, finesse-run, pytest        │
│  • scripts/zemax-export-vm.sh  →  trigger VM job          │
└───────────────────────────┬─────────────────────────────────┘
                            │ SSH or prlctl exec
                            │ shared repo + data/
┌───────────────────────────▼─────────────────────────────────┐
│ Windows 11 (Parallels) — Zemax compute node                 │
│  • Windows .venv + zospy + optical-truss-ifo-sim            │
│  • ZOSPy connect(mode="standalone")  → invisible OpticStudio│
│  • oti-pipeline zemax-export configs/nominal.yaml           │
│  • writes data/intermediate/beam_states.parquet             │
└─────────────────────────────────────────────────────────────┘
```

**Shared folder:** mount the same repo tree in the VM (e.g. Parallels shared Mac home or
a dedicated share) so paths in YAML resolve consistently. Prefer **repo-relative** paths
(`zemax/models/oti_input_stage.zmx`) as already done in `config.py`.

---

## 3. Headless OpticStudio (no GUI)

### 3.1 ZOSPy standalone mode

Use **standalone** connection (ZOSPy default): OpticStudio starts **invisibly**, runs the
script, and exits. This is the right mode for batch export and CI-style checks.

```python
import zospy as zp

zos = zp.ZOS()
oss = zos.connect()  # standalone: invisible instance
# ... load or build system, run analysis, export ...
```

Avoid **extension** mode unless you intentionally attach to an open GUI session for
debugging.

References:

- [ZOSPy: Connecting to OpticStudio](https://zospy.readthedocs.io/en/stable/usage/01_connection.html)
- [ZOSPy: Creating an optical system (LDE)](https://zospy.readthedocs.io/en/latest/usage/02_lens_data_editor.html)

### 3.2 What you can do without opening the GUI

- Create or load a sequential system (`oss.new()`, `SaveAs`, load `.zmx`)
- Set surfaces, materials, wavelengths, apertures via LDE API
- Run Gaussian beam / paraxial analyses and read results programmatically
- Save `.zmx` as a versioned artifact under `zemax/models/`
- Drive `oti-pipeline zemax-export` (Milestone 3) from PowerShell or Task Scheduler

### 3.3 What may still need a GUI (once)

- First validation of a new prescription (ray fans, layout sanity)
- Unusual surface types or merit functions that are faster to prototype interactively
- Licensing / activation UI

After a golden nominal model is validated, routine work should not require the GUI.

---

## 4. How optical models are created

Three approaches, in order of preference for this repo:

### 4.1 Spec-driven ZOSPy builder (preferred for reproducibility)

1. Freeze nominal optics in a machine-readable spec (see
   `.cursor/read-only-references/REFERENCE.md` §2.3 or a future `configs/oti_optics.yaml`).
2. Implement `zemax/build_oti_input_stage.py` (runs in VM) that reads the spec and builds
   the LDE via ZOSPy, then saves `zemax/models/oti_input_stage.zmx`.
3. Re-run the builder when the prescription changes; review **diffs in Python/YAML**, not
   clicks in Zemax.

An LLM is useful here to **draft builder code from your spec**, not to invent radii or
glass names. All numbers must come from the dissertation / REFERENCE table.

### 4.2 Checked-in `.zmx` + API-only changes (pragmatic bootstrap)

- Build or import the nominal system once (GUI or vendor file), save
  `zemax/models/oti_input_stage.zmx`.
- Milestone 3 only **loads** that file and exports beam states; tolerancing arrives in
  Milestones 4–5.

### 4.3 LLM-generated `.zmx` text (not recommended)

`.zmx` files are fragile when hand-edited. Prefer generated artifacts from tested Python
builders.

---

## 5. OTI nominal prescription (source of truth)

Until `configs/oti_optics.yaml` exists, use the table in
`.cursor/read-only-references/REFERENCE.md` §2.3 (fiber 1064 nm, collimator, Lens 1/2,
cavity waist 279 µm at cavity center, HR coatings, etc.).

**Critical modeling note:** Lens 2’s back surface is the **HR cavity input mirror**. Do not
model Lens 2 and the input mirror as independent elements unless that is an explicit,
documented simplification.

The FINESSE reference table `tests/reference_data/beam_states_nominal.csv` uses waists
`2.79e-04` m and `zx = zy = 0.35` m (half cavity length for a 0.70 m round-trip). Exported
Zemax nominal rows should be validated against these targets at `reference_plane:
cavity_input` (`configs/nominal.yaml`).

---

## 6. Beam export contract (Milestone 3)

### 6.1 Schema

Each row must validate as `optical_truss_ifo_sim.schemas.BeamState` (SI units):

| Field | Unit | Meaning |
|-------|------|---------|
| `sample_id` | — | Unique label |
| `x_offset_m`, `y_offset_m` | m | Centroid at cavity input plane |
| `x_angle_rad`, `y_angle_rad` | rad | Propagation tilt |
| `wx_m`, `wy_m` | m | Waist radii ($> 0$) |
| `zx_m`, `zy_m` | m | Waist positions relative to reference plane |

Optional: `zemax_status`, `zemax_merit`, collimator fields, $q$-parameters.

See [coordinate_conventions.md](coordinate_conventions.md) and REFERENCE §5.2–5.3 (legacy
column-order pitfalls — **explicit column mapping**, never blind copy of old macros).

### 6.2 Output layout

| Path | Role |
|------|------|
| `data/raw/zemax/<run>/...` | Immutable raw Zemax export (traceability) |
| `data/intermediate/beam_states.parquet` | Normalized `BeamState` table for `finesse-run` |
| `<run.output_dir>/run_manifest.yaml` | Config snapshot, versions, checksums (Milestone 3+) |

### 6.3 Downstream on macOS

```bash
source .venv/bin/activate
oti-pipeline finesse-run data/intermediate/beam_states.parquet configs/finesse_validation.yaml
```

Mac `.venv` does **not** need `zospy` for FINESSE-only development; install `zospy` only
in the **Windows** `.venv`.

---

## 7. One-time Windows VM setup

Perform once per VM image (then snapshot the VM):

1. Install OpticStudio (licensed) and Python 3.11+.
2. Clone or open the repo via Parallels shared folder.
3. Create Windows venv and install the package + ZOSPy:

   ```powershell
   cd Z:\path\to\optical-truss-ifo-sim
   python -m venv .venv
   .venv\Scripts\pip install -e ".[dev]"
   .venv\Scripts\pip install zospy
   ```

4. Verify headless connection:

   ```powershell
   .venv\Scripts\python -c "import zospy as zp; zos=zp.ZOS(); oss=zos.connect(); print('OK', oss)"
   ```

5. (Recommended) Enable **OpenSSH Server** on Windows for remote commands from Mac.

6. Optional: Windows auto-login + disable sleep so batch jobs are not blocked by lock screen.

---

## 8. Day-to-day: trigger Zemax from macOS

### 8.1 Parallels `prlctl exec`

```bash
VM_NAME="Windows 11"
REPO_WIN='Z:\Users\mdovale\Work-local\optical-truss-ifo-sim'

prlctl exec "$VM_NAME" -- cmd /c "cd /d ${REPO_WIN} && .venv\Scripts\oti-pipeline zemax-export configs\nominal.yaml"
```

Adjust `VM_NAME`, `REPO_WIN`, and path separators for your share mapping.

### 8.2 SSH (alternative)

```bash
ssh user@<vm-ip> 'cd /path/to/optical-truss-ifo-sim && .venv/Scripts/oti-pipeline zemax-export configs/nominal.yaml'
```

### 8.3 Wrapper script (repo)

Milestone 3 should add `scripts/zemax-export-vm.sh` (Mac-side) that:

1. Runs `oti-pipeline validate-config` locally.
2. Invokes the VM command (`prlctl` or `ssh` from env vars).
3. Checks for `data/intermediate/beam_states.parquet` (or path from config).
4. Optionally chains `oti-pipeline finesse-run` on macOS.

Environment variables (suggested):

| Variable | Example | Purpose |
|----------|---------|---------|
| `OTI_ZEMAX_VM_NAME` | `Windows 11` | Parallels VM name |
| `OTI_ZEMAX_VM_REPO` | `Z:\...\optical-truss-ifo-sim` | Repo path inside VM |
| `OTI_ZEMAX_SSH` | `user@192.168.x.x` | SSH target (if not using prlctl) |

---

## 9. LLM-assisted development (safe use)

| Good use | Poor use |
|----------|----------|
| Draft `zemax/build_*.py` from REFERENCE numbers | Invent optical powers or glass catalogs |
| Draft `zemax_api.py` / `beam_export.py` against ZOSPy docs | Trust `.zmx` XML without load test |
| Generate tests with synthetic `BeamState` rows | Skip sign/convention review |
| Explain Zemax analysis settings for beam export | Replace optical engineer sign-off |

Always validate the first nominal export against `tests/reference_data/beam_states_nominal.csv`
and, if possible, a few GUI spot checks during model bring-up only.

---

## 10. Testing strategy (Zemax side)

| Layer | Runs on | Notes |
|-------|---------|-------|
| Unit tests (parsers, SI conversion, schema) | macOS CI | No OpticStudio required; mock Zemax outputs |
| `zemax_available()` import smoke | Windows VM | Optional marker `pytest -m zemax` |
| Nominal export regression | Windows VM | Compare exported row to reference CSV tolerances |
| End-to-end | Mac + VM | `zemax-export` → `finesse-run` on shared `data/` |

Mark tests that require OpticStudio so default `pytest` on Mac stays green (same pattern as
`finesse_available()` in Milestone 2).

---

## 11. Milestone 3 scope (this repo)

From [BLUEPRINT.md](../BLUEPRINT.md) §16:

- Implement ZOSPy connection (`zemax_api.py`)
- Load nominal model (or build from spec)
- Extract nominal Gaussian beam at `cavity_input`
- Export normalized beam-state table (`beam_export.py`, wire `zemax-export` CLI)
- Validate coordinates and SI units
- Add `docs/zemax_interface.md` (API surface expected from the `.zmx` model)

**Out of scope for Milestone 3:** Monte Carlo tolerancing, compensation optimization,
deterministic sweeps (Milestones 4–6), full `run-full`.

---

## 12. Related files

| Path | Role |
|------|------|
| `src/optical_truss_ifo_sim/zemax_api.py` | ZOSPy connection (stub) |
| `src/optical_truss_ifo_sim/beam_export.py` | Export + normalization (stub) |
| `configs/nominal.yaml` | `zemax.model_path`, wavelength, reference plane |
| `zemax/models/` | `.zmx` prescriptions |
| `tests/reference_data/beam_states_nominal.csv` | FINESSE regression beams; Zemax validation target |
| `docs/milestone-2.md` | Prior milestone; `load_beam_states` consumer |

---

## 13. References

- [ZOSPy documentation](https://zospy.readthedocs.io/en/stable/)
- [Zemax community: Python API in a Windows VM](https://community.zemax.com/zos-api-12/connect-python-api-in-windows-virtual-machine-2078) (Jupyter-on-VM pattern; prefer SSH/prlctl for CLI automation)
- [Ansys ZOS-API Python (.NET)](https://support.zemax.com/hc/en-us/articles/1500005578782-ZOS-API-using-Python-NET)
- Internal: `.cursor/read-only-references/REFERENCE.md` §2.3, §5
