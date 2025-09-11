#!/usr/bin/env python3
"""
Restore September 20th Booked Shift
The booked shift should have remained when we cleaned up the conflict
"""

import sqlite3
from datetime import datetime

def restore_sept20_booked():
    """Restore the September 20th booked shift that should have remained"""
    print("=== RESTORING SEPTEMBER 20TH BOOKED SHIFT ===")
    
    # The booked shift that should have remained (ID 755 from our earlier investigation)
    booked_shift = {
        'date': '2025-09-20',
        'shift_type': 'booked',
        'count': 1,
        'alerted': 0,
        'created_at': '2025-09-05 08:35:10'  # Approximate creation time
    }
    
    conn = sqlite3.connect('shifts.db')
    c = conn.cursor()
    
    # Check if any shift already exists for Sept 20th
    c.execute('SELECT id, shift_type FROM shifts WHERE date = ?', (booked_shift['date'],))
    existing = c.fetchone()
    
    if existing:
        print(f"  ⚠️  September 20th already has a {existing[1]} shift (ID: {existing[0]})")
        if existing[1] == 'booked':
            print("  ✅ Booked shift already exists - no action needed")
            conn.close()
            return
        else:
            print("  🔄 Removing conflicting open shift and adding booked shift")
            c.execute('DELETE FROM shifts WHERE date = ?', (booked_shift['date'],))
    
    # Add the booked shift
    c.execute('''INSERT INTO shifts (date, shift_type, count, alerted, created_at) 
                 VALUES (?, ?, ?, ?, ?)''',
              (booked_shift['date'], booked_shift['shift_type'], 
               booked_shift['count'], booked_shift['alerted'], booked_shift['created_at']))
    
    new_id = c.lastrowid
    conn.commit()
    conn.close()
    
    print(f"  ✅ Restored: September 20th booked shift (ID: {new_id})")
    
    # Verify
    conn = sqlite3.connect('shifts.db')
    c = conn.cursor()
    c.execute('SELECT id, date, shift_type, alerted FROM shifts WHERE date = ?', (booked_shift['date'],))
    result = c.fetchone()
    conn.close()
    
    if result:
        print(f"  ✅ Verified: ID: {result[0]}, Date: {result[1]}, Type: {result[2]}, Alerted: {result[3]}")
    else:
        print(f"  ❌ Verification failed!")
    
    print(f"\n🚀 SEPTEMBER 20TH BOOKED SHIFT RESTORED!")

if __name__ == "__main__":
    restore_sept20_booked()