#!/usr/bin/env python3

import sqlite3

def check_sept20():
    """Check for September 20th shifts"""
    print("=== CHECKING SEPTEMBER 20TH SHIFTS ===")
    
    conn = sqlite3.connect('shifts.db')
    c = conn.cursor()
    c.execute('SELECT id, date, shift_type, alerted, created_at FROM shifts WHERE date = ?', ('2025-09-20',))
    entries = c.fetchall()
    conn.close()
    
    if entries:
        print(f"Found {len(entries)} shift(s) for September 20th:")
        for entry in entries:
            print(f'  ID: {entry[0]}, Date: {entry[1]}, Type: {entry[2]}, Alerted: {entry[3]}, Created: {entry[4]}')
    else:
        print("❌ No shifts found for September 20th")
        print("\nThe September 20th booked shift was NOT restored.")
        print("This was one of the conflicting entries we removed earlier to fix the duplicate issue.")
        print("The emergency restore only recovered the legitimate September shifts (7th, 18th, 19th).")

if __name__ == "__main__":
    check_sept20()