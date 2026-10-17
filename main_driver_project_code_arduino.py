"""
Drowsy Driver Alert - webcam + Arduino buzzer
(your eye detection code + serial output to the Arduino)
Works with new MediaPipe versions (Python 3.13 / 3.14 too).

Install:  pip install opencv-python mediapipe numpy pyserial
Run:      python main_driver_project_code_arduino.py
Quit:     press 'q' in the video window

The first run downloads a small face model (~4 MB) next to this file.
"""

import os
import time
import urllib.request

import cv2
import numpy as np
import mediapipe as mp
import serial
import serial.tools.list_ports
from mediapipe.tasks.python import BaseOptions, vision

EAR_THRESHOLD = 0.21    # below this = eye closed
CLOSED_SECONDS = 1.5    # closed longer than this = SLEEPY
CAMERA_INDEX = 0        # try 1 if the camera doesn't open

SERIAL_PORT = None      # e.g. "COM3" or "/dev/ttyACM0"; None = auto-detect
BAUD_RATE = 9600        # must match Serial.begin(9600) in the Arduino code

MODEL_URL = ("https://storage.googleapis.com/mediapipe-models/"
             "face_landmarker/face_landmarker/float16/1/face_landmarker.task")
MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "face_landmarker.task")

# [outer corner, top1, top2, inner corner, bottom2, bottom1]
LEFT_EYE = [362, 385, 387, 263, 373, 380]
RIGHT_EYE = [33, 160, 158, 133, 153, 144]


def ensure_model():
    if not os.path.exists(MODEL_PATH):
        print("Downloading face model (one time only)...")
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
        print("Done.")


def connect_arduino():
    """Open the Arduino serial port. Returns None if not found (video still works)."""
    port = SERIAL_PORT
    if port is None:
        for p in serial.tools.list_ports.comports():
            info = f"{p.description} {p.manufacturer}".lower()
            if any(k in info for k in ("arduino", "ch340", "usb serial", "usb-serial", "acm")):
                port = p.device
                break
    if port is None:
        print("No Arduino found - running without buzzer.")
        return None
    try:
        ser = serial.Serial(port, BAUD_RATE, timeout=0)
        time.sleep(2)  # Arduino resets when the port opens
        print(f"Arduino connected on {port}")
        return ser
    except serial.SerialException as e:
        print(f"Could not open {port}: {e}\nRunning without buzzer.")
        return None


def send(ser, ch):
    """Send 'S' (sleepy) or 'A' (awake) to the Arduino."""
    if ser is None:
        return
    try:
        ser.write(ch)
    except serial.SerialException:
        pass


def eye_points(lm, idx, w, h):
    return np.array([[lm[i].x * w, lm[i].y * h] for i in idx])


def ear(p):
    a = np.linalg.norm(p[1] - p[5])
    b = np.linalg.norm(p[2] - p[4])
    c = np.linalg.norm(p[0] - p[3])
    return (a + b) / (2.0 * c)


def main():
    ensure_model()
    arduino = connect_arduino()

    options = vision.FaceLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=MODEL_PATH),
        running_mode=vision.RunningMode.VIDEO,
        num_faces=1,
    )
    landmarker = vision.FaceLandmarker.create_from_options(options)

    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        raise SystemExit("Could not open the camera. Close other apps using it, "
                         "or change CAMERA_INDEX.")

    closed_since = None
    start = time.time()

    while True:
        ok, frame = cap.read()
        if not ok:
            break
        frame = cv2.flip(frame, 1)
        h, w = frame.shape[:2]

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        timestamp_ms = int((time.time() - start) * 1000)
        result = landmarker.detect_for_video(mp_image, timestamp_ms)

        status, color = "NO FACE", (200, 200, 200)
        sleepy = False

        if result.face_landmarks:
            lm = result.face_landmarks[0]
            left = eye_points(lm, LEFT_EYE, w, h)
            right = eye_points(lm, RIGHT_EYE, w, h)
            value = (ear(left) + ear(right)) / 2.0

            # draw the eye outline and the 6 points per eye
            for eye in (left, right):
                cv2.polylines(frame, [eye.astype(np.int32)], True, (0, 255, 0), 1)
                for p in eye:
                    cv2.circle(frame, (int(p[0]), int(p[1])), 2, (0, 255, 255), -1)

            if value < EAR_THRESHOLD:
                closed_since = closed_since or time.time()
                secs = time.time() - closed_since
                sleepy = secs >= CLOSED_SECONDS
                cv2.putText(frame, f"Eyes closed: {secs:.1f}s", (10, 110),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)
            else:
                closed_since = None

            status = "SLEEPY! ALERT!" if sleepy else "AWAKE"
            color = (0, 0, 255) if sleepy else (0, 255, 0)
            cv2.putText(frame, f"EAR: {value:.2f}  (threshold {EAR_THRESHOLD})", (10, 80),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        else:
            closed_since = None

        # tell the Arduino: S = sleepy -> buzzer ON, A = awake / no face -> buzzer OFF
        send(arduino, b"S" if sleepy else b"A")

        cv2.putText(frame, status, (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 3)
        cv2.imshow("Drowsy Driver Alert", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    send(arduino, b"A")  # make sure the buzzer is off on exit
    if arduino is not None:
        arduino.close()
    landmarker.close()
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
