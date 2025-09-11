#!/usr/bin/env python3

import sqlite3

def check_current_shifts():
    """Check current shifts in database without making changes"""
    print("=== CURRENT SHIFTS IN DATABASE ===")
    
    conn = sqlite3.connect('shifts.db')
    c = conn.cursor()
    
    # Check September 2025 shifts
    c.execute('SELECT id, date, shift_type, alerted, created_at FROM shifts WHERE date >= "2025-09-01" ORDER BY date')
    september_entries = c.fetchall()
    
    print(f"SEPTEMBER 2025 SHIFTS ({len(september_entries)} entries):")
    if september_entries:
        for entry in september_entries:
            print(f'  ID: {entry[0]}, Date: {entry[1]}, Type: {entry[2]}, Alerted: {entry[3]}, Created: {entry[4]}')
    else:
        print("  No September shifts found")
    
    # Check all recent shifts
    c.execute('SELECT id, date, shift_type, alerted, created_at FROM shifts ORDER BY date DESC LIMIT 20')
    recent_entries = c.fetchall()
    
    print(f"\nMOST RECENT SHIFTS ({len(recent_entries)} entries):")
    for entry in recent_entries:
        print(f'  ID: {entry[0]}, Date: {entry[1]}, Type: {entry[2]}, Alerted: {entry[3]}, Created: {entry[4]}')
    
    conn.close()
    print("\n✅ Database check completed - NO CHANGES MADE")

if __name__ == "__main__":
    check_current_shifts()
