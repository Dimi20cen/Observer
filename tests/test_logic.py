import unittest

from app import (
    ACTIVITY_BY_GESTURE,
    GESTURE_FIST,
    GESTURE_ILY,
    GESTURE_OPEN_PALM,
    GESTURE_THUMBS_UP,
    ActivityTracker,
    GestureHoldGate,
)


class GestureHoldGateTests(unittest.TestCase):
    def test_requires_min_hold_before_emitting(self):
        gate = GestureHoldGate(min_hold_seconds=1.5)
        self.assertIsNone(gate.update(GESTURE_OPEN_PALM, 0.0))
        self.assertIsNone(gate.update(GESTURE_OPEN_PALM, 1.49))
        self.assertEqual(gate.update(GESTURE_OPEN_PALM, 1.5), GESTURE_OPEN_PALM)

    def test_resets_when_gesture_changes(self):
        gate = GestureHoldGate(min_hold_seconds=1.5)
        self.assertIsNone(gate.update(GESTURE_OPEN_PALM, 0.0))
        self.assertIsNone(gate.update(GESTURE_THUMBS_UP, 0.8))
        self.assertIsNone(gate.update(GESTURE_THUMBS_UP, 2.2))
        self.assertEqual(gate.update(GESTURE_THUMBS_UP, 2.31), GESTURE_THUMBS_UP)


class ActivityTrackerTests(unittest.TestCase):
    def test_mapping_contract(self):
        self.assertEqual(ACTIVITY_BY_GESTURE[GESTURE_ILY], "studying")
        self.assertEqual(ACTIVITY_BY_GESTURE[GESTURE_THUMBS_UP], "youtube")
        self.assertEqual(ACTIVITY_BY_GESTURE[GESTURE_OPEN_PALM], "lol")
        self.assertNotIn(GESTURE_FIST, ACTIVITY_BY_GESTURE)

    def test_switch_and_accumulate(self):
        tracker = ActivityTracker(cooldown_seconds=0.8)
        self.assertTrue(tracker.apply_gesture(GESTURE_ILY, 0.0))
        self.assertTrue(tracker.apply_gesture(GESTURE_OPEN_PALM, 1.0))
        self.assertTrue(tracker.apply_gesture(GESTURE_FIST, 2.0))
        totals = tracker.snapshot(2.0)
        self.assertAlmostEqual(totals["studying"], 1.0, places=3)
        self.assertAlmostEqual(totals["lol"], 1.0, places=3)
        self.assertAlmostEqual(totals["youtube"], 0.0, places=3)

    def test_cooldown_blocks_fast_switch(self):
        tracker = ActivityTracker(cooldown_seconds=0.8)
        self.assertTrue(tracker.apply_gesture(GESTURE_ILY, 0.0))
        self.assertFalse(tracker.apply_gesture(GESTURE_THUMBS_UP, 0.2))
        self.assertEqual(tracker.active_activity, "studying")
        self.assertTrue(tracker.apply_gesture(GESTURE_THUMBS_UP, 1.0))
        self.assertEqual(tracker.active_activity, "youtube")


if __name__ == "__main__":
    unittest.main()
