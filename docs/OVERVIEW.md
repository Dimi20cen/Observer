# Observer v2 Overview

## Goal
Recognize hand gestures from a live camera feed, map them to activities, and track per-activity time.

- `OPEN PALM` -> stop current activity
- `ILY SIGN` -> studying
- `ONE FINGER` -> watching YouTube
- `TWO FINGERS` -> playing LoL

## Input
- iPhone camera feed via Iriun (appears as a webcam device on desktop).

## Runtime
- `app.py` is a thin CLI entrypoint.
- MediaPipe detects hand landmarks (Solutions API when available, Tasks API fallback on Python 3.13 builds).
- Rule-based gesture logic classifies hand shape (`OPEN PALM`, `ILY SIGN`, `ONE FINGER`, `TWO FINGERS`).
- Temporal smoothing stabilizes predictions.
- Gesture hold gate requires `1.5s` of stable gesture before activity transitions.
- Outside-hand gate rejects gestures when the back/outside of the hand is showing.
- Activity state machine applies gesture->activity transitions.
- Timer accumulator keeps elapsed seconds for each activity.

## Package structure
- `observer/constants.py`: gesture and activity constants.
- `observer/gestures.py`: detection and outside-hand rejection geometry.
- `observer/gates.py`: temporal gate components.
- `observer/activity.py`: activity tracker + timer formatting.
- `observer/runtime.py`: camera/model runtime loops.
- `observer/ui.py`: frame HUD renderer.

## Output behavior
- Prints activity changes (`ACTIVE: ...` / `STOPPED`).
- Shows live preview window with gesture, active activity, and timers.
- Quit key: `q`.
