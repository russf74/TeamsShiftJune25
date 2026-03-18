#!/usr/bin/env python3
"""
Basic OCR Test - No emojis, just test the images
"""

import cv2
import pytesseract
import os

def test_image(image_path, expected):
    """Test OCR on a single image"""
    print(f"\n=== Testing: {os.path.basename(image_path)} (expecting '{expected}') ===")
    
    if not os.path.exists(image_path):
        print(f"ERROR: File not found: {image_path}")
        return False
    
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        print("ERROR: Could not load image")
        return False
    
    print(f"Image size: {img.shape[1]}x{img.shape[0]}")
    
    # Test different OCR methods
    configs = [
        ("PSM6", "--psm 6 -c tessedit_char_whitelist=0123456789"),
        ("PSM8", "--psm 8 -c tessedit_char_whitelist=0123456789"),
        ("PSM7", "--psm 7 -c tessedit_char_whitelist=0123456789"),
    ]
    
    for name, config in configs:
        try:
            text = pytesseract.image_to_string(img, config=config).strip()
            digits = ''.join(c for c in text if c.isdigit())
            print(f"  {name}: '{text}' -> '{digits}'")
            
            if digits == expected:
                print(f"  SUCCESS: {name} got correct result '{expected}'")
                return True
                
        except Exception as e:
            print(f"  {name}: ERROR - {e}")
    
    print(f"  FAILED: Expected '{expected}' but no method succeeded")
    return False

def main():
    # Test the problem images
    test_cases = [
        ("screenshots/0-shifts_screenshot_20251001_181548_ocr_region_X895.png", "13"),
        ("screenshots/0-shifts_screenshot_20251001_181548_ocr_region_X787.png", "11"),
    ]
    
    print("BASIC OCR TEST")
    print("=" * 50)
    
    results = []
    for image_path, expected in test_cases:
        success = test_image(image_path, expected)
        results.append(success)
    
    successful = sum(results)
    total = len(results)
    
    print(f"\nSUMMARY: {successful}/{total} successful ({successful/total*100:.1f}%)")

if __name__ == "__main__":
    main()