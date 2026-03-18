#!/usr/bin/env python3

import sqlite3
import os
import glob
from datetime import datetime

def analyze_recent_scan():
    """Analyze the most recent scan to understand what went wrong"""
    print("=== ANALYZING RECENT SCAN ===")
    
    # Check for recent screenshots
    screenshot_dir = os.path.join(os.getcwd(), 'screenshots')
    if os.path.exists(screenshot_dir):
        files = glob.glob(os.path.join(screenshot_dir, '*.png'))
        if files:
            # Get the most recent timestamp
            timestamps = set()
            for f in files:
                import re
                m = re.search(r'(\d{8}_\d{6})', f)
                if m:
                    timestamps.add(m.group(1))
            
            if timestamps:
                latest_timestamp = sorted(timestamps)[-1]
                print(f"Latest scan timestamp: {latest_timestamp}")
                
                # Check which months were scanned
                month_files = []
                for i in range(4):
                    pattern = f"{i}-shifts_screenshot_{latest_timestamp}*.png"
                    matches = glob.glob(os.path.join(screenshot_dir, pattern))
                    if matches:
                        month_files.append((i, matches[0]))
                        print(f"  Month {i+1}: {os.path.basename(matches[0])}")
                
                # Try to extract what was detected from each month
                print(f"\nAnalyzing detection results:")
                for scan_index, file_path in month_files:
                    print(f"\n--- SCAN {scan_index + 1} ---")
                    # Look for corresponding debug files
                    base_name = os.path.basename(file_path).replace('.png', '')
                    debug_files = glob.glob(os.path.join(screenshot_dir, f"{base_name}*"))
                    
                    # Check for specific debug files that show what was detected
                    open_blocks_file = None
                    booked_regions_file = None
                    
                    for debug_file in debug_files:
                        if 'open_shifts_blocks' in debug_file:
                            open_blocks_file = debug_file
                        elif 'booked_shifts_date_regions' in debug_file:
                            booked_regions_file = debug_file
                    
                    if open_blocks_file:
                        print(f"  Open shifts detected: {os.path.basename(open_blocks_file)}")
                    if booked_regions_file:
                        print(f"  Booked shifts detected: {os.path.basename(booked_regions_file)}")
            else:
                print("No timestamps found in screenshot files")
        else:
            print("No screenshot files found")
    else:
        print("Screenshots directory doesn't exist")
    
    # Check current scan counts for each month
    print(f"\n=== CURRENT DATABASE STATE ===")
    conn = sqlite3.connect('shifts.db')
    c = conn.cursor()
    
    for month_offset in range(4):
        base_date = datetime(2025, 9 + month_offset, 1)  # Starting from September
        if base_date.month > 12:
            base_date = datetime(base_date.year + 1, base_date.month - 12, 1)
        
        start_date = f"{base_date.year}-{base_date.month:02d}-01"
        if base_date.month == 12:
            end_date = f"{base_date.year + 1}-01-01"
        else:
            end_date = f"{base_date.year}-{base_date.month + 1:02d}-01"
        
        c.execute('SELECT shift_type, COUNT(*) FROM shifts WHERE date >= ? AND date < ? GROUP BY shift_type', 
                 (start_date, end_date))
        results = c.fetchall()
        
        from calendar import month_name
        print(f"{month_name[base_date.month]} {base_date.year}:")
        if results:
            for shift_type, count in results:
                print(f"  {shift_type}: {count} shifts")
        else:
            print(f"  No shifts")
    
    conn.close()

if __name__ == "__main__":
    analyze_recent_scan()