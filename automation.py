# --- WhatsApp Automation ---

def send_whatsapp_message(group_name, shift_dates):
    """
    Brings WhatsApp Desktop to the front and sends a message with new shift info directly to the open chat window.
    Assumes WhatsApp is already open and the correct chat is selected.
    shift_dates: List of date strings (YYYY-MM-DD) to include in the message.
    Returns True if sent, False otherwise.
    """
    import time
    try:
        from pywinauto import Desktop
        import pyautogui
    except ImportError as e:
        _whatsapp_log(f"Required automation packages not installed: {e}")
        return False

    # 1. Focus WhatsApp window
    try:
        windows = Desktop(backend="uia").windows()
        wa_windows = [w for w in windows if w.is_visible() and 'whatsapp' in w.window_text().lower()]
        if not wa_windows:
            _whatsapp_log("WhatsApp Desktop window not found.")
            return False
        wa_win = wa_windows[0]
        wa_win.set_focus()
        _whatsapp_log(f"Focused WhatsApp window: {wa_win.window_text()}")
        time.sleep(0.7)
    except Exception as e:
        _whatsapp_log(f"Could not focus WhatsApp window: {e}")
        return False

    # 2. Use image recognition to find the WhatsApp input box and click 100px to the right
    try:
        import pyautogui
        import os
        template_path = os.path.join(os.path.dirname(__file__), 'whatsapp.png')
        match = find_and_click_template(template_path, confidence=0.85, pause=0.2)
        if match is None:
            _whatsapp_log(f"Could not find WhatsApp input box using template: {template_path}")
            return False
        # Click 100 pixels to the right of the match
        x, y = match
        pyautogui.moveTo(x + 100, y, duration=0)
        pyautogui.click()
        time.sleep(0.2)
    except Exception as e:
        _whatsapp_log(f"Could not click message input using image recognition: {e}")
        return False

    # 3. Format and send the message
    try:
        if not shift_dates:
            _whatsapp_log("No shift dates to send.")
            return False
        msg = _format_whatsapp_shift_message(shift_dates)
        pyautogui.typewrite(msg, interval=0.01)
        pyautogui.press('enter')
        _whatsapp_log(f"Sent message to open chat window:\n{msg}")
        return True
    except Exception as e:
        _whatsapp_log(f"Could not send message: {e}")
        return False

