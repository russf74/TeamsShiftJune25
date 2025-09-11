#!/usr/bin/env python3
"""
Emergency Recovery Script for Lost September Shifts
Recreates the September shifts that were accidentally deleted
"""

import sqlite3
from datetime import datetime

def restore_september_shifts():
    """Restore the lost September shifts based on the IDs we know were deleted"""
    print("=== EMERGENCY SEPTEMBER SHIFTS RECOVERY ===")
    
    # The shifts we know were deleted (from our earlier check):
    lost_shifts = [
        {
            'id': 751,
            'date': '2025-09-18',
            'shift_type': 'open',
            'count': 1,
            'alerted': 0,
            'created_at': '2025-09-05 08:35:10'
        },
        {
            'id': 753,
            'date': '2025-09-07',
            'shift_type': 'open', 
            'count': 1,
            'alerted': 0,
            'created_at': '2025-09-05 08:35:11'
        },
        {
            'id': 761,
            'date': '2025-09-19',
            'shift_type': 'open',
            'count': 1, 
            'alerted': 0,
            'created_at': '2025-09-11 15:47:57'
        }
    ]
    
    conn = sqlite3.connect('shifts.db')
    c = conn.cursor()
    
    print("Restoring lost September shifts:")
    for shift in lost_shifts:
        # Check if this ID or date already exists
        c.execute('SELECT id FROM shifts WHERE id = ? OR date = ?', (shift['id'], shift['date']))
        existing = c.fetchone()
        
        if existing:
            print(f"  ⚠️  Skipping {shift['date']} - already exists (ID: {existing[0]})")
            continue
            
        # Insert the shift back
        c.execute('''INSERT INTO shifts (id, date, shift_type, count, alerted, created_at) 
                     VALUES (?, ?, ?, ?, ?, ?)''',
                  (shift['id'], shift['date'], shift['shift_type'], 
                   shift['count'], shift['alerted'], shift['created_at']))
        
        print(f"  ✅ Restored: {shift['date']} (ID: {shift['id']}) - {shift['shift_type']} shift")
    
    conn.commit()
    conn.close()
    
    print("\n=== VERIFICATION ===")
    # Verify restoration
    conn = sqlite3.connect('shifts.db')
    c = conn.cursor()
    c.execute('SELECT id, date, shift_type FROM shifts WHERE date >= "2025-09-01" AND date < "2025-10-01" ORDER BY date')
    restored = c.fetchall()
    conn.close()
    
    print(f"September shifts now in database ({len(restored)} total):")
    for shift in restored:
        print(f"  ID: {shift[0]}, Date: {shift[1]}, Type: {shift[2]}")
    
    print(f"\n🚀 RECOVERY COMPLETED!")
    return True

if __name__ == "__main__":
    restore_september_shifts()