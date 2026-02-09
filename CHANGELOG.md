# Changelog

All notable changes to this project are documented in this file.

## [Unreleased]

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
