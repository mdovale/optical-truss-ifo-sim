# Agent instructions

## Python environment

Use the repository **`.venv`** at the project root (not system Python):

`.venv/bin/python`

- **FINESSE 3** and **ZOSPy** should be installed in this venv.
- **This repo’s** pip dependencies and CLI are defined in `pyproject.toml`; install with `pip install -e ".[dev]"` after activating `.venv` (see `BLUEPRINT.md` §5.1).
- See `.cursor/rules/python-venv.mdc` for shell and command conventions.
