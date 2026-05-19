# Validation cases

Physics and regression checks for the OTI tolerance pipeline. Milestone 2 covers
FINESSE-only cases; cross-tool Zemax checks arrive in Milestone 3+.

## FINESSE-only (Milestone 2)

Reference beam states: `tests/reference_data/beam_states_nominal.csv`.

| Case | Perturbation | Expected behaviour |
|------|--------------|-------------------|
| `nominal` | Mode-matched Gaussian at cavity input | $V_{00} \gtrsim 0.5$ (high visibility) |
| `offset_x` | 5 µm lateral offset | $V_{00}$ lower than nominal |
| `angle_x` | 50 µrad yaw | $V_{00}$ lower than nominal |
| `waist_mismatch` | Larger $w_x$ | $V_{00}$ lower than nominal |

Automated tests: `tests/test_finesse_runner.py` (skipped when FINESSE is not installed).

Run manually:

```bash
oti-pipeline finesse-run tests/reference_data/beam_states_nominal.csv \
  configs/finesse_validation.yaml
```

## Visibility unit tests (synthetic traces)

`tests/test_visibility.py` exercises $V_{00}$ extraction without FINESSE using
Lorentzian dips and edge cases (flat baseline, narrow scan, formula consistency).

## Planned (later milestones)

- Zemax-exported beam vs analytic expectations
- `maxtem` convergence sweeps
- Paired compensated / uncompensated Monte Carlo statistics

See [BLUEPRINT.md](../BLUEPRINT.md) section 12 for the full test strategy.
