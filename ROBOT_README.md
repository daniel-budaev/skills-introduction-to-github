# Orange Ball Following Robot for Jetson Nano

This project provides a complete solution for a Jetson Nano-based robot that can detect orange balls, move toward them, stop nearby, turn 90 degrees, and search for the next ball.

## Features

- **Computer Vision**: Real-time orange ball detection using OpenCV and HSV color filtering
- **Autonomous Navigation**: State-based robot control for searching, approaching, and turning
- **Motor Control**: PWM-based differential drive control for smooth movement
- **Configurable Parameters**: Easy-to-adjust settings for different environments and hardware
- **Color Calibration Tool**: Interactive tool to tune orange detection for your lighting conditions
- **Simulation Mode**: Test the code without GPIO hardware

## Hardware Requirements

### Essential Components
- NVIDIA Jetson Nano Developer Kit
- USB Camera (or CSI camera module)
- Robot chassis with differential drive (2 wheels + motors)
- Motor driver board (L298N or similar)
- Orange ball(s) for testing

### Recommended Hardware
- 2x DC geared motors (6V-12V)
- L298N Dual H-Bridge Motor Driver
- Jumper wires for connections
- Power supply for motors (separate from Jetson Nano)
- Robot chassis or frame

## Wiring Diagram

Connect your motor driver to the Jetson Nano GPIO pins as follows (default configuration):

```
Jetson Nano GPIO    →    L298N Motor Driver
GPIO 18             →    IN1 (Left Motor Forward)
GPIO 19             →    IN2 (Left Motor Backward)
GPIO 20             →    IN3 (Right Motor Forward)
GPIO 21             →    IN4 (Right Motor Backward)
GPIO 12 (PWM)       →    ENA (Left Motor Speed)
GPIO 13 (PWM)       →    ENB (Right Motor Speed)
GND                 →    GND
```

**Note**: Adjust pin numbers in `config.py` if your wiring is different.

## Software Installation

### 1. Quick Setup (Recommended)
```bash
# Make setup script executable
chmod +x setup.sh

# Run the automated setup
./setup.sh

# Reboot to apply camera permissions
sudo reboot
```

### 2. Manual Installation
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3 python3-pip python3-opencv libgtk-3-dev

# Install Python packages
pip3 install -r requirements.txt

# Set camera permissions
sudo usermod -a -G video $USER
```

## Configuration

### 1. Color Calibration
Before running the robot, calibrate the orange ball detection:

```bash
python3 color_calibration.py
```

- Use the trackbars to adjust HSV values until only the orange ball is highlighted
- Press 's' to save the values to `config.py`
- Press 'q' to quit

### 2. Hardware Configuration
Edit `config.py` to match your hardware setup:

```python
# Motor GPIO pins - adjust based on your wiring
MOTOR_PINS = {
    'left_forward': 18,
    'left_backward': 19,
    'right_forward': 20,
    'right_backward': 21,
    'left_enable': 12,
    'right_enable': 13
}

# Speed settings - adjust based on your motors
BASE_SPEED = 0.5        # Normal driving speed (0.0 to 1.0)
TURN_SPEED = 0.4        # Turning speed
SEARCH_SPEED = 0.3      # Search rotation speed

