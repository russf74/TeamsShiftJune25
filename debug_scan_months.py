#!/usr/bin/env python3

from datetime import datetime

def debug_scan_months():
    """Debug what months should be scanned"""
    print("=== DEBUGGING SCAN MONTHS ===")
    
    # This mimics the logic in gui.py
    import datetime as pydatetime
    now = pydatetime.datetime.now()
    
    print(f"Current date: {now.strftime('%Y-%m-%d')}")
    print(f"Scan starting from: {now.year}-{now.month:02d}")
    
    # Generate list of all months that should be scanned (4 months starting from current)
    scan_start_date = pydatetime.datetime(now.year, now.month, 1)
    scanned_months = []
    for i in range(4):
        scan_year = scan_start_date.year
        scan_month = scan_start_date.month + i
        # Handle year rollover
        while scan_month > 12:
            scan_month -= 12
            scan_year += 1
        scanned_months.append((scan_year, scan_month))
    
    print(f"\nMonths that should be scanned:")
    for i, (year, month) in enumerate(scanned_months):
        from calendar import month_name
        print(f"  Scan {i+1}: {month_name[month]} {year}")
    
    # Check what scan_four_months_with_automation should be doing
    print(f"\nAutomation call: scan_four_months_with_automation(ocr_and_store, {now.year}, {now.month})")

if __name__ == "__main__":
    debug_scan_months()