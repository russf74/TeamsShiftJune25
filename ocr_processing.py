import cv2
import numpy as np
import pytesseract
import calendar
from datetime import datetime
import re # Ensure re is imported
import logging

# Configure logging for this module
logging.basicConfig(
    level=logging.INFO,  # Changed from WARNING to INFO to show shift detection logs
    format='[%(levelname)s] %(message)s'
)

def extract_shifts_from_image(image_path, year, month):
    """
    Detects open and booked shifts in Teams Shifts screenshot from distinct rows.
    Returns a dict: {date_str: {'type': 'open'|'booked', 'coords': (x, y, w, h)}}.
    """
    # Load image
    image = cv2.imread(image_path)
    if image is None:
        logging.error(f"Could not load image from {image_path}")
        return {}

    date_mask_debug_img = image.copy()
    original_image_height, original_image_width = image.shape[:2]
    logging.debug(f"Original image dimensions: {original_image_width}x{original_image_height}")

    # Define Date OCR Crop Parameters
    DATE_CROP_CAL_GRID_Y = 150
    DATE_CROP_BOX_HEIGHT = 30
    DATE_CROP_BOX_WIDTH = 40
    DATE_CROP_X_OFFSET = 5

    # Remove only the bottom 100 pixels for detection
    proc_image = image[:-100, :, :]
    proc_height, proc_width = proc_image.shape[:2]

    # --- Step 0: Find the arrow and OCR the month/year label ---
    arrow_template = cv2.imread('arrow.png', cv2.IMREAD_UNCHANGED)
    if arrow_template is not None:
        if arrow_template.shape[2] == 4:
            arrow_template = cv2.cvtColor(arrow_template, cv2.COLOR_BGRA2BGR)
        search_img_arrow = image.copy() # Use original image for arrow template matching
        if search_img_arrow.shape[2] == 4:
            search_img_arrow = cv2.cvtColor(search_img_arrow, cv2.COLOR_BGRA2BGR)
        
        res_arrow = cv2.matchTemplate(search_img_arrow, arrow_template, cv2.TM_CCOEFF_NORMED)
        min_val_arrow, max_val_arrow, min_loc_arrow, max_loc_arrow = cv2.minMaxLoc(res_arrow)
        logging.debug(f"Arrow template match: max_val={max_val_arrow:.3f}")
        
        month_label_text = ""
        if max_val_arrow > 0.85: # Threshold for arrow detection
            arrow_x, arrow_y = max_loc_arrow
            arrow_h, arrow_w = arrow_template.shape[:2]
            crop_x1 = arrow_x + arrow_w + 10
            crop_x2 = crop_x1 + 200 
            crop_y1 = arrow_y
            crop_y2 = crop_y1 + arrow_h
            crop_x1 = max(0, crop_x1)
            crop_x2 = min(image.shape[1], crop_x2)
            crop_y1 = max(0, crop_y1)
            crop_y2 = min(image.shape[0], crop_y2)
            month_label_crop = image[crop_y1:crop_y2, crop_x1:crop_x2]
            if month_label_crop.size > 0:
                debug_month_label_path = image_path.replace('.png', '_month_label_crop_dynamic.png')
                cv2.imwrite(debug_month_label_path, month_label_crop)
                month_label_gray = cv2.cvtColor(month_label_crop, cv2.COLOR_BGR2GRAY)
                month_label_text = pytesseract.image_to_string(month_label_gray, config='--psm 7').strip()
                logging.debug(f"OCR month label (dynamic): '{month_label_text}'")
            else:
                logging.debug("Dynamic month label crop is empty.")
        
        if not month_label_text: # Fallback if dynamic failed or arrow not found
            logging.debug("Arrow not found or dynamic OCR failed, falling back to static month/year crop.")
            month_label_crop = image[130:180, 210:420] # Static region
            if month_label_crop.size > 0:
                debug_month_label_path = image_path.replace('.png', '_month_label_crop_static.png')
                cv2.imwrite(debug_month_label_path, month_label_crop)
                month_label_gray = cv2.cvtColor(month_label_crop, cv2.COLOR_BGR2GRAY)
                month_label_text = pytesseract.image_to_string(month_label_gray, config='--psm 7').strip()
                logging.debug(f"OCR month label (static): '{month_label_text}'")
            else:
                logging.debug("Static month label crop is empty.")
    else:
        logging.debug("arrow.png template not found, using static month/year crop.")
        month_label_crop = image[130:180, 210:420] # Static region
        if month_label_crop.size > 0:
            debug_month_label_path = image_path.replace('.png', '_month_label_crop_static_no_template.png')
            cv2.imwrite(debug_month_label_path, month_label_crop)
            month_label_gray = cv2.cvtColor(month_label_crop, cv2.COLOR_BGR2GRAY)
            month_label_text = pytesseract.image_to_string(month_label_gray, config='--psm 7').strip()
            logging.debug(f"OCR month label (static, no arrow template): '{month_label_text}'")
        else:
            logging.debug("Static month label crop is empty (no arrow template).")

    month_num = month # Default to input
    year_num = year   # Default to input
    month_names = {m.lower(): i for i, m in enumerate(calendar.month_name) if m}
    # Updated regex for more robust month/year parsing
    match_date_text = re.search(r'([A-Za-z]+)\s*.*?\b(20\d{2})\b', month_label_text)
    if match_date_text:
        m_name = match_date_text.group(1).lower()
        y_val_str = match_date_text.group(2) # Get the year string
        try:
            y_val = int(y_val_str)
            if m_name in month_names:
                month_num = month_names[m_name]
                year_num = y_val
                logging.debug(f"Parsed month/year from screenshot: {month_num}/{year_num}")
            else:
                logging.warning(f"Could not parse month name '{m_name}' from OCR label '{month_label_text}'. Using input {month}/{year}.")
        except ValueError:
            logging.warning(f"Could not convert year '{y_val_str}' to int from OCR label '{month_label_text}'. Using input {month}/{year}.")
    else:
        logging.warning(f"Could not parse month/year from OCR label '{month_label_text}'. Using input {month}/{year}.")
    # --- End of Month/Year OCR ---

    all_shifts_map = {}

    # --- Open and Booked Shift Detection Logic moved to separate modules ---
    from open_shift_ocr import detect_open_shifts
    from booked_shift_ocr import detect_booked_shifts

    logging.info("Calling detect_open_shifts module...")    
    open_shifts = detect_open_shifts(proc_image, image, image_path, year_num, month_num)
    # --- AGGREGATE open shift counts by date and print summary ---
    open_shift_counts = {k: v['count'] for k, v in open_shifts.items()}
    total_open_blocks = sum(open_shift_counts.values())
    if open_shift_counts:
        log_lines = [f"  {k[-2:]} {calendar.month_abbr[int(k[5:7])]} ({v})" for k, v in open_shift_counts.items()]
        logging.info(f"[Open Shifts Summary] Total: {total_open_blocks} blocks\n" + "\n".join(log_lines))
    else:
        logging.info("[Open Shifts Summary] Total: 0 blocks")
    all_shifts_map = dict(open_shifts)
    logging.info("Calling detect_booked_shifts module...")
    booked_shifts = detect_booked_shifts(proc_image, image, image_path, year_num, month_num)
    all_shifts_map.update(booked_shifts)

    # Don't log the technical details of shift map
    return all_shifts_map

