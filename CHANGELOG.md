# Changelog

All notable changes to this project are documented in this file.

## [Unreleased]

### Added
- v2 gesture map with activity state transitions:
  - `FIST` -> stop
  - `ILY SIGN` -> studying
  - `THUMBS UP` -> youtube
  - `OPEN PALM` -> lol
- Per-activity timers with live HUD display while app is running.

### Changed
- Console output now reports activity transitions (`ACTIVE: ...` / `STOPPED`) instead of numeric gesture ids.

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
