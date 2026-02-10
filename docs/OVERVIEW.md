# Observer v2 Overview

## Goal
Recognize hand gestures from a live camera feed, map them to activities, and track per-activity time.

- `FIST` -> stop current activity
- `ILY SIGN` -> studying
- `THUMBS UP` -> watching YouTube
- `OPEN PALM` -> playing LoL

## Input
- iPhone camera feed via Iriun (appears as a webcam device on desktop).

## Runtime
- `app.py` captures frames with OpenCV.
- MediaPipe detects hand landmarks (Solutions API when available, Tasks API fallback on Python 3.13 builds).
- Rule-based gesture logic classifies hand shape (`FIST`, `ILY SIGN`, `THUMBS UP`, `OPEN PALM`).
- Temporal smoothing stabilizes predictions.
- Activity state machine applies gesture->activity transitions.
- Timer accumulator keeps elapsed seconds for each activity.

## Output behavior
- Prints activity changes (`ACTIVE: ...` / `STOPPED`).
- Shows live preview window with gesture, active activity, and timers.
- Quit key: `q`.
