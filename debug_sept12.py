#!/usr/bin/env python3

from database import *
import sqlite3

def check_september_12():
    conn = sqlite3.connect('shifts.db')
    c = conn.cursor()
    
    # Check all September 12th shifts
    c.execute("SELECT date, shift_type, alerted FROM shifts WHERE date LIKE '%-09-12'")
    sept12_shifts = c.fetchall()
    
    print("September 12th shifts in database:")
    for row in sept12_shifts:
        print(f"  Date: {row[0]}, Type: {row[1]}, Alerted: {row[2]}")
    
    # Check if is_shift_alerted function works correctly
    print("\nTesting is_shift_alerted function:")
    for row in sept12_shifts:
        date_str = row[0]
        shift_type = row[1]
        result = is_shift_alerted(date_str, shift_type)
        print(f"  is_shift_alerted('{date_str}', '{shift_type}') = {result}")
    
    conn.close()

if __name__ == "__main__":
    check_september_12()
