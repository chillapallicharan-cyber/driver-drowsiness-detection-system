# Drowsy Driver Alert
Detects eye closure with a webcam (MediaPipe + OpenCV) and sounds an Arduino buzzer.
# Driver Drowsiness Detection System

Detects driver drowsiness using a webcam (MediaPipe + OpenCV) and sounds an Arduino buzzer when the eyes stay closed too long.

## How it works
- Python calculates the Eye Aspect Ratio (EAR) from face landmarks.
- If EAR stays below 0.21 for 1.5 seconds, it sends `S` to the Arduino over USB serial.
- The Arduino beeps the buzzer (pin 8) until it receives `A`.

## Hardware
- Arduino Uno
- Buzzer: (+) to pin 8, (-) to GND
- Webcam

## Setup
1. Upload `arduino/drowsy_buzzer/drowsy_buzzer.ino` to the Arduino.
2. Install libraries: `pip install -r requirements.txt`
3. Run: `python main_driver_project_code_arduino.py`
4. Press `q` in the video window to quit.

## Demo
(add your video link here)