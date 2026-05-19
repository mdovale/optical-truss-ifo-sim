"""TEM00 visibility extraction from reflected-power detuning scans."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from optical_truss_ifo_sim.schemas import VisibilityQCFlag


@dataclass(frozen=True)
class VisibilityResult:
    """Extracted visibility and quality metadata."""

    v_00: float
    p_max: float
    p_min: float
    detuning_at_min_hz: float
    qc_flags: tuple[VisibilityQCFlag, ...] = field(default_factory=tuple)

    @property
    def ok(self) -> bool:
        return len(self.qc_flags) == 0


def compute_visibility_00(
    detuning_hz: np.ndarray,
    reflected_power: np.ndarray,
    *,
    edge_fraction: float = 0.1,
    min_prominence_fraction: float = 0.01,
    v_bounds: tuple[float, float] = (-1e-6, 1.0 + 1e-6),
) -> VisibilityResult:
    """
    Compute $V_{00} = (P_{\\max} - P_{\\min}) / (P_{\\max} + P_{\\min})$ from a scan.

    * ``P_max`` is the median of edge samples (first/last ``edge_fraction`` of points).
    * ``P_min`` is the global minimum over the scan (expected TEM00 dip).
    """
    detuning_hz = np.asarray(detuning_hz, dtype=np.float64)
    reflected_power = np.asarray(reflected_power, dtype=np.float64)
    flags: list[VisibilityQCFlag] = []

    if detuning_hz.shape != reflected_power.shape:
        msg = "detuning_hz and reflected_power must have the same shape"
        raise ValueError(msg)
    if detuning_hz.size < 3:
        flags.append(VisibilityQCFlag.SCAN_RANGE_TOO_NARROW)
        return _failed_result(detuning_hz, reflected_power, flags)

    span = float(detuning_hz[-1] - detuning_hz[0])
    if span <= 0.0:
        flags.append(VisibilityQCFlag.SCAN_RANGE_TOO_NARROW)

    n_edge = max(1, int(edge_fraction * detuning_hz.size))
    edge_samples = np.concatenate(
        (reflected_power[:n_edge], reflected_power[-n_edge:])
    )
    p_max = float(np.median(edge_samples))
    p_min = float(np.min(reflected_power))
    idx_min = int(np.argmin(reflected_power))
    detuning_at_min = float(detuning_hz[idx_min])

    if not np.isfinite(p_max) or not np.isfinite(p_min):
        flags.append(VisibilityQCFlag.BASELINE_UNSTABLE)
        return _failed_result(detuning_hz, reflected_power, flags, p_max, p_min, detuning_at_min)

    edge_std = float(np.std(edge_samples))
    if p_max <= 0.0 or edge_std > 0.25 * abs(p_max):
        flags.append(VisibilityQCFlag.BASELINE_UNSTABLE)

    prominence = p_max - p_min
    if prominence < min_prominence_fraction * max(abs(p_max), 1e-30):
        flags.append(VisibilityQCFlag.RESONANCE_NOT_FOUND)

    if _has_competing_minima(reflected_power, p_min, min_prominence_fraction):
        flags.append(VisibilityQCFlag.MULTIPLE_MINIMA)

    denom = p_max + p_min
    if denom <= 0.0:
        flags.append(VisibilityQCFlag.BASELINE_UNSTABLE)
        v_00 = 0.0
    else:
        v_00 = (p_max - p_min) / denom

    if v_00 < v_bounds[0] or v_00 > v_bounds[1]:
        flags.append(VisibilityQCFlag.VISIBILITY_OUT_OF_BOUNDS)

    return VisibilityResult(
        v_00=v_00,
        p_max=p_max,
        p_min=p_min,
        detuning_at_min_hz=detuning_at_min,
        qc_flags=tuple(flags),
    )


def _has_competing_minima(
    power: np.ndarray,
    p_min: float,
    min_prominence_fraction: float,
) -> bool:
    """True if more than one local minimum is nearly as deep as the global minimum."""
    threshold = p_min + min_prominence_fraction * max(abs(p_min), 1e-30)
    local_mins: list[float] = []
    for i in range(1, len(power) - 1):
        if power[i] <= power[i - 1] and power[i] <= power[i + 1]:
            local_mins.append(float(power[i]))
    deep = [v for v in local_mins if v <= threshold]
    return len(deep) > 1


def _failed_result(
    detuning_hz: np.ndarray,
    reflected_power: np.ndarray,
    flags: list[VisibilityQCFlag],
    p_max: float = float("nan"),
    p_min: float = float("nan"),
    detuning_at_min: float = float("nan"),
) -> VisibilityResult:
    if detuning_hz.size:
        detuning_at_min = float(detuning_hz[int(np.argmin(reflected_power))])
        if reflected_power.size:
            p_min = float(np.min(reflected_power))
            p_max = float(np.median(reflected_power))
    return VisibilityResult(
        v_00=float("nan"),
        p_max=p_max,
        p_min=p_min,
        detuning_at_min_hz=detuning_at_min,
        qc_flags=tuple(flags),
    )
