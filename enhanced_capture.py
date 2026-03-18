#!/usr/bin/env python3
"""
Enhanced Screenshot Capture Module
Improves image quality for better OCR accuracy
"""

import pyautogui
import cv2
import numpy as np
import os
from PIL import Image, ImageEnhance
import time

class EnhancedCapture:
    def __init__(self):
        # Disable pyautogui failsafe for automation
        pyautogui.FAILSAFE = False
        
        # Configure for high-quality captures
        self.capture_delay = 0.1  # Small delay after positioning
        
    def capture_region_enhanced(self, x, y, width, height, save_path=None):
        """
        Enhanced screenshot capture with multiple quality improvements
        """
        print(f"Enhanced capture: region ({x}, {y}) size {width}x{height}")
        
        # Method 1: Try pyautogui with confidence disabled (faster)
        try:
            # Small delay to ensure UI is stable
            time.sleep(self.capture_delay)
            
            # Capture with pyautogui
            screenshot = pyautogui.screenshot(region=(x, y, width, height))
            
            # Convert to numpy array for processing
            img_array = np.array(screenshot)
            
            # Convert RGB to BGR for OpenCV
            img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            
            # Apply enhancements
            enhanced_img = self._enhance_image_quality(img_bgr)
            
            if save_path:
                # Save original for comparison
                cv2.imwrite(save_path.replace('.png', '_original.png'), img_bgr)
                # Save enhanced version
                cv2.imwrite(save_path, enhanced_img)
                print(f"  Saved: {save_path}")
            
            return enhanced_img
            
        except Exception as e:
            print(f"Enhanced capture failed: {e}")
            return None
    
    def _enhance_image_quality(self, img):
        """
        Apply multiple image enhancement techniques
        """
        # Convert to grayscale for processing
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img.copy()
        
        # 1. Scale up for better OCR (2x or 3x)
        scale_factor = 3
        height, width = gray.shape
        new_width = width * scale_factor
        new_height = height * scale_factor
        
        # Use INTER_CUBIC for smooth upscaling
        scaled = cv2.resize(gray, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
        
        # 2. Apply sharpening kernel
        sharpening_kernel = np.array([
            [-1, -1, -1],
            [-1,  9, -1],
            [-1, -1, -1]
        ])
        sharpened = cv2.filter2D(scaled, -1, sharpening_kernel)
        
        # 3. Enhance contrast
        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        contrast_enhanced = clahe.apply(sharpened)
        
        # 4. Noise reduction while preserving edges
        denoised = cv2.bilateralFilter(contrast_enhanced, 9, 75, 75)
        
        # 5. Optimal thresholding for text
        # Try adaptive threshold first
        adaptive_thresh = cv2.adaptiveThreshold(
            denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        
        # Also try Otsu's method
        _, otsu_thresh = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Choose the better threshold based on text area
        adaptive_text_area = np.sum(adaptive_thresh == 0)  # Black pixels
        otsu_text_area = np.sum(otsu_thresh == 0)
        
        # Use the method that produces reasonable text area (not too much, not too little)
        total_pixels = adaptive_thresh.shape[0] * adaptive_thresh.shape[1]
        adaptive_ratio = adaptive_text_area / total_pixels
        otsu_ratio = otsu_text_area / total_pixels
        
        # Good text should be 5-30% of the image
        if 0.05 <= adaptive_ratio <= 0.30:
            final_thresh = adaptive_thresh
            method = "adaptive"
        elif 0.05 <= otsu_ratio <= 0.30:
            final_thresh = otsu_thresh
            method = "otsu"
        else:
            # Fallback to simple threshold
            _, final_thresh = cv2.threshold(denoised, 127, 255, cv2.THRESH_BINARY)
            method = "simple"
        
        print(f"  Enhancement: {scale_factor}x scaled, sharpened, {method} threshold")
        
        return final_thresh
    
    def capture_and_compare_methods(self, x, y, width, height, base_name):
        """
        Capture the same region with different methods for comparison
        """
        print(f"Comparing capture methods for region ({x}, {y}) size {width}x{height}")
        
        methods = []
        
        # Method 1: Standard pyautogui
        try:
            time.sleep(0.1)
            standard = pyautogui.screenshot(region=(x, y, width, height))
            standard_array = np.array(standard)
            standard_bgr = cv2.cvtColor(standard_array, cv2.COLOR_RGB2BGR)
            
            cv2.imwrite(f"{base_name}_standard.png", standard_bgr)
            methods.append(("Standard", standard_bgr))
            print("  ✓ Standard capture")
        except Exception as e:
            print(f"  ✗ Standard capture failed: {e}")
        
        # Method 2: Enhanced version
        try:
            enhanced = self.capture_region_enhanced(x, y, width, height)
            if enhanced is not None:
                cv2.imwrite(f"{base_name}_enhanced.png", enhanced)
                methods.append(("Enhanced", enhanced))
                print("  ✓ Enhanced capture")
        except Exception as e:
            print(f"  ✗ Enhanced capture failed: {e}")
        
        # Method 3: PIL-based capture with enhancements
        try:
            import PIL.ImageGrab as ImageGrab
            
            # Capture with PIL
            pil_img = ImageGrab.grab(bbox=(x, y, x + width, y + height))
            
            # Enhance with PIL
            enhancer = ImageEnhance.Sharpness(pil_img)
            sharpened = enhancer.enhance(2.0)  # Increase sharpness
            
            enhancer = ImageEnhance.Contrast(sharpened)
            contrasted = enhancer.enhance(1.5)  # Increase contrast
            
            # Convert to OpenCV format
            pil_array = np.array(contrasted)
            pil_bgr = cv2.cvtColor(pil_array, cv2.COLOR_RGB2BGR)
            
            cv2.imwrite(f"{base_name}_pil_enhanced.png", pil_bgr)
            methods.append(("PIL Enhanced", pil_bgr))
            print("  ✓ PIL enhanced capture")
        except Exception as e:
            print(f"  ✗ PIL enhanced capture failed: {e}")
        
        return methods

def test_enhanced_capture():
    """
    Test enhanced capture on the problem region
    """
    print("ENHANCED CAPTURE TEST")
    print("=" * 40)
    
    # Coordinates for the X787 region that should show '11'
    # These are the approximate coordinates from the OCR region
    test_x = 787
    test_y = 200  # Approximate Y coordinate 
    test_width = 35
    test_height = 35
    
    capture = EnhancedCapture()
    
    print("NOTE: Make sure Teams is visible and showing the calendar with '11'")
    print("Capturing in 3 seconds...")
    
    for i in range(3, 0, -1):
        print(f"  {i}...")
        time.sleep(1)
    
    # Test different capture methods
    methods = capture.capture_and_compare_methods(
        test_x, test_y, test_width, test_height, "capture_test_11"
    )
    
    print(f"\nCreated {len(methods)} test captures:")
    for method_name, _ in methods:
        print(f"  - {method_name}")
    
    print("\nNext steps:")
    print("1. Check the generated images: capture_test_11_*.png")
    print("2. See which method produces the clearest '11'")
    print("3. Test OCR on each version")

if __name__ == "__main__":
    test_enhanced_capture()