def extract_month_year_from_image(image_path):
    """
    Utility function to OCR the month/year label from a Teams screenshot.
    Returns (month_num, year_num) or (None, None) if not found.
    """
    import cv2
    import pytesseract
    import calendar
    import re
    image = cv2.imread(image_path)
    if image is None:
        return None, None
    # Try dynamic crop (arrow-based)
    arrow_template = cv2.imread('arrow.png', cv2.IMREAD_UNCHANGED)
    month_label_text = ""
    if arrow_template is not None:
        if arrow_template.shape[2] == 4:
            arrow_template = cv2.cvtColor(arrow_template, cv2.COLOR_BGRA2BGR)
        search_img_arrow = image.copy()
        if search_img_arrow.shape[2] == 4:
            search_img_arrow = cv2.cvtColor(search_img_arrow, cv2.COLOR_BGRA2BGR)
        res_arrow = cv2.matchTemplate(search_img_arrow, arrow_template, cv2.TM_CCOEFF_NORMED)
        min_val_arrow, max_val_arrow, min_loc_arrow, max_loc_arrow = cv2.minMaxLoc(res_arrow)
        if max_val_arrow > 0.85:
            arrow_x, arrow_y = max_loc_arrow
            arrow_h, arrow_w = arrow_template.shape[:2]
            crop_x1 = arrow_x + arrow_w + 10
            crop_x2 = crop_x1 + 200
            crop_y1 = arrow_y
            crop_y2 = crop_y1 + arrow_h
            crop_x1 = max(0, crop_x1)
            crop_x2 = min(image.shape[1], crop_x2)
            crop_y1 = max(0, crop_y1)
            crop_y2 = min(image.shape[0], crop_y2)
            month_label_crop = image[crop_y1:crop_y2, crop_x1:crop_x2]
            if month_label_crop.size > 0:
                month_label_gray = cv2.cvtColor(month_label_crop, cv2.COLOR_BGR2GRAY)
                month_label_text = pytesseract.image_to_string(month_label_gray, config='--psm 7').strip()
    if not month_label_text:
        # Fallback to static region
        month_label_crop = image[130:180, 210:420]
        if month_label_crop.size > 0:
            month_label_gray = cv2.cvtColor(month_label_crop, cv2.COLOR_BGR2GRAY)
            month_label_text = pytesseract.image_to_string(month_label_gray, config='--psm 7').strip()
    month_names = {m.lower(): i for i, m in enumerate(calendar.month_name) if m}
    match_date_text = re.search(r'([A-Za-z]+)\s*.*?\b(20\d{2})\b', month_label_text)
    if match_date_text:
        m_name = match_date_text.group(1).lower()
        y_val_str = match_date_text.group(2)
        try:
            y_val = int(y_val_str)
            if m_name in month_names:
                month_num = month_names[m_name]
                year_num = y_val
                return month_num, year_num
        except Exception:
            pass
    return None, None

# ...existing code...
