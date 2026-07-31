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

# Configure logging for this module only - use a named logger to avoid
# wiping handlers (like RotatingFileHandler) registered by other modules
class CustomFormatter(logging.Formatter):
    def format(self, record):
        now = datetime.now().strftime("[%d/%m %H:%M:%S]")
        record.msg = f"{now} {record.msg}"
        return super().format(record)

_auto_handler = logging.StreamHandler()
_auto_handler.setFormatter(CustomFormatter("%(message)s"))
_auto_logger = logging.getLogger('automation')
if not _auto_logger.handlers:
    _auto_logger.addHandler(_auto_handler)
_auto_logger.setLevel(logging.INFO)
_auto_logger.propagate = False

def _teams_windows():
    from pywinauto import Desktop

    windows = []
    for win in Desktop(backend="uia").windows():
        try:
            title = win.window_text()
            if title and "microsoft teams" in title.lower():
                windows.append(win)
        except Exception:
            continue
    return windows


def get_teams_window():
    """Return the first visible Teams window, or None."""
    teams_windows = _teams_windows()
    for win in teams_windows:
        try:
            if win.is_visible() and win.get_show_state() != 2:  # 2 = minimized
                return win
        except Exception:
            continue
    return teams_windows[0] if teams_windows else None


# Production geometry: full width, short height.
# ~0.65 leaves room for up to 3 open-shift rows above the personal row
# (extra rows appear when multiple open shifts fall on the same day),
# plus a small margin so the personal row is not clipped by the taskbar.
TEAMS_SCAN_HEIGHT_RATIO = 0.65


def configure_teams_window(height_ratio=None):
    """
    Restore Teams to the production scan geometry:
    full screen width x short height at the top of the display.
    """
    import time
    import pyautogui

    if height_ratio is None:
        height_ratio = TEAMS_SCAN_HEIGHT_RATIO

    try:
        import win32con
        import win32gui
    except ImportError as e:
        logging.error(f"pywin32 is required to size the Teams window: {e}")
        return False

    win = get_teams_window()
    if not win:
        logging.warning("No suitable Teams window found.")
        return False

    try:
        sw, sh = pyautogui.size()
        target_h = max(360, int(sh * height_ratio))
        hwnd = win.handle
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        win32gui.MoveWindow(hwnd, 0, 0, sw, target_h, True)
        win32gui.SetWindowPos(
            hwnd,
            win32con.HWND_TOP,
            0,
            0,
            sw,
            target_h,
            win32con.SWP_SHOWWINDOW,
        )
        try:
            win.set_focus()
        except Exception:
            pass
        time.sleep(0.8)
        return True
    except Exception as e:
        logging.error(f"Failed to size Teams window: {e}")
        return False


def maximize_teams_window():
    """Maximize Teams temporarily so left-rail app icons are fully visible."""
    import time

    win = get_teams_window()
    if not win:
        logging.warning("No suitable Teams window found.")
        return False
    try:
        try:
            win.maximize()
        except Exception:
            import win32con
            import win32gui

            win32gui.ShowWindow(win.handle, win32con.SW_MAXIMIZE)
        try:
            win.set_focus()
        except Exception:
            pass
        time.sleep(1.0)
        return True
    except Exception as e:
        logging.error(f"Failed to maximize Teams window: {e}")
        return False


def focus_teams_window():
    """
    Bring Microsoft Teams to the foreground in the production scan geometry
    (full width, short height). Returns True if successful.
    """
    if configure_teams_window():
        win = get_teams_window()
        if win:
            logging.debug(f"Focused Teams window: {win.window_text()}")
            return True
    return False


def is_teams_shifts_page():
    win = get_teams_window()
    try:
        return bool(win and win.window_text().lower().startswith("shifts"))
    except Exception:
        return False


