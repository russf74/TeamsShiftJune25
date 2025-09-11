#!/usr/bin/env python3

import sqlite3

def cleanup_conflicting_shifts():
    """Remove open shifts for dates where you're already booked"""
    conn = sqlite3.connect('shifts.db')
    c = conn.cursor()
    
    print('=== CLEANING UP CONFLICTING SHIFTS ===')
    
    # Find all dates where both open and booked shifts exist
    c.execute("""
        SELECT date 
        FROM shifts 
        WHERE shift_type = 'booked' 
        AND date IN (
            SELECT date 
            FROM shifts 
            WHERE shift_type = 'open'
        )
    """)
    
    conflicting_dates = [row[0] for row in c.fetchall()]
    
    print(f'Found {len(conflicting_dates)} dates with conflicting shifts:')
    for date in conflicting_dates:
        print(f'  - {date}')
    
    # Remove open shifts for dates where you're booked
    for date in conflicting_dates:
        print(f'Removing open shift for {date} (you are already booked)')
        c.execute('DELETE FROM shifts WHERE date = ? AND shift_type = "open"', (date,))
    
    conn.commit()
    
    print(f'\nCleaned up {len(conflicting_dates)} conflicting entries')
    
    # Verify cleanup
    print('\n=== VERIFICATION ===')
    c.execute("""
        SELECT date 
        FROM shifts 
        WHERE shift_type = 'booked' 
        AND date IN (
            SELECT date 
            FROM shifts 
            WHERE shift_type = 'open'
        )
    """)
    
    remaining_conflicts = c.fetchall()
    if remaining_conflicts:
        print(f'WARNING: {len(remaining_conflicts)} conflicts still remain!')
    else:
        print('✅ All conflicts resolved!')
    
    conn.close()

if __name__ == "__main__":
    cleanup_conflicting_shifts()
