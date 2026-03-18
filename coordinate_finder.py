#!/usr/bin/env python3
"""
Coordinate Finder - Help find the exact coordinates for capturing "11"
Takes a larger screenshot and lets you identify where the "11" is located
"""

import pyautogui
import cv2
import numpy as np
import time
import os

def find_coordinates_interactive():
    """
    Interactive coordinate finding for the "11" 
    """
    print("COORDINATE FINDER FOR '11'")
    print("=" * 40)
    print("This will help you find the exact coordinates of the '11' in Teams")
    print()
    
    print("Step 1: Make sure Teams is open with the calendar showing '11'")
    print("Step 2: Position your mouse over the '11' you want to capture")
    print("Step 3: Press ENTER when ready...")
    
    input("Press ENTER when mouse is positioned over the '11': ")
    
    # Get current mouse position
    mouse_x, mouse_y = pyautogui.position()
    print(f"Mouse position: ({mouse_x}, {mouse_y})")
    
    # Capture a larger area around the mouse position
    capture_size = 200  # 200x200 area around mouse
    start_x = mouse_x - capture_size // 2
    start_y = mouse_y - capture_size // 2
    
    print(f"Capturing {capture_size}x{capture_size} area around mouse...")
    
    time.sleep(0.5)  # Brief pause
    
    # Take screenshot
    screenshot = pyautogui.screenshot(region=(start_x, start_y, capture_size, capture_size))
    screenshot_array = np.array(screenshot)
    screenshot_bgr = cv2.cvtColor(screenshot_array, cv2.COLOR_RGB2BGR)
    
    # Save the large capture
    large_capture_file = "coordinate_finder_large.png"
    cv2.imwrite(large_capture_file, screenshot_bgr)
    print(f"Saved large capture: {large_capture_file}")
    
    # Now let's analyze this image to find text regions
    gray = cv2.cvtColor(screenshot_bgr, cv2.COLOR_BGR2GRAY)
    
    # Find text regions using thresholding
    _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)
    
    # Find contours (potential text regions)
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Filter contours by size (looking for text-sized regions)
    text_regions = []
    
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        area = w * h
        
        # Filter by size - text regions are usually 10-100 pixels in width/height
        if 10 <= w <= 100 and 10 <= h <= 50 and area >= 50:
            # Convert back to screen coordinates
            screen_x = start_x + x
            screen_y = start_y + y
            
            text_regions.append({
                'screen_x': screen_x,
                'screen_y': screen_y,
                'width': w,
                'height': h,
                'local_x': x,
                'local_y': y
            })
    
    # Draw rectangles around potential text regions
    debug_image = screenshot_bgr.copy()
    
    for i, region in enumerate(text_regions):
        x, y, w, h = region['local_x'], region['local_y'], region['width'], region['height']
        
        # Draw rectangle and label
        cv2.rectangle(debug_image, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.putText(debug_image, str(i), (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
    
    # Save debug image
    debug_file = "coordinate_finder_debug.png"
    cv2.imwrite(debug_file, debug_image)
    print(f"Saved debug image with regions marked: {debug_file}")
    
    # Show potential regions
    print(f"\nFound {len(text_regions)} potential text regions:")
    
    for i, region in enumerate(text_regions):
        print(f"  Region {i}: screen({region['screen_x']}, {region['screen_y']}) size {region['width']}x{region['height']}")
    
    if text_regions:
        print(f"\nTest these coordinates by capturing individual regions:")
        
        for i, region in enumerate(text_regions):
            # Capture this specific region
            test_screenshot = pyautogui.screenshot(region=(
                region['screen_x'], 
                region['screen_y'], 
                region['width'], 
                region['height']
            ))
            
            test_array = np.array(test_screenshot)
            test_bgr = cv2.cvtColor(test_array, cv2.COLOR_RGB2BGR)
            
            test_file = f"coordinate_test_region_{i}.png"
            cv2.imwrite(test_file, test_bgr)
            
            print(f"  Saved region {i}: {test_file}")
    
    print(f"\nNext steps:")
    print(f"1. Open coordinate_finder_debug.png to see marked regions")
    print(f"2. Check coordinate_test_region_*.png files")
    print(f"3. Identify which region contains the clearest '11'")
    print(f"4. Use those coordinates for enhanced capture")

def test_specific_coordinates():
    """
    Test OCR on specific coordinates you provide
    """
    print("\nTEST SPECIFIC COORDINATES")
    print("=" * 30)
    
    # You can manually input coordinates here after finding them
    test_coords = [
        # Add coordinates here in format: (x, y, width, height)
        # Example: (787, 200, 35, 35),
    ]
    
    if not test_coords:
        print("No coordinates specified. Use the interactive finder first.")
        return
    
    for i, (x, y, w, h) in enumerate(test_coords):
        print(f"\nTesting coordinates: ({x}, {y}) size {w}x{h}")
        
        # Capture
        screenshot = pyautogui.screenshot(region=(x, y, w, h))
        screenshot_array = np.array(screenshot)
        screenshot_bgr = cv2.cvtColor(screenshot_array, cv2.COLOR_RGB2BGR)
        screenshot_gray = cv2.cvtColor(screenshot_bgr, cv2.COLOR_BGR2GRAY)
        
        # Save
        test_file = f"coord_test_{i}.png"
        cv2.imwrite(test_file, screenshot_gray)
        
        # Test OCR
        try:
            text = pytesseract.image_to_string(screenshot_gray, config="--psm 8 -c tessedit_char_whitelist=0123456789").strip()
            digits = ''.join(c for c in text if c.isdigit())
            print(f"  OCR result: '{text}' -> '{digits}'")
            
            if digits == "11":
                print(f"  ✓ SUCCESS! Use coordinates ({x}, {y}, {w}, {h})")
            
        except Exception as e:
            print(f"  ✗ OCR failed: {e}")

if __name__ == "__main__":
    find_coordinates_interactive()
    test_specific_coordinates()