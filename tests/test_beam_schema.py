"""Tests for beam-state schema validation."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from optical_truss_ifo_sim.schemas import BeamState


def test_minimal_beam_state() -> None:
    row = BeamState(
        sample_id="mc_00001",
        x_offset_m=0.0,
        y_offset_m=0.0,
        x_angle_rad=0.0,
        y_angle_rad=0.0,
        wx_m=50e-6,
        wy_m=50e-6,
        zx_m=0.0,
        zy_m=0.0,
    )
    assert row.sample_id == "mc_00001"
    assert row.wx_m == pytest.approx(50e-6)


def test_negative_waist_rejected() -> None:
    with pytest.raises(ValidationError):
        BeamState(
            sample_id="bad",
            x_offset_m=0.0,
            y_offset_m=0.0,
            x_angle_rad=0.0,
            y_angle_rad=0.0,
            wx_m=-1.0,
            wy_m=50e-6,
            zx_m=0.0,
            zy_m=0.0,
        )


def test_empty_sample_id_rejected() -> None:
    with pytest.raises(ValidationError):
        BeamState(
            sample_id="",
            x_offset_m=0.0,
            y_offset_m=0.0,
            x_angle_rad=0.0,
            y_angle_rad=0.0,
            wx_m=50e-6,
            wy_m=50e-6,
            zx_m=0.0,
            zy_m=0.0,
        )
