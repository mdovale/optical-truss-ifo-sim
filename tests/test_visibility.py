"""Tests for TEM00 visibility extraction from synthetic traces."""

from __future__ import annotations

import numpy as np
import pytest

from optical_truss_ifo_sim.schemas import VisibilityQCFlag
from optical_truss_ifo_sim.visibility import compute_visibility_00


def _lorentzian_dip(
    detuning_hz: np.ndarray,
    *,
    p_max: float = 1.0,
    depth: float = 0.8,
    width_hz: float = 1.0e5,
) -> np.ndarray:
    """Synthetic reflected power with a single Lorentzian dip at zero detuning."""
    return p_max - depth * (width_hz**2) / (detuning_hz**2 + width_hz**2)


def test_ideal_visibility_near_unity() -> None:
    detuning = np.linspace(-10e6, 10e6, 2001)
    power = _lorentzian_dip(detuning, p_max=1.0, depth=0.99, width_hz=2e5)
    result = compute_visibility_00(detuning, power)
    assert result.ok
    assert result.v_00 == pytest.approx(0.99, rel=0.02, abs=0.02)
    assert result.p_max == pytest.approx(1.0, rel=0.05)
    assert result.p_min < result.p_max


def test_zero_contrast_gives_zero_visibility() -> None:
    detuning = np.linspace(-1e6, 1e6, 501)
    power = np.ones_like(detuning)
    result = compute_visibility_00(detuning, power)
    assert VisibilityQCFlag.RESONANCE_NOT_FOUND in result.qc_flags
    assert result.v_00 == pytest.approx(0.0, abs=1e-6)


def test_symmetric_dip_centered_at_zero() -> None:
    detuning = np.linspace(-5e6, 5e6, 1001)
    power = _lorentzian_dip(detuning, depth=0.5)
    result = compute_visibility_00(detuning, power)
    assert result.detuning_at_min_hz == pytest.approx(0.0, abs=5e4)


def test_mismatched_array_lengths() -> None:
    with pytest.raises(ValueError, match="same shape"):
        compute_visibility_00(np.array([0.0, 1.0]), np.array([1.0]))


def test_too_few_points_flags_narrow_scan() -> None:
    detuning = np.array([0.0, 1.0])
    power = np.array([1.0, 0.5])
    result = compute_visibility_00(detuning, power)
    assert VisibilityQCFlag.SCAN_RANGE_TOO_NARROW in result.qc_flags


def test_visibility_formula_manual() -> None:
    detuning = np.linspace(-1e7, 1e7, 401)
    p_max, p_min = 2.0, 0.5
    power = np.full(detuning.shape, p_max)
    power[len(power) // 2] = p_min
    result = compute_visibility_00(detuning, power, edge_fraction=0.2)
    expected = (p_max - p_min) / (p_max + p_min)
    assert result.v_00 == pytest.approx(expected, rel=0.05)
