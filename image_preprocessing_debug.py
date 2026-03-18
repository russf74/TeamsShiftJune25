#!/usr/bin/env python3
"""
Image Preprocessing Debug Tool
Test various image preprocessing techniques on the failing OCR regions.
"""

import cv2
import pytesseract
import numpy as np

def preprocess_and_test(img_path, expected_number):
    """Test various preprocessing techniques on a single image"""
    
    print(f"\n{'='*60}")
    print(f"Testing: {img_path}")
    print(f"Expected: {expected_number}")
    print(f"{'='*60}")
    
    # Load original image
    original = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
    if original is None:
        print(f"Could not load {img_path}")
        return
    
    # Test different preprocessing techniques
    techniques = [
        ("Original", original),
        ("Inverted", 255 - original),
        ("Threshold Binary", cv2.threshold(original, 127, 255, cv2.THRESH_BINARY)[1]),
        ("Threshold Otsu", cv2.threshold(original, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]),
        ("Adaptive Thresh", cv2.adaptiveThreshold(original, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)),
        ("Morphology Close", cv2.morphologyEx(original, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (3,3)))),
        ("Gaussian Blur", cv2.GaussianBlur(original, (3,3), 0)),
        ("Scale 3x", cv2.resize(original, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)),
        ("Scale 4x", cv2.resize(original, None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC)),
    ]
    
    # Test each preprocessing with best OCR configs
    ocr_configs = [
        ("PSM 8 digits", "--psm 8 -c tessedit_char_whitelist=0123456789"),
        ("PSM 6 digits", "--psm 6 -c tessedit_char_whitelist=0123456789"),
        ("PSM 10 digits", "--psm 10 -c tessedit_char_whitelist=0123456789"),
    ]
    
    best_results = []
    
    for technique_name, processed_img in techniques:
        print(f"\n--- {technique_name} ---")
        
        for config_name, config in ocr_configs:
            try:
                result = pytesseract.image_to_string(processed_img, config=config).strip()
                digits = ''.join(c for c in result if c.isdigit())
                
                # Check if we got the right answer
                is_correct = digits == expected_number
                status = "✅ CORRECT!" if is_correct else "❌"
                
                print(f"  {config_name:15} -> '{result}' (digits: '{digits}') {status}")
                
                if is_correct:
                    best_results.append((technique_name, config_name, result))
                    
            except Exception as e:
                print(f"  {config_name:15} -> ERROR: {e}")
    
    # Summary of successful techniques
    if best_results:
        print(f"\n🎉 SUCCESSFUL TECHNIQUES for {expected_number}:")
        for technique, config, result in best_results:
            print(f"  - {technique} + {config} -> '{result}'")
    else:
        print(f"\n😞 No techniques successfully read '{expected_number}'")
    
    return best_results

def main():
    """Test the two failing OCR regions"""
    
    # Test the specific failing files
    files_to_test = [
        ("screenshots/0-shifts_screenshot_20251001_181548_ocr_region_X895.png", "11"),
        ("screenshots/0-shifts_screenshot_20251001_181548_ocr_region_X787.png", "13"),
    ]
    
    all_successful_techniques = []
    
    for file_path, expected in files_to_test:
        results = preprocess_and_test(file_path, expected)
        all_successful_techniques.extend(results)
    
    # Final summary
    print(f"\n{'='*60}")
    print("FINAL SUMMARY")
    print(f"{'='*60}")
    
    if all_successful_techniques:
        print("✅ Found working techniques:")
        for technique, config, result in all_successful_techniques:
            print(f"  - {technique} + {config}")
    else:
        print("❌ No preprocessing techniques worked for both numbers")
    
    print("\nNext steps:")
    print("1. If techniques found: Apply best one to main OCR processing")
    print("2. If no techniques work: Consider template matching approach")

if __name__ == "__main__":
    main()