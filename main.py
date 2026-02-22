# SmartNightLamp (Raspberry Pi + USB Relay + IR Camera + USB LED)
# --- Required Libraries ---
# pyserial: Control USB relay modules
# opencv-python: Capture frames from camera
# mediapipe: Perform human pose estimation
# datetime: Check active time window

import cv2
import mediapipe as mp
import time
import serial
from datetime import datetime

# Device paths (check using: ls /dev/serial/by-id/)
USB_LED_PORT = '/dev/serial/by-id/usb-relay-usbled'
IR_LED_PORT = '/dev/serial/by-id/usb-relay-irled'

# Initialize USB relay connections
usb_led = serial.Serial(USB_LED_PORT, 9600)
ir_led = serial.Serial(IR_LED_PORT, 9600)

def relay_on(relay):
    relay.write(b'\xA0\x01\x01\xA2')

def relay_off(relay):
    relay.write(b'\xA0\x01\x00\xA1')

def in_night_mode():
    now = datetime.now()
    return now.hour >= 0 and now.hour < 6

# Initialize MediaPipe pose estimation
mp_pose = mp.solutions.pose
pose = mp_pose.Pose()

# Initialize camera (Pi Camera or USB camera)
cap = cv2.VideoCapture(0)

print("System started... Detection only active during night mode.")

led_on_time = 0
LED_DURATION = 120  # seconds

while True:
    if not in_night_mode():
        time.sleep(60)
        continue

    # Turn on IR illuminator
    relay_on(ir_led)

    ret, frame = cap.read()  # Capture a frame from the camera
    if not ret:
        continue

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # Convert BGR to RGB
    results = pose.process(rgb_frame)                   # Run pose estimation

    if results.pose_landmarks:
        landmarks = results.pose_landmarks.landmark  # Extract detected landmarks
        nose_y = landmarks[mp_pose.PoseLandmark.NOSE].y
        hip_y = landmarks[mp_pose.PoseLandmark.LEFT_HIP].y

        # If nose is significantly higher than hip,
        # interpret it as a standing-up action
        if nose_y < hip_y - 0.1:
            print("Standing detected! Turning on USB LED.")
            relay_on(usb_led)
            led_on_time = time.time()

    # Turn off LED after predefined duration
    if led_on_time != 0 and time.time() - led_on_time > LED_DURATION:
        print("Timeout reached. Turning off USB LED.")
        relay_off(usb_led)
        led_on_time = 0

    time.sleep(1)  # Check once per second