# Ball detection - adjust based on distance and ball size
TARGET_BALL_AREA = 15000  # Stop when ball reaches this size
MIN_BALL_AREA = 500       # Minimum size to detect as ball
```

## Usage

### Running the Robot
```bash
python3 orange_ball_robot.py
```

The robot will:
1. **Search**: Rotate slowly to find an orange ball
2. **Approach**: Move toward the detected ball, adjusting direction as needed
3. **Stop**: Stop when close enough to the ball
4. **Turn**: Execute a 90-degree right turn
5. **Repeat**: Search for the next orange ball

### Controls
- Press 'q' to quit the program
- The robot shows live camera feed with detection overlay
- Current state is displayed on screen

### Robot States
- **SEARCHING**: Looking for orange ball by rotating
- **MOVING_TO_BALL**: Approaching detected ball
- **STOPPING**: Brief pause before turning
- **TURNING**: Executing 90-degree turn

## File Structure

```
├── orange_ball_robot.py     # Main robot control script
├── color_calibration.py     # HSV color tuning tool
├── config.py               # Configuration parameters
├── requirements.txt        # Python dependencies
├── setup.sh               # Automated setup script
└── ROBOT_README.md        # This documentation
```

## Algorithm Overview

### Ball Detection
1. Convert camera frame from BGR to HSV color space
2. Apply color mask using configured HSV thresholds
3. Use morphological operations to clean up noise
4. Find contours and select largest valid contour as ball
5. Calculate ball center and area

### Movement Control
```
if ball_area > TARGET_AREA:
    → STOP (close enough)
elif ball_center_x > frame_center + threshold:
    → TURN_RIGHT (ball is right of center)
elif ball_center_x < frame_center - threshold:
    → TURN_LEFT (ball is left of center)
else:
    → MOVE_FORWARD (ball is centered)
```

### State Machine
```
SEARCHING → (ball detected) → MOVING_TO_BALL
MOVING_TO_BALL → (ball reached) → STOPPING → TURNING
TURNING → (turn complete) → SEARCHING
MOVING_TO_BALL → (ball lost) → SEARCHING
```

## Troubleshooting

### Camera Issues
```bash
# Check if camera is detected
ls /dev/video*

# Test camera access
python3 -c "import cv2; cap = cv2.VideoCapture(0); print('Camera OK' if cap.read()[0] else 'Camera Error')"
```

### GPIO Issues
- Ensure you're in the `gpio` group: `groups $USER`
- Try running with sudo (not recommended for production)
- Check pin connections with multimeter

### Detection Issues
- Use `color_calibration.py` to retune HSV values
- Adjust lighting conditions
- Try different colored balls
- Modify `MIN_BALL_AREA` and `MAX_BALL_AREA` in config

### Motor Issues
- Check motor driver connections
- Verify power supply voltage
- Test motors individually
- Adjust speed values in config

## Customization

### Adding Obstacle Avoidance
Add ultrasonic sensor code in the movement functions:

```python
def move_forward(self, speed=None):
    # Add ultrasonic sensor check here
    if distance_sensor() < MIN_DISTANCE:
        self.stop_motors()
        return
    # ... existing motor code
```

### Different Turn Angles
Modify the turn duration in config or add angle parameter:

```python
# For 45-degree turn instead of 90
TURN_DURATION = 0.75  # Half the time
```

### Multiple Ball Types
Extend the detection to handle multiple colors:

```python
# Add different HSV ranges for different colored balls
BLUE_HSV_LOWER = [100, 100, 100]
BLUE_HSV_UPPER = [130, 255, 255]
```

## Performance Tips

1. **Reduce camera resolution** for faster processing:
   ```python
   CAMERA_WIDTH = 320
   CAMERA_HEIGHT = 240
   ```

2. **Optimize detection area** - only process center region of frame

3. **Adjust detection frequency** - skip frames for better performance

4. **Use GPU acceleration** for OpenCV operations on Jetson Nano

## Safety Considerations

- Always have a way to quickly stop the robot (emergency stop button)
- Test in a safe, enclosed area first
- Keep motor speeds reasonable to prevent damage
- Monitor battery levels if using battery power
- Ensure proper ventilation for the Jetson Nano

## License

This project is open source. Feel free to modify and distribute.

## Contributing

To contribute to this project:
1. Fork the repository
2. Create a feature branch
3. Test your changes thoroughly
4. Submit a pull request

## Support

For issues and questions:
- Check the troubleshooting section above
- Verify your hardware connections
- Test with the calibration tool first
- Ensure all dependencies are installed correctly