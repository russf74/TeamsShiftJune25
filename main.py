import ctypes
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)  # Per-monitor DPI aware
except Exception:
    pass

import tkinter as tk
from tkinter import messagebox
from database import init_db, remove_past_shifts, cleanup_erroneous_open_shifts, record_verified_bookings
from gui import launch_gui
from config import load_config
from version import __version__, print_version
import os
import sys
import subprocess
import logging
from datetime import datetime

# Configure logging at application start
def setup_logging():
    # Configure root logger to show INFO level logs
    logging.basicConfig(
     level=logging.INFO,
     format='[%(levelname)s] %(message)s'
  )
    # Persist crashes/startup so a dead monitor is visible after reboot.
    from logging.handlers import RotatingFileHandler
    app_log = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app_runtime.log")
    file_handler = RotatingFileHandler(app_log, maxBytes=2 * 1024 * 1024, backupCount=2)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S"))
    logging.getLogger().addHandler(file_handler)
    # Add timestamp formatter for all loggers
    for handler in logging.root.handlers:
        if not isinstance(handler, RotatingFileHandler):
            handler.setFormatter(logging.Formatter('[%(levelname)s] %(message)s'))
    
    # Print version banner
    print_version()
    
    # Log startup message with timestamp
    now = datetime.now().strftime("[%d/%m %H:%M:%S]")
    print(f"{now} Teams Shift App v{__version__} starting...")

def kill_other_instances():
    import psutil
    this_pid = os.getpid()
    this_exe = sys.executable.lower()
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['pid'] == this_pid:
                continue
            # Check if process is python and running main.py in this folder
            cmdline = proc.info.get('cmdline')
            if not cmdline:
                continue
            if (('python' in proc.info['name'].lower() or 'python' in cmdline[0].lower())
                and 'main.py' in ' '.join(cmdline)
                and os.path.abspath('.') in ' '.join(cmdline)):
                proc.kill()
        except Exception:
            pass

def main():
    try:
        import psutil
    except ImportError:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'psutil'])
        import psutil
    
    # Setup logging first thing
    setup_logging()
    
    kill_other_instances()
    # Initialize database and config
    init_db()
    # Remove any shifts whose dates have already passed
    remove_past_shifts()
    # Remove open shifts that were incorrectly detected from unavailable ('U') shift
    # tiles in Teams (identified from the purple/lavender colour blocks in prior scans).
    # These had alerted=0 so no alert was ever sent; they will be re-evaluated correctly
    # on the next scan now that the OCR fix is in place.
    cleanup_erroneous_open_shifts([
        '2026-06-17',  # scan 0 – purple block at x=1132 (June, scan 2026-06-22)
        '2026-07-15',  # scan 1 – purple block at x=997  (July,  scan 2026-06-22)
        '2026-08-04',  # scan 2 – purple block at x=406  (Aug,   scan 2026-06-22)
    ])
    # User-confirmed booking that late-month tile rejection / A-vote OCR missed.
    record_verified_bookings(
        ["2026-09-26"],
        "user-confirmed booking missed on late-month personal row",
    )
    config = load_config()

    # Start web status server in background
    try:
        from status_server import run_status_server
        run_status_server()
        logging.info("Status web server started on http://localhost:5000/")
    except Exception as e:
        logging.error(f"Failed to start status web server: {e}")
    # Start GUI
    root = tk.Tk()
    launch_gui(root, config)
    root.mainloop()

if __name__ == "__main__":
    main()
