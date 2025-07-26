# booked_shift_ocr.py
# Placeholder for booked shift detection logic

import cv2
import numpy as np
import os
import logging
import pytesseract
from datetime import datetime

def detect_booked_shifts(proc_image, image, image_path, year, month):
    """
    Detect booked shifts (orange or red blocks), OCR the date above each block, and log summary.
    Returns a dict: {date_str: {'type': 'booked', 'coords': (x, y, w, h)}}
    """
    # Load the booked shifts marker template
    template_path = os.path.join(os.path.dirname(__file__), 'bookedshifts.png')
    template = cv2.imread(template_path, cv2.IMREAD_UNCHANGED)
    if template is None:
        logging.warning(f"Booked shifts marker not found at {template_path}")
        return {}

    # Match template in the full image (use BGR for both)
    search_img = image.copy()
    if search_img.shape[2] == 4:
        search_img = cv2.cvtColor(search_img, cv2.COLOR_BGRA2BGR)
    if template.shape[2] == 4:
        template = cv2.cvtColor(template, cv2.COLOR_BGRA2BGR)

    res = cv2.matchTemplate(search_img, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
    if max_val < 0.85:
        logging.info("Booked shifts marker not found with high confidence.")
        return {}

    # Get the y position of the marker
    marker_x, marker_y = max_loc
    band_height = 80
    band_y1 = max(0, marker_y - 10)
    band_y2 = min(band_y1 + band_height, image.shape[0])
    band = image[band_y1:band_y2, :, :]

    # Save the band for debug/inspection (like open_shift_ocr)
    band_save_path = image_path.replace('.png', '_booked_shifts_band.png')
    cv2.imwrite(band_save_path, band)

    # Convert band to HSV color space
    hsv_band = cv2.cvtColor(band, cv2.COLOR_BGR2HSV)

    # Orange mask
    lower_orange = np.array([5, 40, 40])
    upper_orange = np.array([30, 255, 255])
    mask_orange = cv2.inRange(hsv_band, lower_orange, upper_orange)
    # Red mask (broadened)
    lower_red1 = np.array([0, 30, 120])
    upper_red1 = np.array([15, 255, 255])
    lower_red2 = np.array([160, 30, 120])
    upper_red2 = np.array([180, 255, 255])
    mask_red1 = cv2.inRange(hsv_band, lower_red1, upper_red1)
    mask_red2 = cv2.inRange(hsv_band, lower_red2, upper_red2)
    mask_red = cv2.bitwise_or(mask_red1, mask_red2)
    # Pink mask (for pinkish booked shifts)
    lower_pink = np.array([140, 20, 150])
    upper_pink = np.array([170, 120, 255])
    mask_pink = cv2.inRange(hsv_band, lower_pink, upper_pink)
    # Combine all masks
    mask_combined = cv2.bitwise_or(mask_orange, mask_red)
    mask_combined = cv2.bitwise_or(mask_combined, mask_pink)

    # Find contours of combined mask
    contours, _ = cv2.findContours(mask_combined, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    orange_blocks = []
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        if w > 10 and h > 10:
            block_top = band_y1 + y
            block_info = {'rect': (x, block_top, w, h)}
            orange_blocks.append(block_info)
    # Date region extraction and OCR
    # --- Use the same date header Y as open shifts for robust date extraction ---
    # Try to find the open shift marker and use the same DATE_HEADER_Y_OFFSET as open_shift_ocr
    DATE_HEADER_Y_OFFSET = 195  # Final fine-tune for perfect date region alignment
    DATE_HEADER_HEIGHT = 25
    DATE_HEADER_WIDTH = 60
    booked_date_regions_img = image.copy()
    openshifts_marker_path = os.path.join(os.path.dirname(__file__), 'openshifts.png')
    openshifts_marker = cv2.imread(openshifts_marker_path, cv2.IMREAD_UNCHANGED)
    open_y = None
    if openshifts_marker is not None:
        img_bgr = image.copy()
        if img_bgr.shape[2] == 4:
            img_bgr = cv2.cvtColor(img_bgr, cv2.COLOR_BGRA2BGR)
        if openshifts_marker.shape[2] == 4:
            openshifts_marker = cv2.cvtColor(openshifts_marker, cv2.COLOR_BGRA2BGR)
        res_open = cv2.matchTemplate(img_bgr, openshifts_marker, cv2.TM_CCOEFF_NORMED)
        _, max_val_open, _, max_loc_open = cv2.minMaxLoc(res_open)
        if max_val_open > 0.85:
            open_y = max_loc_open[1]
    result = {}
    date_strs = []
    for i, block in enumerate(orange_blocks):
        x, y, w, h = block['rect']
        center_x = x + (w // 2)
        # Always use the header row Y for date extraction
        if open_y is not None:
            date_x1 = max(0, center_x - (DATE_HEADER_WIDTH // 2))
            date_y1 = max(0, open_y - DATE_HEADER_Y_OFFSET)
            date_x2 = min(image.shape[1], date_x1 + DATE_HEADER_WIDTH)
            date_y2 = min(image.shape[0], date_y1 + DATE_HEADER_HEIGHT)
        else:
            # Fallback: just above the block
            date_x1 = max(0, center_x - (DATE_HEADER_WIDTH // 2))
            date_y2 = max(0, y - 2)
            date_y1 = max(0, date_y2 - DATE_HEADER_HEIGHT)
            date_x2 = min(image.shape[1], date_x1 + DATE_HEADER_WIDTH)
        date_region = image[date_y1:date_y2, date_x1:date_x2]
        # Save each date region for debug
        date_region_path = image_path.replace('.png', f'_booked_shift_{i}_date_region.png')
        cv2.imwrite(date_region_path, date_region)
        # Draw rectangle on debug image
        cv2.rectangle(booked_date_regions_img, (date_x1, date_y1), (date_x2, date_y2), (0, 0, 255), 2)
        date_region_gray = cv2.cvtColor(date_region, cv2.COLOR_BGR2GRAY)
        day_text = pytesseract.image_to_string(date_region_gray, config='--psm 7 digits').strip()
        day_text = ''.join(c for c in day_text if c.isdigit())
        date_str = ""
        if day_text:
            try:
                day = int(day_text)
                if 1 <= day <= 31:
                    try:
                        date_obj = datetime(year, month, day)
                        date_str = date_obj.strftime("%d %b")
                        key = f'{year}-{month:02d}-{day:02d}'
                        result[key] = {
                            'type': 'booked',
                            'coords': block['rect'],
                            'date': date_str,
                            'day': day,
                            'month': month,
                            'year': year
                        }
                        date_strs.append(date_str)
                    except ValueError:
                        print(f"[BOOKED OCR] Invalid date for block {i}, day={day}, skipping")
                        # Don't add invalid entries to result
                else:
                    print(f"[BOOKED OCR] No valid day text for block {i}, skipping")
                    # Don't add invalid entries to result
            except ValueError:
                print(f"[BOOKED OCR] Day parsing failed for block {i}, skipping")
                # Don't add invalid entries to result
        else:
            print(f"[BOOKED OCR] No OCR text for block {i}, skipping")
            # Don't add invalid entries to result
    # Save a debug image showing all booked date regions
    debug_dates_path = image_path.replace('.png', '_booked_shifts_date_regions.png')
    cv2.imwrite(debug_dates_path, booked_date_regions_img)
    # Logging for booked shifts detected
    if len(orange_blocks) == 0:
        logging.info("Booked Shifts Detected : 0")
    else:
        if date_strs:
            unique_dates = sorted(list(set(date_strs)))
            logging.info(f"Booked Shifts Detected : {len(orange_blocks)} on {', '.join(unique_dates)}")
        else:
            logging.info(f"Booked Shifts Detected : {len(orange_blocks)}")
    return result
