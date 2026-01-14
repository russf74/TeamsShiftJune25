# Teams Shift Application - Complete System Analysis

**Analysis Date:** January 26, 2025  
**Repository:** https://github.com/russf74/TeamsShiftJune25  
**Branch:** enhancement/whatsapp-disable-sms-alerts  
**Status:** Production-ready with pending changes

---

## 1. APPLICATION OVERVIEW

### Purpose
Automated monitoring and alerting system for Microsoft Teams Shifts application. Detects open shifts matching user availability and sends multi-channel notifications (Email, WhatsApp, SMS).

### Technology Stack
- **Language:** Python 3.9+
- **GUI Framework:** Tkinter
- **Database:** SQLite3
- **OCR Engine:** Tesseract (via pytesseract)
- **Image Processing:** OpenCV, Pillow
- **UI Automation:** pyautogui, pywinauto
- **Email:** yagmail (Gmail)
- **SMS:** Email-to-SMS gateways or Twilio API
- **Scheduling:** APScheduler
- **Platform:** Windows Desktop

---

## 2. CORE ARCHITECTURE

### Application Entry Point
**`main.py`** - Initializes database, configuration, logging, kills duplicate instances, launches GUI

### Key Components

#### **GUI Layer** (`gui.py`)
- **CalendarView Class:** Monthly calendar display with color-coded shift status
  - Blue: Booked shifts
  - Green: Open shifts matching availability
  - Orange: Open shifts without availability
  - Grey: Past dates
- **MainApp Class:** Main application window with:
  - Automated scan scheduling (configurable interval)
  - Manual scan trigger
  - Test messaging (Email, WhatsApp, SMS)
  - Daily summary email system
  - Midnight Teams app refresh with video recording
  - Calendar navigation (prev/next month, return to current)
  - Shift availability checkbox tracking

#### **Database Layer** (`database.py`)
- **Tables:**
  - `shifts`: Shift records (date, type, count, alerted status, created_at)
  - `availability`: User availability dates
  - `config`: Application configuration
  - `shift_history`: First-seen tracking to prevent false "NEW!" alerts
  - `email_log`: Daily summary email tracking (via `email_db.py`)

- **Key Functions:**
  - `add_shift()`: Prevents conflicting shift types, handles open?booked conversions
  - `delete_shifts_not_in_list()`: Cleanup stale shifts after scan
  - `shift_exists()`: Check for existing shifts
  - `mark_shift_alerted()`: Track notification status
  - `get_shifts_for_month()`: Calendar data retrieval
  - `set_availability_for_date()`: User availability management

#### **Automation Layer** (`automation.py`)
- **Teams UI Automation:**
  - `focus_teams_window()`: Window focus using pywinauto
  - `capture_shifts_screen()`: Screenshot capture (full screen minus bottom 100px)
  - `find_and_click_template()`: OpenCV template matching for UI elements
  - `scan_four_months_with_automation()`: Main scan workflow:
    1. Focus Teams window
    2. Click "Today" button to reset position
    3. For each of 4 months:
       - Capture screenshot
       - OCR month/year validation
       - Extract shifts via OCR
   - Click right arrow to next month
  4. Return to current month

- **WhatsApp Automation:**
- `send_whatsapp_message()`: Template-based input field detection and message sending
  - Config-based enable/disable toggle

#### **OCR Processing Layer**
**`ocr_processing.py`** - Main OCR coordinator
- `extract_shifts_from_image()`: Main entry point
- `extract_month_year_from_image()`: Month/year validation
- Delegates to specialized modules:

**`open_shift_ocr.py`** - Open shift detection
- Template matching for "openshifts.png"
- Digit extraction in defined regions
- Count aggregation by date

**`booked_shift_ocr.py`** - Booked shift detection
- Template matching for "bookedshifts.png"
- Date extraction using calendar grid coordinates
- Conflict prevention (booked overrides open)

#### **Alert System**

**`email_alert.py`** - Email notifications
- `send_email_alert()`: Generic email sender via yagmail
- `send_availability_alert()`: New shift match notifications
- `send_summary_email()`: Daily summary (8pm+, once per day)
  - Scan statistics
  - Future shifts status (with NEW! tags)
  - Error logs
- `send_shift_confirmation_email()`: Immediate booking confirmations
  - **SAFETY:** Never sends for past dates
  - Tracks `confirmed_email_sent` flag to prevent duplicates

**`sms_alert.py`** - SMS notifications
- **Two provider modes:**
  - **Email-to-SMS (FREE):** Carrier-specific gateways (Verizon, AT&T, T-Mobile, etc.)
  - **Twilio API (PAID):** $0.01/message via Twilio REST API
- Configuration in `sms_config.json` (not committed to Git)
- Multi-recipient support via `phone_numbers` array
- Methods:
  - `send_shift_alert_sms()`: New shift notifications
  - `test_sms()`: Test message sender

