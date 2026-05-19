#!/usr/bin/env bash
# Verify the shared optisim venv exists and FINESSE is importable.
set -euo pipefail

OPTISIM_VENV="/Users/mdovale/Work-local/__virtual-environments/optisim"
PYTHON="${OPTISIM_VENV}/bin/python"

if [[ ! -x "${PYTHON}" ]]; then
  echo "optisim venv not found: ${OPTISIM_VENV}" >&2
  exit 1
fi

"${PYTHON}" -c "import finesse"

echo "optisim venv OK: ${OPTISIM_VENV}"
