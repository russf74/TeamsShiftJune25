#!/usr/bin/env python3
"""
Image Analysis Tool - Examine the actual problem images 
to understand why OCR consistently fails on "11" and "13"
"""

import cv2
import numpy as np
import os

def analyze_image_details(image_path, expected_value):
    """Deep analysis of an image to understand OCR challenges"""
    print(f"\n🔍 ANALYZING: {os.path.basename(image_path)} (expecting '{expected_value}')")
    print("=" * 60)
    
    # Load image
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        print("❌ Could not load image")
        return
    
    height, width = img.shape
    print(f"📐 Dimensions: {width} x {height} pixels")
    
    # Pixel analysis
    unique_values = np.unique(img)
    print(f"🎨 Unique pixel values: {len(unique_values)} ({unique_values})")
    
    # Calculate statistics
    mean_val = np.mean(img)
    std_val = np.std(img)
    print(f"📊 Mean: {mean_val:.1f}, Std: {std_val:.1f}")
    
    # Check if it's already binary-like
    if len(unique_values) <= 3:
        print("✓ Image appears to be nearly binary")
    else:
        print("⚠️ Image has grayscale values")
    
    # Apply different thresholds and analyze
    print(f"\n🔍 THRESHOLD ANALYSIS:")
    thresholds = [100, 127, 150, 180]
    
    for thresh_val in thresholds:
        _, binary = cv2.threshold(img, thresh_val, 255, cv2.THRESH_BINARY)
        
        # Count black pixels (text)
        black_pixels = np.sum(binary == 0)
        total_pixels = width * height
        text_ratio = black_pixels / total_pixels
        
        print(f"  Threshold {thresh_val:3d}: {black_pixels:4d} black pixels ({text_ratio*100:.1f}% text)")
        
        # Save debug version
        debug_name = f"debug_{expected_value}_thresh{thresh_val}.png"
        cv2.imwrite(debug_name, binary)
    
    # Connected component analysis
    print(f"\n🔗 CONNECTED COMPONENT ANALYSIS:")
    _, binary = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY_INV)  # Invert for analysis
    
    # Find connected components
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary)
    
    print(f"  Components found: {num_labels - 1}")  # Subtract background
    
    for i in range(1, num_labels):  # Skip background (label 0)
        x, y, w, h, area = stats[i]
        aspect_ratio = w / h if h > 0 else 0
        cx, cy = centroids[i]
        
        print(f"  Component {i}: pos=({x},{y}) size={w}x{h} area={area} ratio={aspect_ratio:.2f}")
    
    # Create visualization
    print(f"\n🎯 CREATING VISUALIZATION...")
    
    # Original
    debug_img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    
    # Mark components
    _, binary = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    colors = [(0, 255, 0), (255, 0, 0), (0, 0, 255), (255, 255, 0)]
    
    for i, contour in enumerate(contours):
        color = colors[i % len(colors)]
        cv2.drawContours(debug_img, [contour], -1, color, 1)
        
        # Add bounding box
        x, y, w, h = cv2.boundingRect(contour)
        cv2.rectangle(debug_img, (x, y), (x + w, y + h), color, 1)
        
        # Add component number
        cv2.putText(debug_img, str(i+1), (x, y-2), cv2.FONT_HERSHEY_SIMPLEX, 0.3, color, 1)
    
    # Save visualization
    debug_name = f"debug_{expected_value}_analysis.png"
    cv2.imwrite(debug_name, debug_img)
    print(f"  Saved: {debug_name}")
    
    # Manual pattern recognition
    print(f"\n🧠 MANUAL PATTERN ANALYSIS:")
    
    if num_labels == 2:  # Background + 1 component
        print("  Pattern: Single connected component")
        if expected_value == "11":
            print("  ⚠️  Expected '11' but only 1 component - digits might be touching")
        elif expected_value == "13":
            print("  ⚠️  Expected '13' but only 1 component - digits might be touching")
    
    elif num_labels == 3:  # Background + 2 components  
        print("  Pattern: Two connected components")
        if expected_value == "11":
            print("  ✓ Expected '11' with 2 components - looks correct")
        elif expected_value == "13":
            print("  ✓ Expected '13' with 2 components - could be correct")
    
    print(f"✅ Analysis complete for {expected_value}")

def main():
    """Analyze both problem images"""
    print("🔬 IMAGE ANALYSIS TOOL")
    print("Examining why OCR fails on specific date images")
    
    problem_images = [
        ("screenshots/0-shifts_screenshot_20251001_181548_ocr_region_X895.png", "11"),
        ("screenshots/0-shifts_screenshot_20251001_181548_ocr_region_X787.png", "13"),
    ]
    
    for image_path, expected in problem_images:
        if os.path.exists(image_path):
            analyze_image_details(image_path, expected)
        else:
            print(f"❌ Image not found: {image_path}")
    
    print(f"\n🎯 NEXT STEPS:")
    print("1. Check the debug images created")
    print("2. Compare component patterns between '11' and '13'")  
    print("3. Use this analysis to improve the hybrid OCR logic")

if __name__ == "__main__":
    main()