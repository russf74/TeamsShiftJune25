import pyautogui
import time
from PIL import Image, ImageDraw

print("Testing PNG detection with visual boxes...")

def find_and_mark_matches(image_name, description, color='yellow', confidence=0.8):
    print(f"\nLooking for {description} ({image_name}) with confidence {confidence}...")
    
    # Take screenshot
    screenshot = pyautogui.screenshot()
    draw = ImageDraw.Draw(screenshot)
    
    matches_found = 0
    
    try:
        # Find all matches
        matches = list(pyautogui.locateAllOnScreen(image_name, confidence=confidence))
        matches_found = len(matches)
        
        print(f"Found {matches_found} matches for {description}")
        
        # Draw boxes around each match
        for i, match in enumerate(matches):
            # Draw yellow box
            left, top, width, height = match.left, match.top, match.width, match.height
            right = left + width
            bottom = top + height
            
            # Draw rectangle outline
            draw.rectangle([left, top, right, bottom], outline=color, width=3)
            
            # Calculate center
            center_x = left + width // 2
            center_y = top + height // 2
            
            # Draw a small circle at center
            circle_size = 5
            draw.ellipse([center_x - circle_size, center_y - circle_size, 
                         center_x + circle_size, center_y + circle_size], 
                        fill=color, outline='red')
            
            print(f"  Match {i+1}: Box({left}, {top}, {width}, {height}) -> Center({center_x}, {center_y})")
        
        # Save the marked screenshot
        filename = f'debug_{image_name.replace(".png", "")}_marked.png'
        screenshot.save(filename)
        print(f"Saved marked screenshot as {filename}")
        
        # Also try to find the best single match
        try:
            single_match = pyautogui.locateCenterOnScreen(image_name, confidence=confidence)
            if single_match:
                print(f"Single match center: {single_match}")
                
                # Draw a red X at the single match location
                x, y = single_match.x, single_match.y
                size = 10
                draw.line([x-size, y-size, x+size, y+size], fill='red', width=3)
                draw.line([x-size, y+size, x+size, y-size], fill='red', width=3)
                
                # Save with X marked
                filename_x = f'debug_{image_name.replace(".png", "")}_single_marked.png'
                screenshot.save(filename_x)
                print(f"Saved single match screenshot as {filename_x}")
        except:
            print("No single match found")
            
        return matches_found > 0
        
    except pyautogui.ImageNotFoundException:
        print(f"{description} not found (ImageNotFoundException)")
        # Still save the unmarked screenshot for reference
        filename = f'debug_{image_name.replace(".png", "")}_not_found.png'
        screenshot.save(filename)
        return False
    except Exception as e:
        print(f"Error with {description}: {e}")
        return False

def test_full_sequence():
    print("=== Testing Full Reset Sequence with Visual Debugging ===")
    
    # Step 1: Test Calendar
    print("\n1. Testing calendar.png...")
    if find_and_mark_matches('calendar.png', 'Calendar button', 'green', confidence=0.8):
        
        # Step 2: Test Dots
        print("\n2. Testing dots.png...")
        if find_and_mark_matches('dots.png', 'Dots button', 'blue', confidence=0.8):
            
            # Step 3: Test Shifts with higher confidence
            print("\n3. Testing shifts.png...")
            find_and_mark_matches('shifts.png', 'Shifts button', 'yellow', confidence=0.9)
            
            # Step 4: Test Shift Loaded
            print("\n4. Testing shiftloaded.png...")
            find_and_mark_matches('shiftloaded.png', 'Shift Loaded indicator', 'purple', confidence=0.8)
        else:
            print("Skipping shifts test since dots not found")
    else:
        print("Skipping remaining tests since calendar not found")

# Run the test
test_full_sequence()

print("\n=== Test Complete ===")
print("Check the generated debug_*_marked.png files to see where matches were found.")
print("Yellow boxes = shifts.png matches")
print("Green boxes = calendar.png matches") 
print("Blue boxes = dots.png matches")
print("Purple boxes = shiftloaded.png matches")
print("Red X = single best match location where click would occur")
