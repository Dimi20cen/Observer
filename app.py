import argparse
import math
import os
from collections import Counter, deque
from typing import Optional

import cv2
import mediapipe as mp

HAS_SOLUTIONS = hasattr(mp, "solutions")


def dist(a, b) -> float:
    return math.hypot(a.x - b.x, a.y - b.y)


def finger_extended(landmarks, tip_idx: int, pip_idx: int, mcp_idx: int) -> bool:
    tip = landmarks[tip_idx]
    pip = landmarks[pip_idx]
    mcp = landmarks[mcp_idx]
    return tip.y < pip.y < mcp.y and (mcp.y - tip.y) > 0.05


def finger_curled(landmarks, tip_idx: int, pip_idx: int, mcp_idx: int) -> bool:
    tip = landmarks[tip_idx]
    pip = landmarks[pip_idx]
    mcp = landmarks[mcp_idx]
    return tip.y > pip.y or dist(tip, mcp) < 0.11


def thumb_up_strict(landmarks) -> bool:
    thumb_tip = landmarks[4]
    thumb_ip = landmarks[3]
    thumb_mcp = landmarks[2]
    wrist = landmarks[0]

    dy = thumb_tip.y - thumb_mcp.y
    dx = thumb_tip.x - thumb_mcp.x
    mostly_vertical = abs(dy) > abs(dx) * 1.2
    long_enough = dist(thumb_tip, thumb_mcp) > 0.14
    return (
        thumb_tip.y < thumb_ip.y < wrist.y
        and dy < -0.06
        and mostly_vertical
        and long_enough
    )


def detect_gesture(landmarks) -> Optional[str]:
    index_up = finger_extended(landmarks, 8, 6, 5)
    middle_up = finger_extended(landmarks, 12, 10, 9)
    ring_up = finger_extended(landmarks, 16, 14, 13)
    pinky_up = finger_extended(landmarks, 20, 18, 17)

    index_curled = finger_curled(landmarks, 8, 6, 5)
    middle_curled = finger_curled(landmarks, 12, 10, 9)
    ring_curled = finger_curled(landmarks, 16, 14, 13)
    pinky_curled = finger_curled(landmarks, 20, 18, 17)

    thumb_up = thumb_up_strict(landmarks)
    thumb_tip = landmarks[4]
    palm_center = landmarks[9]

    four_fingers_up = index_up and middle_up and ring_up and pinky_up
    four_fingers_curled = (
        index_curled and middle_curled and ring_curled and pinky_curled
    )
    thumb_near_palm = dist(thumb_tip, palm_center) < 0.18
    thumb_away_from_palm = dist(thumb_tip, palm_center) > 0.22

    if four_fingers_curled and thumb_near_palm:
        return "1"  # FIST
    if four_fingers_up and thumb_away_from_palm:
        return "2"  # OPEN PALM
    if thumb_up and four_fingers_curled:
        return "3"  # THUMBS UP
    return None


class GestureSmoother:
    def __init__(self, window: int = 7, min_count: int = 5) -> None:
        self.history = deque(maxlen=window)
        self.min_count = min_count

    def update(self, gesture: Optional[str]) -> Optional[str]:
        self.history.append(gesture)
        votes = Counter(g for g in self.history if g is not None)
        if not votes:
            return None
        winner, count = votes.most_common(1)[0]
        if count >= self.min_count:
            return winner
        return None


def run_with_solutions(cap: cv2.VideoCapture) -> None:
    mp_hands = mp.solutions.hands
    mp_drawing = mp.solutions.drawing_utils
    previous = None
    smoother = GestureSmoother()

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

            current = None
            if result.multi_hand_landmarks:
                hand = result.multi_hand_landmarks[0]
                mp_drawing.draw_landmarks(frame, hand, mp_hands.HAND_CONNECTIONS)
                current = smoother.update(detect_gesture(hand.landmark))
            else:
                current = smoother.update(None)

            if current is not None and current != previous:
                print(current, flush=True)
                previous = current

            label = current if current is not None else "-"
            cv2.putText(
                frame,
                f"Gesture: {label}",
                (10, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2,
                cv2.LINE_AA,
            )
            cv2.imshow("Observer v1", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break


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
    previous = None
    smoother = GestureSmoother()
    frame_idx = 0

    with HandLandmarker.create_from_options(options) as hand_landmarker:
        while True:
            ok, frame = cap.read()
            if not ok:
                break

            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            result = hand_landmarker.detect_for_video(mp_image, frame_idx * 33)
            frame_idx += 1

            current = None
            if result.hand_landmarks:
                landmarks = result.hand_landmarks[0]
                current = smoother.update(detect_gesture(landmarks))

                for lm in landmarks:
                    x = int(lm.x * frame.shape[1])
                    y = int(lm.y * frame.shape[0])
                    cv2.circle(frame, (x, y), 3, (255, 255, 0), -1)
            else:
                current = smoother.update(None)

            if current is not None and current != previous:
                print(current, flush=True)
                previous = current

            label = current if current is not None else "-"
            cv2.putText(
                frame,
                f"Gesture: {label}",
                (10, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2,
                cv2.LINE_AA,
            )
            cv2.imshow("Observer v1", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--camera-index", type=int, default=0)
    parser.add_argument("--model-path", default="models/hand_landmarker.task")
    args = parser.parse_args()

    cap = cv2.VideoCapture(args.camera_index)
    if not cap.isOpened():
        raise RuntimeError(
            f"Could not open camera index {args.camera_index}. Try --camera-index 1/2/3."
        )

    try:
        if HAS_SOLUTIONS:
            run_with_solutions(cap)
        else:
            run_with_tasks(cap, args.model_path)
    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
