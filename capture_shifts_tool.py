#!/usr/bin/env python3
"""
Interactive tool to help capture a better shifts.png image
Run this and follow the instructions to capture a proper Shifts button image.
"""

import pyautogui
import time
import tkinter as tk
from tkinter import messagebox
import os

def capture_shifts_image():
    print("=" * 60)
    print("SHIFTS.PNG CAPTURE TOOL")
    print("=" * 60)
    print()
    print("Current shifts.png is too small (27x27 pixels) and matches everywhere!")
    print("We need to capture a better, larger image.")
    print()
    print("INSTRUCTIONS:")
    print("1. Go to Microsoft Teams")
    print("2. Navigate to where you can see the 'Shifts' button/tab")
    print("3. Make sure the Shifts button is clearly visible")
    print("4. Come back to this window and press ENTER")
    print()
    
    input("Press ENTER when Teams is ready and Shifts button is visible...")
    
    print()
    print("In 5 seconds, your mouse cursor will become a crosshair.")
    print("Use it to draw a rectangle around the Shifts button.")
    print("Make sure to include:")
    print("- The word 'Shifts'")
    print("- Some surrounding context")
    print("- Make it at least 80x30 pixels")
    print()
    
    for i in range(5, 0, -1):
        print(f"Starting in {i}...")
        time.sleep(1)
    
    print("NOW! Click and drag to select the Shifts button area...")
    
    try:
        # Let user select region
        print("Move your mouse to the TOP-LEFT of the Shifts button and click...")
        
        # Get the region from user
        region = pyautogui.screenshot()
        
        # Save current screenshot for reference
        region.save('debug_full_screen_for_shifts.png')
        print("Full screen saved as debug_full_screen_for_shifts.png")
        
        # Ask user to manually specify coordinates
        print()
        print("Please open debug_full_screen_for_shifts.png and find the Shifts button.")
        print("Then note down the coordinates and size.")
        print()
        print("Example: If Shifts button is at position (100, 200) and is 120x40 pixels:")
        print("Enter: 100,200,120,40")
        print()
        
        coords_input = input("Enter coordinates as: left,top,width,height: ").strip()
        
        if coords_input:
            try:
                left, top, width, height = map(int, coords_input.split(','))
                
                if width < 50 or height < 20:
                    print("WARNING: Image might be too small!")
                    print(f"You specified: {width}x{height} pixels")
                    proceed = input("Continue anyway? (y/n): ")
                    if proceed.lower() != 'y':
                        return
                
                # Capture the specified region
                shifts_region = pyautogui.screenshot(region=(left, top, width, height))
                
                # Save as new shifts.png
                backup_name = f"shifts_old_{int(time.time())}.png"
                if os.path.exists('shifts.png'):
                    os.rename('shifts.png', backup_name)
                    print(f"Old shifts.png backed up as {backup_name}")
                
                shifts_region.save('shifts.png')
                print(f"New shifts.png saved! Size: {width}x{height} pixels")
                
                # Test the new image
                print()
                print("Testing new image...")
                time.sleep(2)
                
                try:
                    matches = list(pyautogui.locateAllOnScreen('shifts.png', confidence=0.8))
                    print(f"Found {len(matches)} matches with new image")
                    
                    if len(matches) == 0:
                        print("WARNING: No matches found! Image might be too specific or confidence too high.")
                    elif len(matches) > 10:
                        print("WARNING: Too many matches! Image might still be too generic.")
                    else:
                        print("GOOD: Found reasonable number of matches!")
                        for i, match in enumerate(matches):
                            center = pyautogui.center(match)
                            print(f"  Match {i+1}: {match} -> Center: {center}")
                
                except Exception as e:
                    print(f"Error testing image: {e}")
                
            except ValueError:
                print("Invalid format! Please use: left,top,width,height")
        
    except KeyboardInterrupt:
        print("\nCancelled by user")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    capture_shifts_image()
