# Teams Shift Database and Alert

A professional Windows desktop application for automating Microsoft Teams Shifts monitoring, using Python, Tkinter, SQLite, OpenCV, pytesseract, pyautogui/pywinauto, and Gmail integration.

## Features
- GUI for entering your shift availability and settings
- Automated screen scanning and OCR to detect open/booked shifts
- Local SQLite database for shift and availability tracking
- Email alerts via Gmail for available open shifts
- Robust, modular, and production-ready codebase

## Getting Started
1. Ensure you have Python 3.9+ installed on Windows.
2. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
3. Run the application:
   ```powershell
   python main.py
   ```

## Project Structure
- `main.py` - Entry point
- `gui.py` - Tkinter GUI
- `automation.py` - Teams window automation
- `ocr_processing.py` - Image processing and OCR
- `database.py` - SQLite logic
- `email_alert.py` - Gmail integration
- `scheduler.py` - Periodic scanning
- `config.py` - App configuration

## Notes
- You will need to set up a Gmail app password for email alerts.
- All data is stored locally in SQLite.

---
