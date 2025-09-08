#!/usr/bin/env python3

from database import *
import sqlite3

def debug_shift_logic():
    date_str = "2025-09-12"
    
    print(f"=== Debugging logic for {date_str} ===")
    
    # Test shift_exists
    exists_open = shift_exists(date_str, 'open')
    exists_booked = shift_exists(date_str, 'booked')
    print(f"shift_exists('{date_str}', 'open') = {exists_open}")
    print(f"shift_exists('{date_str}', 'booked') = {exists_booked}")
    
    # Test is_shift_alerted
    is_alerted = is_shift_alerted(date_str, 'open')
    print(f"is_shift_alerted('{date_str}', 'open') = {is_alerted}")
    
    # Test availability
    availability = get_availability_for_date(date_str)
    print(f"get_availability_for_date('{date_str}') = {availability}")
    
    # Check all database entries for this date
    conn = sqlite3.connect('shifts.db')
    c = conn.cursor()
    c.execute("SELECT * FROM shifts WHERE date = ?", (date_str,))
    all_entries = c.fetchall()
    print(f"\nAll database entries for {date_str}:")
    for entry in all_entries:
        print(f"  {entry}")
    
    # Check availability table
    c.execute("SELECT * FROM availability WHERE date = ?", (date_str,))
    avail_entries = c.fetchall()
    print(f"\nAvailability entries for {date_str}:")
    for entry in avail_entries:
        print(f"  {entry}")
    
    conn.close()
    
    print(f"\n=== Logic Flow Analysis ===")
    if not exists_open:
        print("Would take NEW SHIFT path (line 757)")
        print("  - Would add to database")
        print("  - Would check availability without checking alerted status")
        if availability and availability.get('is_available'):
            print("  - Would add to matched_dates (PROBLEM!)")
        else:
            print("  - Would NOT add to matched_dates (availability check fails)")
    else:
        print("Would take EXISTING SHIFT path (line 771)")
        print(f"  - is_already_alerted = {is_alerted}")
        if availability and availability.get('is_available') and not exists_booked and not is_alerted:
            print("  - Would add to matched_dates")
        else:
            print("  - Would NOT add to matched_dates (checks prevent it)")

if __name__ == "__main__":
    debug_shift_logic()
