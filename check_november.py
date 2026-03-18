#!/usr/bin/env python3

import sqlite3

def check_november_shifts():
    """Check what shifts exist for November 2025"""
    print("=== NOVEMBER 2025 SHIFTS ===")
    
    conn = sqlite3.connect('shifts.db')
    c = conn.cursor()
    c.execute('SELECT id, date, shift_type, alerted, created_at FROM shifts WHERE date >= "2025-11-01" AND date < "2025-12-01" ORDER BY date')
    entries = c.fetchall()
    conn.close()
    
    if entries:
        print(f"Found {len(entries)} November shifts:")
        for entry in entries:
            print(f'  ID: {entry[0]}, Date: {entry[1]}, Type: {entry[2]}, Alerted: {entry[3]}, Created: {entry[4]}')
    else:
        print("No November shifts found in database")
    
    return entries

def explain_cleanup_system():
    """Explain how the cleanup should work"""
    print("\n=== HOW CLEANUP SHOULD WORK ===")
    print("1. When you scan, the app finds shifts currently available in Teams")
    print("2. It stores these in found_open_shifts_by_month and found_booked_shifts_by_month")
    print("3. After scanning, it calls delete_shifts_not_in_list() for each month")
    print("4. This removes any shifts from database that are NOT in the current scan results")
    print("5. So if a shift was there before but not found in latest scan, it gets removed")
    
    print("\n=== POSSIBLE ISSUES ===")
    print("• The scanning might not be reaching November (only scanning near months)")
    print("• The cleanup might be skipped for November due to safety checks")
    print("• The shift detection logic might not be working for future months")

if __name__ == "__main__":
    november_shifts = check_november_shifts()
    explain_cleanup_system()
    
    if november_shifts:
        print(f"\n❓ INVESTIGATION NEEDED:")
        print(f"You have {len(november_shifts)} November shifts in database")
        print(f"If these aren't showing in Teams anymore, the cleanup should have removed them")
        print(f"This suggests either:")
        print(f"  1. The scan isn't reaching November")
        print(f"  2. The cleanup is being skipped") 
        print(f"  3. There's a bug in the shift detection")