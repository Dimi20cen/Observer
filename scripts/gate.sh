#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="./venv/bin/python"
if [[ ! -x "$PYTHON_BIN" ]]; then
  PYTHON_BIN="python"
fi

echo "[gate] lint (syntax)"
"$PYTHON_BIN" -m py_compile app.py tests/test_logic.py

echo "[gate] typecheck"
echo "SKIP: no type checker configured"

echo "[gate] test"
"$PYTHON_BIN" -m unittest discover -s tests -p "test_*.py"

echo "[gate] docs"
test -f README.md
test -f docs/OVERVIEW.md
test -f docs/changes.md

echo "[gate] done"
