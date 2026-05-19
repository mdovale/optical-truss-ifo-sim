"""Pydantic models for pipeline configuration and beam-state handoff."""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class SampleStatus(StrEnum):
    """Per-sample pipeline status (see BLUEPRINT section 14)."""

    OK = "OK"
    ZEMAX_FAILED = "ZEMAX_FAILED"
    ZEMAX_OPTIMIZATION_FAILED = "ZEMAX_OPTIMIZATION_FAILED"
    BEAM_EXPORT_INVALID = "BEAM_EXPORT_INVALID"
    FINESSE_FAILED = "FINESSE_FAILED"
    VISIBILITY_EXTRACTION_FAILED = "VISIBILITY_EXTRACTION_FAILED"
    QC_FAILED = "QC_FAILED"


class VisibilityQCFlag(StrEnum):
    """Quality-control flags for visibility extraction."""

    RESONANCE_NOT_FOUND = "resonance_not_found"
    MULTIPLE_MINIMA = "multiple_competing_minima"
    SCAN_RANGE_TOO_NARROW = "scan_range_too_narrow"
    BASELINE_UNSTABLE = "reflected_baseline_unstable"
    FINESSE_RUN_FAILED = "finesse_run_failed"
    VISIBILITY_OUT_OF_BOUNDS = "visibility_out_of_bounds"


class RunConfig(BaseModel):
    """Top-level run metadata."""

    model_config = ConfigDict(extra="forbid")

    name: str
    random_seed: int = Field(ge=0)
    n_samples: int = Field(ge=1)
    output_dir: Path

    @field_validator("output_dir", mode="before")
    @classmethod
    def _path(cls, value: str | Path) -> Path:
        return Path(value)


class ZemaxConfig(BaseModel):
    """Zemax / ZOSPy model settings."""

    model_config = ConfigDict(extra="forbid")

    model_path: Path
    reference_plane: Literal["cavity_input"] = "cavity_input"
    wavelength_m: float = Field(gt=0.0)

    @field_validator("model_path", mode="before")
    @classmethod
    def _path(cls, value: str | Path) -> Path:
        return Path(value)


class FinesseConfig(BaseModel):
    """FINESSE cavity scan settings."""

    model_config = ConfigDict(extra="forbid")

    model_template: Path | None = None
    model_path: Path | None = None
    maxtem: int = Field(ge=0, default=10)
    detuning_start_hz: float
    detuning_stop_hz: float
    detuning_points: int = Field(ge=3)

    @field_validator("model_template", "model_path", mode="before")
    @classmethod
    def _optional_path(cls, value: str | Path | None) -> Path | None:
        if value is None:
            return None
        return Path(value)

    @model_validator(mode="after")
    def _detuning_range(self) -> FinesseConfig:
        if self.detuning_stop_hz <= self.detuning_start_hz:
            msg = "detuning_stop_hz must be greater than detuning_start_hz"
            raise ValueError(msg)
        return self

    @model_validator(mode="after")
    def _model_source(self) -> FinesseConfig:
        if self.model_template is None and self.model_path is None:
            msg = "Either model_template or model_path must be set"
            raise ValueError(msg)
        return self


class CompensationConfig(BaseModel):
    """Input-beam collimator compensation bounds and resolution."""

    model_config = ConfigDict(extra="forbid")

    enabled: bool = False
    x_range_m: tuple[float, float]
    y_range_m: tuple[float, float]
    theta_x_range_rad: tuple[float, float]
    theta_y_range_rad: tuple[float, float]
    x_resolution_m: float = Field(gt=0.0)
    y_resolution_m: float = Field(gt=0.0)
    theta_x_resolution_rad: float = Field(gt=0.0)
    theta_y_resolution_rad: float = Field(gt=0.0)

    @model_validator(mode="after")
    def _ordered_ranges(self) -> CompensationConfig:
        for name, pair in (
            ("x_range_m", self.x_range_m),
            ("y_range_m", self.y_range_m),
            ("theta_x_range_rad", self.theta_x_range_rad),
            ("theta_y_range_rad", self.theta_y_range_rad),
        ):
            if pair[1] <= pair[0]:
                msg = f"{name} must be (min, max) with max > min"
                raise ValueError(msg)
        return self


