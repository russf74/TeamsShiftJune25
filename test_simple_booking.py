#!/usr/bin/env python3

import sqlite3
from database import add_shift

def simple_test():
    """Simple test of booking conflict resolution"""
    date_str = "2025-09-28"
    
    # Clean slate
    conn = sqlite3.connect('shifts.db')
    c = conn.cursor()
    c.execute('DELETE FROM shifts WHERE date = ?', (date_str,))
    conn.commit()
    conn.close()
    
    print(f"Testing booking conflict for {date_str}")
    
    # Add open shift
    print("1. Adding open shift")
    add_shift(date_str, 'open', 1)
    
    conn = sqlite3.connect('shifts.db')
    c = conn.cursor()
    c.execute('SELECT id, shift_type, created_at FROM shifts WHERE date = ?', (date_str,))
    entries = c.fetchall()
    print(f"   After adding open: {entries}")
    conn.close()
    
    # Book the shift
    print("2. Booking the shift")
    add_shift(date_str, 'booked', 1)
    
    conn = sqlite3.connect('shifts.db')
    c = conn.cursor()
    c.execute('SELECT id, shift_type, created_at FROM shifts WHERE date = ?', (date_str,))
    entries = c.fetchall()
    print(f"   After booking: {entries}")
    conn.close()
    
    print("✅ Simple test completed")

if __name__ == "__main__":
    simple_test()
