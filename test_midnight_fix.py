#!/usr/bin/env python3
"""
Quick test to verify the midnight reset fix is working
"""

import pyautogui
import os

print("="*70)
print("MIDNIGHT RESET FIX VERIFICATION")
print("="*70)
print()

# Check if shiftloaded.png exists
if not os.path.exists('shiftloaded.png'):
    print("? ERROR: shiftloaded.png not found!")
    print("   The midnight reset needs this file to work.")
    exit(1)

print("? shiftloaded.png exists")
print()

print("INSTRUCTIONS:")
print("1. Open Teams and navigate to Calendar > Shifts")
print("2. Wait for the page to fully load")
print("3. Press ENTER when ready")
print()

input("Press ENTER when Teams Shifts page is loaded...")

print()
print("Testing detection with NEW threshold (0.7)...")
print()

try:
    # Test with the NEW confidence level (0.7)
    result = pyautogui.locateOnScreen('shiftloaded.png', confidence=0.7)
    
    if result:
        print("? SUCCESS! Detection works at confidence 0.7")
        print(f"   Found at: {result}")
        print()
        print("?? THE FIX IS WORKING!")
        print()
        print("The midnight reset should now work correctly.")
        print("It will be able to detect when Teams finishes loading.")
    else:
        print("? WARNING: No match found at confidence 0.7")
        print()
        print("This might mean:")
        print("- Teams hasn't fully loaded yet")
        print("- The shiftloaded.png image needs to be recaptured")
        print()
        print("Try running diagnose_shiftloaded.py for more details.")
 
except Exception as e:
    print(f"? ERROR: {e}")
    print()
    print("Detection failed. Run diagnose_shiftloaded.py for details.")

print()
print("="*70)
print("Next step: Click 'Test Shift App Reset' button in the app")
print("="*70)