# Helper for WhatsApp message formatting
def _format_whatsapp_shift_message(shift_dates):
    """
    Returns WhatsApp message string for new shifts, e.g.:
    'New Shifts matching your availability : Mon 9th June\nTue 10th June'
    """
    from datetime import datetime
    def day_suffix(day):
        if 11 <= day <= 13:
            return 'th'
        return {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')
    lines = []
    for date_str in shift_dates:
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            day = dt.day
            suffix = day_suffix(day)
            line = dt.strftime(f"%a {day}{suffix} %B")
        except Exception:
            line = date_str
        lines.append(line)
    # Compose a single-line message with colons/commas, only one return at the end
    if lines:
        msg = "New Shifts matching your availability: " + ", ".join(lines)
    else:
        msg = "New Shifts matching your availability: (none)"
    return msg
# Placeholder for automation logic using pyautogui/pywinauto

import logging
from datetime import datetime

# Configure logging for this module
class CustomFormatter(logging.Formatter):
    def format(self, record):
        now = datetime.now().strftime("[%d/%m %H:%M:%S]")
        record.msg = f"{now} {record.msg}"
        return super().format(record)

handler = logging.StreamHandler()
handler.setFormatter(CustomFormatter("%(message)s"))
logging.root.handlers = [handler]
logging.root.setLevel(logging.INFO)  # Changed from WARNING to INFO to show shift detection logs

def focus_teams_window():
    """
    Use pywinauto to bring Microsoft Teams window to foreground and maximize.
    Returns True if successful, False otherwise.
    """
    try:
        from pywinauto import Desktop
        import time
        # Enumerate all top-level windows and filter for Teams
        windows = Desktop(backend="uia").windows()
        teams_windows = []
        for win in windows:
            try:
                title = win.window_text()
                if not title:
                    continue
                title_lower = title.lower()
                # Accept any window with 'microsoft teams' anywhere in the title
                if "microsoft teams" in title_lower:
                    teams_windows.append(win)
            except Exception:
                continue
        # Prefer a window that is visible and not minimized
        for win in teams_windows:
            try:
                if win.is_visible() and win.get_show_state() != 2:  # 2 = minimized
                    win.set_focus()
                    logging.debug(f"Focused Teams window: {win.window_text()}")
                    time.sleep(0.7)
                    return True
            except Exception:
                continue
        # Fallback: try the first Teams window
        if teams_windows:
            win = teams_windows[0]
            win.set_focus()
            logging.debug(f"Focused first Teams window: {win.window_text()}")
            time.sleep(0.7)
            return True
        logging.warning("No suitable Teams window found.")
    except Exception as e:
        logging.error(f"pywinauto failed to focus Teams: {e}")
    return False


def capture_shifts_screen():
    """
    Takes a screenshot focused on the calendar area of the Teams Shifts app.
    Returns the path to the saved screenshot.
    """
    import pyautogui
    import datetime
    import time
    import os
    
    # Create screenshots directory if it doesn't exist
    screenshots_dir = "screenshots"
    if not os.path.exists(screenshots_dir):
        os.makedirs(screenshots_dir)

    # --- Clear screenshots directory on app start (only once) ---
    if not hasattr(capture_shifts_screen, "_screenshots_cleared"):
        for f in os.listdir(screenshots_dir):
            try:
                os.remove(os.path.join(screenshots_dir, f))
            except Exception as e:
                _automation_log(f"Could not delete {f}: {e}")
        capture_shifts_screen._screenshots_cleared = True

    # Give Teams window time to fully maximize and stabilize
    time.sleep(0.5)

    # Generate a unique filename based on timestamp and scan index if present
    scan_index = getattr(capture_shifts_screen, "_scan_index", None)
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    if scan_index is not None:
        screenshot_prefix = f"{scan_index}-"
    else:
        screenshot_prefix = ""
    screenshot_path = os.path.join(screenshots_dir, f"{screenshot_prefix}shifts_screenshot_{timestamp}.png")

    # Get screen dimensions
    screen_width, screen_height = pyautogui.size()
    # Teams shifts typically displays calendar in the main content area
    # Capture the entire screen except for the bottom 100 pixels
    calendar_region = {
        'left': 0,
        'top': 0,
        'width': screen_width,
        'height': screen_height - 100  # trim only the bottom 100 pixels
    }

    logging.debug(f"Capturing region: {calendar_region}")

    region_tuple = (
        calendar_region['left'],
        calendar_region['top'],
        calendar_region['width'],
        calendar_region['height']
    )

    try:
        calendar_screenshot = pyautogui.screenshot(region=region_tuple)
        calendar_screenshot.save(screenshot_path)
        logging.debug(f"Captured Teams calendar screenshot: {screenshot_path}")
        return screenshot_path
    except Exception as e:
        logging.error(f"Error capturing screenshot: {e}")
        # Fallback to full screen capture
        try:
            full_screenshot = pyautogui.screenshot()
            full_screenshot.save(screenshot_path)
            logging.debug(f"Fell back to full screenshot: {screenshot_path}")
            return screenshot_path
        except Exception as e2:
            logging.error(f"Failed to capture even a full screenshot: {e2}")
            return None


def find_and_click_template(template_path, screenshot=None, confidence=0.9, pause=0.25):
    """
    Finds the template on the screen (or given screenshot), clicks the center of the match.
    Returns (x, y) of the click, or None if not found.
    """
    import cv2
    import numpy as np
    import pyautogui
    import time

    try:
        if screenshot is None:
            screenshot = pyautogui.screenshot()
            screenshot = np.array(screenshot)
            screenshot = cv2.cvtColor(screenshot, cv2.COLOR_RGB2BGR)
        else:
            screenshot = cv2.imread(screenshot)
            if screenshot is None:
                _automation_log(f"Could not load screenshot for template matching: {screenshot}")
                return None

        template = cv2.imread(template_path, cv2.IMREAD_UNCHANGED)
        if template is None:
            _automation_log(f"Could not load template image: {template_path}")
            return None

        # If template has alpha channel, remove it
        if template.shape[2] == 4:
            template = cv2.cvtColor(template, cv2.COLOR_BGRA2BGR)
        # If screenshot has alpha channel, remove it (shouldn't, but just in case)
        if screenshot.shape[2] == 4:
            screenshot = cv2.cvtColor(screenshot, cv2.COLOR_BGRA2BGR)

        # Now both should be BGR (3 channels)
        if template.shape[2] != 3 or screenshot.shape[2] != 3:
            _automation_log(f"Channel mismatch after conversion: template {template.shape}, screenshot {screenshot.shape}")
            return None

        res = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        logging.debug(f"Template match for {template_path}: max_val={max_val:.3f}")
        if max_val < confidence:
            logging.debug(f"Template {template_path} not found with confidence {confidence}")
            return None

        t_h, t_w = template.shape[:2]
        center_x = max_loc[0] + t_w // 2
        center_y = max_loc[1] + t_h // 2
        
        # Move mouse and click with more deliberate timing
        pyautogui.moveTo(center_x, center_y, duration=0)  # Instantly jump to position
        pyautogui.click()
        logging.debug(f"Clicked at ({center_x}, {center_y}) for template {template_path}")
        time.sleep(pause)  # Pause after click for Teams to respond
        return (center_x, center_y)
        
    except Exception as e:
        logging.error(f"Error in template matching for {template_path}: {e}")
        return None


def scan_four_months_with_automation(ocr_func, year, month):
    """
    Full workflow: click Today, scan, click right arrow, scan, repeat for four months.
    ocr_func: function to call for OCR, e.g. extract_shifts_from_image(image_path, year, month)
    """
    import time
    from datetime import datetime
    import calendar

    # Step 1: Focus Teams window
    if not focus_teams_window():
        _automation_log("Could not focus Teams window. Aborting scan.")
        return

    # Step 2: Click Today button to ensure we start from current month
    if not find_and_click_template('today.png', confidence=0.9, pause=0.2):
        _automation_log("Could not find/click Today button. Aborting scan.")
        return

    # Give Teams more time to stabilize after Today click
    time.sleep(0.5)

    # Step 3: Scan current and next 3 months
    for i in range(4):
        scan_year = year
        scan_month = month + i
        # Handle year rollover
        while scan_month > 12:
            scan_month -= 12
            scan_year += 1

        _automation_log(f"Starting scan {i+1}/4 for {calendar.month_name[scan_month]} {scan_year}")

        # Set scan index for image prefixing
        capture_shifts_screen._scan_index = i

        # Wait for UI to stabilize before screenshot
        time.sleep(0.3)

        screenshot_path = capture_shifts_screen()
        # Remove scan index after use to avoid affecting other calls
        del capture_shifts_screen._scan_index

        if screenshot_path:
            # OCR the month label from the screenshot to confirm actual month/year
            from ocr_processing import extract_month_year_from_image
            ocr_month, ocr_year = extract_month_year_from_image(screenshot_path)
            if ocr_month and ocr_year:
                if ocr_month != scan_month or ocr_year != scan_year:
                    _automation_log(f"[WARNING] Expected {calendar.month_name[scan_month]} {scan_year} but OCR found {calendar.month_name[ocr_month]} {ocr_year}. Using OCR result.")
                scan_month, scan_year = ocr_month, ocr_year
            else:
                _automation_log("[WARNING] Could not OCR month/year from screenshot. Using expected values.")
            _automation_log(f"Scanning {calendar.month_name[scan_month]} {scan_year}")
            try:
                ocr_func(screenshot_path, scan_year, scan_month)
            except Exception as e:
                _automation_log(f"OCR processing failed for {calendar.month_name[scan_month]} {scan_year}: {e}")
                # Continue with next month even if this one fails
        else:
            _automation_log(f"Failed to capture screenshot for {calendar.month_name[scan_month]} {scan_year}")

        # Click right arrow to go to next month, except after last month
        if i < 3:
            _automation_log(f"Navigating to next month ({i+2}/4)...")
            # Wait a bit before clicking arrow to ensure Teams is ready
            time.sleep(0.2)
            if not find_and_click_right_arrow():
                _automation_log("Could not find/click right arrow. Stopping scan early.")
                break
            # Wait after clicking arrow for Teams to load the next month
            time.sleep(0.5)

    # Step 4: Return to current month by clicking Today again
    _automation_log("Returning to current month by clicking Today button...")
    time.sleep(0.2)  # Wait before final Today click
    if not find_and_click_template('today.png', confidence=0.9, pause=0.2):
        _automation_log("Could not find/click Today button at end of scan.")
    else:
        # Give Teams time to return to current month
        time.sleep(0.5)
    
    _automation_log("Completed scan for four months and returned to current month.")

# Helper for right arrow click
def find_and_click_right_arrow():
    return find_and_click_template('arrow.png', confidence=0.85, pause=0.5)

def _automation_log(msg):
    now = datetime.now().strftime("[%d/%m %H:%M:%S]")
    print(f"{now} {msg}")

# WhatsApp log helper

def _whatsapp_log(msg):
    now = datetime.now().strftime("[%d/%m %H:%M:%S]")
    print(f"{now} {msg}")
