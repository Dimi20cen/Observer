import cv2

from observer.activity import format_seconds


def draw_hud(frame, current_gesture, palm_ok: bool, tracker, now: float) -> None:
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

