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
from observer.gestures import outside_of_hand_showing, thumb_extended_for_ily


class _LM:
    def __init__(self, x: float, y: float, z: float = 0.0):
        self.x = x
        self.y = y
        self.z = z


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


class GestureHeuristicTests(unittest.TestCase):
    def test_thumb_extended_for_ily_is_more_permissive(self):
        landmarks = [_LM(0.5, 0.5, 0.0) for _ in range(21)]
        landmarks[9] = _LM(0.5, 0.5, 0.0)   # palm center
        landmarks[2] = _LM(0.48, 0.52, 0.0)  # thumb mcp
        landmarks[4] = _LM(0.66, 0.50, 0.0)  # thumb tip
        self.assertTrue(thumb_extended_for_ily(landmarks))


if __name__ == "__main__":
    unittest.main()
