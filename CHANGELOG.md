# Changelog

All notable changes to this project are documented in this file.

## [Unreleased]

### Added
- v2 gesture map with activity state transitions:
  - `OPEN PALM` -> stop
  - `ILY SIGN` -> studying
  - `ONE FINGER` -> youtube
  - `TWO FINGERS` -> lol
- Per-activity timers with live HUD display while app is running.
- Runtime gate script at `scripts/gate.sh`.
- Unit tests for activity tracking and gesture hold behavior.

### Changed
- Console output now reports activity transitions (`ACTIVE: ...` / `STOPPED`) instead of numeric gesture ids.
- Gestures must remain stable for at least 1.5 seconds before registration.
- Gesture registration now requires palm-facing orientation.
- Refactored runtime code into `observer/` modules to improve maintainability while preserving behavior.
- Replaced strict palm-threshold gating with a simpler outside-of-hand rejection rule.
- Relaxed `ILY SIGN` detection thresholds to reduce missed detections.
- Added on-screen debug breakdown for all gesture check predicates.
- Added `d` hotkey to toggle debug overlay visibility.
- Hardened outside-hand gating fallback and added direct gesture classifier tests.

## [0.1.0] - 2026-02-09

### Added
- Initial v1 hand gesture recognizer app (`FIST`, `OPEN PALM`, `THUMBS UP`) with camera input and console output.
- MediaPipe Tasks fallback path for Python 3.13 environments.
- Gesture robustness improvements:
  - stricter geometric gesture checks
  - temporal smoothing to reduce flicker/misclassification
- Setup and run documentation in `README.md`.
- Project overview in `docs/OVERVIEW.md`.
- Repository hygiene files: `.gitignore` and `AGENTS.md`.
