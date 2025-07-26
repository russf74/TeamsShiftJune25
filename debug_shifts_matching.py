import pyautogui
import cv2
import numpy as np
from PIL import Image

def test_shifts_matching():
    print("Testing shifts.png matching...")
    
    # Check the shifts.png image properties
    try:
        shifts_img = cv2.imread('shifts.png')
        if shifts_img is None:
            print("ERROR: Could not load shifts.png")
            return
        
        height, width = shifts_img.shape[:2]
        print(f"shifts.png dimensions: {width}x{height}")
        
        # Test with different confidence levels
        for confidence in [0.95, 0.9, 0.85, 0.8]:
            try:
                matches = list(pyautogui.locateAllOnScreen('shifts.png', confidence=confidence))
                print(f"Confidence {confidence}: Found {len(matches)} matches")
                
                if len(matches) <= 10:
                    print(f"  Sample matches at confidence {confidence}:")
                    for i, match in enumerate(matches[:5]):  # Show first 5
                        center = pyautogui.center(match)
                        print(f"    Match {i+1}: {match} -> Center: {center}")
                    
                    # If we have reasonable matches, try to click the leftmost one
                    if 1 <= len(matches) <= 10:
                        leftmost = min(matches, key=lambda m: pyautogui.center(m).x)
                        center = pyautogui.center(leftmost)
                        print(f"  Would click leftmost match at: {center}")
                        return center
                        
            except Exception as e:
                print(f"  Error at confidence {confidence}: {e}")
    
    except Exception as e:
        print(f"ERROR: {e}")
    
    # Test alternative approach - just use locateCenterOnScreen like other buttons
    print("\nTesting simple locateCenterOnScreen approach...")
    for confidence in [0.95, 0.9, 0.85, 0.8]:
        try:
            center = pyautogui.locateCenterOnScreen('shifts.png', confidence=confidence)
            if center:
                print(f"locateCenterOnScreen with confidence {confidence}: Found at {center}")
                return center
        except Exception as e:
            print(f"locateCenterOnScreen with confidence {confidence}: {e}")
    
    print("No matches found with any method")
    return None

if __name__ == "__main__":
    test_shifts_matching()
