#!/usr/bin/env python3
"""
Deep OCR Investigation Tool
Investigate exactly what's happening in the OCR pipeline to understand why clear "11" and "13" are failing.
"""

import cv2
import pytesseract
import numpy as np
from PIL import Image
import tempfile
import os

def investigate_ocr_pipeline(image_path, expected_text):
    """Deep dive into what Tesseract is actually seeing and processing"""
    
    print(f"\n{'='*80}")
    print(f"DEEP OCR INVESTIGATION: {os.path.basename(image_path)}")
    print(f"Expected: '{expected_text}'")
    print(f"{'='*80}")
    
    # Load image with OpenCV
    cv_img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if cv_img is None:
        print(f"❌ Could not load image: {image_path}")
        return
    
    print(f"📊 IMAGE PROPERTIES:")
    print(f"  • File size: {os.path.getsize(image_path)} bytes")
    print(f"  • Dimensions: {cv_img.shape[1]}x{cv_img.shape[0]} pixels")
    print(f"  • Data type: {cv_img.dtype}")
    print(f"  • Min value: {cv_img.min()}")
    print(f"  • Max value: {cv_img.max()}")
    print(f"  • Mean value: {cv_img.mean():.1f}")
    
    # Test if image is actually readable by PIL (what pytesseract uses internally)
    try:
        pil_img = Image.open(image_path)
        print(f"  • PIL format: {pil_img.format}")
        print(f"  • PIL mode: {pil_img.mode}")
        print(f"  • PIL size: {pil_img.size}")
    except Exception as e:
        print(f"  ❌ PIL error: {e}")
    
    # Check Tesseract version and capabilities
    print(f"\n🔧 TESSERACT ENVIRONMENT:")
    try:
        version = pytesseract.get_tesseract_version()
        print(f"  • Tesseract version: {version}")
    except Exception as e:
        print(f"  ❌ Version check error: {e}")
    
    try:
        langs = pytesseract.get_languages()
        print(f"  • Available languages: {langs}")
    except Exception as e:
        print(f"  ❌ Language check error: {e}")
    
    # Test various image formats to see if format matters
    print(f"\n🖼️  FORMAT TESTING:")
    
    # Save as different formats and test
    formats_to_test = ['PNG', 'TIFF', 'BMP']
    
    for fmt in formats_to_test:
        try:
            with tempfile.NamedTemporaryFile(suffix=f'.{fmt.lower()}', delete=False) as tmp_file:
                # Convert CV image to PIL and save in different format
                pil_converted = Image.fromarray(cv_img)
                pil_converted.save(tmp_file.name, format=fmt)
                
                # Test OCR on this format
                result = pytesseract.image_to_string(tmp_file.name, config='--psm 8 -c tessedit_char_whitelist=0123456789').strip()
                digits = ''.join(c for c in result if c.isdigit())
                
                print(f"  • {fmt:4s}: '{result}' (digits: '{digits}')")
                
                # Cleanup
                os.unlink(tmp_file.name)
                
        except Exception as e:
            print(f"  ❌ {fmt:4s}: Error - {e}")
    
    # Test with exact pixel values
    print(f"\n🔍 PIXEL ANALYSIS:")
    
    # Get exact pixel values around text area
    h, w = cv_img.shape
    center_y, center_x = h//2, w//2
    
    # Sample a small area around center
    sample_size = min(10, h//2, w//2)
    sample_area = cv_img[center_y-sample_size:center_y+sample_size, 
                        center_x-sample_size:center_x+sample_size]
    
    print(f"  • Center region pixels ({sample_size*2}x{sample_size*2}):")
    print(f"    {sample_area.flatten()}")
    
    # Check if there are any unusual values
    unique_values = np.unique(cv_img)
    print(f"  • Unique pixel values: {unique_values}")
    print(f"  • Number of unique values: {len(unique_values)}")
    
    # Test if it's a color depth issue
    if len(unique_values) <= 2:
        print(f"  ⚠️  Binary image detected (only {len(unique_values)} values)")
    elif len(unique_values) <= 16:
        print(f"  ⚠️  Low color depth ({len(unique_values)} values)")
    
    # Test raw pytesseract with minimal config
    print(f"\n🧪 RAW TESSERACT TESTING:")
    
    configs_to_test = [
        ('No config', ''),
        ('PSM only', '--psm 8'),
        ('Whitelist only', '-c tessedit_char_whitelist=0123456789'),
        ('Both', '--psm 8 -c tessedit_char_whitelist=0123456789'),
        ('Verbose', '--psm 8 -c tessedit_char_whitelist=0123456789 -c debug_file=/tmp/tesseract_debug'),
    ]
    
    for config_name, config in configs_to_test:
        try:
            result = pytesseract.image_to_string(cv_img, config=config).strip()
            digits = ''.join(c for c in result if c.isdigit())
            print(f"  • {config_name:15s}: '{result}' -> digits: '{digits}'")
            
            # Also try with PIL image directly
            pil_result = pytesseract.image_to_string(Image.fromarray(cv_img), config=config).strip()
            pil_digits = ''.join(c for c in pil_result if c.isdigit())
            if pil_result != result:
                print(f"    PIL version:      '{pil_result}' -> digits: '{pil_digits}'")
                
        except Exception as e:
            print(f"  ❌ {config_name:15s}: {e}")
    
    # Test with image data info
    print(f"\n📋 TESSERACT IMAGE DATA:")
    try:
        data = pytesseract.image_to_data(cv_img, output_type=pytesseract.Output.DICT)
        print(f"  • Words detected: {len([w for w in data['text'] if w.strip()])}")
        for i, text in enumerate(data['text']):
            if text.strip():
                conf = data['conf'][i]
                print(f"    - '{text}' (confidence: {conf})")
    except Exception as e:
        print(f"  ❌ Data extraction error: {e}")

def main():
    """Investigate the two failing OCR images"""
    
    test_files = [
        ("screenshots/0-shifts_screenshot_20251001_181548_ocr_region_X895.png", "11"),
        ("screenshots/0-shifts_screenshot_20251001_181548_ocr_region_X787.png", "13"),
    ]
    
    for image_path, expected in test_files:
        if os.path.exists(image_path):
            investigate_ocr_pipeline(image_path, expected)
        else:
            print(f"❌ File not found: {image_path}")
    
    print(f"\n{'='*80}")
    print("INVESTIGATION COMPLETE")
    print(f"{'='*80}")

if __name__ == "__main__":
    main()