import ctypes
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)  # Per-monitor DPI aware
except Exception:
    pass

import tkinter as tk
from tkinter import messagebox
from database import init_db
from gui import launch_gui
from config import load_config
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
    # Add timestamp formatter for all loggers
    for handler in logging.root.handlers:
        handler.setFormatter(logging.Formatter('[%(levelname)s] %(message)s'))
    
    # Log startup message with timestamp
    now = datetime.now().strftime("[%d/%m %H:%M:%S]")
    print(f"{now} Teams Shift App starting...")

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
