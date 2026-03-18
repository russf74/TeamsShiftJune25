#!/usr/bin/env python3
"""
Capture Quality Test - Compare different capture methods and test OCR on each
"""

import cv2
import pytesseract
import numpy as np
import os
import glob

def test_ocr_on_captures():
    """
    Test OCR on all the different capture method results
    """
    print("OCR COMPARISON ON DIFFERENT CAPTURE METHODS")
    print("=" * 50)
    
    # Find all capture test files
    capture_files = glob.glob("capture_test_11_*.png")
    
    if not capture_files:
        print("No capture test files found. Run enhanced_capture.py first.")
        return
    
    ocr_configs = [
        ("PSM6", "--psm 6 -c tessedit_char_whitelist=0123456789"),
        ("PSM8", "--psm 8 -c tessedit_char_whitelist=0123456789"),
        ("PSM7", "--psm 7 -c tessedit_char_whitelist=0123456789"),
    ]
    
    results = {}
    
    for capture_file in sorted(capture_files):
        print(f"\nTesting: {capture_file}")
        
        # Load image
        img = cv2.imread(capture_file, cv2.IMREAD_GRAYSCALE)
        if img is None:
            print(f"  ERROR: Could not load {capture_file}")
            continue
        
        print(f"  Image size: {img.shape[1]}x{img.shape[0]}")
        
        capture_results = []
        
        # Test each OCR config
        for config_name, config in ocr_configs:
            try:
                text = pytesseract.image_to_string(img, config=config).strip()
                digits = ''.join(c for c in text if c.isdigit())
                
                # Get confidence
                try:
                    data = pytesseract.image_to_data(img, config=config, output_type=pytesseract.Output.DICT)
                    confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
                    avg_confidence = sum(confidences) / len(confidences) if confidences else 0
                except:
                    avg_confidence = 0
                
                success = digits == "11"
                capture_results.append({
                    'config': config_name,
                    'text': text,
                    'digits': digits,
                    'confidence': avg_confidence,
                    'success': success
                })
                
                status = "✓" if success else "✗"
                print(f"    {config_name}: '{text}' -> '{digits}' (conf: {avg_confidence:.1f}) {status}")
                
            except Exception as e:
                print(f"    {config_name}: ERROR - {e}")
        
        results[capture_file] = capture_results
    
    # Summary
    print(f"\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    
    best_method = None
    best_success_rate = 0
    
    for capture_file, capture_results in results.items():
        successful_configs = sum(1 for r in capture_results if r['success'])
        total_configs = len(capture_results)
        success_rate = successful_configs / total_configs if total_configs > 0 else 0
        
        print(f"{capture_file:25s}: {successful_configs}/{total_configs} configs successful ({success_rate*100:.1f}%)")
        
        if success_rate > best_success_rate:
            best_success_rate = success_rate
            best_method = capture_file
    
    if best_method:
        print(f"\nBEST METHOD: {best_method} ({best_success_rate*100:.1f}% success rate)")
        print("Use this capture method in the main application!")
    else:
        print("\nNo method achieved 100% success. Need further improvements.")

def analyze_image_quality():
    """
    Analyze the quality metrics of different capture methods
    """
    print(f"\n" + "=" * 50)
    print("IMAGE QUALITY ANALYSIS")
    print("=" * 50)
    
    capture_files = glob.glob("capture_test_11_*.png")
    
    for capture_file in sorted(capture_files):
        img = cv2.imread(capture_file, cv2.IMREAD_GRAYSCALE)
        if img is None:
            continue
        
        height, width = img.shape
        
        # Calculate quality metrics
        
        # 1. Sharpness (Laplacian variance)
        laplacian_var = cv2.Laplacian(img, cv2.CV_64F).var()
        
        # 2. Contrast (standard deviation)
        contrast = img.std()
        
        # 3. Text area (assuming text is darker)
        _, binary = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY)
        text_pixels = np.sum(binary == 0)
        text_ratio = text_pixels / (width * height)
        
        print(f"{capture_file:25s}: sharpness={laplacian_var:6.1f}, contrast={contrast:5.1f}, text={text_ratio*100:4.1f}%")

if __name__ == "__main__":
    test_ocr_on_captures()
    analyze_image_quality()