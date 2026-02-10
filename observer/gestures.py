import math
from typing import Optional

from observer.constants import (
    GESTURE_ILY,
    GESTURE_ONE_FINGER,
    GESTURE_OPEN_PALM,
    GESTURE_TWO_FINGERS,
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


def thumb_side_extended(landmarks) -> bool:
    thumb_tip = landmarks[4]
    thumb_mcp = landmarks[2]
    dx = abs(thumb_tip.x - thumb_mcp.x)
    dy = abs(thumb_tip.y - thumb_mcp.y)
    return dx > dy and dist(thumb_tip, thumb_mcp) > 0.14


def thumb_extended_for_ily(landmarks) -> bool:
    thumb_tip = landmarks[4]
    thumb_mcp = landmarks[2]
    palm_center = landmarks[9]
    dx = abs(thumb_tip.x - thumb_mcp.x)
    dy = abs(thumb_tip.y - thumb_mcp.y)
    return dist(thumb_tip, palm_center) > 0.16 and dx > (dy * 0.6)


def _atomic_flags(landmarks) -> dict[str, bool]:
    index_up = finger_extended(landmarks, 8, 6, 5)
    middle_up = finger_extended(landmarks, 12, 10, 9)
    ring_up = finger_extended(landmarks, 16, 14, 13)
    pinky_up = finger_extended(landmarks, 20, 18, 17)

    index_curled = finger_curled(landmarks, 8, 6, 5)
    middle_curled = finger_curled(landmarks, 12, 10, 9)
    ring_curled = finger_curled(landmarks, 16, 14, 13)
    pinky_curled = finger_curled(landmarks, 20, 18, 17)

    thumb_tip = landmarks[4]
    palm_center = landmarks[9]
    thumb_near_palm = dist(thumb_tip, palm_center) < 0.20
    thumb_away_from_palm = dist(thumb_tip, palm_center) > 0.24
    thumb_side = thumb_side_extended(landmarks)
    thumb_ily = thumb_extended_for_ily(landmarks)

    four_fingers_up = index_up and middle_up and ring_up and pinky_up
    three_curled = middle_curled and ring_curled and pinky_curled
    two_curled = ring_curled and pinky_curled

    return {
        "index_up": index_up,
        "middle_up": middle_up,
        "ring_up": ring_up,
        "pinky_up": pinky_up,
        "middle_curled": middle_curled,
        "ring_curled": ring_curled,
        "pinky_curled": pinky_curled,
        "thumb_near_palm": thumb_near_palm,
        "thumb_away_from_palm": thumb_away_from_palm,
        "thumb_side": thumb_side,
        "thumb_ily": thumb_ily,
        "four_fingers_up": four_fingers_up,
        "three_curled": three_curled,
        "two_curled": two_curled,
    }


def gesture_checklines(landmarks) -> list[str]:
    f = _atomic_flags(landmarks)
    checks = [
        (
            "OPEN",
            f["four_fingers_up"] and f["thumb_away_from_palm"],
            [("4UP", f["four_fingers_up"]), ("TH_AWAY", f["thumb_away_from_palm"])],
        ),
        (
            "ILY",
            f["index_up"]
            and f["pinky_up"]
            and (not f["middle_up"])
            and (not f["ring_up"])
            and (f["thumb_side"] or f["thumb_ily"]),
            [
                ("IDX", f["index_up"]),
                ("PNK", f["pinky_up"]),
                ("MID_DN", not f["middle_up"]),
                ("RNG_DN", not f["ring_up"]),
                ("TH", f["thumb_side"] or f["thumb_ily"]),
            ],
        ),
        (
            "ONE",
            f["index_up"] and f["three_curled"] and f["thumb_near_palm"],
            [
                ("IDX", f["index_up"]),
                ("3CURL", f["three_curled"]),
                ("TH_NEAR", f["thumb_near_palm"]),
            ],
        ),
        (
            "TWO",
            f["index_up"] and f["middle_up"] and f["two_curled"] and f["thumb_near_palm"],
            [
                ("IDX", f["index_up"]),
                ("MID", f["middle_up"]),
                ("2CURL", f["two_curled"]),
                ("TH_NEAR", f["thumb_near_palm"]),
            ],
        ),
    ]
    lines = []
    for name, matched, parts in checks:
        prefix = "*" if matched else "-"
        status = " ".join(f"{k}:{'T' if v else 'F'}" for k, v in parts)
        lines.append(f"{prefix}{name} {status}")
    return lines


def detect_gesture(landmarks) -> Optional[str]:
    f = _atomic_flags(landmarks)

    if f["four_fingers_up"] and f["thumb_away_from_palm"]:
        return GESTURE_OPEN_PALM
    if (
        f["index_up"]
        and f["pinky_up"]
        and not f["middle_up"]
        and not f["ring_up"]
        and (f["thumb_side"] or f["thumb_ily"])
    ):
        return GESTURE_ILY
    if f["index_up"] and f["three_curled"] and f["thumb_near_palm"]:
        return GESTURE_ONE_FINGER
    if f["index_up"] and f["middle_up"] and f["two_curled"] and f["thumb_near_palm"]:
        return GESTURE_TWO_FINGERS
    return None


def palm_facing_camera(landmarks, handedness_label: Optional[str]) -> bool:
    return not outside_of_hand_showing(landmarks, handedness_label)


def outside_of_hand_showing(landmarks, handedness_label: Optional[str]) -> bool:
    wrist = landmarks[0]
    index_mcp = landmarks[5]
    middle_mcp = landmarks[9]
    pinky_mcp = landmarks[17]
    index_tip = landmarks[8]
    middle_tip = landmarks[12]
    pinky_tip = landmarks[20]

    v1x = index_mcp.x - wrist.x
    v1y = index_mcp.y - wrist.y
    v2x = pinky_mcp.x - wrist.x
    v2y = pinky_mcp.y - wrist.y
    normal_z = (v1x * v2y) - (v1y * v2x)
    depth_score = (
        (index_tip.z - index_mcp.z)
        + (middle_tip.z - middle_mcp.z)
        + (pinky_tip.z - pinky_mcp.z)
    ) / 3.0

    if handedness_label == "Right":
        return normal_z > 0.01 and depth_score > -0.02
    if handedness_label == "Left":
        return normal_z < -0.01 and depth_score > -0.02

    # Unknown handedness: only block when depth strongly indicates outside hand.
    return depth_score > 0.0
