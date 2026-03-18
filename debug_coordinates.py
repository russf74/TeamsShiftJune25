#!/usr/bin/env python3
"""
Simple coordinate finder - capture around X787 and X895 with larger area
"""

import pyautogui
import cv2
import numpy as np

def capture_around_coordinates():
    """Capture larger areas around X787 and X895 to see the actual content"""
    
    print("Capturing larger areas around X787 and X895...")
    
    # Capture larger areas around the expected X coordinates
    regions = [
        (787, 200, 100, 100, "X787"),  # 100x100 around X787
        (895, 200, 100, 100, "X895"),  # 100x100 around X895
    ]
    
    for x, y, w, h, name in regions:
        print(f"Capturing {name} region: ({x}, {y}) size {w}x{h}")
        
        try:
            # Capture with pyautogui
            screenshot = pyautogui.screenshot(region=(x, y, w, h))
            img = np.array(screenshot)
            img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            
            # Save the capture
            filename = f"debug_{name}_large.png"
            cv2.imwrite(filename, img_bgr)
            print(f"  Saved: {filename}")
            
            # Also create a grid overlay to help identify coordinates
            grid_img = img_bgr.copy()
            
            # Draw grid lines every 10 pixels
            for i in range(0, w, 10):
                cv2.line(grid_img, (i, 0), (i, h), (0, 255, 0), 1)
            for i in range(0, h, 10):
                cv2.line(grid_img, (0, i), (w, i), (0, 255, 0), 1)
            
            # Add coordinate labels
            cv2.putText(grid_img, f"{x},{y}", (5, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
            cv2.putText(grid_img, f"{x+w},{y+h}", (w-70, h-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
            
            # Save grid version
            grid_filename = f"debug_{name}_grid.png"
            cv2.imwrite(grid_filename, grid_img)
            print(f"  Saved grid: {grid_filename}")
            
        except Exception as e:
            print(f"  Error capturing {name}: {e}")
    
    print("\nNext steps:")
    print("1. Look at debug_X787_large.png and debug_X895_large.png")
    print("2. Identify where the '11' and '13' actually appear")
    print("3. Use the grid images to find exact coordinates")

if __name__ == "__main__":
    capture_around_coordinates()