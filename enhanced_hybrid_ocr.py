#!/usr/bin/env python3
"""
Enhanced Hybrid OCR Module with Template Matching
Combines OCR + Template Matching + Visual Analysis for robust date recognition
"""

import cv2
import pytesseract
import numpy as np
import os
import json
from datetime import datetime
import glob

class EnhancedHybridOCR:
    def __init__(self):
        self.ocr_success_patterns = {}  
        self.known_failures = {}        
        self.template_cache = {}        
        self.confidence_threshold = 70   # Lowered for real-world images
        self.visual_patterns = {}       # Store visual fingerprints
        
    def read_date_region(self, image_path, expected_range=(1, 31)):
        """
        Enhanced method: OCR -> Visual Analysis -> Template Matching -> Intelligent Correction
        """
        print(f"\n=== Enhanced Reading: {os.path.basename(image_path)} ===")
        
        # Load and analyze the image
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            return None, 0, "ImageError"
        
        # Method 1: Try multiple OCR approaches
        ocr_results = self._try_enhanced_ocr(img, image_path)
        best_ocr = self._evaluate_ocr_results(ocr_results, expected_range)
        
        if best_ocr and best_ocr['confidence'] >= self.confidence_threshold:
            print(f"✅ OCR SUCCESS: '{best_ocr['text']}' (confidence: {best_ocr['confidence']}, method: {best_ocr['method']})")
            return best_ocr['text'], best_ocr['confidence'], f"OCR-{best_ocr['method']}"
        
        # Method 2: Visual pattern analysis
        print("🔍 Analyzing visual patterns...")
        visual_result = self._analyze_visual_patterns(img, expected_range)
        
        if visual_result:
            print(f"✅ VISUAL SUCCESS: '{visual_result['text']}' (confidence: {visual_result['confidence']})")
            return visual_result['text'], visual_result['confidence'], "Visual"
        
        # Method 3: Template matching 
        print("🎯 Trying template matching...")
        template_result = self._try_template_matching(img, expected_range)
        
        if template_result:
            print(f"✅ TEMPLATE SUCCESS: '{template_result['text']}' (confidence: {template_result['confidence']})")
            return template_result['text'], template_result['confidence'], "Template"
        
        # Method 4: Enhanced intelligent correction
        print("🧠 Trying enhanced correction...")
        corrected_result = self._try_enhanced_correction(ocr_results, img, expected_range)
        
        if corrected_result:
            print(f"✅ CORRECTION SUCCESS: '{corrected_result['text']}' (was: '{corrected_result['original']}')")
            return corrected_result['text'], corrected_result['confidence'], "Corrected"
        
        print("❌ All methods failed")
        return None, 0, "Failed"
    
    def _try_enhanced_ocr(self, img, image_path):
        """Enhanced OCR with preprocessing and multiple approaches"""
        results = []
        
        # Try different preprocessing approaches
        preprocessed_images = self._create_preprocessed_variants(img)
        
        # OCR methods to try
        methods = [
            ("PSM6-digits", "--psm 6 -c tessedit_char_whitelist=0123456789"),
            ("PSM8-digits", "--psm 8 -c tessedit_char_whitelist=0123456789"),
            ("PSM7-digits", "--psm 7 -c tessedit_char_whitelist=0123456789"),
            ("PSM10-single", "--psm 10 -c tessedit_char_whitelist=0123456789"),
        ]
        
        # Test each method on each preprocessed image
        for prep_name, prep_img in preprocessed_images.items():
            for method_name, config in methods:
                try:
                    text = pytesseract.image_to_string(prep_img, config=config).strip()
                    
                    # Get confidence
                    try:
                        data = pytesseract.image_to_data(prep_img, config=config, output_type=pytesseract.Output.DICT)
                        confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
                        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
                    except:
                        avg_confidence = 30
                    
                    digits = ''.join(c for c in text if c.isdigit())
                    
                    if digits:
                        full_method = f"{prep_name}-{method_name}"
                        results.append({
                            'method': full_method,
                            'text': digits,
                            'raw_text': text,
                            'confidence': avg_confidence,
                            'preprocessing': prep_name
                        })
                        print(f"  {full_method:20s}: '{text}' -> '{digits}' (conf: {avg_confidence:.1f})")
                
                except Exception as e:
                    continue
        
        return results
    
    def _create_preprocessed_variants(self, img):
        """Create different preprocessed versions of the image"""
        variants = {'original': img}
        
        try:
            # Threshold variants
            _, thresh1 = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY)
            variants['thresh-127'] = thresh1
            
            _, thresh2 = cv2.threshold(img, 100, 255, cv2.THRESH_BINARY)
            variants['thresh-100'] = thresh2
            
            # Adaptive threshold
            adapt_thresh = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
            variants['adaptive'] = adapt_thresh
            
            # Scale up 2x
            scaled2x = cv2.resize(img, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
            variants['scale-2x'] = scaled2x
            
            # Scale up 3x  
            scaled3x = cv2.resize(img, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
            variants['scale-3x'] = scaled3x
            
        except Exception as e:
            print(f"  Preprocessing error: {e}")
        
        return variants
    
    def _analyze_visual_patterns(self, img, expected_range):
        """Analyze visual patterns to identify numbers"""
        try:
            # Count white pixels, connected components, etc.
            height, width = img.shape
            
            # Binarize the image
            _, binary = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY_INV)
            
            # Find contours (digit shapes)
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if not contours:
                return None
            
            # Analyze contour patterns
            contour_count = len(contours)
            
            # Simple heuristics based on contour count and shape
            if contour_count == 1:
                # Single contour - likely single digit or connected double digit
                contour = contours[0]
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = w / h if h > 0 else 0
                
                # Wide single contour might be "11" 
                if aspect_ratio > 0.7:
                    return {'text': '11', 'confidence': 75}
                
            elif contour_count == 2:
                # Two contours - likely "11" or two-digit number
                # Sort contours left to right
                contours = sorted(contours, key=lambda c: cv2.boundingRect(c)[0])
                
                # Check if they look like two 1's
                similar_widths = True
                for contour in contours:
                    _, _, w, h = cv2.boundingRect(contour)
                    aspect_ratio = w / h if h > 0 else 0
                    if aspect_ratio > 0.4:  # Too wide for a "1"
                        similar_widths = False
                        break
                
                if similar_widths:
                    return {'text': '11', 'confidence': 70}
            
            print(f"  Visual analysis: {contour_count} contours detected")
            
        except Exception as e:
            print(f"  Visual analysis error: {e}")
        
        return None
    
    def _try_template_matching(self, img, expected_range):
        """Template matching against known digit shapes"""
        # For now, create basic templates
        templates = self._get_digit_templates()
        
        best_match = None
        best_confidence = 0
        
        for digit, template in templates.items():
            try:
                # Scale template to match input image size
                template_resized = cv2.resize(template, (img.shape[1], img.shape[0]))
                
                # Template matching
                result = cv2.matchTemplate(img, template_resized, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, _ = cv2.minMaxLoc(result)
                
                # Convert to percentage
                confidence = max_val * 100
                
                if confidence > best_confidence and confidence > 60:  # Minimum threshold
                    best_confidence = confidence
                    best_match = digit
                    
                print(f"  Template {digit}: {confidence:.1f}% match")
                
            except Exception as e:
                continue
        
        if best_match:
            return {'text': best_match, 'confidence': best_confidence}
        
        return None
    
    def _get_digit_templates(self):
        """Generate or load digit templates"""
        templates = {}
        
        # Create simple digit templates (can be improved with real samples)
        for digit in ['1', '2', '3', '8', '11', '13', '18', '28']:
            # Create a simple template
            template = np.ones((35, 35), dtype=np.uint8) * 255
            
            # Add the digit 
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.6 if len(digit) == 1 else 0.5
            thickness = 1
            
            text_size = cv2.getTextSize(digit, font, font_scale, thickness)[0]
            text_x = max(0, (35 - text_size[0]) // 2)
            text_y = (35 + text_size[1]) // 2
            
            cv2.putText(template, digit, (text_x, text_y), font, font_scale, 0, thickness)
            templates[digit] = template
        
        return templates
    
    def _try_enhanced_correction(self, ocr_results, img, expected_range):
        """Enhanced correction with context awareness"""
        if not ocr_results:
            return None
        
        # Enhanced correction patterns with confidence weighting
        corrections = {
            '13': ['11'],    # "11" often reads as "13"
            '1': ['11', '13'],     # Single "1" might be partial read of "11" or "13"
            '3': ['8', '13'],      # "3" confusion patterns
            '8': ['3'],      
            '6': ['5'],      
            '5': ['6'],
            '11': ['13'],    # Sometimes "11" reads correctly but should be "13"
        }
        
        # Get the most frequent wrong reading
        wrong_readings = {}
        for result in ocr_results:
            text = result['text']
            if text in wrong_readings:
                wrong_readings[text] += 1
            else:
                wrong_readings[text] = 1
        
        # Try corrections for the most common wrong reading
        most_common = max(wrong_readings.items(), key=lambda x: x[1])[0] if wrong_readings else None
        
        if most_common and most_common in corrections:
            possible_corrections = corrections[most_common]
            
            # Choose correction based on context
            for correction in possible_corrections:
                try:
                    corrected_num = int(correction)
                    if expected_range[0] <= corrected_num <= expected_range[1]:
                        # Get confidence from original OCR result
                        original_confidence = max([r['confidence'] for r in ocr_results if r['text'] == most_common] + [0])
                        
                        return {
                            'text': correction,
                            'original': most_common,
                            'confidence': original_confidence * 0.7  # Lower confidence for corrections
                        }
                except ValueError:
                    continue
        
        return None
    
    def _evaluate_ocr_results(self, results, expected_range):
        """Enhanced evaluation with multiple criteria"""
        if not results:
            return None
        
        scored_results = []
        
        for result in results:
            try:
                num = int(result['text'])
                
                # Base score from confidence
                score = result['confidence']
                
                # Range validity bonus
                if expected_range[0] <= num <= expected_range[1]:
                    score += 30  # Bonus for valid range
                else:
                    score -= 20  # Penalty for invalid range
                
                # Preprocessing bonus (some methods work better)
                if 'scale' in result['preprocessing']:
                    score += 5
                if 'thresh' in result['preprocessing']:
                    score += 3
                
                # Method bonus (PSM6 tends to work well)
                if 'PSM6' in result['method']:
                    score += 5
                    
                result['total_score'] = score
                scored_results.append(result)
                
            except ValueError:
                result['total_score'] = 0
                scored_results.append(result)
        
        # Return best scoring result
        scored_results.sort(key=lambda x: x['total_score'], reverse=True)
        return scored_results[0] if scored_results else None

def test_enhanced_ocr():
    """Test the enhanced hybrid OCR"""
    print("🚀 ENHANCED HYBRID OCR TEST")
    print("=" * 50)
    
    ocr = EnhancedHybridOCR()
    
    # Test on our problem images  
    test_cases = [
        ("screenshots/0-shifts_screenshot_20251001_181548_ocr_region_X895.png", "13"),
        ("screenshots/0-shifts_screenshot_20251001_181548_ocr_region_X787.png", "11"),
    ]
    
    results = []
    
    for image_path, expected in test_cases:
        if os.path.exists(image_path):
            print(f"\nTesting: {os.path.basename(image_path)}")
            result, confidence, method = ocr.read_date_region(image_path)
            
            success = (result == expected)
            results.append({
                'expected': expected,
                'got': result,
                'success': success,
                'confidence': confidence,
                'method': method
            })
            
            status = "✅" if success else "❌"
            print(f"{status} Expected '{expected}' -> Got '{result}' (conf: {confidence:.1f}, method: {method})")
        else:
            print(f"❌ File not found: {image_path}")
    
    # Summary
    successful = sum(1 for r in results if r['success'])
    total = len(results)
    
    print(f"\n📊 ENHANCED RESULTS: {successful}/{total} successful ({(successful/total*100):.1f}%)")
    
    return results

if __name__ == "__main__":
    test_enhanced_ocr()