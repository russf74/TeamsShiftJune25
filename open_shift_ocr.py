# open_shift_ocr.py
# Open Shift Detection Logic

import cv2
import numpy as np
import os
import logging
import pytesseract
import calendar
from datetime import datetime

def detect_open_shifts(proc_image, image, image_path, year, month):
    """
    Detect open shifts by extracting the dynamic region between the 'Open shifts' and 'Booked shifts' markers,
    then running color block and date mapping logic on the entire region. This is robust to any number of rows/lines.
    Only saves one date region crop per date, even if multiple blocks are mapped to the same date.
    """
    import hashlib
    # --- Step 1: Extract dynamic region between markers ---
    openshifts_marker_path = os.path.join(os.path.dirname(__file__), 'openshifts.png')
    bookedshifts_marker_path = os.path.join(os.path.dirname(__file__), 'bookedshifts.png')
    openshifts_marker = cv2.imread(openshifts_marker_path, cv2.IMREAD_UNCHANGED)
    bookedshifts_marker = cv2.imread(bookedshifts_marker_path, cv2.IMREAD_UNCHANGED)
    if openshifts_marker is None or bookedshifts_marker is None:
        logging.warning("Marker images for open or booked shifts not found. Skipping dynamic region extraction.")
        return {}
    img_bgr = image.copy()
    if img_bgr.shape[2] == 4:
        img_bgr = cv2.cvtColor(img_bgr, cv2.COLOR_BGRA2BGR)
    if openshifts_marker.shape[2] == 4:
        openshifts_marker = cv2.cvtColor(openshifts_marker, cv2.COLOR_BGRA2BGR)
    if bookedshifts_marker.shape[2] == 4:
        bookedshifts_marker = cv2.cvtColor(bookedshifts_marker, cv2.COLOR_BGRA2BGR)
    res_open = cv2.matchTemplate(img_bgr, openshifts_marker, cv2.TM_CCOEFF_NORMED)
    _, max_val_open, _, max_loc_open = cv2.minMaxLoc(res_open)
    res_booked = cv2.matchTemplate(img_bgr, bookedshifts_marker, cv2.TM_CCOEFF_NORMED)
    _, max_val_booked, _, max_loc_booked = cv2.minMaxLoc(res_booked)
    if max_val_open < 0.85 or max_val_booked < 0.85:
        logging.warning("Could not confidently find both open and booked shift markers for dynamic region extraction.")
        return {}
    margin_top = 20
    margin_bottom = 10
    open_y = max(0, max_loc_open[1] - margin_top)
    booked_y = max(0, max_loc_booked[1] - margin_bottom)
    if booked_y <= open_y:
        booked_y = open_y + 10
    dynamic_region = image[open_y:booked_y, :, :]
    dynamic_region_path = image_path.replace('.png', '_dynamic_open_shifts_region.png')
    cv2.imwrite(dynamic_region_path, dynamic_region)
    debug_markers_img = image.copy()
    cv2.rectangle(debug_markers_img, max_loc_open, (max_loc_open[0]+openshifts_marker.shape[1], max_loc_open[1]+openshifts_marker.shape[0]), (0,255,0), 2)
    cv2.rectangle(debug_markers_img, max_loc_booked, (max_loc_booked[0]+bookedshifts_marker.shape[1], max_loc_booked[1]+bookedshifts_marker.shape[0]), (0,0,255), 2)
    cv2.rectangle(debug_markers_img, (0, open_y), (image.shape[1]-1, booked_y), (255,0,0), 2)
    debug_markers_path = image_path.replace('.png', '_dynamic_region_debug.png')
    cv2.imwrite(debug_markers_path, debug_markers_img)
    logging.info(f"Dynamic Open Shifts Region (ends above booked marker): {open_y} to {booked_y} (open marker at {max_loc_open[1]}, booked marker at {max_loc_booked[1]})")

    # --- Step 2: Detect all color blocks in the dynamic region ---
    hsv_dyn = cv2.cvtColor(dynamic_region, cv2.COLOR_BGR2HSV)
    lower_orange = np.array([5, 50, 50])
    upper_orange = np.array([30, 255, 255])
    lower_purple = np.array([90, 20, 60])
    upper_purple = np.array([160, 255, 255])
    mask_orange_dyn = cv2.inRange(hsv_dyn, lower_orange, upper_orange)
    mask_purple_dyn = cv2.inRange(hsv_dyn, lower_purple, upper_purple)
    mask_combined_dyn = cv2.bitwise_or(mask_orange_dyn, mask_purple_dyn)
    mask_dyn_path = image_path.replace('.png', '_dynamic_open_shifts_mask.png')
    cv2.imwrite(mask_dyn_path, mask_combined_dyn)
    contours_dyn, _ = cv2.findContours(mask_combined_dyn, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    color_blocks = []
    for cnt in contours_dyn:
        x, y, w, h = cv2.boundingRect(cnt)
        if w > 10 and h > 10:
            abs_y = open_y + y
            block_info = {'rect': (x, abs_y, w, h)}
            color_blocks.append(block_info)
    debug_blocks = image.copy()
    for block in color_blocks:
        x, y, w, h = block['rect']
        cv2.rectangle(debug_blocks, (x, y), (x+w, y+h), (0, 255, 0), 2)
    debug_blocks_path = image_path.replace('.png', '_open_shifts_blocks.png')
    cv2.imwrite(debug_blocks_path, debug_blocks)

    # --- Step 3: Remove duplicate blocks (by hash of rect) ---
    unique_blocks = []
    seen = set()
    for block in color_blocks:
        rect = block['rect']
        rect_hash = hashlib.md5(str(rect).encode()).hexdigest()
        if rect_hash not in seen:
            unique_blocks.append(block)
            seen.add(rect_hash)

    # --- Step 4: For each unique block, extract date and count ---
    DATE_HEADER_Y_OFFSET = 185  # Adjusted offset to properly capture date headers
    DATE_HEADER_HEIGHT = 35     # Increased height to ensure full capture
    DATE_HEADER_WIDTH = 35      # Much smaller width to prevent overlap, properly centered
    result = {}
    debug_image_with_dates = image.copy()
    block_to_date_debug = []  # For debug output
    from collections import defaultdict
    col_blocks = defaultdict(list)
    for i, block in enumerate(unique_blocks):
        x, y, w, h = block['rect']
        col_blocks[x].append((i, block))
    print(f"[OCR DEBUG] Found {len(unique_blocks)} unique blocks grouped into {len(col_blocks)} columns")
    for x, blocks in col_blocks.items():
        print(f"[OCR DEBUG] Column at X={x}: {len(blocks)} blocks")
    col_dates = {}
    # First pass: try to OCR date for each column (use topmost block in column)
    for x, blocks in col_blocks.items():
        i, block = sorted(blocks, key=lambda b: b[1]['rect'][1])[0]
        x0, y0, w0, h0 = block['rect']
        center_x = x0 + (w0 // 2)
        date_x1 = max(0, center_x - (DATE_HEADER_WIDTH // 2))
        date_y1 = max(0, y0 - DATE_HEADER_Y_OFFSET)
        date_x2 = min(image.shape[1], date_x1 + DATE_HEADER_WIDTH)
        date_y2 = min(image.shape[0], date_y1 + DATE_HEADER_HEIGHT)
        date_region = image[date_y1:date_y2, date_x1:date_x2]
        date_region_gray = cv2.cvtColor(date_region, cv2.COLOR_BGR2GRAY)
        # Draw red rectangle on debug image to show OCR region
        cv2.rectangle(debug_image_with_dates, (date_x1, date_y1), (date_x2, date_y2), (0, 0, 255), 2)
        # Save individual OCR region for debugging
        ocr_debug_path = image_path.replace('.png', f'_ocr_region_X{x}.png')
        cv2.imwrite(ocr_debug_path, date_region_gray)
        # Scale up 2x for better OCR accuracy on small text
        scaled_region = cv2.resize(date_region_gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        day_text = pytesseract.image_to_string(scaled_region, config='--psm 6 -c tessedit_char_whitelist=0123456789').strip()
        day_text_digits = ''.join(c for c in day_text if c.isdigit())
        print(f"[OCR DEBUG] Column X={x}: OCR='{day_text}' -> digits='{day_text_digits}'")
        if day_text_digits:
            try:
                day = int(day_text_digits)
                if 1 <= day <= 31:
                    date_obj = datetime(year, month, day)
                    key = f'{year}-{month:02d}-{day:02d}'
                    col_dates[x] = (key, day_text)
                    print(f"[OCR DEBUG] Column X={x}: SUCCESS -> {key}")
                else:
                    print(f"[OCR DEBUG] Column X={x}: INVALID DAY -> {day}")
            except Exception as e:
                print(f"[OCR DEBUG] Column X={x}: EXCEPTION -> {e}")
        else:
            print(f"[OCR DEBUG] Column X={x}: NO DIGITS FOUND")
    # Only process columns with a valid date
    for x, blocks in col_blocks.items():
        if x in col_dates:
            key, ocr_text = col_dates[x]
            for i, block in blocks:
                if key not in result:
                    result[key] = {
                        'type': 'open',
                        'coords': [block['rect']],
                        'date': datetime.strptime(key, '%Y-%m-%d').strftime('%d %b'),
                        'day': int(key[-2:]),
                        'month': month,
                        'year': year,
                        'count': 1
                    }
                else:
                    result[key]['coords'].append(block['rect'])
                    result[key]['count'] += 1
                block_to_date_debug.append(f"Block {i}: COLUMN OCR='{ocr_text}' -> {key}")
        else:
            for i, block in blocks:
                block_to_date_debug.append(f"Block {i}: COLUMN OCR='' -> NO DATE (IGNORED)")
    debug_dates_path = image_path.replace('.png', '_open_shifts_date_regions.png')
    cv2.imwrite(debug_dates_path, debug_image_with_dates)
    # --- Draw shift count in each date cell for debug/visualization ---
    for key, entry in result.items():
        if entry.get('count', 0) > 0 and entry.get('coords'):
            x, y, w, h = entry['coords'][0]
            text = str(entry['count'])
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.8
            thickness = 2
            color = (0, 0, 255)
            text_x = x + w // 2 - 10
            text_y = max(0, y - DATE_HEADER_Y_OFFSET - 10)
            cv2.putText(debug_image_with_dates, text, (text_x, text_y), font, font_scale, color, thickness, cv2.LINE_AA)
    debug_counts_path = image_path.replace('.png', '_open_shifts_date_counts.png')
    cv2.imwrite(debug_counts_path, debug_image_with_dates)
    # --- Print per-block OCR debug info ---
    if block_to_date_debug:
        print("[Open Shift OCR Debug]")
        for line in block_to_date_debug:
            print("  ", line)
    if len(result) == 0:
        logging.info("Open Shifts Detected : 0")
    else:
        date_strs = [entry['date'] for entry in result.values() for _ in range(entry['count'])]
        if date_strs:
            unique_dates = sorted(list(set(date_strs)))
            logging.info(f"Open Shifts Detected : {sum([entry['count'] for entry in result.values()])} on {', '.join(unique_dates)}")
        else:
            logging.info(f"Open Shifts Detected : {sum([entry['count'] for entry in result.values()])}")
    return result
