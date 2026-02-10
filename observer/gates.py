from collections import Counter, deque
from typing import Optional


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

