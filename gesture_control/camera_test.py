"""Basic webcam test for NOVA gesture control."""

import sys

import cv2


CAMERA_INDEX = 0


def main() -> None:
    """Open the webcam and display its live feed."""

    camera = cv2.VideoCapture(CAMERA_INDEX)

    if not camera.isOpened():
        print("ERROR: The webcam could not be opened.")
        print("Close Camera, Teams, Discord, Zoom, or other camera apps.")
        sys.exit(1)

    print("Webcam started successfully.")
    print("Press Q inside the camera window to close it.")

    while True:
        success, frame = camera.read()

        if not success:
            print("ERROR: Could not read a frame from the webcam.")
            break

        # Mirror the image so movement feels natural.
        frame = cv2.flip(frame, 1)

        cv2.putText(
            frame,
            "NOVA Gesture Camera Test | Press Q to exit",
            (20, 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
        )

        cv2.imshow("NOVA Gesture Control", frame)

        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):
            break

    camera.release()
    cv2.destroyAllWindows()
    print("Webcam closed safely.")


if __name__ == "__main__":
    main()