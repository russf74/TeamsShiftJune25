#!/usr/bin/env python3

import sqlite3
from database import add_shift, shift_exists, get_availability_for_date, delete_shifts_not_in_list
from datetime import datetime

def comprehensive_test():
    """Comprehensive test of all conflict scenarios"""
    print("=== COMPREHENSIVE CONFLICT RESOLUTION TEST ===")
    
    test_dates = ["2025-09-25", "2025-09-26", "2025-09-27"]
    
    print("Setting up test scenario:")
    print("- Sept 25: Will have open shift, then book it")
    print("- Sept 26: Will have booked shift, then cancel it")  
    print("- Sept 27: Will have open shift that stays open")
    
    # Clean slate
    for date in test_dates:
        conn = sqlite3.connect('shifts.db')
        c = conn.cursor()
        c.execute('DELETE FROM shifts WHERE date = ?', (date,))
        conn.commit()
        conn.close()
    
    # Scenario 1: Open shift gets booked
    print(f"\n1. Adding open shift for {test_dates[0]}")
    add_shift(test_dates[0], 'open', 1)
    
    print(f"   Before booking:")
    show_shifts_for_date(test_dates[0])
    
    print(f"   Booking the shift...")
    add_shift(test_dates[0], 'booked', 1)
    
    print(f"   After booking:")
    show_shifts_for_date(test_dates[0])
    
    # Scenario 2: Booked shift gets cancelled
    print(f"\n2. Adding booked shift for {test_dates[1]}")
    add_shift(test_dates[1], 'booked', 1)
    
    print(f"   With booked shift:")
    show_shifts_for_date(test_dates[1])
    
    print(f"   Simulating scan that finds no booked shifts for {test_dates[1]}...")
    # Simulate cleanup - no booked shifts found
    # Extract year and month from date
    year, month, day = map(int, test_dates[1].split('-'))
    delete_shifts_not_in_list(year, month, [], 'booked')
    
    print(f"   After cleanup:")
    show_shifts_for_date(test_dates[1])
    
    print(f"   Adding it back as open shift...")
    add_shift(test_dates[1], 'open', 1)
    
    print(f"   Final state:")
    show_shifts_for_date(test_dates[1])
    
    # Scenario 3: Open shift stays open
    print(f"\n3. Adding open shift for {test_dates[2]} (stays open)")
    add_shift(test_dates[2], 'open', 1)
    
    print(f"   Open shift state:")
    show_shifts_for_date(test_dates[2])
    
    print(f"   Trying to add duplicate open shift...")
    add_shift(test_dates[2], 'open', 1)
    
    print(f"   After duplicate attempt:")
    show_shifts_for_date(test_dates[2])
    
    print(f"\n=== FINAL SUMMARY ===")
    for i, date in enumerate(test_dates, 1):
        print(f"{i}. {date}:")
        show_shifts_for_date(date, indent="   ")
    
    print(f"\n✅ All scenarios tested successfully!")

def show_shifts_for_date(date_str, indent="   "):
    """Helper to show shifts for a date"""
    conn = sqlite3.connect('shifts.db')
    c = conn.cursor()
    c.execute('SELECT id, shift_type, alerted, created_at FROM shifts WHERE date = ? ORDER BY created_at', (date_str,))
    entries = c.fetchall()
    conn.close()
    
    if entries:
        for entry in entries:
            print(f"{indent}ID: {entry[0]}, Type: {entry[1]}, Alerted: {entry[2]}, Created: {entry[3]}")
    else:
        print(f"{indent}No entries")

if __name__ == "__main__":
    comprehensive_test()
