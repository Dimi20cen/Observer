import unittest

from app import (
    ACTIVITY_BY_GESTURE,
    GESTURE_ILY,
    GESTURE_ONE_FINGER,
    GESTURE_OPEN_PALM,
    GESTURE_TWO_FINGERS,
    ActivityTracker,
    GestureHoldGate,
)
from observer.gestures import detect_gesture, outside_of_hand_showing, thumb_extended_for_ily


class _LM:
    def __init__(self, x: float, y: float, z: float = 0.0):
        self.x = x
        self.y = y
        self.z = z


def _make_landmarks() -> list[_LM]:
    points = [_LM(0.5, 0.7, 0.0) for _ in range(21)]
    points[0] = _LM(0.5, 0.8, 0.0)   # wrist
    points[9] = _LM(0.5, 0.55, 0.0)  # palm center (middle MCP)
    return points


def _set_finger(points, finger: str, up: bool) -> None:
    idx = {
        "index": (5, 6, 8, 0.45),
        "middle": (9, 10, 12, 0.50),
        "ring": (13, 14, 16, 0.55),
        "pinky": (17, 18, 20, 0.60),
    }[finger]
    mcp_i, pip_i, tip_i, x = idx
    if up:
        points[mcp_i] = _LM(x, 0.62, -0.02)
        points[pip_i] = _LM(x, 0.46, -0.03)
        points[tip_i] = _LM(x, 0.26, -0.05)
    else:
        points[mcp_i] = _LM(x, 0.62, 0.00)
        points[pip_i] = _LM(x, 0.58, 0.01)
        points[tip_i] = _LM(x, 0.68, 0.02)


def _set_thumb(points, mode: str) -> None:
    points[2] = _LM(0.40, 0.60, 0.00)  # thumb MCP
    if mode == "near":
        points[4] = _LM(0.52, 0.56, 0.00)
    elif mode == "away":
        points[4] = _LM(0.80, 0.40, -0.04)
    elif mode == "side":
        points[4] = _LM(0.74, 0.56, -0.01)
    else:
        raise ValueError(mode)


class GestureHoldGateTests(unittest.TestCase):
    def test_requires_min_hold_before_emitting(self):
        gate = GestureHoldGate(min_hold_seconds=1.5)
        self.assertIsNone(gate.update(GESTURE_OPEN_PALM, 0.0))
        self.assertIsNone(gate.update(GESTURE_OPEN_PALM, 1.49))
        self.assertEqual(gate.update(GESTURE_OPEN_PALM, 1.5), GESTURE_OPEN_PALM)

    def test_resets_when_gesture_changes(self):
        gate = GestureHoldGate(min_hold_seconds=1.5)
        self.assertIsNone(gate.update(GESTURE_OPEN_PALM, 0.0))
        self.assertIsNone(gate.update(GESTURE_ONE_FINGER, 0.8))
        self.assertIsNone(gate.update(GESTURE_ONE_FINGER, 2.2))
        self.assertEqual(gate.update(GESTURE_ONE_FINGER, 2.31), GESTURE_ONE_FINGER)


class ActivityTrackerTests(unittest.TestCase):
    def test_mapping_contract(self):
        self.assertEqual(ACTIVITY_BY_GESTURE[GESTURE_ILY], "studying")
        self.assertEqual(ACTIVITY_BY_GESTURE[GESTURE_ONE_FINGER], "youtube")
        self.assertEqual(ACTIVITY_BY_GESTURE[GESTURE_TWO_FINGERS], "lol")
        self.assertNotIn(GESTURE_OPEN_PALM, ACTIVITY_BY_GESTURE)

    def test_switch_and_accumulate(self):
        tracker = ActivityTracker(cooldown_seconds=0.8)
        self.assertTrue(tracker.apply_gesture(GESTURE_ILY, 0.0))
        self.assertTrue(tracker.apply_gesture(GESTURE_TWO_FINGERS, 1.0))
        self.assertTrue(tracker.apply_gesture(GESTURE_OPEN_PALM, 2.0))
        totals = tracker.snapshot(2.0)
        self.assertAlmostEqual(totals["studying"], 1.0, places=3)
        self.assertAlmostEqual(totals["lol"], 1.0, places=3)
        self.assertAlmostEqual(totals["youtube"], 0.0, places=3)

    def test_cooldown_blocks_fast_switch(self):
        tracker = ActivityTracker(cooldown_seconds=0.8)
        self.assertTrue(tracker.apply_gesture(GESTURE_ILY, 0.0))
        self.assertFalse(tracker.apply_gesture(GESTURE_ONE_FINGER, 0.2))
        self.assertEqual(tracker.active_activity, "studying")
        self.assertTrue(tracker.apply_gesture(GESTURE_ONE_FINGER, 1.0))
        self.assertEqual(tracker.active_activity, "youtube")