def ensure_shifts_month_view():
    """
    Force the Shifts calendar into Month view (single header row of day numbers).
    Returns True if Month view appears selected/visible.
    """
    import time
    import pyautogui
    import pytesseract
    from difflib import SequenceMatcher

    if not configure_teams_window():
        return False

    win = get_teams_window()
    if not win:
        return False

    rect = win.rectangle()
    region = (rect.left, rect.top, rect.width(), rect.height())
    img = pyautogui.screenshot(region=region)
    text = pytesseract.image_to_string(img).lower()

    # Already on a monthly calendar if the day strip and Month marker are present.
    if "month" in text and any(token in text for token in ("july", "august", "september", "october", "november", "december", "january", "february", "march", "april", "may", "june")):
        if "week" not in text or "month:" in text or "people scheduled" in text:
            # Click Today to anchor current month without changing view mode.
            find_and_click_template(
                __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "today.png"),
                confidence=0.5,
                pause=0.3,
            )
            time.sleep(1.0)
            return True

    def _ocr_click(target, x_min=1400, x_max=1900, y_min=80, y_max=320, min_score=0.7):
        shot = pyautogui.screenshot(region=region)
        data = pytesseract.image_to_data(shot, output_type=pytesseract.Output.DICT)
        candidates = []
        for i, raw in enumerate(data["text"]):
            cleaned = "".join(ch for ch in raw.strip().lower() if ch.isalpha())
            if not cleaned:
                continue
            score = SequenceMatcher(None, cleaned, target).ratio()
            left = data["left"][i]
            top = data["top"][i]
            if score >= min_score and x_min <= left <= x_max and y_min <= top <= y_max:
                candidates.append((score, left, top, data["width"][i], data["height"][i], cleaned))
        if not candidates:
            return False
        candidates.sort(reverse=True)
        _, left, top, width, height, cleaned = candidates[0]
        x = region[0] + left + width // 2
        y = region[1] + top + height // 2
        pyautogui.click(x, y)
        _automation_log(f"Clicked '{cleaned}' ({target}) at ({x}, {y}) while selecting Month view.")
        return True

    # Open the view mode dropdown (often labelled Week/Month) then choose Month.
    if not _ocr_click("week", y_min=90, y_max=160) and not _ocr_click("month", y_min=90, y_max=160):
        # Fallback hard coords near the known control on 1920-wide layouts.
        pyautogui.click(region[0] + 1625, region[1] + 130)
    time.sleep(1.0)
    if not _ocr_click("month", y_min=150, y_max=320, min_score=0.65):
        pyautogui.click(region[0] + 1610, region[1] + 270)
    time.sleep(1.5)

    find_and_click_template(
        __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "today.png"),
        confidence=0.5,
        pause=0.3,
    )
    time.sleep(1.0)

    win = get_teams_window()
    if not win:
        return False
    rect = win.rectangle()
    final_text = pytesseract.image_to_string(
        pyautogui.screenshot(region=(rect.left, rect.top, rect.width(), rect.height()))
    ).lower()
    ok = "month" in final_text and ("people scheduled" in final_text or "open shifts" in final_text)
    if not ok:
        _automation_log("Month view confirmation failed after selection attempt.")
    return ok


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

    # Keep Teams in the production short monthly layout before capture.
    configure_teams_window()
    time.sleep(1.0)

    # Generate a unique filename based on timestamp and scan index if present
    scan_index = getattr(capture_shifts_screen, "_scan_index", None)
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    if scan_index is not None:
        screenshot_prefix = f"{scan_index}-"
    else:
        screenshot_prefix = ""
    screenshot_path = os.path.join(screenshots_dir, f"{screenshot_prefix}shifts_screenshot_{timestamp}.png")

    # Capture the production Teams window region when available.
    win = get_teams_window()
    if win is not None:
        rect = win.rectangle()
        region_tuple = (rect.left, rect.top, rect.width(), rect.height())
    else:
        screen_width, screen_height = pyautogui.size()
        region_tuple = (0, 0, screen_width, max(320, screen_height // 3))

    logging.debug(f"Capturing region: {region_tuple}")

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


def navigate_to_shifts(prepare_monthly_view=True):
    """
    Navigate Teams to the Shifts app and optionally restore the production
    single-row monthly view (full width, ~1/3 height + Today).
    """
    from difflib import SequenceMatcher
    import os
    import time
    import pyautogui
    import pytesseract

    if not maximize_teams_window():
        _automation_log("Could not focus/maximize Teams while navigating to Shifts.")
        return False

    pyautogui.press("esc")
    time.sleep(0.4)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    shifts_unselected_path = os.path.join(base_dir, "shifts_unselected.png")
    shifts_selected_path = os.path.join(base_dir, "shifts_selected.png")
    dots_path = os.path.join(base_dir, "dots.png")
    away_icon_path = os.path.join(base_dir, "away_icon.png")
    today_path = os.path.join(base_dir, "today.png")

    clicked = find_and_click_template(shifts_unselected_path, confidence=0.85, pause=0.5)
    if not clicked:
        clicked = find_and_click_template(shifts_selected_path, confidence=0.85, pause=0.5)

    if not clicked:
        # Fall back: open Calendar rail / More apps and OCR-select Shifts.
        if not find_and_click_template(away_icon_path, confidence=0.8, pause=0.5):
            _automation_log("Pinned Shifts icon and away/calendar fallback both unavailable.")
        time.sleep(2)
        maximize_teams_window()
        if find_and_click_template(dots_path, confidence=0.85, pause=0.5):
            time.sleep(1.2)
            data = pytesseract.image_to_data(
                pyautogui.screenshot(), output_type=pytesseract.Output.DICT
            )
            candidates = []
            for index, text in enumerate(data["text"]):
                cleaned = "".join(ch for ch in text.strip().lower() if ch.isalpha())
                if not cleaned:
                    continue
                score = SequenceMatcher(None, cleaned, "shifts").ratio()
                left = data["left"][index]
                top = data["top"][index]
                if score >= 0.55 and 40 <= left <= 300 and 40 <= top <= 1000:
                    candidates.append(
                        (
                            score,
                            cleaned,
                            left,
                            top,
                            data["width"][index],
                            data["height"][index],
                        )
                    )
            if candidates:
                candidates.sort(reverse=True)
                _, text, left, top, width, height = candidates[0]
                x = left + width // 2
                y = top + height // 2
                pyautogui.click(x, y)
                _automation_log(f"Selected Shifts from More apps menu at ({x}, {y}) via '{text}'.")
                clicked = True

    if not clicked:
        _automation_log("Could not navigate Teams to Shifts.")
        return False

    time.sleep(8)
    if not is_teams_shifts_page():
        _automation_log("Teams did not land on the Shifts page after navigation.")
        return False

    if prepare_monthly_view:
        if not configure_teams_window():
            _automation_log("Reached Shifts but failed to restore the production window size.")
            return False
        if not ensure_shifts_month_view():
            _automation_log("Reached Shifts but could not lock Month view.")
            # Still return True if we are on Shifts; scan may recover via Today.
            return is_teams_shifts_page()

    return is_teams_shifts_page()


def refresh_teams_shifts_view():
    """
    Force-refresh Teams Shifts and restore production monthly single-row view.
    Returns True on success.
    """
    import os
    import time
    import pyautogui

    # Navigate away then back to force a full Shifts reload.
    if not maximize_teams_window():
        return False

    away_icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "away_icon.png")

    pyautogui.press("esc")
    time.sleep(0.3)
    # Click a non-Shifts rail icon when available so the later Shifts click reloads the app.
    find_and_click_template(away_icon_path, confidence=0.8, pause=0.5)
    time.sleep(2)

    if not navigate_to_shifts(prepare_monthly_view=True):
        return False

    # Extra hard refresh once we know we are on Shifts at production size.
    if not focus_teams_window():
        return False
    pyautogui.hotkey("ctrl", "r")
    _automation_log("Sent Ctrl+R to refresh Teams Shifts.")
    time.sleep(20)

    if not navigate_to_shifts(prepare_monthly_view=True):
        return False
    return is_teams_shifts_page() and ensure_shifts_month_view()


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

    # Max seconds to wait for a single screenshot capture before giving up on that month
    SCREENSHOT_TIMEOUT = 45

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

        # Run screenshot in a thread with a timeout so a hung Teams can't block forever
        import threading
        _result = [None]
        def _take_screenshot():
            _result[0] = capture_shifts_screen()
        _t = threading.Thread(target=_take_screenshot, daemon=True)
        _t.start()
        _t.join(timeout=SCREENSHOT_TIMEOUT)

        if hasattr(capture_shifts_screen, "_scan_index"):
            del capture_shifts_screen._scan_index

        if _t.is_alive():
            _automation_log(f"[TIMEOUT] Screenshot timed out after {SCREENSHOT_TIMEOUT}s for {calendar.month_name[scan_month]} {scan_year} � skipping month.")
            if i < 3:
                # Try to advance to the next month anyway
                time.sleep(0.2)
                if not find_and_click_right_arrow():
                    _automation_log("Could not navigate past stuck month. Stopping scan early.")
                    break
                time.sleep(1.5)
            continue

        screenshot_path = _result[0]

        if screenshot_path:
            # OCR the month label from the screenshot to confirm actual month/year
            from ocr_processing import extract_month_year_from_image
            ocr_month, ocr_year = extract_month_year_from_image(screenshot_path)
            if ocr_month and ocr_year:
                if ocr_month != scan_month or ocr_year != scan_year:
                    warning_msg = f"[WARNING] Expected {calendar.month_name[scan_month]} {scan_year} but OCR found {calendar.month_name[ocr_month]} {ocr_year}. Using OCR result."
                    _automation_log(warning_msg)
                    
                    # Send warning email about navigation failure
                    try:
                        from email_alert import send_email_alert
                        subject = "Teams Shift Scanner: Month Navigation Warning"
                        body = f"""Teams Shift Scanner detected a navigation issue:

Expected to be on: {calendar.month_name[scan_month]} {scan_year}
Actually found: {calendar.month_name[ocr_month]} {ocr_year}

This usually indicates:
- Teams may have logged you out
- Navigation between months failed
- App may need refreshing

Please check Teams is still logged in and working properly.

Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
                        
                        send_email_alert(subject, body, "russfray74@gmail.com")
                        _automation_log("[EMAIL] Navigation warning email sent")
                    except Exception as e:
                        _automation_log(f"[EMAIL] Failed to send navigation warning email: {e}")
                
                scan_month, scan_year = ocr_month, ocr_year
            else:
                # OCR could not read the month label (low contrast, Teams still loading, etc.).
                # The midnight race is already blocked by _midnight_reset_in_progress in gui.py,
                # so skipping here would break every normal scan.  Log a warning and proceed
                # with the expected month value instead.
                _automation_log(
                    f"[WARNING] Could not OCR month/year from screenshot for expected "
                    f"{calendar.month_name[scan_month]} {scan_year}. "
                    f"Proceeding with expected month (midnight guard already prevents scans during reset)."
                )
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
            time.sleep(1.5)  # Increased delay for month navigation

    # Step 4: Return to current month by clicking Today again
    _automation_log("Returning to current month by clicking Today button...")
    time.sleep(1.0)  # Wait before final Today click - increased for stability
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
