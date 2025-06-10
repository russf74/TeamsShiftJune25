
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
    kill_other_instances()
    # Initialize database and config
    init_db()
    config = load_config()

    # Start GUI
    root = tk.Tk()
    launch_gui(root, config)
    # Background scheduler removed; all auto-scanning is now controlled by the GUI.
    root.mainloop()

if __name__ == "__main__":
    main()
