#!/usr/bin/env python3

import sqlite3
from datetime import datetime

def manual_november_cleanup():
    """Manually clean up the stale November shifts based on what's actually in Teams"""
    print("=== MANUAL NOVEMBER CLEANUP ===")
    
    # Based on your Teams screenshot, November should only have these open shifts:
    correct_november_shifts = {
        '2025-11-03': 'open',  # 3rd 
        '2025-11-05': 'open',  # 5th
        '2025-11-25': 'open',  # 25th
        '2025-11-26': 'open',  # 26th
    }
    
    conn = sqlite3.connect('shifts.db')
    c = conn.cursor()
    
    # Get all current November shifts
    c.execute('SELECT id, date, shift_type FROM shifts WHERE date >= "2025-11-01" AND date < "2025-12-01"')
    current_shifts = c.fetchall()
    
    print(f"Current November shifts in database: {len(current_shifts)}")
    for shift in current_shifts:
        print(f"  ID: {shift[0]}, Date: {shift[1]}, Type: {shift[2]}")
    
    # Remove shifts that shouldn't exist
    removed_count = 0
    for shift in current_shifts:
        shift_id, date, shift_type = shift
        
        if date in correct_november_shifts:
            # Check if type matches
            if correct_november_shifts[date] == shift_type:
                print(f"  ✅ Keeping: {date} ({shift_type}) - matches Teams")
            else:
                print(f"  ❌ Removing: {date} ({shift_type}) - wrong type, should be {correct_november_shifts[date]}")
                c.execute('DELETE FROM shifts WHERE id = ?', (shift_id,))
                removed_count += 1
        else:
            print(f"  ❌ Removing: {date} ({shift_type}) - not in Teams anymore")
            c.execute('DELETE FROM shifts WHERE id = ?', (shift_id,))
            removed_count += 1
    
    # Add any missing shifts that should exist
    added_count = 0
    for date, shift_type in correct_november_shifts.items():
        c.execute('SELECT id FROM shifts WHERE date = ? AND shift_type = ?', (date, shift_type))
        if not c.fetchone():
            print(f"  ➕ Adding missing: {date} ({shift_type})")
            c.execute('INSERT INTO shifts (date, shift_type, count, alerted, created_at) VALUES (?, ?, 1, 0, ?)', 
                     (date, shift_type, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            added_count += 1
    
    conn.commit()
    conn.close()
    
    print(f"\n🧹 CLEANUP COMPLETED:")
    print(f"  • Removed {removed_count} stale shifts")
    print(f"  • Added {added_count} missing shifts")
    
    # Verify final state
    conn = sqlite3.connect('shifts.db')
    c = conn.cursor()
    c.execute('SELECT id, date, shift_type FROM shifts WHERE date >= "2025-11-01" AND date < "2025-12-01" ORDER BY date')
    final_shifts = c.fetchall()
    conn.close()
    
    print(f"\nFinal November state ({len(final_shifts)} shifts):")
    for shift in final_shifts:
        print(f"  ID: {shift[0]}, Date: {shift[1]}, Type: {shift[2]}")
    
    print(f"\n✅ November should now match Teams exactly!")

if __name__ == "__main__":
    manual_november_cleanup()