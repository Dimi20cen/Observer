from typing import Optional

from observer.constants import ACTIVITIES, ACTIVITY_BY_GESTURE, GESTURE_STOP


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
        target = None if gesture == GESTURE_STOP else ACTIVITY_BY_GESTURE.get(gesture)
        if gesture != GESTURE_STOP and target is None:
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
