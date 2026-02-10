# Changes Log

## 2026-02-10
- Summary: Added stricter gesture registration rules for v2 runtime. Gestures now require 1.5 seconds of stable detection and palm-facing orientation before activity transitions.
- Affected files: `app.py`, `README.md`, `docs/OVERVIEW.md`, `tests/test_logic.py`, `scripts/gate.sh`
- Migration notes: None.
- Validation status: Passed (`./scripts/gate.sh`).

## 2026-02-10
- Summary: Refactored monolithic `app.py` into a small `observer/` package without changing runtime behavior.
- Affected files: `app.py`, `observer/constants.py`, `observer/gestures.py`, `observer/gates.py`, `observer/activity.py`, `observer/runtime.py`, `observer/ui.py`, `README.md`, `docs/OVERVIEW.md`
- Migration notes: None (CLI remains `python app.py`).
- Validation status: Passed (`./scripts/gate.sh`).
