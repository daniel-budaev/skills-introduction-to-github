#!/usr/bin/env python3
"""
Color Calibration Tool for Orange Ball Detection
Use this script to find the optimal HSV color thresholds for your orange ball
under your specific lighting conditions.
"""

import cv2
import numpy as np

class ColorCalibrator:
    def __init__(self):
        self.camera = cv2.VideoCapture(0)
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        # Create trackbars for HSV adjustments
        cv2.namedWindow('Controls')
        cv2.createTrackbar('H Min', 'Controls', 5, 179, self.nothing)
        cv2.createTrackbar('S Min', 'Controls', 100, 255, self.nothing)
        cv2.createTrackbar('V Min', 'Controls', 100, 255, self.nothing)
        cv2.createTrackbar('H Max', 'Controls', 25, 179, self.nothing)
        cv2.createTrackbar('S Max', 'Controls', 255, 255, self.nothing)
        cv2.createTrackbar('V Max', 'Controls', 255, 255, self.nothing)
        
    def nothing(self, val):
        """Callback function for trackbars"""
        pass
        
    def run(self):
        """Main calibration loop"""
        print("Orange Ball Color Calibration Tool")
        print("Adjust the trackbars to isolate the orange ball")
        print("Press 's' to save current values to config")
        print("Press 'q' to quit")
        
        while True:
            ret, frame = self.camera.read()
            if not ret:
                break
                
            # Get trackbar values
            h_min = cv2.getTrackbarPos('H Min', 'Controls')
            s_min = cv2.getTrackbarPos('S Min', 'Controls')
            v_min = cv2.getTrackbarPos('V Min', 'Controls')
            h_max = cv2.getTrackbarPos('H Max', 'Controls')
            s_max = cv2.getTrackbarPos('S Max', 'Controls')
            v_max = cv2.getTrackbarPos('V Max', 'Controls')
            
            # Create HSV thresholds
            lower = np.array([h_min, s_min, v_min])
            upper = np.array([h_max, s_max, v_max])
            
            # Convert to HSV and create mask
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            mask = cv2.inRange(hsv, lower, upper)
            
            # Apply morphological operations
            kernel = np.ones((5, 5), np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
            
            # Find contours and draw them
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            result = frame.copy()
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 500:  # Filter small contours
                    cv2.drawContours(result, [contour], -1, (0, 255, 0), 2)
                    
                    # Draw center point
                    M = cv2.moments(contour)
                    if M["m00"] > 0:
                        cx = int(M["m10"] / M["m00"])
                        cy = int(M["m01"] / M["m00"])
                        cv2.circle(result, (cx, cy), 5, (255, 0, 0), -1)
                        cv2.putText(result, f"Area: {int(area)}", (cx + 10, cy),
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # Display current HSV values
            cv2.putText(result, f"HSV Lower: [{h_min}, {s_min}, {v_min}]", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.putText(result, f"HSV Upper: [{h_max}, {s_max}, {v_max}]", 
                       (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # Show windows
            cv2.imshow('Original', frame)
            cv2.imshow('Mask', mask)
            cv2.imshow('Result', result)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('s'):
                self.save_config(lower, upper)
                
        self.cleanup()
        
    def save_config(self, lower, upper):
        """Save the current HSV values to config file"""
        config_lines = []
        
        try:
            with open('config.py', 'r') as f:
                lines = f.readlines()
                
            for line in lines:
                if 'ORANGE_HSV_LOWER' in line:
                    config_lines.append(f"ORANGE_HSV_LOWER = {lower.tolist()}    # Lower HSV threshold for orange\n")
                elif 'ORANGE_HSV_UPPER' in line:
                    config_lines.append(f"ORANGE_HSV_UPPER = {upper.tolist()}   # Upper HSV threshold for orange\n")
                else:
                    config_lines.append(line)
                    
            with open('config.py', 'w') as f:
                f.writelines(config_lines)
                
            print(f"Saved HSV values to config.py:")
            print(f"  Lower: {lower}")
            print(f"  Upper: {upper}")
            
        except Exception as e:
            print(f"Error saving config: {e}")
            print(f"Manual values to use:")
            print(f"  ORANGE_HSV_LOWER = {lower.tolist()}")
            print(f"  ORANGE_HSV_UPPER = {upper.tolist()}")
            
    def cleanup(self):
        """Clean up resources"""
        self.camera.release()
        cv2.destroyAllWindows()

def main():
    calibrator = ColorCalibrator()
    calibrator.run()

if __name__ == "__main__":
    main()