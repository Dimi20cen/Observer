import os
import time

import cv2
import mediapipe as mp

from observer.activity import ActivityTracker
from observer.gates import GestureHoldGate, GestureSmoother
from observer.gestures import detect_gesture, gesture_checklines, palm_facing_camera
from observer.ui import draw_gesture_debug, draw_hud

HAS_SOLUTIONS = hasattr(mp, "solutions")


def handle_activity_update(stable_gesture, tracker: ActivityTracker) -> None:
    now = time.monotonic()
    changed = tracker.apply_gesture(stable_gesture, now)
    if not changed:
        return

    current = tracker.active_activity
    if current is None:
        print("STOPPED", flush=True)
    else:
        print(f"ACTIVE: {current}", flush=True)


def run_with_solutions(cap: cv2.VideoCapture) -> None:
    mp_hands = mp.solutions.hands
    mp_drawing = mp.solutions.drawing_utils
    smoother = GestureSmoother()
    hold_gate = GestureHoldGate(1.5)
    tracker = ActivityTracker()
    debug_enabled = True

    with mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        min_detection_confidence=0.6,
        min_tracking_confidence=0.6,
    ) as hands:
        while True:
            ok, frame = cap.read()
            if not ok:
                break

            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = hands.process(rgb)

            stable_gesture = None
            held_gesture = None
            palm_ok = False
            debug_lines = []
            if result.multi_hand_landmarks:
                hand = result.multi_hand_landmarks[0]
                mp_drawing.draw_landmarks(frame, hand, mp_hands.HAND_CONNECTIONS)
                handedness = None
                if result.multi_handedness:
                    handedness = result.multi_handedness[0].classification[0].label
                palm_ok = palm_facing_camera(hand.landmark, handedness)
                if debug_enabled:
                    debug_lines = gesture_checklines(hand.landmark)
                stable_gesture = smoother.update(detect_gesture(hand.landmark))
                if palm_ok:
                    held_gesture = hold_gate.update(stable_gesture, time.monotonic())
                else:
                    held_gesture = hold_gate.update(None, time.monotonic())
            else:
                stable_gesture = smoother.update(None)
                held_gesture = hold_gate.update(None, time.monotonic())

            handle_activity_update(held_gesture, tracker)
            draw_hud(frame, stable_gesture, palm_ok, tracker, time.monotonic())
            if debug_enabled:
                draw_gesture_debug(frame, debug_lines)
            cv2.imshow("Observer v2", frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            if key == ord("d"):
                debug_enabled = not debug_enabled


def run_with_tasks(cap: cv2.VideoCapture, model_path: str) -> None:
    if not os.path.exists(model_path):
        raise RuntimeError(
            "MediaPipe Tasks backend requires a model file.\n"
            f"Missing: {model_path}\n"
            "Download it with:\n"
            "mkdir -p models && "
            "wget -O models/hand_landmarker.task "
            "https://storage.googleapis.com/mediapipe-models/"
            "hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
        )
    with open(model_path, "rb") as f:
        header = f.read(32)
    if header.startswith(b"<?xml"):
        raise RuntimeError(
            "Model file is XML, not a .task archive. Re-download with the full URL on one line:\n"
            "wget -O models/hand_landmarker.task "
            "https://storage.googleapis.com/mediapipe-models/"
            "hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
        )

    from mediapipe.tasks.python.core.base_options import BaseOptions
    from mediapipe.tasks.python.vision import (
        HandLandmarker,
        HandLandmarkerOptions,
        RunningMode,
    )

    options = HandLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=model_path),
        running_mode=RunningMode.VIDEO,
        num_hands=1,
        min_hand_detection_confidence=0.6,
        min_hand_presence_confidence=0.6,
        min_tracking_confidence=0.6,
    )
    smoother = GestureSmoother()
    hold_gate = GestureHoldGate(1.5)
    tracker = ActivityTracker()
    start = time.monotonic()
    debug_enabled = True

    with HandLandmarker.create_from_options(options) as hand_landmarker:
        while True:
            ok, frame = cap.read()
            if not ok:
                break

            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            timestamp_ms = int((time.monotonic() - start) * 1000.0)
            result = hand_landmarker.detect_for_video(mp_image, timestamp_ms)

            stable_gesture = None
            held_gesture = None
            palm_ok = False
            debug_lines = []
            if result.hand_landmarks:
                landmarks = result.hand_landmarks[0]
                handedness = None
                if result.handedness and result.handedness[0]:
                    handedness = result.handedness[0][0].category_name
                palm_ok = palm_facing_camera(landmarks, handedness)
                if debug_enabled:
                    debug_lines = gesture_checklines(landmarks)
                stable_gesture = smoother.update(detect_gesture(landmarks))
                if palm_ok:
                    held_gesture = hold_gate.update(stable_gesture, time.monotonic())
                else:
                    held_gesture = hold_gate.update(None, time.monotonic())

                for lm in landmarks:
                    x = int(lm.x * frame.shape[1])
                    y = int(lm.y * frame.shape[0])
                    cv2.circle(frame, (x, y), 3, (255, 255, 0), -1)
            else:
                stable_gesture = smoother.update(None)
                held_gesture = hold_gate.update(None, time.monotonic())

            handle_activity_update(held_gesture, tracker)
            draw_hud(frame, stable_gesture, palm_ok, tracker, time.monotonic())
            if debug_enabled:
                draw_gesture_debug(frame, debug_lines)
            cv2.imshow("Observer v2", frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            if key == ord("d"):
                debug_enabled = not debug_enabled
