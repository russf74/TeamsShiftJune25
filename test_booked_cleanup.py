#!/usr/bin/env python3

import sqlite3
from database import delete_shifts_not_in_list

def test_booked_shift_cleanup():
    """Test the cleanup of stale booked shifts"""
    print("=== TESTING BOOKED SHIFT CLEANUP ===")
    
    # Current state: September 19th should have a stale booked entry
    print("Before cleanup:")
    conn = sqlite3.connect('shifts.db')
    c = conn.cursor()
    c.execute('SELECT * FROM shifts WHERE date = ?', ('2025-09-19',))
    entries = c.fetchall()
    for entry in entries:
        print(f'  ID: {entry[0]}, Date: {entry[1]}, Type: {entry[2]}, Created: {entry[6]}')
    conn.close()
    
    # Simulate a scan that finds no booked shifts for September 2025
    # (i.e., September 19th is no longer booked)
    print(f"\nSimulating scan: No booked shifts found for September 2025")
    found_booked_dates = set()  # Empty set = no booked shifts found
    
    # Run cleanup
    delete_shifts_not_in_list(2025, 9, found_booked_dates, shift_type='booked')
    
    print("After cleanup:")
    conn = sqlite3.connect('shifts.db')
    c = conn.cursor()
    c.execute('SELECT * FROM shifts WHERE date = ?', ('2025-09-19',))
    entries = c.fetchall()
    if entries:
        for entry in entries:
            print(f'  ID: {entry[0]}, Date: {entry[1]}, Type: {entry[2]}, Created: {entry[6]}')
    else:
        print('  No entries found for 2025-09-19')
    conn.close()
    
    print("\n✅ Test completed!")

if __name__ == "__main__":
    test_booked_shift_cleanup()
