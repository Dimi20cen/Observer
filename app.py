import argparse

import cv2

from observer.activity import ActivityTracker
from observer.constants import (
    ACTIVITY_BY_GESTURE,
    GESTURE_ILY,
    GESTURE_ONE_FINGER,
    GESTURE_OPEN_PALM,
    GESTURE_TWO_FINGERS,
)
from observer.gates import GestureHoldGate
from observer.runtime import HAS_SOLUTIONS, run_with_solutions, run_with_tasks


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
