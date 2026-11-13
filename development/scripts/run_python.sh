#!/bin/bash
set -euo pipefail
project_dir="$(cd "$(dirname "$0")/.." && pwd)"
cad_support="${GYRE_CAD_SUPPORT:-$HOME/Library/Application Support/Codex/Tools/Keyboard}"
if [[ -n "${GYRE_PYTHON:-}" ]]; then
  gyre_python="$GYRE_PYTHON"
elif [[ -x "$project_dir/.venv/bin/python" ]]; then
  gyre_python="$project_dir/.venv/bin/python"
elif [[ -x "$cad_support/build123d-mcp-venv/bin/python" ]]; then
  gyre_python="$cad_support/build123d-mcp-venv/bin/python"
  export PYTHONPATH="$cad_support/mesh-python${PYTHONPATH:+:$PYTHONPATH}"
else
  gyre_python="python3"
fi
export MPLCONFIGDIR="${MPLCONFIGDIR:-${TMPDIR:-/tmp}/gyre-mpl}"
export PYTHONDONTWRITEBYTECODE=1
export GYRE_PROJECT_ROOT="$project_dir"
cd "$project_dir"
exec "$gyre_python" "$@"
