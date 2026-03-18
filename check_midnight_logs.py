#!/usr/bin/env python3
"""Quick script to check logs around midnight (00:00-00:30)"""

import os
from datetime import datetime

log_file = 'shift_operations.log'

if not os.path.exists(log_file):
    print(f"ERROR: {log_file} not found")
    exit(1)

# Get today's date
today = datetime.now().strftime('%Y-%m-%d')

print(f"Searching for logs from {today} 00:00 to 00:30...")
print("=" * 80)

found = False
with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
    for line in f:
        # Look for today's date and hour 00
        if today in line and ' 00:' in line:
            # Extract time to filter 00:00-00:30
      try:
            time_part = line.split('][')[0].split('[')[1]
        if ':' in time_part:
          parts = time_part.split(':')
   if len(parts) >= 3:
        hour = int(parts[1])
      minute = int(parts[2])
          if hour == 0 and minute <= 30:
                print(line.rstrip())
       found = True
            except:
     pass

if not found:
    print(f"\nNo logs found for {today} 00:00-00:30")
    print("\nShowing last 50 lines of log file instead:")
    print("=" * 80)
    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
  lines = f.readlines()
      for line in lines[-50:]:
      print(line.rstrip())
