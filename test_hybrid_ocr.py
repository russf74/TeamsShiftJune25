#!/usr/bin/env python3
"""
Comprehensive Test Suite for Hybrid OCR Module
Tests against known problem cases and validates the hybrid approach.
"""

import os
import cv2
import numpy as np
from hybrid_ocr_module import HybridOCR

def create_test_digits():
    """Create synthetic test digit images to validate OCR behavior"""
    print("🧪 Creating synthetic test digits...")
    
    # Create test directory
    test_dir = "test_digits"
    os.makedirs(test_dir, exist_ok=True)
    
    # Create simple digit images similar to Teams calendar style
    digits = ['1', '2', '3', '8', '11', '13', '18', '28']
    
    for digit in digits:
        # Create a white background image (35x35 like our OCR regions)
        img = np.ones((35, 35), dtype=np.uint8) * 255
        
        # Add the digit in black text (simple font)
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.6 if len(digit) == 1 else 0.5
        thickness = 1
        
        # Get text size to center it
        text_size = cv2.getTextSize(digit, font, font_scale, thickness)[0]
        text_x = (35 - text_size[0]) // 2
        text_y = (35 + text_size[1]) // 2
        
        cv2.putText(img, digit, (text_x, text_y), font, font_scale, 0, thickness)
        
        # Save the test image
        cv2.imwrite(f"{test_dir}/{digit}.png", img)
        print(f"  Created: {digit}.png")

def test_known_problem_cases():
    """Test against the specific problem cases we identified"""
    print("\n🎯 Testing Known Problem Cases")
    print("-" * 40)
    
    ocr = HybridOCR()
    
    problem_cases = [
        ("screenshots/0-shifts_screenshot_20251001_181548_ocr_region_X895.png", "13"),
        ("screenshots/0-shifts_screenshot_20251001_181548_ocr_region_X787.png", "11"),
    ]
    
    results = []
    
    for image_path, expected in problem_cases:
        if not os.path.exists(image_path):
            print(f"⚠️  File not found: {image_path}")
            continue
            
        print(f"\nTesting: {os.path.basename(image_path)} (expecting '{expected}')")
        
        result, confidence, method = ocr.read_date_region(image_path, expected_range=(1, 31))
        
        success = (result == expected)
        results.append({
            'file': image_path,
            'expected': expected,
            'got': result,
            'confidence': confidence,
            'method': method,
            'success': success
        })
        
        status = "✅" if success else "❌"
        print(f"{status} Result: '{result}' (confidence: {confidence:.1f}, method: {method})")
    
    return results

def test_synthetic_digits():
    """Test against synthetic digit images"""
    print("\n🧪 Testing Synthetic Digits")
    print("-" * 30)
    
    ocr = HybridOCR()
    test_dir = "test_digits"
    
    if not os.path.exists(test_dir):
        print("⚠️  No synthetic digits found. Run create_test_digits() first.")
        return []
    
    results = []
    
    for filename in os.listdir(test_dir):
        if filename.endswith('.png'):
            expected = filename.replace('.png', '')
            image_path = os.path.join(test_dir, filename)
            
            print(f"Testing: {filename} (expecting '{expected}')")
            
            result, confidence, method = ocr.read_date_region(image_path, expected_range=(1, 31))
            
            success = (result == expected)
            results.append({
                'file': image_path,
                'expected': expected,
                'got': result,
                'confidence': confidence,
                'method': method,
                'success': success
            })
            
            status = "✅" if success else "❌"
            print(f"  {status} Result: '{result}' (confidence: {confidence:.1f}, method: {method})")
    
    return results

def analyze_results(all_results):
    """Analyze test results and provide recommendations"""
    print("\n📊 ANALYSIS SUMMARY")
    print("=" * 50)
    
    if not all_results:
        print("❌ No test results to analyze")
        return
    
    total_tests = len(all_results)
    successful_tests = sum(1 for r in all_results if r['success'])
    
    print(f"Total Tests: {total_tests}")
    print(f"Successful: {successful_tests}")
    print(f"Failed: {total_tests - successful_tests}")
    print(f"Success Rate: {(successful_tests/total_tests)*100:.1f}%")
    
    # Method breakdown
    method_stats = {}
    for result in all_results:
        method = result['method']
        if method not in method_stats:
            method_stats[method] = {'total': 0, 'success': 0}
        method_stats[method]['total'] += 1
        if result['success']:
            method_stats[method]['success'] += 1
    
    print(f"\n📈 Method Performance:")
    for method, stats in method_stats.items():
        success_rate = (stats['success'] / stats['total']) * 100
        print(f"  {method:15s}: {stats['success']}/{stats['total']} ({success_rate:.1f}%)")
    
    # Failure analysis
    failures = [r for r in all_results if not r['success']]
    if failures:
        print(f"\n❌ Failed Cases:")
        for failure in failures:
            print(f"  Expected '{failure['expected']}' -> Got '{failure['got']}' ({failure['method']})")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    if successful_tests == total_tests:
        print("✅ All tests passed! This hybrid approach is working.")
        print("🚀 Ready to create production module and integrate.")
    elif successful_tests >= total_tests * 0.8:
        print("⚠️  Good success rate but needs refinement.")
        print("🔧 Focus on improving failure cases before integration.")
    else:
        print("❌ Success rate too low for production use.")
        print("🔧 Need to add template matching and improve intelligence.")

def run_comprehensive_test():
    """Run all tests and provide complete analysis"""
    print("🚀 HYBRID OCR COMPREHENSIVE TEST SUITE")
    print("=" * 60)
    
    all_results = []
    
    # Create synthetic digits for baseline testing
    create_test_digits()
    
    # Test synthetic digits (baseline)
    synthetic_results = test_synthetic_digits()
    all_results.extend(synthetic_results)
    
    # Test known problem cases (real-world)
    problem_results = test_known_problem_cases()
    all_results.extend(problem_results)
    
    # Analyze everything
    analyze_results(all_results)
    
    return all_results

if __name__ == "__main__":
    results = run_comprehensive_test()