"""Load and validate YAML pipeline configuration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from optical_truss_ifo_sim.schemas import PipelineConfig


class ConfigError(Exception):
    """Raised when configuration files cannot be loaded or validated."""


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge *override* into *base* (override wins on leaves)."""
    merged = dict(base)
    for key, value in override.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_yaml(path: Path) -> dict[str, Any]:
    """Parse a YAML file; raise ConfigError on I/O or syntax errors."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigError(f"Cannot read config file: {path}") from exc
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise ConfigError(f"Invalid YAML in {path}") from exc
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ConfigError(f"Config root must be a mapping: {path}")
    return data


def _resolve_includes(
    data: dict[str, Any],
    config_dir: Path,
    *,
    _stack: frozenset[Path] = frozenset(),
) -> dict[str, Any]:
    """Expand ``includes`` list by deep-merging referenced YAML files."""
    includes = data.pop("includes", None)
    if not includes:
        return data
    if not isinstance(includes, list):
        raise ConfigError("'includes' must be a list of paths")

    merged: dict[str, Any] = {}
    for entry in includes:
        include_path = (config_dir / str(entry)).resolve()
        if include_path in _stack:
            raise ConfigError(f"Circular include detected: {include_path}")
        if not include_path.is_file():
            raise ConfigError(f"Included config not found: {include_path}")
        child = load_yaml(include_path)
        child = _resolve_includes(child, include_path.parent, _stack=_stack | {include_path})
        merged = _deep_merge(merged, child)
    return _deep_merge(merged, data)


def load_config(path: Path, *, repo_root: Path | None = None) -> PipelineConfig:
    """
    Load a pipeline config from *path*, resolving ``includes`` relative to its directory.

    Paths inside the validated model are left as written in YAML; callers may resolve
    them against *repo_root* when checking file existence.
    """
    path = path.resolve()
    if not path.is_file():
        raise ConfigError(f"Config file not found: {path}")

    raw = load_yaml(path)
    raw = _resolve_includes(raw, path.parent)
    try:
        return PipelineConfig.model_validate(raw)
    except ValidationError as exc:
        raise ConfigError(f"Config validation failed for {path}:\n{exc}") from exc


def resolve_repo_paths(config: PipelineConfig, repo_root: Path) -> PipelineConfig:
    """Return a copy with relative paths resolved against *repo_root*."""
    root = repo_root.resolve()
    updates: dict[str, Any] = {}

    run = config.run.model_copy(
        update={"output_dir": _resolve_path(config.run.output_dir, root)}
    )
    updates["run"] = run

    zemax = config.zemax.model_copy(
        update={"model_path": _resolve_path(config.zemax.model_path, root)}
    )
    updates["zemax"] = zemax

    finesse_updates: dict[str, Any] = {}
    if config.finesse.model_template is not None:
        finesse_updates["model_template"] = _resolve_path(
            config.finesse.model_template, root
        )
    if config.finesse.model_path is not None:
        finesse_updates["model_path"] = _resolve_path(config.finesse.model_path, root)
    updates["finesse"] = config.finesse.model_copy(update=finesse_updates)

    return config.model_copy(update=updates)


def _resolve_path(path: Path, repo_root: Path) -> Path:
    if path.is_absolute():
        return path
    return (repo_root / path).resolve()
