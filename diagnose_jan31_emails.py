#!/usr/bin/env python3
"""Diagnostic: Check Jan 31st shift confirmation email status"""

import sqlite3
from datetime import datetime

conn = sqlite3.connect('shifts.db')
c = conn.cursor()

print("=" * 60)
print("JAN 31ST CONFIRMATION EMAIL DIAGNOSTIC")
print("=" * 60)

# Check the shift record for Jan 31st
c.execute("""
    SELECT date, shift_type, count, alerted, confirmed_email_sent, created_at 
    FROM shifts 
    WHERE date = '2025-01-31'
""")

shift = c.fetchone()

if shift:
    print("\nFOUND SHIFT FOR 2025-01-31:")
    print(f"  Date: {shift[0]}")
    print(f"  Type: {shift[1]}")
    print(f"  Count: {shift[2]}")
    print(f"  Alerted: {shift[3]}")
    print(f"  Confirmed Email Sent: {shift[4]}")
    print(f"  Created At: {shift[5]}")
    
    # Check if it's a past date
    shift_date = datetime.strptime(shift[0], "%Y-%m-%d").date()
    today = datetime.now().date()
    days_diff = (today - shift_date).days
    
    if days_diff > 0:
        print(f"\n  WARNING: This shift was {days_diff} days AGO")
        print("  WARNING: Past-date safety check should prevent confirmation emails")
    
    # The problem: confirmed_email_sent flag
    if shift[4] == 0:
        print("\nPROBLEM FOUND:")
        print("  confirmed_email_sent flag is 0 (NOT SET)")
        print("  This means the system thinks NO confirmation email was ever sent")
        print("  BUT you say you keep getting confirmation emails!")
        print("\nPOSSIBLE CAUSES:")
        print("  1. Email is NOT the confirmation email - check your inbox for subject line")
        print("  2. The flag is getting reset somehow (scan re-adding the shift)")
        print("  3. You're seeing the Jan 31st shift in DAILY SUMMARY emails (different)")
    elif shift[4] == 1:
        print("\nconfirmed_email_sent flag is 1 (SET)")
        print("  The system thinks a confirmation email WAS sent")
        print("  No more confirmation emails should be sent for this shift")
        print("\n  If you're still getting emails about Jan 31st, they are likely:")
        print("  - DAILY SUMMARY emails (sent at 8pm daily)")
        print("  - NOT confirmation emails")
else:
    print("\nNO SHIFT FOUND FOR 2025-01-31")
    print("  The shift may have been deleted or never existed")
    print("\n  If you're getting emails about Jan 31st, check:")
    print("  - Email subject line - is it 'Shift Confirmed' or 'Daily Summary'?")
    print("  - The shift might be showing in daily summary for a different reason")

# Check all future booked shifts to see pattern
print("\n" + "=" * 60)
print("ALL BOOKED SHIFTS (INCLUDING PAST):")
print("=" * 60)

c.execute("""
    SELECT date, confirmed_email_sent, created_at
    FROM shifts
    WHERE shift_type = 'booked'
    ORDER BY date ASC
""")

all_booked = c.fetchall()

if all_booked:
    for shift_data in all_booked:
        date_str, conf_sent, created = shift_data
        conf_status = "SENT" if conf_sent == 1 else "NOT SENT"
        print(f"  {date_str} - Confirmation: {conf_status} - Created: {created}")
else:
    print("  No booked shifts found")

conn.close()

print("\n" + "=" * 60)
print("RECOMMENDATION:")
print("=" * 60)
print("1. Check your email inbox - what is the EXACT SUBJECT LINE?")
print("   - 'Shift Confirmed: Fri 31 Jan' = Confirmation email (one-time)")
print("   - 'Teams Shift Daily Summary' = Daily summary (every evening)")
print("")
print("2. If subject is 'Daily Summary', the Jan 31st shift is appearing")
print("   in your daily summary list because it's appearing incorrectly")
print("")
print("3. Run this script again to check the confirmed_email_sent flag")
