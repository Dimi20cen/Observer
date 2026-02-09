# Observer v1

Recognize 3 hand gestures from an iPhone camera feed (via Iriun) and print:

- `1` for `FIST`
- `2` for `OPEN PALM`
- `3` for `THUMBS UP`

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

## Controls

- Press `q` to quit.
