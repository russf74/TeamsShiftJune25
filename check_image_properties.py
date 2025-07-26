#!/usr/bin/env python3
"""
Check the properties of the shifts.png file
"""

import os
from PIL import Image

def check_image_properties():
    filename = 'shifts.png'
    
    if not os.path.exists(filename):
        print(f"ERROR: {filename} not found!")
        return
    
    try:
        # Get file size
        file_size = os.path.getsize(filename)
        print(f"File: {filename}")
        print(f"File size: {file_size} bytes")
        
        # Open with PIL to get image properties
        with Image.open(filename) as img:
            print(f"Image size: {img.size} (width x height)")
            print(f"Image mode: {img.mode}")
            print(f"Image format: {img.format}")
            
            # Check if it's too small (pyautogui might have issues with very small images)
            if img.size[0] < 10 or img.size[1] < 10:
                print("WARNING: Image is very small, this might cause recognition issues")
            
            # Check if it's too large
            if img.size[0] > 500 or img.size[1] > 500:
                print("WARNING: Image is quite large, this might slow down recognition")
                
        print("Image properties check complete!")
        
    except Exception as e:
        print(f"Error checking image properties: {e}")

if __name__ == "__main__":
    check_image_properties()
