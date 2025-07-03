#!/bin/bash

# Orange Ball Robot Setup Script for Jetson Nano
# This script installs necessary dependencies and prepares the system

echo "========================================="
echo "Orange Ball Robot Setup for Jetson Nano"
echo "========================================="

# Update system
echo "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Python3 and pip if not already installed
echo "Installing Python3 and pip..."
sudo apt install -y python3 python3-pip python3-dev

# Install system dependencies for OpenCV
echo "Installing system dependencies for OpenCV..."
sudo apt install -y \
    libopencv-dev \
    python3-opencv \
    libgtk-3-dev \
    libcanberra-gtk-module \
    libcanberra-gtk3-module

# Install additional dependencies
echo "Installing additional system dependencies..."
sudo apt install -y \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libv4l-dev \
    libxvidcore-dev \
    libx264-dev \
    libgtk-3-dev \
    libatlas-base-dev \
    gfortran \
    beep \
    alsa-utils \
    pulseaudio

# Install Python packages
echo "Installing Python packages..."
pip3 install --upgrade pip
pip3 install -r requirements.txt

# Set up camera permissions
echo "Setting up camera permissions..."
sudo usermod -a -G video $USER

# Make Python scripts executable
echo "Making Python scripts executable..."
chmod +x orange_ball_robot.py
chmod +x color_calibration.py
chmod +x test_audio.py

# Create desktop shortcut for easy access
echo "Creating desktop shortcuts..."
cat > ~/Desktop/orange_ball_robot.desktop << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Orange Ball Robot
Comment=Start the orange ball following robot
Exec=python3 $(pwd)/orange_ball_robot.py
Icon=system-run
Terminal=true
Categories=Application;
EOF

cat > ~/Desktop/color_calibration.desktop << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Color Calibration
Comment=Calibrate orange ball color detection
Exec=python3 $(pwd)/color_calibration.py
Icon=preferences-system
Terminal=true
Categories=Application;
EOF

cat > ~/Desktop/test_audio.desktop << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Audio Test
Comment=Test beep functionality for robot
Exec=python3 $(pwd)/test_audio.py
Icon=audio-speakers
Terminal=true
Categories=Application;
EOF

chmod +x ~/Desktop/orange_ball_robot.desktop
chmod +x ~/Desktop/color_calibration.desktop
chmod +x ~/Desktop/test_audio.desktop

echo ""
echo "========================================="
echo "Setup completed successfully!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Reboot the system to apply camera permissions"
echo "2. Run 'python3 test_audio.py' to test audio functionality"
echo "3. Run 'python3 color_calibration.py' to calibrate orange detection"
echo "4. Adjust motor pin configuration in config.py for your robot"
echo "5. Run 'python3 orange_ball_robot.py' to start the robot"
echo ""
echo "Files created:"
echo "- orange_ball_robot.py (main robot control)"
echo "- color_calibration.py (color tuning tool)"
echo "- test_audio.py (audio beep testing)"
echo "- config.py (configuration settings)"
echo "- requirements.txt (Python dependencies)"
echo ""
echo "Desktop shortcuts created for easy access!"