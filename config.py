#!/usr/bin/env python3
"""
Configuration file for Orange Ball Robot
Adjust these parameters based on your specific robot hardware and environment
"""

# Camera settings
CAMERA_INDEX = 0
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
CAMERA_FPS = 30

# Orange color detection in HSV color space
# You may need to adjust these values based on lighting conditions
ORANGE_HSV_LOWER = [5, 100, 100]    # Lower HSV threshold for orange
ORANGE_HSV_UPPER = [25, 255, 255]   # Upper HSV threshold for orange

# Ball detection parameters
MIN_BALL_AREA = 500        # Minimum area to consider as a ball (pixels²)
TARGET_BALL_AREA = 15000   # Target area when robot should stop (pixels²)
MAX_BALL_AREA = 50000      # Maximum area to prevent false positives (pixels²)

# Robot movement parameters
BASE_SPEED = 0.5           # Base motor speed (0.0 to 1.0)
TURN_SPEED = 0.4           # Speed when turning (0.0 to 1.0)
SEARCH_SPEED = 0.3         # Speed when searching for ball (0.0 to 1.0)

# Control thresholds
X_CENTER_THRESHOLD = 50    # Pixels offset before turning to center ball
TURN_DURATION = 1.5        # Duration for 90-degree turn (seconds)
SEARCH_TIMEOUT = 10        # Maximum search time before pausing (seconds)

# Motor GPIO pin configuration
# Adjust these pin numbers based on your motor driver connections
MOTOR_PINS = {
    'left_forward': 18,     # GPIO pin for left motor forward
    'left_backward': 19,    # GPIO pin for left motor backward
    'right_forward': 20,    # GPIO pin for right motor forward
    'right_backward': 21,   # GPIO pin for right motor backward
    'left_enable': 12,      # PWM pin for left motor speed control
    'right_enable': 13      # PWM pin for right motor speed control
}

# PWM frequency for motor speed control
PWM_FREQUENCY = 1000       # Hz

# Display settings
SHOW_DEBUG_WINDOWS = True  # Show camera feed and mask windows
SHOW_DETECTION_INFO = True # Show ball detection information on screen

# Audio settings
ENABLE_AUDIO = True        # Enable beep sounds when no ball is found
BEEP_INTERVAL = 3.0        # Seconds between beep sounds