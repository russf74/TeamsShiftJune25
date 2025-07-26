import pyautogui
import time

print("Testing shifts.png detection and click coordinates...")

# Take a screenshot first
screenshot = pyautogui.screenshot()
screenshot.save('debug_before_shifts_test.png')
print("Saved current screen as debug_before_shifts_test.png")

try:
    # Find the shifts button
    result = pyautogui.locateCenterOnScreen('shifts.png', confidence=0.8)
    if result:
        print(f"Found shifts.png at center coordinates: {result}")
        
        # Also get the full region
        region = pyautogui.locateOnScreen('shifts.png', confidence=0.8)
        if region:
            print(f"Full region: left={region.left}, top={region.top}, width={region.width}, height={region.height}")
            print(f"Region center calculated: x={region.left + region.width//2}, y={region.top + region.height//2}")
        
        # Show mouse position before clicking
        current_mouse = pyautogui.position()
        print(f"Current mouse position: {current_mouse}")
        
        # Move mouse to the location (but don't click yet)
        pyautogui.moveTo(result.x, result.y)
        print(f"Moved mouse to: {result}")
        
        # Wait a moment so you can see where it moved
        print("Mouse moved to target location. Check if it's in the right place.")
        print("Press Ctrl+C to cancel or wait 5 seconds for auto-click...")
        time.sleep(5)
        
        # Click
        pyautogui.click(result.x, result.y)
        print(f"Clicked at: {result}")
        
    else:
        print("shifts.png not found")
        
except pyautogui.ImageNotFoundException:
    print("shifts.png not found (ImageNotFoundException)")
except Exception as e:
    print(f"Error: {e}")

print("Test complete!")