**`email_db.py`** - Email tracking
- Prevents duplicate daily summaries
- Timestamp tracking for "NEW!" shift tagging

#### **Configuration Management**

**`config.py`** - Main app config
- Loads/saves `config.json`
- Contains: scan_interval, Gmail credentials, alert email

**Configuration Files (Not in Git):**
- `smtp_settings.json`: Gmail SMTP settings
- `sms_config.json`: SMS provider settings
- `config.json`: App preferences

---

## 3. KEY WORKFLOWS

### Automated Scan Workflow
1. **Trigger:** Countdown timer (default 600 seconds) or manual button
2. **Process:**
 - Clear screenshots directory
   - Run `scan_four_months_with_automation()`
   - For each month:
     - Capture screenshot
     - Validate month/year via OCR
     - Detect open shifts (template + OCR)
     - Detect booked shifts (template + OCR)
     - Store in database with counts
   - Cleanup stale shifts not found in scan
   - Check for new matches (open shifts + user availability + not already alerted)
3. **Alerts:**
   - Email all recipients
   - WhatsApp group message (if enabled)
   - SMS to all configured numbers (if enabled)
   - Mark shifts as alerted to prevent duplicates

### Midnight Teams Refresh
1. **Trigger:** Daily at 00:00-00:05
2. **Process:**
   - Start screen recording (5 min, 5 FPS, 1280x720, saves as `midnight_reset.mp4`)
   - Pause scanning
   - Click Calendar button (if found)
   - Click Dots (...) button
 - Click Shifts button
   - Wait for `shiftloaded.png` confirmation
   - Max 10 retry attempts
3. **Notifications:**
   - Success email on completion
   - Failure email after 10 attempts
4. **Resume:** Restart scanning timer

### Daily Summary Email
1. **Trigger:** After 8:00 PM daily
2. **Content:**
   - Scan count, error count, emails sent, SMS sent
   - Last scan timestamp
   - All future shifts with color coding:
     - **Blue (Booked):** User confirmed shifts
  - **Bold (Matched):** Open shifts matching availability
     - **Normal (Open):** Open shifts without availability
     - **Green NEW!:** Shifts added since last summary
3. **Safety:** Checks `email_log` to prevent duplicate sends

---

## 4. DATA SAFETY FEATURES

### Conflict Prevention
- **Database-level:** `add_shift()` deletes open shifts when adding booked shifts
- **OCR-level:** Booked shift detection skips dates with existing bookings
- **UI-level:** Calendar forces availability checkbox off for booked dates

### Date Validation
- Strict YYYY-MM-DD format validation before database insertion
- Rejects malformed dates to prevent database corruption

### False Alert Prevention
- `shift_history` table tracks first-seen timestamps
- Re-adding deleted shifts uses original timestamp (prevents false "NEW!" tags)
- `alerted` flag prevents duplicate notifications
- `confirmed_email_sent` flag prevents duplicate booking confirmations

### Past Date Safety
- **Confirmation emails:** Never sent for past dates (checked in `add_shift()` and `send_shift_confirmation_email()`)
- **Stale shift cleanup:** Only runs for months actually scanned (prevents accidental deletion)
- **Empty scan safety:** Never deletes shifts if no valid_dates found (prevents deletion on scan failure)

---

## 5. CURRENT FILE STRUCTURE

### Python Core Files (Committed to Git)
```
main.py    # Entry point
gui.py                   # GUI and main application logic
automation.py  # Teams automation and WhatsApp
database.py    # SQLite database operations
email_alert.py  # Email notification system
email_db.py              # Email tracking database
sms_alert.py            # SMS notification system
ocr_processing.py    # Main OCR coordinator
open_shift_ocr.py                # Open shift detection
booked_shift_ocr.py              # Booked shift detection
config.py           # Configuration management
scheduler.py          # Task scheduling
status_server.py           # Web status server (port 5000)
```

### Reference Images (Committed to Git)
```
arrow.png              # Right arrow navigation
bookedshifts.png          # Booked shift template
calendar.png   # Calendar button
dots.png   # Three-dots menu
openshifts.png         # Open shift template
shifts.png # Shifts button
shiftloaded.png    # Shifts page loaded confirmation
today.png        # Today button
whatsapp.png # WhatsApp input field
```

### Configuration Files (NOT in Git - Security)
```
config.json   # App preferences
smtp_settings.json       # Gmail SMTP credentials
sms_config.json             # SMS provider settings
```

### Database Files (NOT in Git - User Data)
```
shifts.db         # Main shift database
email.db       # Email tracking (deprecated/merged)
```

### Generated/Temporary Files (NOT in Git)
```
screenshots/         # Scan screenshots (auto-cleaned)
midnight_reset.mp4     # Latest midnight refresh recording
__pycache__/         # Python bytecode
*.pyc, *.pyo, *.pyd      # Compiled Python
```

