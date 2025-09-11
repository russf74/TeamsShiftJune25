#!/usr/bin/env python3

from database import add_shift, shift_exists
import sqlite3

def test_conflict_prevention():
    """Test that the database prevents conflicting shift types"""
    print("=== TESTING CONFLICT PREVENTION ===")
    
    test_date = "2025-12-25"  # Use a future date for testing
    
    # Clean up any existing test data
    conn = sqlite3.connect('shifts.db')
    c = conn.cursor()
    c.execute('DELETE FROM shifts WHERE date = ?', (test_date,))
    conn.commit()
    conn.close()
    
    print(f"Testing with date: {test_date}")
    
    # Test 1: Add booked shift first, then try to add open shift
    print("\n--- Test 1: Booked first, then open ---")
    add_shift(test_date, 'booked', 1)
    print(f"Added booked shift for {test_date}")
    
    print(f"Booked shift exists: {shift_exists(test_date, 'booked')}")
    print(f"Open shift exists: {shift_exists(test_date, 'open')}")
    
    # This should be prevented
    add_shift(test_date, 'open', 2)
    print("Attempted to add open shift...")
    
    print(f"After attempt - Booked shift exists: {shift_exists(test_date, 'booked')}")
    print(f"After attempt - Open shift exists: {shift_exists(test_date, 'open')}")
    
    # Test 2: Clean up and test the reverse
    print("\n--- Test 2: Open first, then booked ---")
    conn = sqlite3.connect('shifts.db')
    c = conn.cursor()
    c.execute('DELETE FROM shifts WHERE date = ?', (test_date,))
    conn.commit()
    conn.close()
    
    add_shift(test_date, 'open', 1)
    print(f"Added open shift for {test_date}")
    
    print(f"Open shift exists: {shift_exists(test_date, 'open')}")
    print(f"Booked shift exists: {shift_exists(test_date, 'booked')}")
    
    # This should remove the open shift and add the booked shift
    add_shift(test_date, 'booked', 1)
    print("Added booked shift...")
    
    print(f"After addition - Open shift exists: {shift_exists(test_date, 'open')}")
    print(f"After addition - Booked shift exists: {shift_exists(test_date, 'booked')}")
    
    # Clean up
    conn = sqlite3.connect('shifts.db')
    c = conn.cursor()
    c.execute('DELETE FROM shifts WHERE date = ?', (test_date,))
    conn.commit()
    conn.close()
    
    print(f"\n✅ Test completed - cleaned up {test_date}")

if __name__ == "__main__":
    test_conflict_prevention()
