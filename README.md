# Observer v2

Recognize hand gestures from an iPhone camera feed (via Iriun), switch activities, and keep a running timer per activity:

- `FIST` -> stop current activity (`IDLE`)
- `ILY SIGN` -> `studying`
- `THUMBS UP` -> `youtube`
- `OPEN PALM` -> `lol`

## Setup

1. Install Python 3.10+.
2. Create and activate a virtual environment.
3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Run

1. Start Iriun Webcam on iPhone and desktop.
2. If you are on Python 3.13 (no `mp.solutions`), download the tasks model once:

```bash
mkdir -p models
wget -O models/hand_landmarker.task https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task
```

3. Run:

```bash
python app.py --camera-index 0
```

If no video appears, try other indexes (`1`, `2`, `3`).

## Runtime behavior

- Gesture is smoothed over multiple frames before switching activity.
- Gesture must remain stable for at least `1.5` seconds before it is accepted.
- Gesture is accepted only when palm side is facing the camera (`Palm OK: YES` in HUD).
- A cooldown prevents accidental rapid switching.
- On each valid switch, the app prints:
  - `ACTIVE: studying|youtube|lol`
  - `STOPPED`
- HUD displays current gesture, active activity, and timers.

## Code layout

- `app.py`: CLI entrypoint.
- `observer/constants.py`: gesture/activity constants and mapping.
- `observer/gestures.py`: hand geometry rules + palm-facing check.
- `observer/gates.py`: smoothing and hold gates.
- `observer/activity.py`: activity state machine and timer helpers.
- `observer/runtime.py`: MediaPipe runtime loops (Solutions + Tasks).
- `observer/ui.py`: HUD drawing.

## Controls

- Press `q` to quit.
