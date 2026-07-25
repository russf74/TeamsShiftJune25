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
    min_block_width = 20
    min_block_height = 20
    max_block_width = 90
    max_aspect_ratio = 3.0
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        contour_area = cv2.contourArea(cnt)
        fill_ratio = contour_area / float(w * h) if w and h else 0
        aspect_ratio = w / float(h) if h else 0
        if (min_block_width <= w <= max_block_width and h >= min_block_height
                and aspect_ratio <= max_aspect_ratio and fill_ratio >= 0.20):
            block_top = band_y1 + y
            block_info = {'rect': (x, block_top, w, h), 'fill_ratio': fill_ratio}
            orange_blocks.append(block_info)
        else:
            logging.debug(
                "Ignoring non-tile booked contour at (%d,%d,%d,%d), fill=%.2f, aspect=%.2f",
                x, band_y1 + y, w, h, fill_ratio, aspect_ratio,
            )
    # Date region extraction and OCR
    # --- Use the same date header Y as open shifts for robust date extraction ---
    # Try to find the open shift marker and use the same DATE_HEADER_Y_OFFSET as open_shift_ocr
    DATE_HEADER_Y_OFFSET = 195  # Final fine-tune for perfect date region alignment
    DATE_HEADER_HEIGHT = 25
    DATE_HEADER_WIDTH = 40
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
        # Scale up 2x for better OCR accuracy on small text
        scaled_region = cv2.resize(date_region_gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        ocr_reads = []
        for psm in (7, 8):
            raw_text = pytesseract.image_to_string(scaled_region, config=f'--psm {psm} digits').strip()
            digits = ''.join(c for c in raw_text if c.isdigit())
            if digits:
                ocr_reads.append(digits)
        unique_reads = set(ocr_reads)
        if len(unique_reads) > 1:
            logging.warning("[BOOKED OCR] Conflicting day reads for block %d: %s; ignoring block", i, sorted(unique_reads))
            continue
        day_text = ocr_reads[0] if ocr_reads else ""
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
                            'evidence': {
                                'date_crop': date_region_path,
                                'day_reads': ocr_reads,
                                'tile_fill_ratio': round(block['fill_ratio'], 3),
                            },
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
