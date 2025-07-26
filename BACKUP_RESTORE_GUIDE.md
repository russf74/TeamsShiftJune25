# Teams Shift Application - Full Backup & Restore Guide

## Repository Information
- **GitHub Repository**: https://github.com/russf74/TeamsShiftJune25.git
- **Current Status**: ✅ Fully backed up to GitHub cloud

## Quick Restore Instructions

### 1. Clone Repository
```bash
git clone https://github.com/russf74/TeamsShiftJune25.git
cd TeamsShiftJune25
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Required Manual Setup Files (NOT in GitHub for security)

#### A. SMTP Email Settings (`smtp_settings.json`)
Create this file with your email configuration:
```json
{
    "SmtpHost": "smtp.gmail.com",
    "SmtpPort": 587,
    "FromAddress": "your-email@gmail.com",
    "FromPassword": "your-app-password",
    "FromName": "Teams Shift Alert",
    "ToAddress": "recipient@gmail.com",
    "ToName": "Recipient Name",
    "EnableSsl": true
}
```

#### B. Main Configuration (`config.json`)
```json
{
    "scan_interval_seconds": 600
}
```

### 4. Reference Images (Included in GitHub)
These PNG files are already backed up:
- `calendar.png` - Calendar button image
- `dots.png` - Three dots menu button
- `shifts.png` - Shifts button image  
- `shiftloaded.png` - Confirmation that shifts page loaded
- `arrow.png`, `bookedshifts.png`, `openshifts.png`, `today.png`, `whatsapp.png`

### 5. Database Files (Auto-created)
These will be created automatically on first run:
- `shifts.db` - Main shift database
- `email.db` - Email tracking database

### 6. Folders (Auto-created)
- `screenshots/` - Temporary screenshot storage
- `__pycache__/` - Python cache files

## Application Files Backed Up

### Core Application
- ✅ `main.py` - Application entry point
- ✅ `gui.py` - Main GUI interface
- ✅ `automation.py` - UI automation and screen capture
- ✅ `database.py` - Database operations
- ✅ `config.py` - Configuration management
- ✅ `scheduler.py` - Task scheduling

### OCR and Processing
- ✅ `ocr_processing.py` - Main OCR processing
- ✅ `open_shift_ocr.py` - Open shift detection
- ✅ `booked_shift_ocr.py` - Booked shift detection

### Email and Alerts
- ✅ `email_alert.py` - Email notification system
- ✅ `email_db.py` - Email tracking database

### Utilities and Debug Tools
- ✅ `capture_shifts_tool.py` - Shift capture testing
- ✅ `check_daily_summary_status.py` - Status checking
- ✅ `check_image_properties.py` - Image analysis
- ✅ `debug_*.py` - Various debugging tools
- ✅ `test_*.py` - Test scripts
- ✅ `diagnose_email_status.py` - Email diagnostics
- ✅ `reset_email_db.py` - Database reset utility
- ✅ `status_server.py` - Status monitoring

### Configuration and Setup
- ✅ `requirements.txt` - Python dependencies
- ✅ `.gitignore` - Git ignore rules
- ✅ `README.md` - Project documentation

## Security Notes

### Files NOT in GitHub (for security):
- `smtp_settings.json` - Contains email credentials
- `shifts.db` - May contain personal shift data
- `email.db` - Contains email tracking data
- `screenshots/` - Temporary files, auto-cleaned
- `*.mp4` - Video recordings (midnight_reset.mp4)

### Files TO BACKUP SEPARATELY:
If you want to preserve your data across restores:
1. **Database backup**: Copy `shifts.db` to a secure location
2. **Email settings**: Keep a secure copy of `smtp_settings.json`
3. **Configuration**: Keep a copy of `config.json` with your preferred settings

## Full Restore Process

1. **Clone from GitHub**:
   ```bash
   git clone https://github.com/russf74/TeamsShiftJune25.git
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Create configuration files**:
   - Create `smtp_settings.json` with your email settings
   - Create `config.json` with your preferences
   - Optionally restore `shifts.db` if you have a backup

4. **Run the application**:
   ```bash
   python main.py
   ```

## Key Features Backed Up

✅ **Midnight Teams refresh with video recording**
✅ **Comprehensive shift scanning and OCR detection**  
✅ **Email and WhatsApp alert system**
✅ **Calendar GUI with availability tracking**
✅ **Robust error handling and date validation**
✅ **Daily summary email system**
✅ **Debug and utility tools**

## Last Updated
- **Date**: July 26, 2025
- **Commit**: Latest changes include fixed video recording and enhanced validation
- **Status**: Production ready, fully backed up

---
**Emergency Contact**: If you need help restoring, all code is in the GitHub repository with this documentation.
