"""NOVA gesture recognition with stable UDP robot-command generation."""

from collections import deque
from pathlib import Path
import socket
import sys
import time

import cv2
import mediapipe as mp


# -------------------------------------------------------------------
# SETTINGS
# -------------------------------------------------------------------

CAMERA_INDEX = 0
MIN_GESTURE_CONFIDENCE = 0.55

GESTURE_HISTORY_SIZE = 8
STABLE_GESTURE_COUNT = 6

UDP_IP = "127.0.0.1"
UDP_PORT = 5005

SCRIPT_DIRECTORY = Path(__file__).resolve().parent
MODEL_PATH = SCRIPT_DIRECTORY / "models" / "gesture_recognizer.task"


# -------------------------------------------------------------------
# GESTURE TO ROBOT COMMAND MAPPING
# -------------------------------------------------------------------

GESTURE_COMMANDS = {
    "Open_Palm": "STOP",
    "Pointing_Up": "FORWARD",
    "Victory": "REVERSE",
    "Thumb_Up": "TURN_RIGHT",
    "Thumb_Down": "TURN_LEFT",
    "Closed_Fist": "AUTONOMOUS_MODE",
    "ILoveYou": "GESTURE_MODE",
}


HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (5, 9), (9, 10), (10, 11), (11, 12),
    (9, 13), (13, 14), (14, 15), (15, 16),
    (13, 17), (17, 18), (18, 19), (19, 20),
    (0, 17),
]


# -------------------------------------------------------------------
# DRAWING
# -------------------------------------------------------------------

def draw_hand_landmarks(frame, landmarks) -> None:
    """Draw detected hand joints and connections."""

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


# -------------------------------------------------------------------
# COMMAND STABILIZATION
# -------------------------------------------------------------------

def get_stable_gesture(
    gesture_history: deque[str],
) -> str | None:
    """Return a gesture only when it appears consistently."""

    if len(gesture_history) < GESTURE_HISTORY_SIZE:
        return None

    counts: dict[str, int] = {}

    for gesture in gesture_history:
        counts[gesture] = counts.get(gesture, 0) + 1

    most_common_gesture = max(
        counts,
        key=counts.get,
    )

    if counts[most_common_gesture] >= STABLE_GESTURE_COUNT:
        return most_common_gesture

    return None


# -------------------------------------------------------------------
# MAIN PROGRAM
# -------------------------------------------------------------------

def main() -> None:
    """Recognize gestures and send stable commands to Webots."""

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

    udp_socket = socket.socket(
        socket.AF_INET,
        socket.SOCK_DGRAM,
    )

    gesture_history: deque[str] = deque(
        maxlen=GESTURE_HISTORY_SIZE
    )

    current_command = "STOP"
    previous_command = ""

    start_time = time.monotonic()
    last_timestamp_ms = -1

    print("==========================================")
    print("NOVA GESTURE COMMAND SYSTEM STARTED")
    print("Open palm   -> STOP")
    print("Pointing up -> FORWARD")
    print("Victory     -> REVERSE")
    print("Thumb up    -> TURN RIGHT")
    print("Thumb down  -> TURN LEFT")
    print("Closed fist -> AUTONOMOUS MODE")
    print("I Love You  -> GESTURE MODE")
    print(f"Sending commands to UDP port {UDP_PORT}")
    print("Press Q inside the camera window to exit")
    print("==========================================")

    try:
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

                detected_gesture = "NO_HAND"
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
                        detected_gesture = top_gesture.category_name
                    else:
                        detected_gesture = "UNCERTAIN"

                if detected_gesture in GESTURE_COMMANDS:
                    gesture_history.append(detected_gesture)
                else:
                    gesture_history.append("NO_COMMAND")

                stable_gesture = get_stable_gesture(
                    gesture_history
                )

                if stable_gesture in GESTURE_COMMANDS:
                    current_command = GESTURE_COMMANDS[
                        stable_gesture
                    ]

                if current_command != previous_command:
                    print(f"NOVA COMMAND: {current_command}")

                    udp_socket.sendto(
                        current_command.encode("utf-8"),
                        (UDP_IP, UDP_PORT),
                    )

                    previous_command = current_command

                cv2.rectangle(
                    frame,
                    (10, 10),
                    (590, 145),
                    (0, 0, 0),
                    -1,
                )

                cv2.putText(
                    frame,
                    "NOVA GESTURE CONTROL",
                    (25, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.75,
                    (255, 255, 255),
                    2,
                )

                cv2.putText(
                    frame,
                    f"Detected: {detected_gesture}",
                    (25, 75),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.65,
                    (0, 255, 255),
                    2,
                )

                cv2.putText(
                    frame,
                    f"Confidence: {gesture_score:.0%}",
                    (25, 103),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.55,
                    (255, 255, 255),
                    1,
                )

                cv2.putText(
                    frame,
                    f"NOVA Command: {current_command}",
                    (25, 132),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.65,
                    (0, 255, 0),
                    2,
                )

                cv2.imshow(
                    "NOVA Gesture Command System",
                    frame,
                )

                key = cv2.waitKey(1) & 0xFF

                if key == ord("q"):
                    break

    finally:
        udp_socket.sendto(
            b"STOP",
            (UDP_IP, UDP_PORT),
        )

        udp_socket.close()
        camera.release()
        cv2.destroyAllWindows()

        print("NOVA COMMAND: STOP")
        print("Gesture command system closed safely.")


if __name__ == "__main__":
    main()