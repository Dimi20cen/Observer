import argparse
import math
import os
import time
from collections import Counter, deque
from typing import Optional

import cv2
import mediapipe as mp

HAS_SOLUTIONS = hasattr(mp, "solutions")
GESTURE_FIST = "FIST"
GESTURE_ILY = "ILY_SIGN"
GESTURE_THUMBS_UP = "THUMBS_UP"
GESTURE_OPEN_PALM = "OPEN_PALM"
ACTIVITY_BY_GESTURE = {
    GESTURE_ILY: "studying",
    GESTURE_THUMBS_UP: "youtube",
    GESTURE_OPEN_PALM: "lol",
}
ACTIVITIES = ("studying", "youtube", "lol")


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


def thumb_side_extended(landmarks) -> bool:
    thumb_tip = landmarks[4]
    thumb_mcp = landmarks[2]
    dx = abs(thumb_tip.x - thumb_mcp.x)
    dy = abs(thumb_tip.y - thumb_mcp.y)
    return dx > dy and dist(thumb_tip, thumb_mcp) > 0.14


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
        return GESTURE_FIST
    if (
        index_up
        and pinky_up
        and middle_curled
        and ring_curled
        and thumb_side_extended(landmarks)
        and not thumb_up
    ):
        return GESTURE_ILY
    if four_fingers_up and thumb_away_from_palm:
        return GESTURE_OPEN_PALM
    if thumb_up and four_fingers_curled:
        return GESTURE_THUMBS_UP
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


class GestureHoldGate:
    def __init__(self, min_hold_seconds: float = 1.5) -> None:
        self.min_hold_seconds = min_hold_seconds
        self.current_candidate: Optional[str] = None
        self.candidate_since = 0.0

    def update(self, gesture: Optional[str], now: float) -> Optional[str]:
        if gesture != self.current_candidate:
            self.current_candidate = gesture
            self.candidate_since = now
        if self.current_candidate is None:
            return None
        if (now - self.candidate_since) >= self.min_hold_seconds:
            return self.current_candidate
        return None


class ActivityTracker:
    def __init__(self, cooldown_seconds: float = 0.8) -> None:
        self.totals = {activity: 0.0 for activity in ACTIVITIES}
        self.active_activity: Optional[str] = None
        self.active_started_at: Optional[float] = None
        self.cooldown_seconds = cooldown_seconds
        self.last_switch_at = -10_000.0

    def _close_active(self, now: float) -> None:
        if self.active_activity is None or self.active_started_at is None:
            return
        self.totals[self.active_activity] += max(0.0, now - self.active_started_at)
        self.active_started_at = None

    def apply_gesture(self, gesture: Optional[str], now: float) -> bool:
        if gesture is None:
            return False
        target = None if gesture == GESTURE_FIST else ACTIVITY_BY_GESTURE.get(gesture)
        if gesture != GESTURE_FIST and target is None:
            return False
        if target == self.active_activity:
            return False
        if now - self.last_switch_at < self.cooldown_seconds:
            return False

        self._close_active(now)
        self.active_activity = target
        self.active_started_at = now if target is not None else None
        self.last_switch_at = now
        return True

    def snapshot(self, now: float) -> dict[str, float]:
        values = dict(self.totals)
        if self.active_activity is not None and self.active_started_at is not None:
            values[self.active_activity] += max(0.0, now - self.active_started_at)
        return values


