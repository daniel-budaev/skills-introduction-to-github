#!/usr/bin/env python3
"""
Orange Ball Following Robot for Jetson Nano
This script controls a robot to move toward orange balls, stop near them, 
turn 90 degrees, and search for the next orange ball.
"""

import cv2
import numpy as np
import time
import threading
from enum import Enum

try:
    import RPi.GPIO as GPIO
except ImportError:
    print("Warning: RPi.GPIO not available. Running in simulation mode.")
    GPIO = None

try:
    import config
    print("Using configuration from config.py")
except ImportError:
    print("Warning: config.py not found. Using default values.")
    config = None

class RobotState(Enum):
    SEARCHING = "searching"
    MOVING_TO_BALL = "moving_to_ball"
    STOPPING = "stopping"
    TURNING = "turning"

class OrangeBallRobot:
    def __init__(self):
        # Robot state
        self.state = RobotState.SEARCHING
        self.running = True
        
        # Load configuration values
        camera_index = config.CAMERA_INDEX if config else 0
        camera_width = config.CAMERA_WIDTH if config else 640
        camera_height = config.CAMERA_HEIGHT if config else 480
        camera_fps = config.CAMERA_FPS if config else 30
        
        # Camera setup
        self.camera = cv2.VideoCapture(camera_index)
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, camera_width)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, camera_height)
        self.camera.set(cv2.CAP_PROP_FPS, camera_fps)
        
        # Orange color detection parameters (HSV)
        orange_lower = config.ORANGE_HSV_LOWER if config else [5, 100, 100]
        orange_upper = config.ORANGE_HSV_UPPER if config else [25, 255, 255]
        self.orange_lower = np.array(orange_lower)
        self.orange_upper = np.array(orange_upper)
        
        # Ball detection parameters
        self.min_ball_area = config.MIN_BALL_AREA if config else 500
        self.target_ball_area = config.TARGET_BALL_AREA if config else 15000
        self.max_ball_area = config.MAX_BALL_AREA if config else 50000
        
        # Robot control parameters
        self.base_speed = config.BASE_SPEED if config else 0.5
        self.turn_speed = config.TURN_SPEED if config else 0.4
        self.search_speed = config.SEARCH_SPEED if config else 0.3
        
        # Control thresholds
        self.x_center_threshold = config.X_CENTER_THRESHOLD if config else 50
        self.turn_duration = config.TURN_DURATION if config else 1.5
        self.search_timeout = config.SEARCH_TIMEOUT if config else 10
        
        # Display settings
        self.show_debug_windows = config.SHOW_DEBUG_WINDOWS if config else True
        self.show_detection_info = config.SHOW_DETECTION_INFO if config else True
        
        # Motor GPIO pins
        self.motor_pins = config.MOTOR_PINS if config else {
            'left_forward': 18,
            'left_backward': 19,
            'right_forward': 20,
            'right_backward': 21,
            'left_enable': 12,
            'right_enable': 13
        }
        
        # PWM frequency
        self.pwm_frequency = config.PWM_FREQUENCY if config else 1000
        
        # Initialize GPIO
        self.setup_gpio()
        
        # Control variables
        self.last_ball_center = None
        self.turn_start_time = None
        self.search_start_time = None
        
    def setup_gpio(self):
        """Initialize GPIO pins for motor control"""
        if GPIO is None:
            print("GPIO not available - running in simulation mode")
            return
            
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        # Setup motor pins
        for pin in self.motor_pins.values():
            GPIO.setup(pin, GPIO.OUT)
        
        # Setup PWM for motor speed control
        self.left_pwm = GPIO.PWM(self.motor_pins['left_enable'], self.pwm_frequency)
        self.right_pwm = GPIO.PWM(self.motor_pins['right_enable'], self.pwm_frequency)
        self.left_pwm.start(0)
        self.right_pwm.start(0)
        
    def cleanup_gpio(self):
        """Clean up GPIO pins"""
        if GPIO is None:
            return
        self.stop_motors()
        self.left_pwm.stop()
        self.right_pwm.stop()
        GPIO.cleanup()
        
    def stop_motors(self):
        """Stop both motors"""
        if GPIO is None:
            print("SIMULATION: Motors stopped")
            return
            
        GPIO.output(self.motor_pins['left_forward'], GPIO.LOW)
        GPIO.output(self.motor_pins['left_backward'], GPIO.LOW)
        GPIO.output(self.motor_pins['right_forward'], GPIO.LOW)
        GPIO.output(self.motor_pins['right_backward'], GPIO.LOW)
        self.left_pwm.ChangeDutyCycle(0)
        self.right_pwm.ChangeDutyCycle(0)
        
    def move_forward(self, speed=None):
        """Move robot forward"""
        if speed is None:
            speed = self.base_speed
            
        if GPIO is None:
            print(f"SIMULATION: Moving forward at speed {speed}")
            return
            
        GPIO.output(self.motor_pins['left_forward'], GPIO.HIGH)
        GPIO.output(self.motor_pins['left_backward'], GPIO.LOW)
        GPIO.output(self.motor_pins['right_forward'], GPIO.HIGH)
        GPIO.output(self.motor_pins['right_backward'], GPIO.LOW)
        
        self.left_pwm.ChangeDutyCycle(speed * 100)
        self.right_pwm.ChangeDutyCycle(speed * 100)
        
    def turn_left(self, speed=None):
        """Turn robot left"""
        if speed is None:
            speed = self.turn_speed
            
        if GPIO is None:
            print(f"SIMULATION: Turning left at speed {speed}")
            return
            
        GPIO.output(self.motor_pins['left_forward'], GPIO.LOW)
        GPIO.output(self.motor_pins['left_backward'], GPIO.HIGH)
        GPIO.output(self.motor_pins['right_forward'], GPIO.HIGH)
        GPIO.output(self.motor_pins['right_backward'], GPIO.LOW)
        
        self.left_pwm.ChangeDutyCycle(speed * 100)
        self.right_pwm.ChangeDutyCycle(speed * 100)
        
    def turn_right(self, speed=None):
        """Turn robot right"""
        if speed is None:
            speed = self.turn_speed
            
        if GPIO is None:
            print(f"SIMULATION: Turning right at speed {speed}")
            return
            
        GPIO.output(self.motor_pins['left_forward'], GPIO.HIGH)
        GPIO.output(self.motor_pins['left_backward'], GPIO.LOW)
        GPIO.output(self.motor_pins['right_forward'], GPIO.LOW)
        GPIO.output(self.motor_pins['right_backward'], GPIO.HIGH)
        
        self.left_pwm.ChangeDutyCycle(speed * 100)
        self.right_pwm.ChangeDutyCycle(speed * 100)
        
    def detect_orange_ball(self, frame):
        """Detect orange ball in the frame and return its center and area"""
        # Convert to HSV color space
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Create mask for orange color
        mask = cv2.inRange(hsv, self.orange_lower, self.orange_upper)
        
        # Apply morphological operations to clean up the mask
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        
        # Find contours
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return None, None, mask
            
        # Find the largest contour (assuming it's the ball)
        largest_contour = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(largest_contour)
        
        # Check if the area is within reasonable bounds
        if area < self.min_ball_area or area > self.max_ball_area:
            return None, None, mask
            
        # Calculate the center of the ball
        M = cv2.moments(largest_contour)
        if M["m00"] > 0:
            center_x = int(M["m10"] / M["m00"])
            center_y = int(M["m01"] / M["m00"])
            return (center_x, center_y), area, mask
            
        return None, None, mask
        
    def calculate_movement(self, ball_center, frame_center, ball_area):
        """Calculate robot movement based on ball position and size"""
        if ball_center is None:
            return "search"
            
        center_x, center_y = ball_center
        frame_center_x, frame_center_y = frame_center
        
        # Calculate horizontal offset
        x_offset = center_x - frame_center_x
        
        # Check if ball is close enough (large enough area)
        if ball_area > self.target_ball_area:
            return "stop"
        elif abs(x_offset) > self.x_center_threshold:
            if x_offset > 0:
                return "turn_right"
            else:
                return "turn_left"
        else:
            return "forward"
            
    def search_for_ball(self):
        """Search for ball by turning slowly"""
        if self.search_start_time is None:
            self.search_start_time = time.time()
            
        # Turn left slowly to search
        self.turn_left(speed=self.search_speed)
        
        # If we've been searching for too long, stop and wait
        if time.time() - self.search_start_time > self.search_timeout:
            self.stop_motors()
            time.sleep(1)
            self.search_start_time = None
            
    def execute_90_degree_turn(self):
        """Execute a 90-degree turn to the right"""
        if self.turn_start_time is None:
            self.turn_start_time = time.time()
            print("Starting 90-degree turn...")
            
        # Turn right for approximately 90 degrees
        # Adjust the duration based on your robot's turning speed
        if time.time() - self.turn_start_time < self.turn_duration:
            self.turn_right()
        else:
            self.stop_motors()
            self.turn_start_time = None
            self.search_start_time = None
            self.state = RobotState.SEARCHING
            print("90-degree turn completed. Searching for next ball...")
            
    def run(self):
        """Main robot control loop"""
        print("Starting Orange Ball Robot...")
        print("Press 'q' to quit")
        
        try:
            while self.running:
                # Capture frame
                ret, frame = self.camera.read()
                if not ret:
                    print("Failed to capture frame")
                    break
                    
                frame_height, frame_width = frame.shape[:2]
                frame_center = (frame_width // 2, frame_height // 2)
                
                # Detect orange ball
                ball_center, ball_area, mask = self.detect_orange_ball(frame)
                
                # State machine for robot behavior
                if self.state == RobotState.SEARCHING:
                    if ball_center is not None:
                        print(f"Ball detected! Area: {ball_area}")
                        self.state = RobotState.MOVING_TO_BALL
                        self.search_start_time = None
                    else:
                        self.search_for_ball()
                        
                elif self.state == RobotState.MOVING_TO_BALL:
                    if ball_center is None:
                        print("Lost ball, searching again...")
                        self.state = RobotState.SEARCHING
                        continue
                        
                    movement = self.calculate_movement(ball_center, frame_center, ball_area)
                    
                    if movement == "stop":
                        print("Reached ball! Stopping and preparing to turn...")
                        self.stop_motors()
                        self.state = RobotState.STOPPING
                        time.sleep(0.5)  # Brief pause
                        self.state = RobotState.TURNING
                    elif movement == "forward":
                        self.move_forward()
                    elif movement == "turn_left":
                        self.turn_left()
                    elif movement == "turn_right":
                        self.turn_right()
                        
                elif self.state == RobotState.STOPPING:
                    self.stop_motors()
                    time.sleep(0.5)
                    self.state = RobotState.TURNING
                    
                elif self.state == RobotState.TURNING:
                    self.execute_90_degree_turn()
                
                # Display the frame with detection results
                display_frame = frame.copy()
                
                # Draw ball detection
                if ball_center is not None:
                    cv2.circle(display_frame, ball_center, 10, (0, 255, 0), 2)
                    cv2.putText(display_frame, f"Area: {ball_area}", 
                              (ball_center[0] + 15, ball_center[1]), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                
                # Draw center crosshair
                cv2.line(display_frame, (frame_center[0] - 20, frame_center[1]), 
                        (frame_center[0] + 20, frame_center[1]), (255, 0, 0), 2)
                cv2.line(display_frame, (frame_center[0], frame_center[1] - 20), 
                        (frame_center[0], frame_center[1] + 20), (255, 0, 0), 2)
                
                # Display state information
                cv2.putText(display_frame, f"State: {self.state.value}", 
                          (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                
                # Show the frame (if debug windows are enabled)
                if self.show_debug_windows:
                    cv2.imshow('Orange Ball Robot', display_frame)
                    cv2.imshow('Mask', mask)
                
                # Check for quit command
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                    
        except KeyboardInterrupt:
            print("\nStopping robot...")
            
        finally:
            self.cleanup()
            
    def cleanup(self):
        """Clean up resources"""
        self.running = False
        self.stop_motors()
        self.cleanup_gpio()
        self.camera.release()
        cv2.destroyAllWindows()
        print("Cleanup completed")

def main():
    """Main function"""
    robot = OrangeBallRobot()
    
    try:
        robot.run()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        robot.cleanup()

if __name__ == "__main__":
    main()