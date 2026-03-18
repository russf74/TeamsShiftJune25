#!/usr/bin/env python3
"""
Image Examination Tool - Look at the actual pixels in the image
"""

import cv2
import numpy as np
import os

def examine_image(image_path):
    """Examine the actual image content"""
    print(f"Examining: {os.path.basename(image_path)}")
    
    if not os.path.exists(image_path):
        print(f"ERROR: File not found: {image_path}")
        return
    
    # Load image
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        print("ERROR: Could not load image")
        return
    
    height, width = img.shape
    print(f"Image dimensions: {width} x {height}")
    
    # Show pixel values as ASCII art
    print(f"\nPixel values (0=black, 255=white):")
    print("=" * width)
    
    for y in range(height):
        row = ""
        for x in range(width):
            pixel = img[y, x]
            if pixel < 50:
                row += "#"  # Very dark
            elif pixel < 100:
                row += "*"  # Dark
            elif pixel < 200:
                row += "."  # Light
            else:
                row += " "  # Very light/white
        print(row)
    
    print("=" * width)
    
    # Show unique pixel values
    unique_vals = sorted(np.unique(img))
    print(f"Unique pixel values: {unique_vals}")
    
    # Find dark pixels (likely text)
    dark_pixels = np.where(img < 128)
    dark_count = len(dark_pixels[0])
    total_pixels = width * height
    
    print(f"Dark pixels (text): {dark_count}/{total_pixels} ({dark_count/total_pixels*100:.1f}%)")
    
    if dark_count > 0:
        print(f"Dark pixel coordinates:")
        for i in range(min(10, dark_count)):  # Show first 10 dark pixels
            y, x = dark_pixels[0][i], dark_pixels[1][i]
            print(f"  ({x}, {y}): value {img[y, x]}")
    
    # Try to identify the pattern
    print(f"\nPattern analysis:")
    
    # Check vertical lines (like in "1" or "|")
    vertical_lines = 0
    for x in range(width):
        column = img[:, x]
        if np.any(column < 128):  # Has dark pixels
            vertical_lines += 1
    
    print(f"Columns with dark pixels: {vertical_lines}")
    
    # Check horizontal segments 
    horizontal_segments = 0
    for y in range(height):
        row = img[y, :]
        if np.any(row < 128):  # Has dark pixels
            horizontal_segments += 1
    
    print(f"Rows with dark pixels: {horizontal_segments}")

def main():
    """Examine the X787 image that should show '11'"""
    image_path = "screenshots/0-shifts_screenshot_20251001_181548_ocr_region_X787.png"
    examine_image(image_path)

if __name__ == "__main__":
    main()