class PalmSideGateTests(unittest.TestCase):
    def test_outside_detection_respects_handedness(self):
        landmarks = [_LM(0, 0, 0) for _ in range(21)]
        landmarks[0] = _LM(0.5, 0.5, 0.0)   # wrist
        landmarks[5] = _LM(0.5, 0.3, 0.0)   # index_mcp
        landmarks[17] = _LM(0.7, 0.5, 0.0)  # pinky_mcp

        self.assertTrue(outside_of_hand_showing(landmarks, "Right"))
        self.assertFalse(outside_of_hand_showing(landmarks, "Left"))
        self.assertFalse(outside_of_hand_showing(landmarks, None))

    def test_unknown_handedness_uses_depth_fallback(self):
        landmarks = [_LM(0, 0, 0) for _ in range(21)]
        landmarks[0] = _LM(0.5, 0.5, 0.0)   # wrist
        landmarks[5] = _LM(0.5, 0.3, 0.0)   # index_mcp
        landmarks[9] = _LM(0.6, 0.35, 0.0)  # middle_mcp
        landmarks[17] = _LM(0.7, 0.5, 0.0)  # pinky_mcp
        landmarks[8] = _LM(0.5, 0.2, 0.2)   # index_tip further from camera
        landmarks[12] = _LM(0.6, 0.2, 0.2)  # middle_tip
        landmarks[20] = _LM(0.7, 0.3, 0.2)  # pinky_tip
        self.assertTrue(outside_of_hand_showing(landmarks, None))


class GestureHeuristicTests(unittest.TestCase):
    def test_thumb_extended_for_ily_is_more_permissive(self):
        landmarks = [_LM(0.5, 0.5, 0.0) for _ in range(21)]
        landmarks[9] = _LM(0.5, 0.5, 0.0)   # palm center
        landmarks[2] = _LM(0.48, 0.52, 0.0)  # thumb mcp
        landmarks[4] = _LM(0.66, 0.50, 0.0)  # thumb tip
        self.assertTrue(thumb_extended_for_ily(landmarks))


class DetectGestureTests(unittest.TestCase):
    def test_detect_open_palm(self):
        points = _make_landmarks()
        _set_finger(points, "index", True)
        _set_finger(points, "middle", True)
        _set_finger(points, "ring", True)
        _set_finger(points, "pinky", True)
        _set_thumb(points, "away")
        self.assertEqual(detect_gesture(points), GESTURE_OPEN_PALM)

    def test_detect_ily(self):
        points = _make_landmarks()
        _set_finger(points, "index", True)
        _set_finger(points, "middle", False)
        _set_finger(points, "ring", False)
        _set_finger(points, "pinky", True)
        _set_thumb(points, "side")
        self.assertEqual(detect_gesture(points), GESTURE_ILY)

    def test_detect_one_finger(self):
        points = _make_landmarks()
        _set_finger(points, "index", True)
        _set_finger(points, "middle", False)
        _set_finger(points, "ring", False)
        _set_finger(points, "pinky", False)
        _set_thumb(points, "near")
        self.assertEqual(detect_gesture(points), GESTURE_ONE_FINGER)

    def test_detect_two_fingers(self):
        points = _make_landmarks()
        _set_finger(points, "index", True)
        _set_finger(points, "middle", True)
        _set_finger(points, "ring", False)
        _set_finger(points, "pinky", False)
        _set_thumb(points, "near")
        self.assertEqual(detect_gesture(points), GESTURE_TWO_FINGERS)


if __name__ == "__main__":
    unittest.main()
