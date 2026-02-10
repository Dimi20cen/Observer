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

## 2026-02-10
- Summary: Updated gesture/activity contract. `OPEN PALM` now stops activity, with `ONE FINGER` for YouTube and `TWO FINGERS` for LoL based on user examples.
- Affected files: `observer/constants.py`, `observer/gestures.py`, `observer/activity.py`, `tests/test_logic.py`, `README.md`, `docs/OVERVIEW.md`, `CHANGELOG.md`
- Migration notes: Replace any previous expectations of `FIST`/`THUMBS UP` behavior with the new gesture mapping.
- Validation status: Passed (`./scripts/gate.sh`).

## 2026-02-10
- Summary: Simplified orientation gating so gestures are ignored only when the outside/back of the hand is showing, reducing sensitivity to palm-facing threshold tuning.
- Affected files: `observer/gestures.py`, `tests/test_logic.py`, `README.md`, `docs/OVERVIEW.md`, `CHANGELOG.md`
- Migration notes: `Palm OK` now means "outside of hand not detected" instead of strict full-palm orientation.
- Validation status: Passed (`./scripts/gate.sh`).

## 2026-02-10
- Summary: Made `ILY SIGN` detection less strict by loosening thumb requirements while keeping index/pinky up and middle/ring down.
- Affected files: `observer/gestures.py`, `tests/test_logic.py`, `CHANGELOG.md`
- Migration notes: `ILY SIGN` should trigger more reliably with slight thumb-angle variation.
- Validation status: Passed (`./scripts/gate.sh`).

## 2026-02-10
- Summary: Added live per-gesture debug overlay showing pass/fail checks for `OPEN`, `ILY`, `ONE`, and `TWO`.
- Affected files: `observer/gestures.py`, `observer/runtime.py`, `observer/ui.py`, `README.md`, `CHANGELOG.md`
- Migration notes: No behavior change; debug lines are informational only.
- Validation status: Passed (`./scripts/gate.sh`).

## 2026-02-10
- Summary: Added `d` runtime hotkey to toggle debug overlay visibility.
- Affected files: `observer/runtime.py`, `README.md`, `CHANGELOG.md`
- Migration notes: Press `d` in the app window to show/hide debug lines.
- Validation status: Passed (`./scripts/gate.sh`).

## 2026-02-10
- Summary: Addressed review findings by tightening outside-hand fallback logic, skipping debug check computation when debug is hidden, and adding direct classifier tests for all gestures.
- Affected files: `observer/gestures.py`, `observer/runtime.py`, `tests/test_logic.py`, `CHANGELOG.md`
- Migration notes: Unknown-handedness frames now use depth fallback to detect outside-hand orientation.
- Validation status: Passed (`./scripts/gate.sh`).
