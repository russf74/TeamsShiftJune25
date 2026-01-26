#!/usr/bin/env python3
"""
Real-time log viewer for shift operations
Shows all deletions, additions, updates, and emails related to shifts
"""

import os
import sys
from datetime import datetime

log_file = 'shift_operations.log'

def tail_log(n=50):
    """Show last n lines of the log"""
    if not os.path.exists(log_file):
        print(f"No log file found at {log_file}")
        print("The log file will be created when the app runs.")
        return
    
    with open(log_file, 'r') as f:
        lines = f.readlines()
    
    if not lines:
        print("Log file is empty")
        return

    print("=" * 100)
    print(f"LAST {min(n, len(lines))} OPERATIONS (most recent at bottom)")
    print("=" * 100)
    
    for line in lines[-n:]:
        # Highlight important operations
        if 'DELETING' in line:
            print(f"\033[91m{line.strip()}\033[0m")  # Red
        elif 'RE-ADDING' in line:
            print(f"\033[93m{line.strip()}\033[0m")  # Yellow
        elif 'SENDING' in line:
            print(f"\033[92m{line.strip()}\033[0m")  # Green
        elif 'BLOCKED' in line:
            print(f"\033[95m{line.strip()}\033[0m")  # Magenta
        else:
            print(line.strip())

def search_log(search_term):
    """Search for specific term in log"""
    if not os.path.exists(log_file):
        print(f"No log file found at {log_file}")
        return
    
    with open(log_file, 'r') as f:
        lines = f.readlines()
    
    matches = [line for line in lines if search_term.lower() in line.lower()]
    
    if not matches:
        print(f"No matches found for '{search_term}'")
        return
    
    print("=" * 100)
    print(f"FOUND {len(matches)} MATCHES FOR '{search_term}'")
    print("=" * 100)
    
    for line in matches:
        if 'DELETING' in line:
            print(f"\033[91m{line.strip()}\033[0m")
        elif 'RE-ADDING' in line:
            print(f"\033[93m{line.strip()}\033[0m")
        elif 'SENDING' in line:
            print(f"\033[92m{line.strip()}\033[0m")
        else:
            print(line.strip())

def watch_jan31():
    """Show all operations related to Jan 31st"""
    search_log("2026-01-31")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "jan31":
            watch_jan31()
        else:
            search_log(sys.argv[1])
    else:
        tail_log(50)
    
    print("\n" + "=" * 100)
    print("USAGE:")
    print("  python view_shift_logs.py          - Show last 50 operations")
    print("  python view_shift_logs.py jan31    - Show all Jan 31st operations")
    print("  python view_shift_logs.py <term>   - Search for specific term")
    print("=" * 100)
