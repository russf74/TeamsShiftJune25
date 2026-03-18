#!/usr/bin/env python3
"""
Focused OCR Test - Test different OCR configurations on the clear "11" and "13" images
"""

import cv2
import pytesseract
import numpy as np

def test_ocr_configurations():
    """Test multiple OCR configurations on the captured images"""
    
    print("FOCUSED OCR CONFIGURATION TEST")
    print("=" * 40)
    
    # Test the captured images
    test_files = [
        ("test_pyautogui_X787.png", "11"),
        ("test_pyautogui_X895.png", "13"),
    ]
    
    # Different OCR configurations to try
    ocr_configs = [
        ("PSM 6", "--psm 6 -c tessedit_char_whitelist=0123456789"),
        ("PSM 7", "--psm 7 -c tessedit_char_whitelist=0123456789"), 
        ("PSM 8", "--psm 8 -c tessedit_char_whitelist=0123456789"),
        ("PSM 10", "--psm 10 -c tessedit_char_whitelist=0123456789"),
        ("PSM 13", "--psm 13 -c tessedit_char_whitelist=0123456789"),
        ("PSM 6 no whitelist", "--psm 6"),
        ("PSM 8 no whitelist", "--psm 8"),
    ]
    
    for image_file, expected in test_files:
        print(f"\n--- Testing {image_file} (expecting '{expected}') ---")
        
        # Load image
        img = cv2.imread(image_file, cv2.IMREAD_GRAYSCALE)
        if img is None:
            print(f"  ERROR: Could not load {image_file}")
            continue
        
        print(f"  Image size: {img.shape[1]}x{img.shape[0]}")
        
        # Test each configuration
        for config_name, config in ocr_configs:
            try:
                text = pytesseract.image_to_string(img, config=config).strip()
                digits = ''.join(c for c in text if c.isdigit())
                
                # Get confidence if possible
                try:
                    data = pytesseract.image_to_data(img, config=config, output_type=pytesseract.Output.DICT)
                    confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
                    avg_confidence = sum(confidences) / len(confidences) if confidences else 0
                except:
                    avg_confidence = 0
                
                success = digits == expected
                status = "✓" if success else "✗"
                
                print(f"    {config_name:20s}: '{text}' -> '{digits}' (conf: {avg_confidence:.1f}) {status}")
                
            except Exception as e:
                print(f"    {config_name:20s}: ERROR - {e}")
        
        # Test with preprocessing
        print(f"  \n  Testing with preprocessing:")
        
        # Try scaling up
        scaled_2x = cv2.resize(img, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        scaled_3x = cv2.resize(img, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
        
        # Try different thresholds
        _, thresh_otsu = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        _, thresh_100 = cv2.threshold(img, 100, 255, cv2.THRESH_BINARY)
        
        preprocessed_images = [
            ("2x scaled", scaled_2x),
            ("3x scaled", scaled_3x),
            ("Otsu thresh", thresh_otsu),
            ("Thresh 100", thresh_100),
        ]
        
        for prep_name, prep_img in preprocessed_images:
            try:
                # Use best performing config from above (PSM 6 typically)
                text = pytesseract.image_to_string(prep_img, config="--psm 6 -c tessedit_char_whitelist=0123456789").strip()
                digits = ''.join(c for c in text if c.isdigit())
                success = digits == expected
                status = "✓" if success else "✗"
                
                print(f"    {prep_name:20s}: '{text}' -> '{digits}' {status}")
                
            except Exception as e:
                print(f"    {prep_name:20s}: ERROR - {e}")

def test_custom_preprocessing():
    """Test custom preprocessing specifically for small digit images"""
    
    print(f"\n" + "=" * 40)
    print("CUSTOM PREPROCESSING TEST")
    print("=" * 40)
    
    test_files = [
        ("test_pyautogui_X787.png", "11"),
        ("test_pyautogui_X895.png", "13"),
    ]
    
    for image_file, expected in test_files:
        print(f"\nCustom preprocessing for {image_file}:")
        
        img = cv2.imread(image_file, cv2.IMREAD_GRAYSCALE)
        if img is None:
            continue
        
        # Custom preprocessing pipeline
        
        # 1. Scale up significantly
        scaled = cv2.resize(img, None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC)
        
        # 2. Apply Gaussian blur to smooth pixels
        blurred = cv2.GaussianBlur(scaled, (3, 3), 0)
        
        # 3. Sharpen
        kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
        sharpened = cv2.filter2D(blurred, -1, kernel)
        
        # 4. Apply morphological operations to clean up
        kernel = np.ones((2,2), np.uint8)
        cleaned = cv2.morphologyEx(sharpened, cv2.MORPH_CLOSE, kernel)
        
        # 5. Final threshold
        _, final = cv2.threshold(cleaned, 127, 255, cv2.THRESH_BINARY)
        
        # Save the processed image for inspection
        processed_file = image_file.replace('.png', '_processed.png')
        cv2.imwrite(processed_file, final)
        
        # Test OCR on processed image
        try:
            text = pytesseract.image_to_string(final, config="--psm 6 -c tessedit_char_whitelist=0123456789").strip()
            digits = ''.join(c for c in text if c.isdigit())
            success = digits == expected
            status = "✓" if success else "✗"
            
            print(f"  Custom pipeline: '{text}' -> '{digits}' {status}")
            print(f"  Processed image saved: {processed_file}")
            
        except Exception as e:
            print(f"  Custom pipeline: ERROR - {e}")

if __name__ == "__main__":
    test_ocr_configurations()
    test_custom_preprocessing()