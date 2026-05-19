"""Smoke tests for the Milestone 1 command-line interface."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from optical_truss_ifo_sim.cli import app

REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO_ROOT / "configs" / "monte_carlo.yaml"
runner = CliRunner()


def test_version_option() -> None:
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert "optical-truss-ifo-sim 0.1.0" in result.stdout


def test_validate_config_command() -> None:
    result = runner.invoke(app, ["validate-config", str(CONFIG_PATH)])

    assert result.exit_code == 0
    assert "Configuration is valid." in result.stdout


def test_stub_command_returns_exit_2() -> None:
    result = runner.invoke(app, ["zemax-export", str(CONFIG_PATH)])

    assert result.exit_code == 2
    assert "zemax-export" in result.stdout
    assert "CLI skeleton for Milestone 1" in result.stdout
