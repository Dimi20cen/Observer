# Observer v1 Overview

## Goal
Recognize 3 hand gestures from a live camera feed and print:

- `1` for `FIST`
- `2` for `OPEN PALM`
- `3` for `THUMBS UP`

## Input
- iPhone camera feed via Iriun (appears as a webcam device on desktop).

## Runtime
- `app.py` captures frames with OpenCV.
- MediaPipe detects hand landmarks (Solutions API when available, Tasks API fallback on Python 3.13 builds).
- Rule-based gesture logic classifies the hand shape.
- Temporal smoothing stabilizes predictions before printing.

## Output behavior
- Prints only when the stable detected gesture changes.
- Shows live preview window and current label.
- Quit key: `q`.
