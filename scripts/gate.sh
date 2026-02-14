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

echo "[gate] secrets"
tracked_env_files="$(git ls-files | grep -E '(^|/)\\.env($|\\.)' | grep -Ev '(^|/)\\.env\\.(example|sample)$' || true)"
if [[ -n "$tracked_env_files" ]]; then
  echo "FAIL: tracked .env file(s) detected:"
  echo "$tracked_env_files"
  exit 1
fi
if command -v gitleaks >/dev/null 2>&1; then
  gitleaks detect --source . --no-git --redact --exit-code 1
else
  echo "SKIP: gitleaks not installed"
fi

echo "[gate] dependencies"
if [[ -f requirements.txt ]]; then
  test -s requirements.txt
elif [[ -f pyproject.toml ]]; then
  :
else
  echo "FAIL: missing dependency manifest (requirements.txt or pyproject.toml)"
  exit 1
fi
if "$PYTHON_BIN" -m pip --version >/dev/null 2>&1; then
  "$PYTHON_BIN" -m pip check
else
  echo "SKIP: pip not available for dependency integrity check"
fi
if command -v pip-audit >/dev/null 2>&1 && [[ -f requirements.txt ]]; then
  pip-audit -r requirements.txt
else
  echo "SKIP: pip-audit not installed or requirements.txt missing"
fi

echo "[gate] done"
