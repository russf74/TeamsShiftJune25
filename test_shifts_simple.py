import pyautogui
import time

print("Testing simple shifts.png matching...")
try:
    # Use the same approach as calendar.png and dots.png
    result = pyautogui.locateCenterOnScreen('shifts.png', confidence=0.8)
    if result:
        print(f"Found shifts.png at: {result}")
    else:
        print("shifts.png not found")
except pyautogui.ImageNotFoundException:
    print("shifts.png not found (ImageNotFoundException)")
except Exception as e:
    print(f"Error: {e}")

print("Test complete!")
