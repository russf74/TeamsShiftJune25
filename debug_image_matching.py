#!/usr/bin/env python3
"""
Debug script to test pyautogui image matching for shifts.png
Run this script to see if pyautogui can find the shifts.png on your current screen.
"""

import pyautogui
import time
import os

def test_image_matching():
    print("Testing image matching for shifts.png...")
    
    # Check if shifts.png exists
    if not os.path.exists('shifts.png'):
        print("ERROR: shifts.png not found in current directory!")
        return
    
    print("Taking screenshot...")
    screenshot = pyautogui.screenshot()
    screenshot.save('debug_current_screen.png')
    print("Screenshot saved as debug_current_screen.png")
    
    # Test different confidence levels
    confidence_levels = [0.9, 0.8, 0.7, 0.6, 0.5]
    
    for conf in confidence_levels:
        print(f"\nTesting confidence level: {conf}")
        try:
            # Try to find all matches
            matches = list(pyautogui.locateAllOnScreen('shifts.png', confidence=conf))
            if matches:
                print(f"  Found {len(matches)} matches:")
                for i, match in enumerate(matches):
                    print(f"    Match {i+1}: {match}")
                    center = pyautogui.center(match)
                    print(f"    Center: {center}")
            else:
                print(f"  No matches found at confidence {conf}")
        except Exception as e:
            print(f"  Error at confidence {conf}: {e}")
    
    # Try grayscale
    print(f"\nTesting grayscale matching...")
    try:
        matches = list(pyautogui.locateAllOnScreen('shifts.png', confidence=0.6, grayscale=True))
        if matches:
            print(f"  Found {len(matches)} grayscale matches:")
            for i, match in enumerate(matches):
                print(f"    Match {i+1}: {match}")
        else:
            print("  No grayscale matches found")
    except Exception as e:
        print(f"  Grayscale error: {e}")
    
    print("\nImage matching test complete!")
    print("Compare debug_current_screen.png with shifts.png to see if they match visually.")

if __name__ == "__main__":
    print("You have 5 seconds to get your Teams window ready...")
    time.sleep(5)
    test_image_matching()
