#!/usr/bin/env python3
"""
Screenshot Quality Test - Test different capture methods without changing main app
"""

import pyautogui
import cv2
import numpy as np
import time
from PIL import ImageGrab
import pytesseract

def test_screenshot_methods():
    """Compare pyautogui vs PIL.ImageGrab for the same region"""
    
    print("SCREENSHOT QUALITY TEST")
    print("=" * 30)
    
    # Test both failing coordinates from main app
    # Y adjusted: 65 + 80 = 145
    test_regions = [
        (787, 145, 35, 35, "11"),  # X787 should show "11" 
        (895, 145, 35, 35, "13"),  # X895 should show "13"
    ]
    
    print("Make sure Teams is visible with both '11' and '13' showing...")
    
    all_results = []
    
    for i, (test_x, test_y, test_w, test_h, expected) in enumerate(test_regions):
        print(f"\n--- Testing region {i+1}: ({test_x}, {test_y}) expecting '{expected}' ---")
    
        # Method 1: Current pyautogui method (like main app)
        print("1. Testing pyautogui (current method):")
        screenshot1 = pyautogui.screenshot(region=(test_x, test_y, test_w, test_h))
        img1 = np.array(screenshot1)
        img1_bgr = cv2.cvtColor(img1, cv2.COLOR_RGB2BGR)
        cv2.imwrite(f"test_pyautogui_X{test_x}.png", img1_bgr)
        
        # Test OCR
        gray1 = cv2.cvtColor(img1_bgr, cv2.COLOR_BGR2GRAY)
        text1 = pytesseract.image_to_string(gray1, config="--psm 8 -c tessedit_char_whitelist=0123456789").strip()
        digits1 = ''.join(c for c in text1 if c.isdigit())
        success1 = digits1 == expected
        print(f"   Result: '{text1}' -> '{digits1}' {'✓' if success1 else '✗'}")
        
        # Method 2: PIL ImageGrab
        print("2. Testing PIL.ImageGrab:")
        screenshot2 = ImageGrab.grab(bbox=(test_x, test_y, test_x + test_w, test_y + test_h))
        img2 = np.array(screenshot2)
        img2_bgr = cv2.cvtColor(img2, cv2.COLOR_RGB2BGR)
        cv2.imwrite(f"test_pil_X{test_x}.png", img2_bgr)
        
        # Test OCR  
        gray2 = cv2.cvtColor(img2_bgr, cv2.COLOR_BGR2GRAY)
        text2 = pytesseract.image_to_string(gray2, config="--psm 8 -c tessedit_char_whitelist=0123456789").strip()
        digits2 = ''.join(c for c in text2 if c.isdigit())
        success2 = digits2 == expected
        print(f"   Result: '{text2}' -> '{digits2}' {'✓' if success2 else '✗'}")
        
        # Method 3: PIL with sharpening
        print("3. Testing PIL with sharpening:")
        from PIL import ImageEnhance
        screenshot3 = ImageGrab.grab(bbox=(test_x, test_y, test_x + test_w, test_y + test_h))
        
        # Sharpen the image
        enhancer = ImageEnhance.Sharpness(screenshot3)
        sharpened = enhancer.enhance(2.0)
        
        img3 = np.array(sharpened)
        img3_bgr = cv2.cvtColor(img3, cv2.COLOR_RGB2BGR)
        cv2.imwrite(f"test_pil_sharp_X{test_x}.png", img3_bgr)
        
        # Test OCR
        gray3 = cv2.cvtColor(img3_bgr, cv2.COLOR_BGR2GRAY)
        text3 = pytesseract.image_to_string(gray3, config="--psm 8 -c tessedit_char_whitelist=0123456789").strip()
        digits3 = ''.join(c for c in text3 if c.isdigit())
        success3 = digits3 == expected
        print(f"   Result: '{text3}' -> '{digits3}' {'✓' if success3 else '✗'}")
        
        region_results = {
            'expected': expected,
            'pyautogui': (digits1, success1),
            'pil': (digits2, success2), 
            'pil_sharp': (digits3, success3)
        }
        all_results.append(region_results)
    
    # Final summary
    print(f"\n" + "=" * 50)
    print("FINAL SUMMARY")
    print("=" * 50)
    
    for i, results in enumerate(all_results):
        expected = results['expected']
        print(f"Region {i+1} (expecting '{expected}'):")
        for method, (result, success) in [(k, v) for k, v in results.items() if k != 'expected']:
            print(f"  {method:12s}: '{result}' {'✓' if success else '✗'}")
        print()
    
    # Overall success rates
    methods = ['pyautogui', 'pil', 'pil_sharp']
    for method in methods:
        successes = sum(1 for r in all_results if r[method][1])
        total = len(all_results)
        print(f"{method:12s}: {successes}/{total} successful ({successes/total*100:.1f}%)")
    
    print(f"\nSaved test images for visual inspection.")

if __name__ == "__main__":
    test_screenshot_methods()