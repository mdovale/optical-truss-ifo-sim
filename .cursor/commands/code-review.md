# Code Review

## Objective

Review changes in this repository (or a user-specified scope) against
[BLUEPRINT.md](../../BLUEPRINT.md), project rules, and simulation-domain
correctness. Produce an actionable review the author can apply without guessing.

**Read-only by default:** do not `git add`, `git commit`, `git push`, or edit
files unless the user explicitly asks you to fix issues or commit. For strict
read-only mode, see `.cursor/commands/no-git-mutations.md`.

## Invocation

The user may provide:

- Nothing → review the **current working tree** vs `HEAD` (staged + unstaged +
  relevant untracked files under `src/`, `tests/`, `configs/`, `finesse/`,
  `docs/`, not ignored build artifacts).
- A **branch or commit range** (e.g. `main...HEAD`, `abc123..def456`).
- **Paths or a PR URL** — narrow the review to those files.

If scope is ambiguous, ask one concise question, then proceed.

## Phase 1 — Gather context

1. **Scope the diff**
   - `git status -sb`
   - `git diff` / `git diff --cached` as appropriate
   - For a range: `git log --oneline <base>..HEAD` and
     `git diff <base>...HEAD`
2. **Read design context** when the change touches the corresponding area:
   - [BLUEPRINT.md](../../BLUEPRINT.md) — workflow, data model, milestones
   - [docs/coordinate_conventions.md](../../docs/coordinate_conventions.md) —
     beam-state SI units and reference plane
   - [docs/milestone-1.md](../../docs/milestone-1.md) — what is implemented vs
     stubbed
   - [AGENTS.md](../../AGENTS.md) and `.cursor/rules/python-venv.mdc` — `.venv`,
     FINESSE, ZOSPy
3. **Run checks** on changed Python (from repo root, using `.venv`):

   ```bash
   .venv/bin/python -m pytest
   .venv/bin/ruff check src tests
   ```

   If `.venv` is missing, note it and run checks after suggesting
   `pip install -e ".[dev]"` — do not switch to system Python.

   For FINESSE- or Zemax-touching changes, note whether FINESSE/ZOSPy were
   exercised; unit tests alone may suffice for orchestration-only diffs.

## Phase 2 — Review dimensions

Evaluate each applicable category. Skip categories with no relevant changes.

### A. Blueprint and architecture fit

- Does the change belong in the right module (`zemax_api`, `beam_export`,
  `finesse_runner`, `visibility`, `config`, `cli`, …)?
- Are stub boundaries respected (Milestone 1 skeleton vs Milestone 2+ FINESSE,
  Milestone 3+ Zemax)?
- Is configuration in YAML/dataclasses rather than buried in opaque tool files?
- Does the Zemax→FINESSE handoff preserve the beam-state contract (BLUEPRINT
  §6)?

### B. Physics and units

- **SI units** in code paths and intermediate data (`_m`, `_rad`, `_hz`).
- Reference plane: $z=0$ at cavity input; positive $z$ toward return mirror
  ([docs/coordinate_conventions.md](../../docs/coordinate_conventions.md)).
- Visibility: $V_{00} = (P_{\max}-P_{\min})/(P_{\max}+P_{\min})$ consistent with
  BLUEPRINT §9; QC flags for bad scans, not silent nonsense values.
- Tolerance/compensation bounds: ordered ranges, finite resolution, documented
  semantics.

### C. Configuration and schema

- Pydantic models in `optical_truss_ifo_sim.schemas` — `extra="forbid"` where
  intended; validation errors are clear.
- YAML `includes` merge behavior unchanged or intentionally updated with tests.
- New config keys reflected in `configs/*.yaml` examples when user-facing.

### D. Python quality

- Minimal scope; no drive-by refactors unrelated to the change.
- Matches existing naming, types, and import style (`optical_truss_ifo_sim`).
- Comments only for non-obvious physics or tool quirks.
- No new dependencies without `pyproject.toml` justification.

### E. CLI and UX

- `oti-pipeline` commands: correct exit codes, helpful errors, no silent
  failures.
- Stub commands remain clearly stubbed (exit 2 + message) until implemented.

### F. Tests

- Meaningful coverage for real behavior (config load, schema, visibility math,
  future FINESSE regressions in `tests/reference_data/`).
- Avoid tests that only restate types or trivial getters.
- New physics or algorithms need edge cases (empty scan, flat baseline, sign
  symmetry where applicable per BLUEPRINT §12).

### G. Documentation

- User-facing or API changes update `README.md`, `docs/`, or milestone notes when
  appropriate.
- Math in markdown uses `$…$` / `$$…$$` per `.cursor/rules/markdown-math.mdc`.

### H. Process and maintainability

- `.cursor/rules/no-hacky-workarounds.mdc` — no timing retries, silent drops of
  failed Monte Carlo samples, or framework-fighting patches; prefer a handoff in
  `docs/handoffs/` when stuck.
- Reproducibility: seeds, manifests, and metadata paths considered for pipeline
  runs (BLUEPRINT §3.5).
- Secrets, machine-local paths, and generated `data/` artifacts not committed.

## Phase 3 — Report format

Return a structured review in this order:

```markdown
## Code review — <scope summary>

**Verdict:** [Approve | Approve with nits | Request changes]
**Checks:** pytest: <pass/fail/skip> · ruff: <pass/fail/skip>

### Summary
<2–4 sentences: what changed and whether it matches intent>

### Blockers
<Must fix before merge — correctness, security, broken tests, blueprint violations>
- ...

### Suggestions
<Should fix — clarity, missing tests, doc gaps>
- ...

### Nits
<Optional — style, naming>
- ...

### Blueprint / milestone notes
<Only if relevant — e.g. "This belongs in M2 finesse_runner">
- ...
```

For each finding, cite **file paths** (and line ranges when helpful). Prefer
code citation blocks for non-obvious issues. Do not paste entire files.

## Anti-patterns

- Vague praise with no findings when the diff is non-trivial.
- Reviewing only the diff hunk without reading call sites or schema consumers.
- Suggesting system `python`/`pip` instead of `.venv`.
- Recommending large rewrites outside the change scope.
- Auto-committing or auto-fixing without the user asking.

## If the user asks to address findings

1. Fix blockers first, then suggestions.
2. Re-run pytest and ruff.
3. Summarize what changed; offer a commit message via
   `.cursor/commands/commit-message.md` only if they want to commit.
