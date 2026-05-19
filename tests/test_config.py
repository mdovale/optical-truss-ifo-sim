"""Tests for YAML configuration loading and validation."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from optical_truss_ifo_sim.config import ConfigError, load_config, resolve_repo_paths

REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIGS = REPO_ROOT / "configs"


def test_load_monte_carlo_config() -> None:
    cfg = load_config(CONFIGS / "monte_carlo.yaml", repo_root=REPO_ROOT)
    assert cfg.run.name == "nominal_oti_mc"
    assert cfg.run.n_samples == 1000
    assert cfg.run.random_seed == 12345
    assert cfg.zemax.wavelength_m == pytest.approx(1.064e-6)
    assert cfg.finesse.maxtem == 10
    assert cfg.finesse.detuning_points == 2001
    assert cfg.compensation is not None
    assert cfg.compensation.enabled is True
    assert cfg.tolerances is not None
    assert cfg.tolerances is not None
    assert "lens_1_radius" in cfg.tolerances


def test_resolve_repo_paths() -> None:
    cfg = load_config(CONFIGS / "monte_carlo.yaml", repo_root=REPO_ROOT)
    resolved = resolve_repo_paths(cfg, REPO_ROOT)
    assert resolved.run.output_dir.is_absolute()
    assert resolved.zemax.model_path.is_absolute()
    assert resolved.finesse.model_path is not None
    assert resolved.finesse.model_path.name == "test_cavity.kat"


def test_invalid_detuning_range(tmp_path: Path) -> None:
    bad = {
        "run": {
            "name": "bad",
            "random_seed": 0,
            "n_samples": 1,
            "output_dir": "data/processed/bad",
        },
        "zemax": {
            "model_path": "zemax/models/oti_input_stage.zmx",
            "wavelength_m": 1.064e-6,
        },
        "finesse": {
            "model_path": "finesse/models/test_cavity.kat",
            "detuning_start_hz": 10.0,
            "detuning_stop_hz": -10.0,
            "detuning_points": 100,
        },
    }
    path = tmp_path / "bad.yaml"
    path.write_text(yaml.dump(bad), encoding="utf-8")
    with pytest.raises(ConfigError, match="validation failed"):
        load_config(path)


def test_circular_include(tmp_path: Path) -> None:
    a = tmp_path / "a.yaml"
    b = tmp_path / "b.yaml"
    a.write_text("includes:\n  - b.yaml\nrun: {}\n", encoding="utf-8")
    b.write_text("includes:\n  - a.yaml\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="Circular include"):
        load_config(a)


def test_compensation_range_order() -> None:
    from pydantic import ValidationError

    from optical_truss_ifo_sim.schemas import CompensationConfig

    with pytest.raises(ValidationError):
        CompensationConfig(
            enabled=True,
            x_range_m=[1.0, -1.0],
            y_range_m=[-1.0, 1.0],
            theta_x_range_rad=[-1.0, 1.0],
            theta_y_range_rad=[-1.0, 1.0],
            x_resolution_m=1e-6,
            y_resolution_m=1e-6,
            theta_x_resolution_rad=1e-5,
            theta_y_resolution_rad=1e-5,
        )


def test_finesse_yaml_requires_full_pipeline() -> None:
    with pytest.raises(ConfigError, match="validation failed"):
        load_config(CONFIGS / "finesse.yaml", repo_root=REPO_ROOT)
