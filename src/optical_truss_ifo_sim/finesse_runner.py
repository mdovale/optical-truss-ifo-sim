"""FINESSE 3 cavity runner: inject beam states, scan detuning, extract visibility."""

from __future__ import annotations

import importlib
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy as np
import pandas as pd
from jinja2 import Environment, FileSystemLoader, StrictUndefined

from optical_truss_ifo_sim.schemas import BeamState, FinesseConfig, SampleStatus, VisibilityQCFlag
from optical_truss_ifo_sim.visibility import VisibilityResult, compute_visibility_00

if TYPE_CHECKING:
    from types import ModuleType


class FinesseNotAvailableError(RuntimeError):
    """Raised when the FINESSE 3 Python package is missing or shadowed."""


@dataclass(frozen=True)
class CavityPrescription:
    """Fixed two-mirror test cavity used for Milestone 2 validation."""

    cavity_length_m: float = 0.1
    mirror_r: float = 0.99
    mirror_t: float = 0.01
    mirror_rc_m: float = 0.5
    steer_arm_m: float = 0.01
    laser_power_w: float = 1.0


@dataclass(frozen=True)
class FinesseScanResult:
    """One beam state, reflected-power trace, and extracted visibility."""

    sample_id: str
    detuning_hz: np.ndarray
    reflected_power: np.ndarray
    visibility: VisibilityResult
    status: SampleStatus

    @property
    def v_00(self) -> float:
        return self.visibility.v_00


def finesse_available() -> bool:
    """Return True if FINESSE 3 can be imported (not the repo ``finesse/`` shadow)."""
    try:
        _import_finesse()
    except FinesseNotAvailableError:
        return False
    return True


def _repo_finesse_models_dir() -> Path | None:
    """Path to ``finesse/models`` when cwd shadows the Python package."""
    cwd = Path.cwd().resolve()
    models = cwd / "finesse" / "models"
    if models.is_dir():
        return models.resolve()
    return None


def _import_finesse() -> ModuleType:
    """
    Import FINESSE 3, avoiding the repository ``finesse/`` Kat model directory.

    When the working directory is the repo root, Python may load ``finesse/`` as a
    namespace package instead of the conda-installed library.
    """
    module = sys.modules.get("finesse")
    if module is not None and hasattr(module, "Model"):
        return module

    if module is not None:
        del sys.modules["finesse"]

    shadow_models = _repo_finesse_models_dir()
    saved_path = list(sys.path)
    try:
        if shadow_models is not None:
            filtered: list[str] = []
            for entry in sys.path:
                if not entry:
                    if shadow_models.parent == Path.cwd().resolve():
                        continue
                    filtered.append(entry)
                    continue
                try:
                    if (Path(entry).resolve() / "finesse" / "models") == shadow_models:
                        continue
                except OSError:
                    pass
                filtered.append(entry)
            sys.path[:] = filtered

        try:
            finesse = importlib.import_module("finesse")
        except ModuleNotFoundError as exc:
            raise FinesseNotAvailableError(
                "FINESSE 3 is not installed. Install with: conda install -c conda-forge finesse"
            ) from exc
    finally:
        sys.path[:] = saved_path

    if not hasattr(finesse, "Model"):
        msg = (
            "FINESSE 3 is not available. Install with "
            "'conda install -c conda-forge finesse' into this environment. "
            "If already installed, run Python from a directory that does not shadow "
            "the package with the repo's finesse/models/ folder, or use "
            "optical_truss_ifo_sim.finesse_runner.finesse_available() before calling."
        )
        raise FinesseNotAvailableError(msg)
    return finesse


def _steer_mirror_tilts(beam: BeamState, steer_arm_m: float) -> tuple[float, float]:
    """
    Map beam offset and angle at the cavity input to steering-mirror tilts.

    Uses a single mirror one *steer_arm_m* before the input mirror. Reflected-beam
    angle change is approximately ``2 * xbeta``; lateral shift at the cavity is
    approximately ``2 * steer_arm_m * xbeta`` for small angles.
    """
    if steer_arm_m <= 0.0:
        msg = "steer_arm_m must be positive"
        raise ValueError(msg)
    scale = 1.0 / (2.0 * steer_arm_m)
    xbeta = beam.x_angle_rad / 2.0 + beam.x_offset_m * scale
    ybeta = beam.y_angle_rad / 2.0 + beam.y_offset_m * scale
    return xbeta, ybeta


