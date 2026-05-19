#!/usr/bin/env bash
# Verify the repository .venv exists and FINESSE is importable.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
VENV="${REPO_ROOT}/.venv"
PYTHON="${VENV}/bin/python"

if [[ ! -x "${PYTHON}" ]]; then
  echo "Repository .venv not found: ${VENV}" >&2
  echo "Create it from ${REPO_ROOT}: python3 -m venv .venv && .venv/bin/pip install -e \".[dev]\"" >&2
  exit 1
fi

"${PYTHON}" -c "import finesse"

echo "Repository .venv OK: ${VENV}"
