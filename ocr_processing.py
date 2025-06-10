# Placeholder for OCR and image processing logic



def extract_shifts_from_image(image_path, year, month):
    """
    Detects open shifts in Teams Shifts screenshot.
    Returns a dict: {date_str: (x, y, w, h)} for each detected open shift.
    """
    import cv2
    import numpy as np
    import pytesseract
    import calendar
    from datetime import datetime

    # Load image
    image = cv2.imread(image_path)
    if image is None:
        print(f"[ERROR] Could not load image from {image_path}")
        return {}

    height, width = image.shape[:2]
    debug_img = image.copy()

    # Remove only the bottom 100 pixels for detection, but keep debug_img as the full original
    proc_image = image[:-100, :, :]
    proc_height, proc_width = proc_image.shape[:2]

    # --- Step 0: Find the arrow and OCR the month/year label just to its right ---
    import cv2
    import numpy as np
    arrow_template = cv2.imread('arrow.png', cv2.IMREAD_UNCHANGED)
    if arrow_template is not None:
        # Remove alpha if present
        if arrow_template.shape[2] == 4:
            arrow_template = cv2.cvtColor(arrow_template, cv2.COLOR_BGRA2BGR)
        search_img = image.copy()
        if search_img.shape[2] == 4:
            search_img = cv2.cvtColor(search_img, cv2.COLOR_BGRA2BGR)
        res = cv2.matchTemplate(search_img, arrow_template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        print(f"[DEBUG] Arrow template match: max_val={max_val:.3f}")
        if max_val > 0.85:
            arrow_x, arrow_y = max_loc
            arrow_h, arrow_w = arrow_template.shape[:2]
            # Crop a region just to the right of the arrow for month/year label
            crop_x1 = arrow_x + arrow_w + 10
            crop_x2 = crop_x1 + 200  # width for month/year label
            crop_y1 = arrow_y
            crop_y2 = crop_y1 + arrow_h
            # Clamp to image bounds
            crop_x1 = max(0, crop_x1)
            crop_x2 = min(image.shape[1], crop_x2)
            crop_y1 = max(0, crop_y1)
            crop_y2 = min(image.shape[0], crop_y2)
            month_label_crop = image[crop_y1:crop_y2, crop_x1:crop_x2]
            debug_month_label_path = image_path.replace('.png', '_month_label_crop.png')
            cv2.imwrite(debug_month_label_path, month_label_crop)
            month_label_gray = cv2.cvtColor(month_label_crop, cv2.COLOR_BGR2GRAY)
            month_label_text = pytesseract.image_to_string(month_label_gray, config='--psm 7').strip()
            print(f"[DEBUG] OCR month label (dynamic): '{month_label_text}'")
        else:
            print("[DEBUG] Arrow not found, falling back to static month/year crop.")
            # Fallback to static region (legacy)
            month_label_crop = image[130:180, 210:420]
            debug_month_label_path = image_path.replace('.png', '_month_label_crop.png')
            cv2.imwrite(debug_month_label_path, month_label_crop)
            month_label_gray = cv2.cvtColor(month_label_crop, cv2.COLOR_BGR2GRAY)
            month_label_text = pytesseract.image_to_string(month_label_gray, config='--psm 7').strip()
            print(f"[DEBUG] OCR month label (static): '{month_label_text}'")
    else:
        print("[DEBUG] arrow.png template not found, using static month/year crop.")
        month_label_crop = image[130:180, 210:420]
        debug_month_label_path = image_path.replace('.png', '_month_label_crop.png')
        cv2.imwrite(debug_month_label_path, month_label_crop)
        month_label_gray = cv2.cvtColor(month_label_crop, cv2.COLOR_BGR2GRAY)
        month_label_text = pytesseract.image_to_string(month_label_gray, config='--psm 7').strip()
        print(f"[DEBUG] OCR month label (static): '{month_label_text}'")
    # Try to parse month and year
    import re
    month_num = month
    year_num = year
    month_names = {m.lower(): i for i, m in enumerate(calendar.month_name) if m}
    match = re.search(r'([A-Za-z]+)\s*(20\d{2})', month_label_text)
    if match:
        m_name = match.group(1).lower()
        y_val = int(match.group(2))
        if m_name in month_names:
            month_num = month_names[m_name]
            year_num = y_val
            print(f"[DEBUG] Parsed month/year from screenshot: {month_num}/{year_num}")
        else:
            print(f"[DEBUG] Could not parse month name '{m_name}' from OCR label. No shifts will be matched.")
            return {}
    else:
        print(f"[DEBUG] Could not parse month/year from OCR label. No shifts will be matched.")
        return {}

    # --- Detect open shifts (orange) ---
    # Find open shifts row (template or static as before)
    openshifts_template = cv2.imread('openshifts.png', cv2.IMREAD_UNCHANGED)
    found_openshifts = False
    if openshifts_template is not None:
        if openshifts_template.shape[2] == 4:
            openshifts_template = cv2.cvtColor(openshifts_template, cv2.COLOR_BGRA2BGR)
        search_img = proc_image.copy()
        if search_img.shape[2] == 4:
            search_img = cv2.cvtColor(search_img, cv2.COLOR_BGRA2BGR)
        res = cv2.matchTemplate(search_img, openshifts_template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        print(f"[DEBUG] OpenShifts template match: max_val={max_val:.3f}")
        if max_val > 0.85:
            found_openshifts = True
            os_x, os_y = max_loc
            os_h, os_w = openshifts_template.shape[:2]
            row_pad = -50
            row_height = int(os_h * 1.2)
            open_shifts_y1 = os_y + os_h + row_pad
            open_shifts_y2 = open_shifts_y1 + row_height
            open_shifts_y1 = max(0, open_shifts_y1)
            open_shifts_y2 = min(proc_image.shape[0], open_shifts_y2)
            print(f"[DEBUG] Cropping Open Shifts row (dynamic): y1={open_shifts_y1}, y2={open_shifts_y2}, height={proc_height}")
            open_shifts_row = proc_image[open_shifts_y1:open_shifts_y2, :]
        else:
            print("[DEBUG] OpenShifts label not found, falling back to static y-range.")
    if not found_openshifts:
        open_shifts_y1 = int(proc_height * 0.44)
        open_shifts_y2 = int(proc_height * 0.54)
        print(f"[DEBUG] Cropping Open Shifts row (static): y1={open_shifts_y1}, y2={open_shifts_y2}, height={proc_height}")
        open_shifts_row = proc_image[open_shifts_y1:open_shifts_y2, :]

    debug_open_shifts_row_path = image_path.replace('.png', '_open_shifts_row.png')
    cv2.imwrite(debug_open_shifts_row_path, open_shifts_row)

    hsv = cv2.cvtColor(open_shifts_row, cv2.COLOR_BGR2HSV)
    lower_orange = np.array([10, 100, 150])
    upper_orange = np.array([25, 255, 255])
    mask = cv2.inRange(hsv, lower_orange, upper_orange)
    debug_mask_path = image_path.replace('.png', '_open_shifts_mask.png')
    cv2.imwrite(debug_mask_path, mask)

    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    debug_mask_clean_path = image_path.replace('.png', '_open_shifts_mask_clean.png')
    cv2.imwrite(debug_mask_clean_path, mask)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    print(f"[DEBUG] Found {len(contours)} orange contours in open shifts row.")

    open_date_map = {}
    open_box_coords = []  # Store the coordinates for each open shift box
    import re
    for i, cnt in enumerate(contours):
        x, y, w, h = cv2.boundingRect(cnt)
        print(f"[DEBUG] Contour {i}: x={x}, y={y}, w={w}, h={h}")
        if w < 5 or h < 10:
            print(f"[DEBUG] Skipping contour {i} due to size filter.")
            continue
        abs_x = x
        abs_y = y + open_shifts_y1
        ocr_crop_x1 = abs_x
        ocr_crop_x2 = min(abs_x + 40, proc_width)
        ocr_crop_y2 = max(abs_y - 10, 0)
        ocr_crop_y1 = max(ocr_crop_y2 - 40, 0)
        ocr_crop_y1 = max(ocr_crop_y1 - 190, 0)
        ocr_crop_y2 = max(ocr_crop_y2 - 190, 0)
        open_box_coords.append((abs_x, abs_y, w, h, ocr_crop_x1, ocr_crop_x2, ocr_crop_y1, ocr_crop_y2))
        print(f"[DEBUG] OCR crop for contour {i}: x1={ocr_crop_x1}, x2={ocr_crop_x2}, y1={ocr_crop_y1}, y2={ocr_crop_y2}")
        ocr_crop = proc_image[ocr_crop_y1:ocr_crop_y2, ocr_crop_x1:ocr_crop_x2]
        debug_ocr_crop_path = image_path.replace('.png', f'_ocr_crop_{i}.png')
        cv2.imwrite(debug_ocr_crop_path, ocr_crop)
        if ocr_crop.shape[0] < 10 or ocr_crop.shape[1] < 5:
            print(f"[DEBUG] Skipping contour {i} due to small OCR crop.")
            continue
        ocr_text_orig = pytesseract.image_to_string(ocr_crop, config="--psm 6 digits").strip()
        print(f"[DEBUG] OCR (original) for contour {i}: '{ocr_text_orig}'")
        match = re.search(r'\b([0-9]{1,2})\b', ocr_text_orig)
        if not match:
            ocr_gray = cv2.cvtColor(ocr_crop, cv2.COLOR_BGR2GRAY)
            ocr_blur = cv2.GaussianBlur(ocr_gray, (3, 3), 0)
            ocr_adapt = cv2.adaptiveThreshold(ocr_blur, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 15, 10)
            kernel = np.ones((2, 2), np.uint8)
            ocr_adapt = cv2.dilate(ocr_adapt, kernel, iterations=1)
            debug_ocr_preproc_path = image_path.replace('.png', f'_ocr_crop_{i}_preproc.png')
            cv2.imwrite(debug_ocr_preproc_path, ocr_adapt)
            ocr_text = pytesseract.image_to_string(ocr_adapt, config="--psm 6 digits").strip()
            print(f"[DEBUG] OCR (preproc) for contour {i}: '{ocr_text}'")
            match = re.search(r'\b([0-9]{1,2})\b', ocr_text)
        if match:
            day = int(match.group(1))
            date_str = f"{year_num}-{month_num:02d}-{day:02d}"
            open_date_map[date_str] = 'open'
            cv2.rectangle(debug_img, (abs_x, abs_y), (abs_x + w, abs_y + h), (0, 165, 255), 2)
            cv2.putText(debug_img, f"{day}", (abs_x, abs_y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)
        else:
            print(f"[DEBUG] No valid day found for contour {i} (OCR orig='{ocr_text_orig}').")

    # --- Detect booked shifts (orange, offset row, use open shift date coordinates) ---
    booked_shifts_y1 = open_shifts_y1 + 100
    booked_shifts_y2 = open_shifts_y2 + 100
    booked_shifts_y1 = max(0, booked_shifts_y1)
    booked_shifts_y2 = min(proc_image.shape[0], booked_shifts_y2)
    print(f"[DEBUG] Cropping Booked Shifts row (offset): y1={booked_shifts_y1}, y2={booked_shifts_y2}, height={proc_height}")
    booked_shifts_row = proc_image[booked_shifts_y1:booked_shifts_y2, :]

    debug_booked_shifts_row_path = image_path.replace('.png', '_booked_shifts_row.png')
    cv2.imwrite(debug_booked_shifts_row_path, booked_shifts_row)

    hsv_b = cv2.cvtColor(booked_shifts_row, cv2.COLOR_BGR2HSV)
    mask_b = cv2.inRange(hsv_b, lower_orange, upper_orange)
    debug_mask_b_path = image_path.replace('.png', '_booked_shifts_mask.png')
    cv2.imwrite(debug_mask_b_path, mask_b)

    mask_b = cv2.morphologyEx(mask_b, cv2.MORPH_OPEN, kernel)
    mask_b = cv2.morphologyEx(mask_b, cv2.MORPH_CLOSE, kernel)
    debug_mask_b_clean_path = image_path.replace('.png', '_booked_shifts_mask_clean.png')
    cv2.imwrite(debug_mask_b_clean_path, mask_b)

    contours_b, _ = cv2.findContours(mask_b, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    print(f"[DEBUG] Found {len(contours_b)} orange contours in booked shifts row.")

    booked_date_map = {}
    # For each booked shift contour, find the closest open shift box by (x, w) proximity
    # Robust matching: only match if x-center is within threshold, log all matches
    BOOKED_MATCH_X_THRESH = 120  # pixels, increased for more robust matching
    for i, cnt in enumerate(contours_b):
        bx, by, bw, bh = cv2.boundingRect(cnt)
        bx_center = bx + bw // 2
        # Find the open shift box with closest x-center
        min_dist = float('inf')
        best_idx = None
        for j, (ox, oy, ow, oh, ocr_crop_x1, ocr_crop_x2, ocr_crop_y1, ocr_crop_y2) in enumerate(open_box_coords):
            ox_center = ox + ow // 2
            dist = abs(bx_center - ox_center)
            if dist < min_dist:
                min_dist = dist
                best_idx = j
        if best_idx is not None and min_dist <= BOOKED_MATCH_X_THRESH:
            ox, oy, ow, oh, ocr_crop_x1, ocr_crop_x2, ocr_crop_y1, ocr_crop_y2 = open_box_coords[best_idx]
            abs_x, abs_y, w, h = bx, by + booked_shifts_y1, bw, bh
            print(f"[DEBUG] Booked contour {i} x-center={bx_center} matched open box {best_idx} x-center={ox + ow // 2} (dist={min_dist})")
            # The date crop is from the open shift row, not the booked row
            ocr_crop = proc_image[ocr_crop_y1:ocr_crop_y2, ocr_crop_x1:ocr_crop_x2]
        else:
            # No open shift box matched: use the same x as the booked box, and the same y-crop logic as open shifts
            abs_x, abs_y, w, h = bx, by + booked_shifts_y1, bw, bh
            print(f"[DEBUG] Booked contour {i} x-center={bx_center} did not match any open shift box within threshold (min_dist={min_dist}). Using booked box x for OCR.")
            # Use the same crop logic as open shifts, but at this x
            ocr_crop_x1 = abs_x
            ocr_crop_x2 = min(abs_x + 40, proc_width)
            # Use the same y-crop as open shifts (relative to open_shifts_y1/y2)
            ocr_crop_y2 = max(abs_y - 100 - 10, 0)  # shift up by 100px to align with open row
            ocr_crop_y1 = max(ocr_crop_y2 - 40, 0)
            ocr_crop_y1 = max(ocr_crop_y1 - 190, 0)
            ocr_crop_y2 = max(ocr_crop_y2 - 190, 0)
            ocr_crop = proc_image[ocr_crop_y1:ocr_crop_y2, ocr_crop_x1:ocr_crop_x2]
        debug_ocr_crop_path = image_path.replace('.png', f'_ocr_crop_booked_{i}.png')
        cv2.imwrite(debug_ocr_crop_path, ocr_crop)
        if ocr_crop.shape[0] < 10 or ocr_crop.shape[1] < 5:
            print(f"[DEBUG] Skipping booked contour {i} due to small OCR crop.")
            continue
        ocr_text_orig = pytesseract.image_to_string(ocr_crop, config="--psm 6 digits").strip()
        print(f"[DEBUG] OCR (original) for booked contour {i}: '{ocr_text_orig}'")
        match = re.search(r'\b([0-9]{1,2})\b', ocr_text_orig)
        if not match:
            ocr_gray = cv2.cvtColor(ocr_crop, cv2.COLOR_BGR2GRAY)
            ocr_blur = cv2.GaussianBlur(ocr_gray, (3, 3), 0)
            ocr_adapt = cv2.adaptiveThreshold(ocr_blur, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 15, 10)
            kernel = np.ones((2, 2), np.uint8)
            ocr_adapt = cv2.dilate(ocr_adapt, kernel, iterations=1)
            debug_ocr_preproc_path = image_path.replace('.png', f'_ocr_crop_booked_{i}_preproc.png')
            cv2.imwrite(debug_ocr_preproc_path, ocr_adapt)
            ocr_text = pytesseract.image_to_string(ocr_adapt, config="--psm 6 digits").strip()
            print(f"[DEBUG] OCR (preproc) for booked contour {i}: '{ocr_text}'")
            match = re.search(r'\b([0-9]{1,2})\b', ocr_text)
        if match:
            day = int(match.group(1))
            date_str = f"{year_num}-{month_num:02d}-{day:02d}"
            booked_date_map[date_str] = 'booked'
            cv2.rectangle(debug_img, (abs_x, abs_y), (abs_x + w, abs_y + h), (0, 255, 0), 2)
            cv2.putText(debug_img, f"{day}", (abs_x, abs_y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        else:
            print(f"[DEBUG] No valid day found for booked contour {i} (OCR orig='{ocr_text_orig}').")

    # --- Merge results: booked takes precedence over open ---
    date_map = open_date_map.copy()
    date_map.update(booked_date_map)

    debug_path = image_path.replace('.png', '_dates_debug.png')
    cv2.imwrite(debug_path, debug_img)

    return date_map
