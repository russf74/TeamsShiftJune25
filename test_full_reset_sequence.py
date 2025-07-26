import pyautogui
import time

print("Testing full Teams reset sequence...")

def find_and_click(image_name, description, wait_time=2):
    print(f"\nLooking for {description} ({image_name})...")
    try:
        # Take screenshot for debugging
        screenshot = pyautogui.screenshot()
        screenshot.save(f'debug_{image_name.replace(".png", "")}_search.png')
        
        result = pyautogui.locateCenterOnScreen(image_name, confidence=0.8)
        if result:
            print(f"Found {description} at: {result}")
            pyautogui.click(result)
            print(f"Clicked {description}")
            time.sleep(wait_time)
            return True
        else:
            print(f"{description} not found")
            return False
    except pyautogui.ImageNotFoundException:
        print(f"{description} not found (ImageNotFoundException)")
        return False
    except Exception as e:
        print(f"Error with {description}: {e}")
        return False

# Step 1: Try to find and click Calendar
if find_and_click('calendar.png', 'Calendar button', 10):
    
    # Step 2: Try to find and click Dots
    if find_and_click('dots.png', 'Dots button', 2):
        
        # Step 3: Try to find and click Shifts
        # Take a detailed screenshot before looking for shifts
        screenshot = pyautogui.screenshot()
        screenshot.save('debug_full_screen_before_shifts.png')
        print("Saved full screen before shifts search")
        
        if find_and_click('shifts.png', 'Shifts button', 10):
            print("✓ Successfully completed full reset sequence!")
            
            # Check if shifts loaded
            time.sleep(2)
            try:
                loaded = pyautogui.locateOnScreen('shiftloaded.png', confidence=0.8)
                if loaded:
                    print("✓ Shifts app appears to have loaded successfully!")
                else:
                    print("⚠ Shifts app may not have loaded (shiftloaded.png not found)")
            except:
                print("⚠ Could not verify if shifts loaded")
        else:
            print("✗ Failed to find Shifts button")
    else:
        print("✗ Failed to find Dots button")
else:
    print("✗ Failed to find Calendar button")

print("\nTest complete! Check the debug screenshots to see what was found.")
