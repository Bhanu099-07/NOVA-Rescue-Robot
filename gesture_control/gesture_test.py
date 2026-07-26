"""Real-time hand gesture recognition for NOVA."""

from pathlib import Path
import sys
import time

import cv2
import mediapipe as mp


CAMERA_INDEX = 0
MIN_GESTURE_CONFIDENCE = 0.55

SCRIPT_DIRECTORY = Path(__file__).resolve().parent
MODEL_PATH = SCRIPT_DIRECTORY / "models" / "gesture_recognizer.task"


HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (5, 9), (9, 10), (10, 11), (11, 12),
    (9, 13), (13, 14), (14, 15), (15, 16),
    (13, 17), (17, 18), (18, 19), (19, 20),
    (0, 17),
]


def draw_hand_landmarks(frame, landmarks) -> None:
    """Draw hand joints and connecting lines."""

    frame_height, frame_width, _ = frame.shape

    points = []

    for landmark in landmarks:
        x = int(landmark.x * frame_width)
        y = int(landmark.y * frame_height)
        points.append((x, y))

    for start, end in HAND_CONNECTIONS:
        cv2.line(
            frame,
            points[start],
            points[end],
            (255, 255, 255),
            2,
        )

    for point in points:
        cv2.circle(
            frame,
            point,
            5,
            (0, 255, 0),
            -1,
        )


def main() -> None:
    """Start webcam gesture recognition."""

    if not MODEL_PATH.exists():
        print("ERROR: Gesture model was not found.")
        print(f"Expected location: {MODEL_PATH}")
        sys.exit(1)

    base_options = mp.tasks.BaseOptions(
        model_asset_path=str(MODEL_PATH)
    )

    options = mp.tasks.vision.GestureRecognizerOptions(
        base_options=base_options,
        running_mode=mp.tasks.vision.RunningMode.VIDEO,
        num_hands=1,
        min_hand_detection_confidence=0.5,
        min_hand_presence_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    camera = cv2.VideoCapture(CAMERA_INDEX)

    if not camera.isOpened():
        print("ERROR: Webcam could not be opened.")
        print("Close Camera, Discord, Teams, Zoom, or browser camera tabs.")
        sys.exit(1)

    print("NOVA gesture recognizer started.")
    print("Show one hand clearly to the camera.")
    print("Press Q inside the camera window to close.")

    start_time = time.monotonic()
    last_timestamp_ms = -1

    with mp.tasks.vision.GestureRecognizer.create_from_options(
        options
    ) as recognizer:

        while True:
            success, frame = camera.read()

            if not success:
                print("ERROR: Could not read webcam frame.")
                break

            frame = cv2.flip(frame, 1)

            rgb_frame = cv2.cvtColor(
                frame,
                cv2.COLOR_BGR2RGB,
            )

            mp_image = mp.Image(
                image_format=mp.ImageFormat.SRGB,
                data=rgb_frame,
            )

            timestamp_ms = int(
                (time.monotonic() - start_time) * 1000
            )

            if timestamp_ms <= last_timestamp_ms:
                timestamp_ms = last_timestamp_ms + 1

            last_timestamp_ms = timestamp_ms

            result = recognizer.recognize_for_video(
                mp_image,
                timestamp_ms,
            )

            gesture_name = "NO HAND"
            gesture_score = 0.0

            if result.hand_landmarks:
                draw_hand_landmarks(
                    frame,
                    result.hand_landmarks[0],
                )

            if result.gestures and result.gestures[0]:
                top_gesture = result.gestures[0][0]
                gesture_score = top_gesture.score

                if gesture_score >= MIN_GESTURE_CONFIDENCE:
                    gesture_name = top_gesture.category_name
                else:
                    gesture_name = "UNCERTAIN"

            cv2.rectangle(
                frame,
                (10, 10),
                (500, 110),
                (0, 0, 0),
                -1,
            )

            cv2.putText(
                frame,
                "NOVA GESTURE RECOGNITION",
                (25, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2,
            )

            cv2.putText(
                frame,
                f"Gesture: {gesture_name}",
                (25, 73),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.75,
                (0, 255, 255),
                2,
            )

            cv2.putText(
                frame,
                f"Confidence: {gesture_score:.0%}",
                (25, 101),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (255, 255, 255),
                1,
            )

            cv2.imshow(
                "NOVA Hand Gesture Test",
                frame,
            )

            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                break

    camera.release()
    cv2.destroyAllWindows()

    print("Gesture recognizer closed safely.")


if __name__ == "__main__":
    main()