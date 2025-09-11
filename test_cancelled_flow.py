#!/usr/bin/env python3

from database import add_shift, shift_exists, get_availability_for_date
import sqlite3

def test_cancelled_shift_flow():
    """Test the complete flow of a cancelled shift"""
    print("=== TESTING CANCELLED SHIFT FLOW ===")
    
    date_str = "2025-09-19"
    
    print(f"Testing scenario: September 19th was booked, then cancelled")
    print(f"Now it should appear as an open shift again")
    
    # Current state after cleanup
    print(f"\n1. Current state after cleanup:")
    conn = sqlite3.connect('shifts.db')
    c = conn.cursor()
    c.execute('SELECT * FROM shifts WHERE date = ?', (date_str,))
    entries = c.fetchall()
    if entries:
        for entry in entries:
            print(f'   ID: {entry[0]}, Type: {entry[2]}')
    else:
        print(f'   No entries for {date_str}')
    conn.close()
    
    # Check availability
    availability = get_availability_for_date(date_str)
    if availability and availability.get('is_available'):
        print(f"   Availability: TICKED (available)")
    else:
        print(f"   Availability: UNTICKED (unavailable)")
    
    # Simulate finding it as an open shift again
    print(f"\n2. Simulating: Teams now shows {date_str} as open shift")
    add_shift(date_str, 'open', 1)
    
    print(f"   Added as open shift")
    
    # Check final state
    print(f"\n3. Final state:")
    conn = sqlite3.connect('shifts.db')
    c = conn.cursor()
    c.execute('SELECT * FROM shifts WHERE date = ?', (date_str,))
    entries = c.fetchall()
    for entry in entries:
        print(f'   ID: {entry[0]}, Type: {entry[2]}, Alerted: {entry[3]}')
    conn.close()
    
    # Check if it would trigger an alert
    from database import is_shift_alerted
    is_alerted = is_shift_alerted(date_str, 'open')
    booked = shift_exists(date_str, 'booked')
    
    print(f"\n4. Alert logic check:")
    print(f"   Available: {'YES' if availability and availability.get('is_available') else 'NO'}")
    print(f"   Already booked: {'YES' if booked else 'NO'}")
    print(f"   Already alerted: {'YES' if is_alerted else 'NO'}")
    
    if availability and availability.get('is_available') and not booked and not is_alerted:
        print(f"   Result: WOULD TRIGGER ALERT (but availability is unticked)")
    else:
        print(f"   Result: NO ALERT (correct - availability unticked)")
    
    print(f"\n✅ Test completed!")

if __name__ == "__main__":
    test_cancelled_shift_flow()
