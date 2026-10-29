#!/usr/bin/env bash
set -euo pipefail

# Run from any directory; install dependencies into this repository's .venv.
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

if ! command -v python3.13 >/dev/null 2>&1; then
  echo "Python 3.13 is recommended. Install Python 3.13, then rerun this script."
  echo "If your 'python3' is already Python 3.13, run: python3 -m venv .venv"
  exit 1
fi

python3.13 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
printf '\nEnvironment created. Activate it with:\n  source .venv/bin/activate\n'
printf 'Then copy .env.example to .env and configure DATABASE_URL for your local MySQL instance.\n'