def format_seconds(seconds: float) -> str:
    total = int(seconds)
    hours = total // 3600
    minutes = (total % 3600) // 60
    secs = total % 60
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def palm_facing_camera(landmarks, handedness_label: Optional[str]) -> bool:
    wrist = landmarks[0]
    index_mcp = landmarks[5]
    pinky_mcp = landmarks[17]
    middle_mcp = landmarks[9]
    middle_tip = landmarks[12]

    v1x = index_mcp.x - wrist.x
    v1y = index_mcp.y - wrist.y
    v1z = index_mcp.z - wrist.z
    v2x = pinky_mcp.x - wrist.x
    v2y = pinky_mcp.y - wrist.y
    v2z = pinky_mcp.z - wrist.z
    normal_z = (v1x * v2y) - (v1y * v2x)

    if handedness_label == "Right":
        orientation_ok = normal_z < 0.0
    elif handedness_label == "Left":
        orientation_ok = normal_z > 0.0
    else:
        orientation_ok = abs(normal_z) > 0.002

    # Palm-facing frames often place middle fingertip nearer than middle MCP.
    depth_ok = (middle_tip.z - middle_mcp.z) < 0.03
    return orientation_ok and depth_ok


def draw_hud(
    frame,
    current_gesture: Optional[str],
    palm_ok: bool,
    tracker: ActivityTracker,
    now: float,
) -> None:
    totals = tracker.snapshot(now)
    lines = [
        f"Gesture: {current_gesture or '-'}",
        f"Palm OK: {'YES' if palm_ok else 'NO'}",
        f"Activity: {tracker.active_activity or 'IDLE'}",
        f"Studying: {format_seconds(totals['studying'])}",
        f"YouTube : {format_seconds(totals['youtube'])}",
        f"LoL     : {format_seconds(totals['lol'])}",
    ]
    y = 35
    for line in lines:
        cv2.putText(
            frame,
            line,
            (10, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2,
            cv2.LINE_AA,
        )
        y += 30


def handle_activity_update(
    stable_gesture: Optional[str], tracker: ActivityTracker, previous_activity: Optional[str]
) -> Optional[str]:
    now = time.monotonic()
    changed = tracker.apply_gesture(stable_gesture, now)
    if not changed:
        return previous_activity

    current = tracker.active_activity
    if current is None:
        print("STOPPED", flush=True)
    else:
        print(f"ACTIVE: {current}", flush=True)
    return current


def run_with_solutions(cap: cv2.VideoCapture) -> None:
    mp_hands = mp.solutions.hands
    mp_drawing = mp.solutions.drawing_utils
    previous_activity = None
    smoother = GestureSmoother()
    hold_gate = GestureHoldGate(1.5)
    tracker = ActivityTracker()

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
            if result.multi_hand_landmarks:
                hand = result.multi_hand_landmarks[0]
                mp_drawing.draw_landmarks(frame, hand, mp_hands.HAND_CONNECTIONS)
                handedness = None
                if result.multi_handedness:
                    handedness = result.multi_handedness[0].classification[0].label
                palm_ok = palm_facing_camera(hand.landmark, handedness)
                stable_gesture = smoother.update(detect_gesture(hand.landmark))
                if palm_ok:
                    held_gesture = hold_gate.update(stable_gesture, time.monotonic())
                else:
                    held_gesture = hold_gate.update(None, time.monotonic())
            else:
                stable_gesture = smoother.update(None)
                held_gesture = hold_gate.update(None, time.monotonic())

            previous_activity = handle_activity_update(
                held_gesture, tracker, previous_activity
            )
            draw_hud(frame, stable_gesture, palm_ok, tracker, time.monotonic())
            cv2.imshow("Observer v2", frame)
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
    previous_activity = None
    smoother = GestureSmoother()
    hold_gate = GestureHoldGate(1.5)
    tracker = ActivityTracker()
    start = time.monotonic()

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
            if result.hand_landmarks:
                landmarks = result.hand_landmarks[0]
                handedness = None
                if result.handedness and result.handedness[0]:
                    handedness = result.handedness[0][0].category_name
                palm_ok = palm_facing_camera(landmarks, handedness)
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

            previous_activity = handle_activity_update(
                held_gesture, tracker, previous_activity
            )
            draw_hud(frame, stable_gesture, palm_ok, tracker, time.monotonic())
            cv2.imshow("Observer v2", frame)
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
