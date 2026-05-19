"""Command-line interface for the OTI tolerance pipeline."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from optical_truss_ifo_sim import __version__
from optical_truss_ifo_sim.config import ConfigError, load_config, resolve_repo_paths
from optical_truss_ifo_sim.finesse_runner import (
    finesse_available,
    load_beam_states,
    run_beam_batch,
    write_finesse_results,
)

app = typer.Typer(
    name="oti-pipeline",
    help="OTI cavity tolerance simulation: Zemax export, FINESSE, visibility analysis.",
    no_args_is_help=True,
)
console = Console()


def _repo_root() -> Path:
    """Repository root (directory containing pyproject.toml)."""
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "pyproject.toml").is_file():
            return parent
    return Path.cwd()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: Annotated[
        bool,
        typer.Option("--version", "-V", help="Show version and exit."),
    ] = False,
) -> None:
    if version:
        typer.echo(f"optical-truss-ifo-sim {__version__}")
        raise typer.Exit()
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()


@app.command("validate-config")
def validate_config(
    config_path: Annotated[
        Path,
        typer.Argument(help="Path to pipeline YAML (e.g. configs/monte_carlo.yaml)."),
    ],
) -> None:
    """Load and validate a pipeline configuration file."""
    repo = _repo_root()
    try:
        cfg = load_config(config_path, repo_root=repo)
        cfg = resolve_repo_paths(cfg, repo)
    except ConfigError as exc:
        console.print(f"[red]Config error:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    table = Table(title="Validated pipeline configuration")
    table.add_column("Section", style="cyan")
    table.add_column("Summary")
    run_summary = f"{cfg.run.name} — {cfg.run.n_samples} samples, seed {cfg.run.random_seed}"
    table.add_row("run", run_summary)
    table.add_row("zemax", str(cfg.zemax.model_path))
    finesse_src = cfg.finesse.model_path or cfg.finesse.model_template
    finesse_summary = (
        f"{finesse_src} — {cfg.finesse.detuning_points} detuning points, "
        f"maxtem={cfg.finesse.maxtem}"
    )
    table.add_row("finesse", finesse_summary)
    comp = "enabled" if cfg.compensation and cfg.compensation.enabled else "disabled"
    table.add_row("compensation", comp)
    tol_count = len(cfg.tolerances) if cfg.tolerances else 0
    table.add_row("tolerances", f"{tol_count} parameters")
    console.print(table)
    console.print("[green]Configuration is valid.[/green]")


@app.command("zemax-export")
def zemax_export(
    config_path: Annotated[Path, typer.Argument(help="Pipeline configuration YAML.")],
) -> None:
    """Export beam states from Zemax (not implemented until Milestone 3)."""
    _stub_command("zemax-export", config_path)


@app.command("finesse-run")
def finesse_run(
    beam_states: Annotated[
        Path,
        typer.Argument(help="Parquet/CSV beam-state table (manual or Zemax export)."),
    ],
    config_path: Annotated[Path, typer.Argument(help="Pipeline configuration YAML.")],
    output: Annotated[
        Path | None,
        typer.Option(
            "--output",
            "-o",
            help="Results table path (default: <run.output_dir>/finesse_results.csv).",
        ),
    ] = None,
) -> None:
    """Run FINESSE cavity scans and extract TEM00 visibility for each beam state."""
    if not finesse_available():
        console.print(
            "[red]FINESSE 3 is not installed[/red] in this environment. "
            "Install with: conda install -c conda-forge finesse"
        )
        raise typer.Exit(code=1)

    repo = _repo_root()
    try:
        cfg = load_config(config_path, repo_root=repo)
        cfg = resolve_repo_paths(cfg, repo)
    except ConfigError as exc:
        console.print(f"[red]Config error:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    beam_path = beam_states if beam_states.is_absolute() else (repo / beam_states)
    try:
        beams = load_beam_states(beam_path)
    except (FileNotFoundError, ValueError) as exc:
        console.print(f"[red]Beam states:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    console.print(f"Running FINESSE for [cyan]{len(beams)}[/cyan] beam state(s)...")
    results = run_beam_batch(beams, cfg.finesse)
    out_path = output or (cfg.run.output_dir / "finesse_results.csv")
    if not out_path.is_absolute():
        out_path = repo / out_path
    write_finesse_results(results, out_path)

    ok = sum(1 for r in results if r.status.value == "OK")
    console.print(
        f"[green]Wrote {out_path}[/green] — {ok}/{len(results)} samples with status OK."
    )


@app.command("analyze")
def analyze(
    output_dir: Annotated[
        Path,
        typer.Argument(help="Processed run directory (e.g. data/processed/nominal_oti_mc)."),
    ],
) -> None:
    """Compute summary statistics on a completed run (not implemented until later milestones)."""
    _stub_command("analyze", output_dir)


@app.command("run-full")
def run_full(
    config_path: Annotated[Path, typer.Argument(help="Pipeline configuration YAML.")],
) -> None:
    """Execute the full Zemax → FINESSE → analysis workflow (not implemented yet)."""
    _stub_command("run-full", config_path)


@app.command("make-report")
def make_report(
    output_dir: Annotated[
        Path,
        typer.Argument(help="Processed run directory."),
    ],
) -> None:
    """Generate figures and tables for a completed run (not implemented yet)."""
    _stub_command("make-report", output_dir)


def _stub_command(name: str, *paths: Path, extra: str | None = None) -> None:
    parts = ", ".join(str(p) for p in paths)
    detail = f" ({extra})" if extra else ""
    console.print(
        f"[yellow]{name}[/yellow] is a CLI skeleton for Milestone 1; "
        f"implementation is planned in a later milestone. Arguments: {parts}{detail}"
    )
    raise typer.Exit(code=2)


if __name__ == "__main__":
    app()
