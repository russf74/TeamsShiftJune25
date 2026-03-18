#!/usr/bin/env python3
"""
Tesseract Debug Tool
Test different OCR configurations on saved region images without modifying the main app.
"""

import cv2
import pytesseract
import os
import glob

def test_ocr_configs(image_path):
    """Test various OCR configurations on a single image"""
    
    # Load the image
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        print(f"Could not load image: {image_path}")
        return
    
    print(f"\n=== Testing OCR on: {os.path.basename(image_path)} ===")
    
    # Different OCR configurations to test
    configs = [
        ('Original (psm 7 digits)', '--psm 7 digits'),
        ('PSM 8 digits only', '--psm 8 -c tessedit_char_whitelist=0123456789'),
        ('PSM 6 digits only', '--psm 6 -c tessedit_char_whitelist=0123456789'),
        ('PSM 7 no restriction', '--psm 7'),
        ('PSM 8 no restriction', '--psm 8'),
        ('PSM 10 single char', '--psm 10 -c tessedit_char_whitelist=0123456789'),
        ('Default config', ''),
    ]
    
    for config_name, config_str in configs:
        try:
            result = pytesseract.image_to_string(img, config=config_str).strip()
            digits_only = ''.join(c for c in result if c.isdigit())
            print(f"  {config_name:25} -> '{result}' (digits: '{digits_only}')")
        except Exception as e:
            print(f"  {config_name:25} -> ERROR: {e}")

def main():
    """Find and test all OCR region images from the latest scan"""
    
    # Find OCR region files from most recent scan
    ocr_files = glob.glob("screenshots/*_ocr_region_X*.png")
    
    if not ocr_files:
        print("No OCR region files found. Run a scan first to generate them.")
        return
    
    # Sort by modification time to get the most recent ones
    ocr_files.sort(key=os.path.getmtime, reverse=True)
    
    print("Found OCR region files:")
    for f in ocr_files[:10]:  # Show only the 10 most recent
        print(f"  {f}")
    
    print("\n" + "="*60)
    
    # Test each OCR region file
    for ocr_file in ocr_files[:10]:  # Test only the 10 most recent
        test_ocr_configs(ocr_file)
    
    print("\n" + "="*60)
    print("Testing complete!")

if __name__ == "__main__":
    main()