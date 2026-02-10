import math
from typing import Optional

from observer.constants import (
    GESTURE_FIST,
    GESTURE_ILY,
    GESTURE_OPEN_PALM,
    GESTURE_THUMBS_UP,
)


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


def palm_facing_camera(landmarks, handedness_label: Optional[str]) -> bool:
    wrist = landmarks[0]
    index_mcp = landmarks[5]
    pinky_mcp = landmarks[17]
    middle_mcp = landmarks[9]
    middle_tip = landmarks[12]
    palm_center = landmarks[9]
    index_tip = landmarks[8]
    pinky_tip = landmarks[20]

    v1x = index_mcp.x - wrist.x
    v1y = index_mcp.y - wrist.y
    v2x = pinky_mcp.x - wrist.x
    v2y = pinky_mcp.y - wrist.y
    normal_z = (v1x * v2y) - (v1y * v2x)
    normal_strength = abs(normal_z)

    if handedness_label == "Right":
        orientation_ok = normal_z < -0.02
    elif handedness_label == "Left":
        orientation_ok = normal_z > 0.02
    else:
        orientation_ok = normal_strength > 0.03

    middle_depth = middle_tip.z - middle_mcp.z
    index_depth = index_tip.z - index_mcp.z
    pinky_depth = pinky_tip.z - pinky_mcp.z
    depth_score = (middle_depth + index_depth + pinky_depth) / 3.0
    palm_center_vs_wrist = palm_center.z - wrist.z
    depth_ok = depth_score < -0.025 and palm_center_vs_wrist < -0.01
    return orientation_ok and normal_strength > 0.02 and depth_ok

