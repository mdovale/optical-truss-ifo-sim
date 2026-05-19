"""FINESSE cavity runner and physics validation (requires FINESSE 3)."""

from __future__ import annotations

from pathlib import Path

import pytest

from optical_truss_ifo_sim.finesse_runner import (
    CavityPrescription,
    finesse_available,
    load_beam_states,
    render_cavity_kat,
    run_cavity_scan,
)
from optical_truss_ifo_sim.schemas import BeamState, FinesseConfig, SampleStatus

REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_BEAMS = REPO_ROOT / "tests" / "reference_data" / "beam_states_nominal.csv"

pytestmark = pytest.mark.skipif(
    not finesse_available(),
    reason="FINESSE 3 not installed (conda install -c conda-forge finesse)",
)

FINESSE_CFG = FinesseConfig(
    model_template=Path("finesse/templates/cavity_scan.kat.j2"),
    model_path=Path("finesse/models/test_cavity.kat"),
    maxtem=8,
    detuning_start_hz=-5.0e6,
    detuning_stop_hz=5.0e6,
    detuning_points=501,
)

NOMINAL_BEAM = BeamState(
    sample_id="nominal",
    x_offset_m=0.0,
    y_offset_m=0.0,
    x_angle_rad=0.0,
    y_angle_rad=0.0,
    wx_m=279e-6,
    wy_m=279e-6,
    zx_m=0.35,
    zy_m=0.35,
)


def test_render_cavity_kat_contains_beam_parameters() -> None:
    script = render_cavity_kat(NOMINAL_BEAM, FINESSE_CFG, CavityPrescription())
    assert "w0x=0.000279" in script or "w0x=2.79e-4" in script
    assert "Rc=-0.5" in script
    assert "xaxis(L0.f" in script
    assert "pd refl" in script


def test_nominal_visibility_high() -> None:
    result = run_cavity_scan(NOMINAL_BEAM, FINESSE_CFG)
    assert result.status == SampleStatus.OK
    assert result.visibility.ok
    assert result.v_00 > 0.95


def test_lateral_offset_reduces_visibility() -> None:
    offset = NOMINAL_BEAM.model_copy(
        update={"sample_id": "offset", "x_offset_m": 8e-6}
    )
    nominal = run_cavity_scan(NOMINAL_BEAM, FINESSE_CFG)
    misaligned = run_cavity_scan(offset, FINESSE_CFG)
    assert misaligned.v_00 < nominal.v_00


def test_angular_misalignment_reduces_visibility() -> None:
    tilted = NOMINAL_BEAM.model_copy(
        update={"sample_id": "tilt", "x_angle_rad": 80e-6}
    )
    nominal = run_cavity_scan(NOMINAL_BEAM, FINESSE_CFG)
    misaligned = run_cavity_scan(tilted, FINESSE_CFG)
    assert misaligned.v_00 < nominal.v_00


def test_waist_mismatch_reduces_visibility() -> None:
    mismatched = NOMINAL_BEAM.model_copy(
        update={"sample_id": "waist", "wx_m": 350e-6}
    )
    nominal = run_cavity_scan(NOMINAL_BEAM, FINESSE_CFG)
    bad = run_cavity_scan(mismatched, FINESSE_CFG)
    assert bad.v_00 < nominal.v_00


def test_reference_beam_table_loads() -> None:
    beams = load_beam_states(REFERENCE_BEAMS)
    assert len(beams) == 4
    assert beams[0].sample_id == "nominal"
