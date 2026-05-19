"""Tests that do not require a working FINESSE installation."""

from __future__ import annotations

from pathlib import Path

import pytest

from optical_truss_ifo_sim.finesse_runner import (
    CavityPrescription,
    FinesseNotAvailableError,
    _steer_beamsplitter_tilts,
    finesse_available,
    load_beam_states,
    render_cavity_kat,
    results_to_dataframe,
)
from optical_truss_ifo_sim.schemas import BeamState, FinesseConfig

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_finesse_available_is_boolean() -> None:
    assert isinstance(finesse_available(), bool)


def test_render_kat_without_finesse_runtime() -> None:
    beam = BeamState(
        sample_id="unit",
        x_offset_m=1e-6,
        y_offset_m=0.0,
        x_angle_rad=10e-6,
        y_angle_rad=0.0,
        wx_m=279e-6,
        wy_m=279e-6,
        zx_m=0.35,
        zy_m=0.35,
    )
    cfg = FinesseConfig(
        model_template=Path("finesse/templates/cavity_scan.kat.j2"),
        model_path=Path("finesse/models/test_cavity.kat"),
        maxtem=4,
        detuning_start_hz=-1e6,
        detuning_stop_hz=1e6,
        detuning_points=101,
    )
    script = render_cavity_kat(beam, cfg, CavityPrescription())
    assert "bs1" in script
    assert "bs2" in script
    assert "Rc=-0.5" in script
    assert "w0x=0.000279" in script or "w0x=2.79e-4" in script


def test_steer_beamsplitter_tilts_separate_offset_and_angle() -> None:
    beam = BeamState(
        sample_id="s",
        x_offset_m=2e-6,
        y_offset_m=0.0,
        x_angle_rad=4e-6,
        y_angle_rad=0.0,
        wx_m=279e-6,
        wy_m=279e-6,
        zx_m=0.35,
        zy_m=0.35,
    )
    xbeta_1, ybeta_1, xbeta_2, ybeta_2 = _steer_beamsplitter_tilts(
        beam,
        steer_arm_m=0.01,
    )
    assert xbeta_1 == pytest.approx(2e-6 / 0.02 - 4e-6 / 2.0)
    assert xbeta_2 == pytest.approx(4e-6 - 2e-6 / 0.02)
    assert ybeta_1 == 0.0
    assert ybeta_2 == 0.0


def test_load_beam_states_csv() -> None:
    path = REPO_ROOT / "tests" / "reference_data" / "beam_states_nominal.csv"
    rows = load_beam_states(path)
    assert rows[0].sample_id == "nominal"


def test_results_to_dataframe_columns() -> None:
    if not finesse_available():
        pytest.skip("FINESSE not installed")
    from optical_truss_ifo_sim.finesse_runner import run_cavity_scan

    beam = BeamState(
        sample_id="df",
        x_offset_m=0.0,
        y_offset_m=0.0,
        x_angle_rad=0.0,
        y_angle_rad=0.0,
        wx_m=279e-6,
        wy_m=279e-6,
        zx_m=0.35,
        zy_m=0.35,
    )
    cfg = FinesseConfig(
        model_template=Path("finesse/templates/cavity_scan.kat.j2"),
        model_path=Path("finesse/models/test_cavity.kat"),
        maxtem=4,
        detuning_start_hz=-2e6,
        detuning_stop_hz=2e6,
        detuning_points=101,
    )
    result = run_cavity_scan(beam, cfg)
    frame = results_to_dataframe([result])
    assert "v_00" in frame.columns
    assert "x_offset_m" in frame.columns
    assert "scan_points" in frame.columns
    assert frame.iloc[0]["sample_id"] == "df"


def test_import_finesse_raises_clear_error_when_missing() -> None:
    if finesse_available():
        pytest.skip("FINESSE is installed")
    from optical_truss_ifo_sim.finesse_runner import _import_finesse

    with pytest.raises(FinesseNotAvailableError, match="conda install"):
        _import_finesse()
