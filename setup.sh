#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
if command -v python3.12 >/dev/null 2>&1; then
  interpreter=python3.12
else
  interpreter=python3
fi
"$interpreter" -c 'import sys; assert sys.version_info[:2] == (3, 12), "Please install Python 3.12 first"'
"$interpreter" -m venv .venv
.venv/bin/python -m pip install .
printf '\nInstalled. Run: bash start.sh\n'