class ToleranceParameter(BaseModel):
    """Single randomized tolerance entry."""

    model_config = ConfigDict(extra="forbid")

    distribution: Literal["uniform", "normal", "fixed"] = "uniform"
    nominal_m: float | None = None
    nominal_rad: float | None = None
    half_width_m: float | None = Field(default=None, ge=0.0)
    half_width_rad: float | None = Field(default=None, ge=0.0)
    std_m: float | None = Field(default=None, gt=0.0)
    std_rad: float | None = Field(default=None, gt=0.0)

    @model_validator(mode="after")
    def _distribution_parameters(self) -> ToleranceParameter:
        nominal_is_length = self.nominal_m is not None
        nominal_is_angle = self.nominal_rad is not None
        if nominal_is_length == nominal_is_angle:
            msg = "Exactly one of nominal_m or nominal_rad must be set"
            raise ValueError(msg)

        unit = "m" if nominal_is_length else "rad"
        other_unit = "rad" if nominal_is_length else "m"
        half_width = getattr(self, f"half_width_{unit}")
        std = getattr(self, f"std_{unit}")
        other_half_width = getattr(self, f"half_width_{other_unit}")
        other_std = getattr(self, f"std_{other_unit}")
        if other_half_width is not None or other_std is not None:
            msg = "Tolerance spread units must match the nominal unit"
            raise ValueError(msg)

        if self.distribution == "uniform":
            if half_width is None:
                msg = f"uniform distribution requires half_width_{unit}"
                raise ValueError(msg)
            if std is not None:
                msg = f"uniform distribution must not set std_{unit}"
                raise ValueError(msg)
        elif self.distribution == "normal":
            if std is None:
                msg = f"normal distribution requires std_{unit}"
                raise ValueError(msg)
            if half_width is not None:
                msg = f"normal distribution must not set half_width_{unit}"
                raise ValueError(msg)
        elif half_width is not None or std is not None:
            msg = "fixed distribution must not set spread parameters"
            raise ValueError(msg)
        return self


class BeamState(BaseModel):
    """Minimum Zemax→FINESSE handoff row (SI units, cavity input reference plane)."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    sample_id: Annotated[str, Field(min_length=1)]
    x_offset_m: float
    y_offset_m: float
    x_angle_rad: float
    y_angle_rad: float
    wx_m: float = Field(gt=0.0)
    wy_m: float = Field(gt=0.0)
    zx_m: float
    zy_m: float
    seed: int | None = None
    case_type: str | None = None
    compensation_enabled: bool | None = None
    q_x_real_m: float | None = None
    q_x_imag_m: float | None = None
    q_y_real_m: float | None = None
    q_y_imag_m: float | None = None
    collimator_x_m: float | None = None
    collimator_y_m: float | None = None
    collimator_theta_x_rad: float | None = None
    collimator_theta_y_rad: float | None = None
    zemax_status: str | None = None
    zemax_merit: float | None = None


class PipelineConfig(BaseModel):
    """Validated merged configuration for a pipeline run."""

    model_config = ConfigDict(extra="forbid")

    run: RunConfig
    zemax: ZemaxConfig
    finesse: FinesseConfig
    compensation: CompensationConfig | None = None
    tolerances: dict[str, ToleranceParameter] | None = None

    def model_dump_paths_relative(self, base: Path) -> dict[str, Any]:
        """Serialize config with paths relative to *base* for manifests."""

        def _rel(p: Path) -> str:
            try:
                return str(p.relative_to(base))
            except ValueError:
                return str(p)

        data = self.model_dump(mode="json")
        data["run"]["output_dir"] = _rel(self.run.output_dir)
        data["zemax"]["model_path"] = _rel(self.zemax.model_path)
        if self.finesse.model_template is not None:
            data["finesse"]["model_template"] = _rel(self.finesse.model_template)
        if self.finesse.model_path is not None:
            data["finesse"]["model_path"] = _rel(self.finesse.model_path)
        return data
