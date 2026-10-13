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


def get_teams_window(include_minimized=True):
    """Return the best Teams window, preferring a visible Shifts app window."""
    teams_windows = _teams_windows()
    visible = []
    minimized = []
    for win in teams_windows:
        try:
            minimized_state = win.get_show_state() == 2  # 2 = minimized
            if win.is_visible() and not minimized_state:
                visible.append(win)
            elif minimized_state or include_minimized:
                minimized.append(win)
        except Exception:
            continue
    if not visible and include_minimized:
        visible = minimized
    if not visible:
        return teams_windows[0] if teams_windows else None

    def _score(win):
        try:
            title = (win.window_text() or "").lower()
        except Exception:
            title = ""
        score = 0
        if title.startswith("shifts"):
            score += 100
        if "shifts" in title:
            score += 50
        if title.startswith("calendar"):
            score -= 20
        # Prefer larger/production-like windows over tiny helper HWNDs.
        try:
            rect = win.rectangle()
            area = max(0, rect.width()) * max(0, rect.height())
            score += min(area // 50000, 20)
        except Exception:
            pass
        return score

    visible.sort(key=_score, reverse=True)
    return visible[0]


# Production geometry: full width, stacked on the Windows work area.
# ~0.62 keeps Teams calendar rows visible and leaves a usable monitor strip
# that meets Teams with no wallpaper gap.
TEAMS_SCAN_HEIGHT_RATIO = 0.62


def _launch_teams():
    """Start Microsoft Teams if it is closed. Returns True if a launch was attempted."""
    import os
    import time
    import subprocess

    candidates = [
        os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WindowsApps\ms-teams.exe"),
        os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WindowsApps\MicrosoftTeams.exe"),
        r"C:\Program Files\WindowsApps\MSTeams_8wekyb3d8bbwe\ms-teams.exe",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                subprocess.Popen([path], shell=False)
                _automation_log(f"Launched Microsoft Teams from {path}.")
                time.sleep(6)
                return True
            except Exception as exc:
                _automation_log(f"Failed to launch Teams from {path}: {exc}")
    try:
        os.startfile("ms-teams:")
        _automation_log("Launched Microsoft Teams via ms-teams: protocol.")
        time.sleep(6)
        return True
    except Exception as exc:
        _automation_log(f"Failed to launch Teams via protocol: {exc}")
        return False


def ensure_teams_available(max_launch_attempts=2):
    """Restore a minimized Teams window, or launch Teams if it is not running."""
    import time

    try:
        import win32con
        import win32gui
    except ImportError:
        win32con = win32gui = None

    for attempt in range(1, max_launch_attempts + 1):
        win = get_teams_window(include_minimized=True)
        if win is None:
            _automation_log(f"Teams window not found (attempt {attempt}/{max_launch_attempts}); launching.")
            _launch_teams()
            time.sleep(2)
            continue
        try:
            hwnd = win.handle
            if win32gui is not None:
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
                try:
                    win32gui.SetForegroundWindow(hwnd)
                except Exception:
                    pass
            try:
                win.restore()
            except Exception:
                pass
            try:
                win.set_focus()
            except Exception:
                pass
            _automation_log("Restored Microsoft Teams to a visible window.")
            return True
        except Exception as exc:
            _automation_log(f"Could not restore Teams window: {exc}")
            time.sleep(1)
    return get_teams_window(include_minimized=True) is not None


def restart_teams_app(wait_after_kill=3.0):
    """Hard-restart Teams and wait for a window to become available."""
    import subprocess
    import time

    process_names = ("ms-teams.exe", "msteams.exe", "teams.exe", "Microsoft.Teams.exe")
    for proc in process_names:
        try:
            subprocess.run(
                ["taskkill", "/IM", proc, "/F"],
                capture_output=True,
                text=True,
                timeout=10,
            )
        except Exception as exc:
            _automation_log(f"Failed to stop {proc}: {exc}")

    time.sleep(max(0.5, wait_after_kill))
    if not _launch_teams():
        _automation_log("Could not relaunch Teams after restart.")
        return False

    time.sleep(2.0)
    return ensure_teams_available(max_launch_attempts=3)


def recover_from_teams_error_page():
    """Recover when Teams shows 'There was a problem reaching this app'."""
    import time

    text = _ocr_text_for_region(_teams_region())
    compact = " ".join((text or "").split())
    has_problem_marker = ("problem reaching this app" in compact) or ("problem reaching" in compact and "app" in compact)
    if not has_problem_marker:
        return False

    _automation_log("Detected Teams app error page during scan. Trying Retry button first.")

    retry_hit = _ocr_find_token("retry", region=_teams_region(), min_score=0.70)
    if retry_hit:
        rx, ry, _, _ = retry_hit
        _click_xy(rx, ry, pause=0.4)
        time.sleep(3.0)
        dismiss_shifts_popups(max_rounds=2)
        loaded, signals = wait_for_shifts_content(timeout_seconds=12, poll_seconds=1.0)
        if loaded or signals.get("shifts_chrome") or signals.get("title_shifts"):
            _automation_log("Teams recovered after clicking Retry.")
            return True

    _automation_log("Retry button recovery failed. Restarting Teams and re-opening Shifts.")
    if not restart_teams_app():
        _automation_log("Teams restart failed during error-page recovery.")
        return False

    if not navigate_to_shifts(prepare_monthly_view=True):
        _automation_log("Teams reopened, but Shifts navigation failed after restart.")
        return False

    _automation_log("Teams recovered via restart + Shifts re-open.")
    return True


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

    if not ensure_teams_available():
        logging.warning("No suitable Teams window found.")
        return False

    win = get_teams_window(include_minimized=True)
    if not win:
        logging.warning("No suitable Teams window found.")
        return False

    try:
        try:
            from gui import _work_area_split

            split = _work_area_split()
            x, y = split["left"], split["top"]
            sw, target_h = split["width"], split["teams_h"]
        except Exception:
            sw, sh = pyautogui.size()
            target_h = max(360, int(sh * (height_ratio or TEAMS_SCAN_HEIGHT_RATIO)))
            x, y = 0, 0
        hwnd = win.handle
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        win32gui.MoveWindow(hwnd, x, y, sw, target_h, True)
        win32gui.SetWindowPos(
            hwnd,
            win32con.HWND_TOP,
            x,
            y,
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


def _month_name_tokens():
    return (
        "january",
        "february",
        "march",
        "april",
        "may",
        "june",
        "july",
        "august",
        "september",
        "october",
        "november",
        "december",
    )


def _teams_region():
    """Return (left, top, width, height) for the active Teams window, or None."""
    win = get_teams_window()
    if not win:
        return None
    try:
        rect = win.rectangle()
        return (rect.left, rect.top, rect.width(), rect.height())
    except Exception:
        return None


def _template_match_point(template_path, confidence=0.72, region=None):
    """
    Locate a template on screen (or within an optional region) without clicking.
    Returns (x, y, score) in absolute screen coords, or None.
    """
    import os
    import cv2
    import numpy as np
    import pyautogui

    if not template_path or not os.path.exists(template_path):
        return None

    try:
        if region is None:
            shot = pyautogui.screenshot()
            offset_x = offset_y = 0
        else:
            left, top, width, height = region
            shot = pyautogui.screenshot(region=(left, top, width, height))
            offset_x, offset_y = left, top

        screenshot = cv2.cvtColor(np.array(shot), cv2.COLOR_RGB2BGR)
        template = cv2.imread(template_path, cv2.IMREAD_UNCHANGED)
        if template is None or screenshot is None:
            return None
        if len(template.shape) == 3 and template.shape[2] == 4:
            template = cv2.cvtColor(template, cv2.COLOR_BGRA2BGR)
        if screenshot.shape[0] < template.shape[0] or screenshot.shape[1] < template.shape[1]:
            return None

        result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        if max_val < confidence:
            return None
        t_h, t_w = template.shape[:2]
        return (
            offset_x + max_loc[0] + t_w // 2,
            offset_y + max_loc[1] + t_h // 2,
            float(max_val),
        )
    except Exception as exc:
        logging.debug("Template probe failed for %s: %s", template_path, exc)
        return None


def _ocr_text_for_region(region=None):
    """OCR lowercase text for a screen region or the full Teams window."""
    import pyautogui
    import pytesseract

    target = region or _teams_region()
    if target is None:
        shot = pyautogui.screenshot()
    else:
        left, top, width, height = target
        shot = pyautogui.screenshot(region=(left, top, width, height))
    try:
        return pytesseract.image_to_string(shot).lower()
    except Exception as exc:
        logging.debug("OCR region failed: %s", exc)
        return ""


def _ocr_find_token(target, region=None, min_score=0.65, x_min=None, x_max=None, y_min=None, y_max=None):
    """
    Find an OCR token near `target` inside region.
    Returns (abs_x, abs_y, cleaned, score) or None.
    """
    import pyautogui
    import pytesseract
    from difflib import SequenceMatcher

    target = (target or "").strip().lower()
    if not target:
        return None

    if region is None:
        region = _teams_region()
    if region is None:
        shot = pyautogui.screenshot()
        offset_x = offset_y = 0
        width, height = shot.size
        region = (0, 0, width, height)
    else:
        left, top, width, height = region
        shot = pyautogui.screenshot(region=(left, top, width, height))
        offset_x, offset_y = left, top

    if x_min is None:
        x_min = 0
    if x_max is None:
        x_max = width
    if y_min is None:
        y_min = 0
    if y_max is None:
        y_max = height

    try:
        data = pytesseract.image_to_data(shot, output_type=pytesseract.Output.DICT)
    except Exception as exc:
        logging.debug("OCR token scan failed: %s", exc)
        return None

    candidates = []
    for index, raw in enumerate(data.get("text", [])):
        cleaned = "".join(ch for ch in raw.strip().lower() if ch.isalpha())
        if not cleaned:
            continue
        score = SequenceMatcher(None, cleaned, target).ratio()
        left = data["left"][index]
        top = data["top"][index]
        token_w = data["width"][index]
        token_h = data["height"][index]
        if score >= min_score and x_min <= left <= x_max and y_min <= top <= y_max:
            candidates.append((score, left, top, token_w, token_h, cleaned))

    if not candidates:
        return None
    candidates.sort(reverse=True)
    score, left, top, token_w, token_h, cleaned = candidates[0]
    return (
        offset_x + left + token_w // 2,
        offset_y + top + token_h // 2,
        cleaned,
        score,
    )


def _click_xy(x, y, pause=0.35):
    import time
    import pyautogui

    pyautogui.click(int(x), int(y))
    time.sleep(pause)


def _asset_path(name):
    import os

    return os.path.join(os.path.dirname(os.path.abspath(__file__)), name)


def shifts_content_signals(region=None):
    """
    Collect multi-signal evidence that the Shifts calendar content is loaded.
    Returns dict with booleans/details used by page and month-view checks.
    """
    import os

    region = region or _teams_region()
    text = _ocr_text_for_region(region)
    compact = " ".join(text.split())

    templates = {
        "today": _asset_path("today.png"),
        "openshifts": _asset_path("openshifts.png"),
        "shiftloaded": _asset_path("shiftloaded.png"),
        "bookedshifts": _asset_path("bookedshifts.png"),
        "shifts_selected": _asset_path("shifts_selected.png"),
    }
    template_hits = {}
    for key, path in templates.items():
        # shiftloaded is historical and often drifts; keep threshold lower.
        conf = 0.62 if key == "shiftloaded" else 0.70
        hit = _template_match_point(path, confidence=conf, region=region)
        template_hits[key] = hit is not None

    has_month_word = "month" in compact
    has_week_word = "week" in compact
    has_day_word = " day" in f" {compact}" or compact.startswith("day")
    has_open = ("open shifts" in compact) or ("openshifts" in compact.replace(" ", ""))
    has_people = ("people scheduled" in compact) or ("scheduled" in compact and "people" in compact)
    has_month_name = any(token in compact for token in _month_name_tokens())
    has_today = ("today" in compact) or template_hits["today"]
    # Teams Calendar app (not Shifts) also has a month grid + Today control.
    calendar_app = any(
        marker in compact
        for marker in (
            "my calendars",
            "add calendar",
            "show all",
            "event",
            "meet now",
        )
    )

    title = ""
    win = get_teams_window()
    if win is not None:
        try:
            title = (win.window_text() or "").lower()
        except Exception:
            title = ""

    title_shifts = "shifts" in title
    shifts_chrome = any(
        (
            template_hits["openshifts"],
            template_hits["shiftloaded"],
            template_hits["bookedshifts"],
            has_open,
            has_people,
            ("open shifts" in compact),
            ("booked shifts" in compact),
            ("people scheduled" in compact),
        )
    )
    # Never treat generic Calendar month view as Shifts content.
    loaded = bool(shifts_chrome or (title_shifts and (has_open or has_people or template_hits["today"] or has_month_name)))
    if calendar_app and not shifts_chrome and not title_shifts:
        loaded = False

    # Month view: Shifts month grid only (not Teams Calendar month).
    month_view = False
    if loaded and shifts_chrome and has_month_word and has_month_name and not has_week_word:
        month_view = True
    elif loaded and shifts_chrome and has_month_word and has_month_name and (
        has_open or has_people or template_hits["openshifts"]
    ):
        # "Week" can appear in other labels; still accept strong Shifts month signals.
        month_view = True
    elif loaded and shifts_chrome and has_month_name and (
        has_open or template_hits["openshifts"] or has_people
    ) and not has_day_word:
        # OCR sometimes drops the word "month" even when month grid is visible.
        month_view = True
    if calendar_app and not shifts_chrome:
        month_view = False

    return {
        "text": compact,
        "title": title,
        "title_shifts": title_shifts,
        "loaded": loaded,
        "month_view": month_view,
        "has_month_word": has_month_word,
        "has_week_word": has_week_word,
        "has_month_name": has_month_name,
        "has_open": has_open,
        "has_people": has_people,
        "has_today": has_today,
        "shifts_chrome": shifts_chrome,
        "calendar_app": calendar_app,
        "templates": template_hits,
    }


def is_teams_shifts_page():
    """
    True when Teams is on the Shifts app.
    Prefer window title, but fall back to on-screen content so a title-format
    change cannot break midnight refresh.
    """
    win = get_teams_window()
    if not win:
        return False
    try:
        title = (win.window_text() or "").lower()
    except Exception:
        title = ""
    if "shifts" in title:
        return True

    signals = shifts_content_signals()
    if signals.get("shifts_chrome") or signals["templates"].get("shifts_selected"):
        return True
    # Title already checked above; avoid treating Teams Calendar as Shifts.
    if signals.get("calendar_app") and not signals.get("shifts_chrome"):
        return False
    return False


def wait_for_shifts_content(timeout_seconds=45, poll_seconds=1.0):
    """Poll until Shifts content markers appear (or timeout)."""
    import time

    deadline = time.time() + max(1, timeout_seconds)
    last = None
    while time.time() < deadline:
        # Clear rating/NPS nags that can cover Month controls and OCR targets.
        try:
            dismiss_shifts_popups(max_rounds=1)
        except Exception:
            pass
        last = shifts_content_signals()
        if last["loaded"] or last["title_shifts"]:
            return True, last
        time.sleep(poll_seconds)
    return False, last or shifts_content_signals()


def dismiss_shifts_popups(max_rounds=3):
    """
    Close blocking Shifts nags/toasts (rating cards, surveys, coach marks).

    Example: the purple "Enjoying Shifts? Tap the stars..." card with an X.
    Returns the number of dismiss actions performed.
    """
    import time
    import pyautogui
    import pytesseract
    from difflib import SequenceMatcher

    marker_phrases = (
        "enjoying shifts",
        "enjoying",
        "tap the stars",
        "share your rating",
        "share rating",
        "rate your",
        "rating",
        "feedback",
        "how are we doing",
        "got a minute",
        "survey",
        "nps",
        "whats new",
        "what's new",
        "weve updated",
        "we've updated",
        "update available",
        "teams has been updated",
        "restart to update",
        "new version",
    )
    close_labels = (
        "x",
        "close",
        "dismiss",
        "not now",
        "no thanks",
        "later",
        "cancel",
        "ok",
        "okay",
        "got it",
        "continue",
        "restart",
    )

    actions = 0
    region = _teams_region()
    if region is None:
        try:
            pyautogui.press("esc")
        except Exception:
            pass
        return 0

    left, top, width, height = region

    for round_idx in range(1, max_rounds + 1):
        try:
            shot = pyautogui.screenshot(region=(left, top, width, height))
            data = pytesseract.image_to_data(shot, output_type=pytesseract.Output.DICT)
        except Exception as exc:
            _automation_log(f"Popup OCR failed: {exc}")
            break

        tokens = []
        for index, raw in enumerate(data.get("text", [])):
            text = (raw or "").strip()
            if not text:
                continue
            cleaned = "".join(ch for ch in text.lower() if ch.isalnum() or ch.isspace()).strip()
            if not cleaned and text not in {"×", "x", "X"}:
                continue
            tokens.append(
                {
                    "raw": text,
                    "cleaned": cleaned or text.lower(),
                    "left": data["left"][index],
                    "top": data["top"][index],
                    "width": data["width"][index],
                    "height": data["height"][index],
                    "cx": data["left"][index] + data["width"][index] // 2,
                    "cy": data["top"][index] + data["height"][index] // 2,
                }
            )

        if not tokens:
            break

        full_text = " ".join(t["cleaned"] for t in tokens if t["cleaned"])
        marker_hits = []
        for token in tokens:
            for phrase in marker_phrases:
                # Single-token fuzzy match or phrase present in full OCR.
                score = SequenceMatcher(None, token["cleaned"], phrase).ratio()
                if score >= 0.72 or phrase in full_text:
                    marker_hits.append(token)
                    break

        if not marker_hits and not any(p in full_text for p in marker_phrases):
            # A centered Teams update OK button can block midnight refresh
            # without matching the older rating-card phrases.
            ack_hits = [
                t
                for t in tokens
                if t["cleaned"] in {"ok", "okay", "got it", "continue"}
                and int(width * 0.25) <= t["cx"] <= int(width * 0.75)
                and int(height * 0.25) <= t["cy"] <= int(height * 0.80)
            ]
            if ack_hits:
                token = ack_hits[0]
                _click_xy(left + token["cx"], top + token["cy"], pause=0.35)
                actions += 1
                _automation_log(
                    f"Dismissed Teams update/ack dialog via {token['raw']} "
                    f"at ({int(left + token['cx'])}, {int(top + token['cy'])}) "
                    f"(round {round_idx}/{max_rounds})."
                )
                time.sleep(0.8)
                region = _teams_region() or region
                left, top, width, height = region
                continue
            break

        if not marker_hits:
            # Phrase found only in concatenated text; use upper-right tokens as anchor.
            marker_hits = [
                t
                for t in tokens
                if t["left"] > int(width * 0.45) and t["top"] < int(height * 0.55)
            ][:8]

        min_x = min(t["left"] for t in marker_hits)
        max_x = max(t["left"] + t["width"] for t in marker_hits)
        min_y = min(t["top"] for t in marker_hits)
        max_y = max(t["top"] + t["height"] for t in marker_hits)

        # Prefer an explicit close control near the popup card.
        close_click = None
        for token in tokens:
            label = token["cleaned"]
            raw = token["raw"].lower()
            is_close = (
                label in close_labels
                or raw in {"×", "x", "✕", "✖"}
                or SequenceMatcher(None, label, "close").ratio() >= 0.85
            )
            if not is_close:
                continue
            # Close/X usually sits above or on the top-right of the card.
            near_x = (min_x - 40) <= token["left"] <= (max_x + 80)
            near_y = (min_y - 80) <= token["top"] <= (min_y + 70)
            if near_x and near_y:
                close_click = (left + token["cx"], top + token["cy"], token["raw"])
                break

        if close_click is None:
            # Geometric X: top-right corner of the detected card body.
            close_x = left + min(width - 8, max_x + 18)
            close_y = top + max(8, min_y - 28)
            close_click = (close_x, close_y, "geometry-x")

        cx, cy, how = close_click
        _click_xy(cx, cy, pause=0.35)
        actions += 1
        _automation_log(
            f"Dismissed Shifts popup via {how} at ({int(cx)}, {int(cy)}) "
            f"(round {round_idx}/{max_rounds})."
        )
        time.sleep(0.6)

        # Re-read region in case Teams resized/moved.
        region = _teams_region() or region
        left, top, width, height = region

    if actions == 0:
        # Lightweight fallback for non-OCR-able toasts.
        try:
            pyautogui.press("esc")
        except Exception:
            pass
    return actions


def _click_today_anchor(region=None):
    """Best-effort Today click so the calendar returns to the current month."""
    import time

    today_path = _asset_path("today.png")
    clicked = find_and_click_template(today_path, confidence=0.55, pause=0.3)
    if clicked:
        time.sleep(0.8)
        return True

    token = _ocr_find_token("today", region=region, min_score=0.7, y_min=0, y_max=220)
    if token:
        x, y, cleaned, score = token
        _click_xy(x, y, pause=0.4)
        _automation_log(f"Clicked OCR Today '{cleaned}' ({score:.2f}) at ({x}, {y}).")
        time.sleep(0.8)
        return True
    return False


def _select_month_from_view_menu(region):
    """
    Open the Shifts view selector and choose Month.
    Uses OCR first, then resolution-scaled coordinate fallbacks.
    """
    import time
    import pyautogui

    left, top, width, height = region
    # View control lives in the upper-right toolbar on production layouts.
    x_min = int(width * 0.55)
    x_max = width
    y_min = int(height * 0.05)
    y_max = int(height * 0.35)

    opened = False
    for label in ("week", "month", "day"):
        token = _ocr_find_token(
            label,
            region=region,
            min_score=0.68,
            x_min=x_min,
            x_max=x_max,
            y_min=y_min,
            y_max=max(y_min + 40, int(height * 0.22)),
        )
        if token:
            x, y, cleaned, score = token
            _click_xy(x, y, pause=0.45)
            _automation_log(f"Opened view menu via '{cleaned}'/{label} ({score:.2f}) at ({x}, {y}).")
            opened = True
            break

    if not opened:
        # Scaled fallback near historical 1920x1080 control position.
        fallback_x = left + int(width * 0.845)
        fallback_y = top + int(height * 0.145)
        _click_xy(fallback_x, fallback_y, pause=0.45)
        _automation_log(f"Opened view menu via scaled fallback at ({fallback_x}, {fallback_y}).")

    time.sleep(0.8)

    # Choose Month inside the opened menu (slightly below the control).
    menu_y_min = int(height * 0.12)
    menu_y_max = int(height * 0.55)
    month_token = _ocr_find_token(
        "month",
        region=region,
        min_score=0.62,
        x_min=int(width * 0.50),
        x_max=width,
        y_min=menu_y_min,
        y_max=menu_y_max,
    )
    if month_token:
        x, y, cleaned, score = month_token
        _click_xy(x, y, pause=0.5)
        _automation_log(f"Selected Month via OCR '{cleaned}' ({score:.2f}) at ({x}, {y}).")
        return True

    fallback_month_x = left + int(width * 0.84)
    fallback_month_y = top + int(height * 0.30)
    _click_xy(fallback_month_x, fallback_month_y, pause=0.5)
    _automation_log(f"Selected Month via scaled fallback at ({fallback_month_x}, {fallback_month_y}).")
    # Dismiss any residual popover.
    try:
        pyautogui.press("esc")
    except Exception:
        pass
    return True


def ensure_shifts_month_view(max_attempts=3):
    """
    Force the Shifts calendar into Month view (single header row of day numbers).
    Returns True if Month view appears selected/visible.

    Uses multi-signal confirmation (OCR + templates) so a single flaky OCR
    pass cannot fail an otherwise successful midnight refresh.
    """
    import time

    if not configure_teams_window():
        return False

    region = _teams_region()
    if region is None:
        return False

    for attempt in range(1, max_attempts + 1):
        _automation_log(f"Ensuring Shifts Month view (attempt {attempt}/{max_attempts}).")
        dismiss_shifts_popups(max_rounds=2)
        region = _teams_region() or region
        signals = shifts_content_signals(region)
        if signals["month_view"]:
            _click_today_anchor(region)
            # Re-check after Today in case view changed.
            time.sleep(0.6)
            dismiss_shifts_popups(max_rounds=1)
            region = _teams_region() or region
            final = shifts_content_signals(region)
            if final["month_view"] or (final["loaded"] and final["has_month_name"]):
                _automation_log("Month view already active and confirmed.")
                return True

        # If content is not loaded yet, give Teams a moment before interacting.
        if not signals["loaded"] and not signals["title_shifts"]:
            loaded, signals = wait_for_shifts_content(timeout_seconds=12, poll_seconds=1.0)
            region = _teams_region() or region
            if not loaded and not signals["title_shifts"]:
                _automation_log("Shifts content not loaded yet while selecting Month view.")

        try:
            _select_month_from_view_menu(region)
        except Exception as exc:
            _automation_log(f"Month view selection click failed: {exc}")

        time.sleep(1.2)
        dismiss_shifts_popups(max_rounds=2)
        _click_today_anchor(region)
        time.sleep(1.0)
        dismiss_shifts_popups(max_rounds=1)

        region = _teams_region() or region
        final = shifts_content_signals(region)
        if final["month_view"]:
            _automation_log("Month view confirmed after selection.")
            return True

        # Soft success: real Shifts chrome + month name, even if OCR missed "month".
        soft_ok = (
            final.get("shifts_chrome")
            and final["has_month_name"]
            and (
                final["has_open"]
                or final["has_people"]
                or final["templates"].get("openshifts")
                or final["templates"].get("bookedshifts")
            )
        )
        if soft_ok and not final["has_week_word"]:
            _automation_log("Month view soft-confirmed via Shifts chrome signals.")
            return True
        if final.get("calendar_app") and not final.get("shifts_chrome"):
            _automation_log("Detected Teams Calendar app instead of Shifts; Month lock not satisfied.")

        _automation_log(
            "Month view confirmation incomplete "
            f"(loaded={final['loaded']}, month_word={final['has_month_word']}, "
            f"week_word={final['has_week_word']}, month_name={final['has_month_name']}, "
            f"open={final['has_open']}, templates={final['templates']})."
        )
        time.sleep(1.0)

    return False


def capture_debug_shifts_image(prefix="shifts_debug"):
    """Save a Teams screenshot for post-mortem when refresh fails."""
    import os
    import datetime
    import pyautogui

    try:
        folder = "screenshots"
        os.makedirs(folder, exist_ok=True)
        stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(folder, f"{prefix}_{stamp}.png")
        region = _teams_region()
        if region is None:
            pyautogui.screenshot(path)
        else:
            left, top, width, height = region
            pyautogui.screenshot(path, region=(left, top, width, height))
        _automation_log(f"Wrote debug screenshot: {path}")
        return path
    except Exception as exc:
        _automation_log(f"Could not write debug screenshot: {exc}")
        return None


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

    # Teams is expected to already be maximized for the whole 4-month scan
    # (done once by the caller) so every open-shift row renders fully. Do NOT
    # resize here on every capture — repeated maximize/restore per-month was a
    # race: Teams didn't finish redrawing the larger layout before the
    # screenshot was taken, producing "0 shifts found" on months with the
    # most rows (e.g. November). Just give the current layout a brief moment
    # to settle before capturing.
    time.sleep(0.3)

    # Generate a unique filename based on timestamp and scan index if present
    scan_index = getattr(capture_shifts_screen, "_scan_index", None)
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    if scan_index is not None:
        screenshot_prefix = f"{scan_index}-"
    else:
        screenshot_prefix = ""
    screenshot_path = os.path.join(screenshots_dir, f"{screenshot_prefix}shifts_screenshot_{timestamp}.png")

    # Capture the maximized Teams window region so all shift rows are visible.
    win = get_teams_window()
    if win is not None:
        rect = win.rectangle()
        region_tuple = (rect.left, rect.top, rect.width(), rect.height())
    else:
        screen_width, screen_height = pyautogui.size()
        region_tuple = (0, 0, screen_width, screen_height)

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

    # Wait for content instead of a blind sleep + brittle title-only check.
    loaded, signals = wait_for_shifts_content(timeout_seconds=30, poll_seconds=1.0)
    if signals.get("calendar_app") and not signals.get("shifts_chrome") and not signals.get("title_shifts"):
        _automation_log("Navigation landed on Teams Calendar instead of Shifts; retrying Shifts entry.")
        # One more pass through the More-apps menu path.
        maximize_teams_window()
        if find_and_click_template(dots_path, confidence=0.80, pause=0.5):
            time.sleep(1.2)
            data = pytesseract.image_to_data(
                pyautogui.screenshot(), output_type=pytesseract.Output.DICT
            )
            best = None
            for index, text in enumerate(data["text"]):
                cleaned = "".join(ch for ch in text.strip().lower() if ch.isalpha())
                if not cleaned:
                    continue
                score = SequenceMatcher(None, cleaned, "shifts").ratio()
                left = data["left"][index]
                top = data["top"][index]
                if score >= 0.55 and 40 <= left <= 500 and 40 <= top <= 1100:
                    cand = (score, left, top, data["width"][index], data["height"][index], cleaned)
                    if best is None or cand[0] > best[0]:
                        best = cand
            if best:
                _, left, top, width, height, cleaned = best
                x = left + width // 2
                y = top + height // 2
                pyautogui.click(x, y)
                _automation_log(f"Recovered Shifts from menu after Calendar false-landing via '{cleaned}'.")
                time.sleep(6)
                loaded, signals = wait_for_shifts_content(timeout_seconds=25, poll_seconds=1.0)

    if (not loaded and not is_teams_shifts_page()) or (
        signals.get("calendar_app") and not signals.get("shifts_chrome") and not signals.get("title_shifts")
    ):
        _automation_log(
            "Teams did not land on the Shifts page after navigation "
            f"(title_shifts={signals.get('title_shifts')}, loaded={signals.get('loaded')}, "
            f"calendar_app={signals.get('calendar_app')}, shifts_chrome={signals.get('shifts_chrome')})."
        )
        capture_debug_shifts_image(prefix="nav_not_shifts")
        return False

    # Rating/NPS cards often appear right after Shifts loads and block controls.
    dismiss_shifts_popups(max_rounds=3)

    if prepare_monthly_view:
        if not configure_teams_window():
            _automation_log("Reached Shifts but failed to restore the production window size.")
            return False
        if not ensure_shifts_month_view():
            _automation_log("Reached Shifts but could not lock Month view.")
            # Keep navigation success if Shifts itself loaded; caller may retry month lock.
            return is_teams_shifts_page()

    return is_teams_shifts_page()


def refresh_teams_shifts_view(max_attempts=3):
    """
    Force-refresh Teams Shifts and restore production monthly single-row view.
    Returns True on success.

    Retries the full leave/re-enter/Ctrl+R/month-lock sequence so a single
    flaky OCR confirmation cannot mark midnight refresh as failed.
    """
    import os
    import time
    import pyautogui

    away_icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "away_icon.png")
    calendar_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "calendar.png")

    for attempt in range(1, max_attempts + 1):
        _automation_log(f"Refresh Teams Shifts monthly view attempt {attempt}/{max_attempts}.")
        try:
            if not ensure_teams_available():
                _automation_log("Teams was closed or hidden; launch/restore failed.")
                time.sleep(2)
                continue
            if not maximize_teams_window():
                _automation_log("Could not maximize Teams at start of refresh attempt.")
                time.sleep(2)
                continue

            pyautogui.press("esc")
            time.sleep(0.3)

            # Leave Shifts first so re-entering forces a full app reload.
            left_shifts = find_and_click_template(away_icon_path, confidence=0.75, pause=0.5)
            if not left_shifts:
                left_shifts = find_and_click_template(calendar_path, confidence=0.75, pause=0.5)
            if left_shifts:
                time.sleep(2.0)
            else:
                _automation_log("Could not click away/calendar before Shifts re-entry; continuing.")

            if not navigate_to_shifts(prepare_monthly_view=True):
                _automation_log("navigate_to_shifts failed during refresh attempt.")
                capture_debug_shifts_image(prefix=f"refresh_nav_fail_a{attempt}")
                time.sleep(2)
                continue

            # Hard refresh once we are on Shifts at production size.
            if not focus_teams_window():
                _automation_log("Could not focus Teams before Ctrl+R.")
                capture_debug_shifts_image(prefix=f"refresh_focus_fail_a{attempt}")
                time.sleep(2)
                continue

            pyautogui.hotkey("ctrl", "r")
            _automation_log("Sent Ctrl+R to refresh Teams Shifts.")

            loaded, signals = wait_for_shifts_content(timeout_seconds=35, poll_seconds=1.0)
            dismiss_shifts_popups(max_rounds=3)
            if not loaded:
                _automation_log(
                    "Shifts content not detected after Ctrl+R; re-navigating. "
                    f"signals={ {k: signals.get(k) for k in ('title_shifts','loaded','has_month_name','has_open') } }"
                )
                if not navigate_to_shifts(prepare_monthly_view=False):
                    capture_debug_shifts_image(prefix=f"refresh_reload_fail_a{attempt}")
                    time.sleep(2)
                    continue
                loaded, signals = wait_for_shifts_content(timeout_seconds=25, poll_seconds=1.0)
                dismiss_shifts_popups(max_rounds=3)

            if not configure_teams_window():
                _automation_log("Failed to restore production Teams geometry after refresh.")
                capture_debug_shifts_image(prefix=f"refresh_geom_fail_a{attempt}")
                time.sleep(2)
                continue

            month_ok = ensure_shifts_month_view(max_attempts=3)
            dismiss_shifts_popups(max_rounds=2)
            page_ok = is_teams_shifts_page()
            final = shifts_content_signals()

            if month_ok and page_ok and (final.get("shifts_chrome") or final.get("title_shifts")):
                dismiss_shifts_popups(max_rounds=2)
                _automation_log("Teams Shifts monthly view refresh succeeded.")
                return True

            # Final multi-signal acceptance requires real Shifts chrome so we never
            # treat Teams Calendar month view as a successful midnight refresh.
            if final.get("shifts_chrome") and final.get("month_view"):
                _automation_log("Teams Shifts monthly view accepted via content signals.")
                return True
            if final.get("shifts_chrome") and final.get("has_month_name") and (
                final.get("has_open")
                or final.get("templates", {}).get("openshifts")
                or final.get("has_people")
            ):
                _automation_log("Teams Shifts monthly view accepted via soft content signals.")
                return True

            _automation_log(
                "Refresh attempt incomplete: "
                f"page_ok={page_ok}, month_ok={month_ok}, "
                f"loaded={final.get('loaded')}, month_view={final.get('month_view')}, "
                f"shifts_chrome={final.get('shifts_chrome')}, calendar_app={final.get('calendar_app')}."
            )
            capture_debug_shifts_image(prefix=f"refresh_incomplete_a{attempt}")
        except Exception as exc:
            _automation_log(f"Refresh attempt {attempt} raised: {exc}")
            capture_debug_shifts_image(prefix=f"refresh_exception_a{attempt}")
        time.sleep(2.0)

    _automation_log("All Teams Shifts monthly view refresh attempts failed.")
    return False


def scan_four_months_with_automation(ocr_func, year, month, should_abort=None):
    """
    Full workflow: click Today, scan, click right arrow, scan, repeat for four months.
    ocr_func: function to call for OCR, e.g. extract_shifts_from_image(image_path, year, month)
    should_abort: optional zero-arg callable; when true, abandon the scan immediately
        without further OCR/navigation so midnight reset cannot race an in-flight scan.
    """
    import time
    from datetime import datetime
    import calendar

    def _aborted():
        try:
            return bool(should_abort and should_abort())
        except Exception:
            return False

    # Step 1: Focus Teams window
    if not focus_teams_window():
        _automation_log("Could not focus Teams window. Aborting scan.")
        return

    if _aborted():
        _automation_log("Scan aborted before start (reset/invalidation).")
        return

    dismiss_shifts_popups(max_rounds=3)

    if recover_from_teams_error_page():
        dismiss_shifts_popups(max_rounds=2)

    # Step 2: Click Today button to ensure we start from current month
    if not find_and_click_template('today.png', confidence=0.9, pause=0.2):
        if recover_from_teams_error_page() and find_and_click_template('today.png', confidence=0.9, pause=0.2):
            _automation_log("Today button click recovered after Teams error-page handling.")
        else:
            _automation_log("Could not find/click Today button after recovery attempts. Aborting scan.")
            return

    # Give Teams more time to stabilize after Today click
    time.sleep(0.5)
    dismiss_shifts_popups(max_rounds=2)

    if _aborted():
        _automation_log("Scan aborted before view check (reset/invalidation).")
        return

    # Guard against scanning while Teams is stuck in Day/Week view. Scanning
    # in the wrong view produces garbage OCR (missing/incorrect shift dates),
    # which is what caused untracked shifts (e.g. Dec 12 not shown in Day view).
    signals = shifts_content_signals()
    if not signals.get("month_view"):
        _automation_log(
            "Teams is not in Month view before scan "
            f"(month_word={signals.get('has_month_word')}, week_word={signals.get('has_week_word')}, "
            f"day_word={signals.get('has_day_word')}). Attempting auto-fix."
        )
        if not ensure_shifts_month_view(max_attempts=3):
            recovered = recover_from_teams_error_page()
            if recovered:
                dismiss_shifts_popups(max_rounds=2)
            if not recovered or not ensure_shifts_month_view(max_attempts=2):
                _automation_log("Auto-fix failed to restore Month view. Aborting scan to avoid bad data.")
                try:
                    from email_alert import send_email_alert
                    send_email_alert(
                        "Teams Shift Scanner: Month view could not be restored",
                        "Teams Shifts was detected outside of Month view (e.g. Day/Week view) and the "
                        "scanner could not automatically restore Month view. Scanning was aborted for "
                        "this cycle to avoid recording incorrect/missing shift data. Please check the "
                        "Teams Shifts app manually.",
                        "russfray74@gmail.com",
                    )
                except Exception as e:
                    _automation_log(f"Failed to send Month-view-recovery email: {e}")
                return
        _automation_log("Month view auto-fix succeeded. Continuing scan.")
        dismiss_shifts_popups(max_rounds=2)

    # Max seconds to wait for a single screenshot capture before giving up on that month
    SCREENSHOT_TIMEOUT = 45

    # Maximize Teams once for the whole 4-month scan so every open-shift row
    # renders fully (some months have 4+ concurrent rows that get clipped at
    # the short production height). Resizing per-month caused a redraw race
    # where Teams hadn't finished laying out before the screenshot was taken,
    # producing false "0 shifts found" results (e.g. November). We restore the
    # short production layout once at the end so the monitor panel stays visible.
    if not maximize_teams_window():
        _automation_log("Could not maximize Teams before scan; continuing with current layout.")
    else:
        time.sleep(1.0)
        dismiss_shifts_popups(max_rounds=2)

    # Step 3: Scan current and next 3 months
    for i in range(4):
        if _aborted():
            _automation_log("Scan aborted mid-loop (reset/invalidation). Discarding remaining months.")
            configure_teams_window()
            return

        scan_year = year
        scan_month = month + i
        # Handle year rollover
        while scan_month > 12:
            scan_month -= 12
            scan_year += 1

        _automation_log(f"Starting scan {i+1}/4 for {calendar.month_name[scan_month]} {scan_year}")

        if recover_from_teams_error_page():
            dismiss_shifts_popups(max_rounds=2)

        # Re-verify Month view before each month's capture; navigation clicks
        # or transient popups can knock Teams into Day/Week view mid-scan.
        mid_signals = shifts_content_signals()
        if not mid_signals.get("month_view"):
            _automation_log(
                f"Month view lost before scanning {calendar.month_name[scan_month]} {scan_year}. "
                "Attempting auto-fix mid-scan."
            )
            if not ensure_shifts_month_view(max_attempts=2):
                _automation_log(
                    f"Could not restore Month view for {calendar.month_name[scan_month]} {scan_year}; "
                    "skipping this month to avoid bad data."
                )
                if i < 3:
                    time.sleep(0.2)
                    if not find_and_click_right_arrow():
                        _automation_log("Could not navigate past unrecoverable month. Stopping scan early.")
                        break
                    time.sleep(1.5)
                continue
            # ensure_shifts_month_view() shrinks Teams back to the short
            # production height internally; re-maximize so the remaining
            # captures in this scan still render every open-shift row.
            maximize_teams_window()
            time.sleep(0.8)
            dismiss_shifts_popups(max_rounds=2)

        # Set scan index for image prefixing
        capture_shifts_screen._scan_index = i

        # Clear any rating/toast overlays before capture/OCR.
        dismiss_shifts_popups(max_rounds=2)

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
            _automation_log(f"[TIMEOUT] Screenshot timed out after {SCREENSHOT_TIMEOUT}s for {calendar.month_name[scan_month]} {scan_year} - trying Teams error recovery.")
            recover_from_teams_error_page()
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
            month_verified = True
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
                # Never assign dates to a requested month when the screenshot month is unknown.
                _automation_log(
                    f"[WARNING] Could not OCR month/year from screenshot for expected "
                    f"{calendar.month_name[scan_month]} {scan_year}. Skipping this month to avoid misdated shifts."
                )
                month_verified = False
            if month_verified:
                _automation_log(f"Scanning {calendar.month_name[scan_month]} {scan_year}")
                try:
                    ocr_func(screenshot_path, scan_year, scan_month)
                except Exception as e:
                    _automation_log(f"OCR processing failed for {calendar.month_name[scan_month]} {scan_year}: {e}")
                    # Continue with next month even if this one fails
        else:
            _automation_log(f"Failed to capture screenshot for {calendar.month_name[scan_month]} {scan_year}. Trying Teams error-page recovery.")
            recover_from_teams_error_page()

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

    # Re-enforce Month view before leaving the scan. Without this, Teams can
    # be left in Day/Week view for the entire idle/countdown period until the
    # next scan runs, which is what caused the app to display Day view between
    # scans even though scanning itself succeeded.
    if not _aborted():
        # Restore the short production layout now that all captures are done;
        # Teams was kept maximized for the whole scan so every open-shift row
        # rendered fully during OCR.
        configure_teams_window()
        time.sleep(0.5)
        end_signals = shifts_content_signals()
        if not end_signals.get("month_view"):
            _automation_log("Teams left in non-Month view after scan. Restoring Month view before idling.")
            if not ensure_shifts_month_view(max_attempts=3):
                _automation_log("Failed to restore Month view after scan completion.")
                try:
                    from email_alert import send_email_alert
                    send_email_alert(
                        "Teams Shift Scanner: Month view not restored after scan",
                        "The scan completed, but Teams Shifts could not be locked back into Month "
                        "view afterwards. The app may display Day/Week view until the next scan "
                        "cycle. Please check the Teams Shifts app manually.",
                        "russfray74@gmail.com",
                    )
                except Exception as e:
                    _automation_log(f"Failed to send post-scan Month-view email: {e}")
            else:
                _automation_log("Month view restored after scan.")
    
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
