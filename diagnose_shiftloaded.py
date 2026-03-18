#!/usr/bin/env python3
"""
Diagnostic tool for shiftloaded.png detection
This will help us understand why the midnight reset isn't detecting that shifts have loaded.
"""

import pyautogui
import time
import os
import cv2

def diagnose_shiftloaded_detection():
    print("="*70)
    print("SHIFTLOADED.PNG DETECTION DIAGNOSTIC")
    print("="*70)
    print()
    
    # Check if shiftloaded.png exists
    if not os.path.exists('shiftloaded.png'):
        print("? ERROR: shiftloaded.png not found in current directory!")
        print("   The midnight reset needs this file to detect when Teams has finished loading.")
        return
    
    print("? shiftloaded.png file exists")
    
    # Check image properties
    img = cv2.imread('shiftloaded.png')
    if img is not None:
        height, width = img.shape[:2]
        print(f"? Image dimensions: {width}x{height} pixels")
        
        if width < 30 or height < 30:
            print(f"??  WARNING: Image is very small ({width}x{height})")
            print("   Small images may not match reliably")
        elif width > 200 or height > 200:
            print(f"??  WARNING: Image is quite large ({width}x{height})")
            print("   Large images may be too specific")
    else:
        print("? ERROR: Could not load shiftloaded.png image")
        return
    
    print()
    print("INSTRUCTIONS:")
    print("1. Open Microsoft Teams")
    print("2. Navigate to Calendar > Shifts (as the midnight reset would)")
    print("3. Wait for the shifts page to FULLY load")
    print("4. Come back here and press ENTER")
    print()
    
    input("Press ENTER when Teams Shifts page is fully loaded...")
    
    print()
    print("Capturing current screen...")
    screenshot = pyautogui.screenshot()
    screenshot.save('debug_shiftloaded_screen.png')
    print("? Screenshot saved as debug_shiftloaded_screen.png")
    
    print()
    print("Testing detection at different confidence levels...")
    print()
    
    confidence_levels = [0.9, 0.8, 0.7, 0.6, 0.5]
    found_at_any_level = False
    best_confidence = None
    
    for conf in confidence_levels:
        try:
            matches = list(pyautogui.locateAllOnScreen('shiftloaded.png', confidence=conf))
            if matches:
                found_at_any_level = True
                if best_confidence is None:
                    best_confidence = conf
                print(f"? Confidence {conf}: Found {len(matches)} matches")
                for i, match in enumerate(matches[:3]):  # Show first 3
                    center = pyautogui.center(match)
                    print(f"   Match {i+1}: {match} -> Center: {center}")
            else:
                print(f"? Confidence {conf}: No matches found")
        except pyautogui.ImageNotFoundException:
            print(f"? Confidence {conf}: No matches found (ImageNotFoundException)")
        except Exception as e:
            print(f"? Confidence {conf}: Error - {e}")
    
    print()
    print("="*70)
    print("DIAGNOSIS")
    print("="*70)
    
    if not found_at_any_level:
        print()
        print("?? PROBLEM IDENTIFIED:")
        print("   shiftloaded.png was NOT found on the current screen at ANY confidence level!")
        print()
        print("This means:")
        print("  1. The image doesn't match what's actually on screen")
        print("  2. The image might be from an old version of Teams")
        print("  3. The image might be capturing the wrong indicator")
        print()
        print("SOLUTION:")
        print("  You need to capture a fresh shiftloaded.png image that shows")
        print("  a distinctive element that appears ONLY when shifts are fully loaded.")
        print()
        print("  Good indicators to capture:")
        print("  - A specific button that only appears when loaded")
        print("  - A unique label or heading")
        print("  - The 'Open shifts' or 'Booked shifts' header")
        print()
        print("  How to capture:")
        print("  1. Open Teams and wait for Shifts to fully load")
        print("  2. Use Windows Snipping Tool (Win+Shift+S)")
        print("  3. Capture a small region (80x40 pixels) of a UNIQUE element")
        print("  4. Save as shiftloaded.png in this directory")
        print()
    else:
        print()
        print("? DETECTION WORKING:")
        print("   shiftloaded.png was found on screen!")
        print()
        print("   However, the midnight reset uses confidence=0.8")
        if best_confidence and best_confidence > 0.8:
            print(f"   ??  But it only works at confidence={best_confidence} or higher")
            print()
            print("   SOLUTION: Lower the confidence in gui.py")
            print(f"   Change: loaded_img = pyautogui.locateOnScreen('shiftloaded.png', confidence=0.8)")
            print(f"   To:     loaded_img = pyautogui.locateOnScreen('shiftloaded.png', confidence={best_confidence})")
        else:
            print("   ? Works at confidence 0.8 (current setting)")
            print()
            print("   The detection logic seems OK. Check if:")
            print("   1. Teams might not be finishing its load within 10 seconds")
            print("   2. The retry logic is working correctly")
    
    print()
    print("="*70)
    print("NEXT STEPS")
    print("="*70)
    print()
    print("1. Compare debug_shiftloaded_screen.png with shiftloaded.png")
    print("   - Open both images side by side")
    print("   - Check if shiftloaded.png appears in the screenshot")
    print("   - Check if it looks exactly the same")
    print()
    print("2. If shiftloaded.png doesn't match:")
    print("   - Capture a fresh image of a loaded indicator")
    print("   - Make sure it's UNIQUE to the loaded state")
    print()
    print("3. If it does match but detection failed:")
    print("   - Consider lowering confidence threshold")
    print("   - Or wait longer for Teams to stabilize")
    print()

if __name__ == "__main__":
    diagnose_shiftloaded_detection()