def render_cavity_kat(
    beam: BeamState,
    finesse_cfg: FinesseConfig,
    cavity: CavityPrescription,
    *,
    template_dir: Path | None = None,
) -> str:
    """Render KatScript for one cavity scan from the Jinja template."""
    if template_dir is None:
        template_dir = Path(__file__).resolve().parents[2] / "finesse" / "templates"
    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        undefined=StrictUndefined,
        autoescape=False,
    )
    template = env.get_template("cavity_scan.kat.j2")
    xbeta, ybeta = _steer_mirror_tilts(beam, cavity.steer_arm_m)
    return template.render(
        sample_id=beam.sample_id,
        laser_power_w=cavity.laser_power_w,
        wx_m=beam.wx_m,
        wy_m=beam.wy_m,
        zx_m=beam.zx_m,
        zy_m=beam.zy_m,
        maxtem=finesse_cfg.maxtem,
        steer_arm_m=cavity.steer_arm_m,
        steer_xbeta_rad=xbeta,
        steer_ybeta_rad=ybeta,
        mirror_r=cavity.mirror_r,
        mirror_t=cavity.mirror_t,
        mirror_rc_m=cavity.mirror_rc_m,
        cavity_length_m=cavity.cavity_length_m,
        detuning_start_hz=finesse_cfg.detuning_start_hz,
        detuning_stop_hz=finesse_cfg.detuning_stop_hz,
        detuning_points=finesse_cfg.detuning_points,
    )


def run_cavity_scan(
    beam: BeamState,
    finesse_cfg: FinesseConfig,
    cavity: CavityPrescription | None = None,
    *,
    template_dir: Path | None = None,
) -> FinesseScanResult:
    """Run a laser-frequency detuning scan and extract :math:`V_{00}`."""
    cavity = cavity or CavityPrescription()
    finesse = _import_finesse()
    kat_script = render_cavity_kat(beam, finesse_cfg, cavity, template_dir=template_dir)

    detuning_hz = np.linspace(
        finesse_cfg.detuning_start_hz,
        finesse_cfg.detuning_stop_hz,
        finesse_cfg.detuning_points,
    )
    reflected_power = np.full(detuning_hz.shape, np.nan, dtype=np.float64)

    try:
        model = finesse.Model()
        model.parse(kat_script)
        action = (
            f"xaxis(L0.f, lin, {finesse_cfg.detuning_start_hz}, "
            f"{finesse_cfg.detuning_stop_hz}, {finesse_cfg.detuning_points})"
        )
        solution = model.run(action)
        reflected_power = np.asarray(solution["refl"], dtype=np.float64)
        if solution.x is not None and len(solution.x):
            detuning_hz = np.asarray(solution.x[0], dtype=np.float64)
    except Exception:
        flags = (VisibilityQCFlag.FINESSE_RUN_FAILED,)
        visibility = VisibilityResult(
            v_00=float("nan"),
            p_max=float("nan"),
            p_min=float("nan"),
            detuning_at_min_hz=float("nan"),
            qc_flags=flags,
        )
        return FinesseScanResult(
            sample_id=beam.sample_id,
            detuning_hz=detuning_hz,
            reflected_power=reflected_power,
            visibility=visibility,
            status=SampleStatus.FINESSE_FAILED,
        )

    visibility = compute_visibility_00(detuning_hz, reflected_power)
    if not visibility.ok:
        status = SampleStatus.QC_FAILED
    else:
        status = SampleStatus.OK
    return FinesseScanResult(
        sample_id=beam.sample_id,
        detuning_hz=detuning_hz,
        reflected_power=reflected_power,
        visibility=visibility,
        status=status,
    )


def run_beam_batch(
    beams: list[BeamState],
    finesse_cfg: FinesseConfig,
    cavity: CavityPrescription | None = None,
) -> list[FinesseScanResult]:
    """Run FINESSE sequentially for each beam state."""
    return [run_cavity_scan(beam, finesse_cfg, cavity) for beam in beams]


def load_beam_states(path: Path) -> list[BeamState]:
    """Load beam states from CSV or Parquet."""
    path = path.resolve()
    if not path.is_file():
        msg = f"Beam-state file not found: {path}"
        raise FileNotFoundError(msg)

    suffix = path.suffix.lower()
    if suffix == ".parquet":
        frame = pd.read_parquet(path)
    elif suffix in {".csv", ".tsv"}:
        frame = pd.read_csv(path)
    else:
        msg = f"Unsupported beam-state format: {path.suffix}"
        raise ValueError(msg)

    return [BeamState.model_validate(row) for row in frame.to_dict(orient="records")]


def results_to_dataframe(results: list[FinesseScanResult]) -> pd.DataFrame:
    """Flatten scan results for Parquet/CSV export."""
    rows: list[dict[str, Any]] = []
    for item in results:
        row: dict[str, Any] = {
            "sample_id": item.sample_id,
            "status": item.status.value,
            "v_00": item.visibility.v_00,
            "p_max": item.visibility.p_max,
            "p_min": item.visibility.p_min,
            "detuning_at_min_hz": item.visibility.detuning_at_min_hz,
            "qc_flags": ",".join(f.value for f in item.visibility.qc_flags),
        }
        rows.append(row)
    return pd.DataFrame(rows)


def write_finesse_results(
    results: list[FinesseScanResult],
    output_path: Path,
) -> None:
    """Write summary results table to Parquet or CSV."""
    frame = results_to_dataframe(results)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.suffix.lower() == ".parquet":
        frame.to_parquet(output_path, index=False)
    else:
        frame.to_csv(output_path, index=False)
