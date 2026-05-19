# Coordinate conventions

Beam-state handoff between Zemax and FINESSE uses a single reference plane at the
cavity input mirror.

## Reference plane

- $z = 0$ at the cavity input reference plane.
- Positive $z$ points from the input mirror toward the return mirror.

## Beam parameters (SI units)

| Field | Meaning |
|-------|---------|
| `x_offset_m`, `y_offset_m` | Lateral beam-centroid offsets at the reference plane |
| `x_angle_rad`, `y_angle_rad` | Propagation angles relative to the nominal cavity axis |
| `wx_m`, `wy_m` | Waist radii in the two transverse axes (must be $> 0$) |
| `zx_m`, `zy_m` | Waist locations relative to the reference plane |

Optional fields (`q_*`, collimator states, Zemax merit) are validated when present;
see `optical_truss_ifo_sim.schemas.BeamState`.

## Validation

Pydantic models enforce types, sign constraints, and required minimum fields listed in
[BLUEPRINT.md](../BLUEPRINT.md) section 6.1.
