#!/usr/bin/env python3
"""
Template Matching Debug Tool
Use OpenCV template matching as an alternative to OCR for these specific numbers.
"""

import cv2
import numpy as np
import os

def create_digit_templates():
    """Create template images for digits 0-9 by cropping from known good OCR regions"""
    
    # We can use the working OCR regions as templates
    # Look for files that successfully OCR'd and extract digit templates
    known_good_files = [
        ("screenshots/0-shifts_screenshot_20251001_181548_ocr_region_X1866.png", "31"),
        ("screenshots/0-shifts_screenshot_20251001_181548_ocr_region_X1812.png", "30"),
        ("screenshots/0-shifts_screenshot_20251001_181548_ocr_region_X1704.png", "28"),
        ("screenshots/0-shifts_screenshot_20251001_181548_ocr_region_X625.png", "8"),
    ]
    
    print("Available template source files:")
    for file_path, expected in known_good_files:
        if os.path.exists(file_path):
            print(f"  ✅ {file_path} -> {expected}")
        else:
            print(f"  ❌ {file_path} (missing)")

def template_match_digits(image_path, possible_digits=['11', '13']):
    """Try template matching approach for digit recognition"""
    
    target_img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if target_img is None:
        print(f"Could not load {image_path}")
        return None
    
    print(f"\n=== Template matching for {image_path} ===")
    print(f"Image size: {target_img.shape}")
    print(f"Testing against possible digits: {possible_digits}")
    
    # For now, let's try a different approach - analyze the image characteristics
    # Count white/black pixels, check image dimensions, etc.
    
    height, width = target_img.shape
    total_pixels = height * width
    white_pixels = np.sum(target_img > 127)
    black_pixels = total_pixels - white_pixels
    
    print(f"  Dimensions: {width}x{height}")
    print(f"  White pixels: {white_pixels} ({white_pixels/total_pixels*100:.1f}%)")
    print(f"  Black pixels: {black_pixels} ({black_pixels/total_pixels*100:.1f}%)")
    
    # Analyze horizontal and vertical projections
    h_projection = np.sum(target_img < 127, axis=0)  # Count black pixels per column
    v_projection = np.sum(target_img < 127, axis=1)  # Count black pixels per row
    
    print(f"  Horizontal projection (black pixels per column): {h_projection.tolist()}")
    print(f"  Vertical projection (black pixels per row): {v_projection.tolist()}")
    
    # Look for patterns that might distinguish 11 vs 13
    # "11" should have similar left and right halves
    # "13" should have different left and right patterns
    
    left_half = target_img[:, :width//2]
    right_half = target_img[:, width//2:]
    
    left_black = np.sum(left_half < 127)
    right_black = np.sum(right_half < 127)
    
    print(f"  Left half black pixels: {left_black}")
    print(f"  Right half black pixels: {right_black}")
    print(f"  Symmetry ratio: {min(left_black, right_black) / max(left_black, right_black):.2f}")
    
    return {
        'dimensions': (width, height),
        'white_pixels': white_pixels,
        'black_pixels': black_pixels,
        'h_projection': h_projection.tolist(),
        'v_projection': v_projection.tolist(),
        'left_black': left_black,
        'right_black': right_black,
        'symmetry': min(left_black, right_black) / max(left_black, right_black) if max(left_black, right_black) > 0 else 0
    }

def main():
    """Analyze the failing images using template matching approach"""
    
    create_digit_templates()
    
    # Analyze our problem images
    problem_files = [
        ("screenshots/0-shifts_screenshot_20251001_181548_ocr_region_X895.png", "11"),
        ("screenshots/0-shifts_screenshot_20251001_181548_ocr_region_X787.png", "13"),
    ]
    
    results = {}
    for file_path, expected in problem_files:
        if os.path.exists(file_path):
            results[expected] = template_match_digits(file_path)
        else:
            print(f"❌ File not found: {file_path}")
    
    # Compare characteristics
    if "11" in results and "13" in results:
        print(f"\n{'='*60}")
        print("COMPARISON ANALYSIS")
        print(f"{'='*60}")
        
        r11 = results["11"]
        r13 = results["13"]
        
        print(f"Image '11': {r11['dimensions']}, symmetry: {r11['symmetry']:.2f}")
        print(f"Image '13': {r13['dimensions']}, symmetry: {r13['symmetry']:.2f}")
        
        if r11['symmetry'] > r13['symmetry']:
            print("✅ Pattern detected: '11' has higher symmetry than '13' (expected)")
        else:
            print("❌ Unexpected: '13' has higher symmetry than '11'")

if __name__ == "__main__":
    main()