### Documentation (Committed to Git)
```
README.md     # Basic project overview
BACKUP_RESTORE_GUIDE.md          # Full restore instructions
requirements.txt     # Python dependencies
.gitignore# Git exclusions
```

---

## 6. CURRENT UNCOMMITTED CHANGES

### Modified Files (Not Yet Committed)
```
automation.py        # Changes pending
database.py      # Changes pending
email_alert.py     # Changes pending
gui.py          # Changes pending
shifts.db      # Database (never committed)
```

### Untracked Debug/Test Files
```
analyze_scan.py
basic_ocr_test.py
check_november.py
coordinate_finder.py
debug_*.py
enhanced_*.py
examine_image.py
fix_november.py
hybrid_ocr_module.py
image_*.py
simple_ocr_test.py
template_matching_debug.py
tesseract_debug.py
test_*.py
test_digits/
```

---

## 7. DEPENDENCIES

### Required Python Packages
```
pyautogui     # Screen automation
pywinauto            # Windows UI automation
opencv-python    # Image processing
pytesseract # OCR engine wrapper
Pillow     # Image manipulation
APScheduler        # Task scheduling
yagmail     # Gmail API wrapper
psutil           # Process management
twilio (optional)        # SMS via Twilio API
```

### External Dependencies
- **Tesseract OCR:** Must be installed separately on Windows
- **WhatsApp Desktop:** Must be running for WhatsApp alerts
- **Microsoft Teams:** Must be logged in and accessible

---

## 8. KNOWN LIMITATIONS & RISKS

### Technical Limitations
1. **OCR Accuracy:** Dependent on screen resolution and Teams UI consistency
2. **Template Matching:** Brittle to Teams UI updates
3. **Screen Automation:** Requires Teams window to be visible (not minimized)
4. **Single Instance:** Only one user per machine supported

### Security Considerations
1. **Credentials in Plain Text:** `smtp_settings.json` and `sms_config.json` store passwords
2. **No Encryption:** Database and config files unencrypted
3. **Local Only:** No cloud sync or backup

### Operational Risks
1. **False Negatives:** Missed shifts if OCR fails
2. **False Positives:** Rare but possible incorrect shift detection
3. **Duplicate Alerts:** Mitigated but not 100% eliminated
4. **Midnight Refresh Failure:** Could prevent proper scanning if Teams UI changes

---

## 9. BACKUP & RESTORE STRATEGY

### What's Backed Up to GitHub
? All Python source code  
? Reference images (PNG templates)  
? Documentation files  
? Requirements.txt  
? .gitignore  

### What's NOT Backed Up (Security/Privacy)
? Configuration files with credentials  
? Database files with user data  
? Screenshots and recordings  
? Debug/test scripts  

### Restore Process
1. Clone repository from GitHub
2. Install Python dependencies: `pip install -r requirements.txt`
3. Manually create configuration files:
   - `smtp_settings.json`
- `sms_config.json` (if using SMS)
   - `config.json`
4. Run: `python main.py`
5. Database files auto-created on first run

---

## 10. RECOMMENDED IMPROVEMENTS

### High Priority
1. **Encrypt sensitive config files** (credentials)
2. **Add database backup functionality** (scheduled exports)
3. **Improve OCR robustness** (multiple confidence checks)
4. **Add health monitoring dashboard** (expand status_server.py)

### Medium Priority
5. **Multi-user support** (separate databases per user)
6. **Cloud sync option** (OneDrive/Dropbox integration)
7. **Mobile notifications** (push notifications via Pushover/Pushbullet)
8. **Better error recovery** (auto-retry on OCR failures)

### Low Priority
9. **Dark mode UI**
10. **Custom notification sounds**
11. **Shift analytics/reports**
12. **Export to calendar apps** (Google Calendar, Outlook)

---

## 11. CURRENT STATE ASSESSMENT

### Strengths ?
- Robust error handling and logging
- Multi-channel notification system
- Comprehensive safety checks against false alerts
- Well-structured modular codebase
- Active development with version control
- Good documentation

### Weaknesses ??
- Credentials stored in plain text
- No automated backups
- Brittle template-based UI automation
- Limited multi-user support
- No mobile app

### Overall Status
**Production-Ready** but requires manual configuration and monitoring. Suitable for single-user deployment on a dedicated Windows machine.

---

## 12. NEXT STEPS FOR BACKUP

### Immediate Actions
1. ? Create this analysis document
2. ? Commit current working changes to branch
3. ? Create pre-change snapshot tag
4. ? Push to GitHub remote
5. ? Verify backup integrity

### Change Management Strategy
1. Create new feature branch from snapshot
2. Make requested changes
3. Test thoroughly
4. If successful: merge to main
5. If broken: revert to snapshot tag

---

**End of Analysis**
