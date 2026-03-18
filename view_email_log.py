#!/usr/bin/env python3
"""View all email log history"""

import sqlite3
from datetime import datetime

conn = sqlite3.connect('shifts.db')
c = conn.cursor()

print("=" * 80)
print("EMAIL LOG HISTORY (Daily Summary Emails Only)")
print("=" * 80)

# Create table if it doesn't exist
c.execute('''CREATE TABLE IF NOT EXISTS email_log 
     (date TEXT PRIMARY KEY, sent INTEGER, sent_time TEXT)''')

# Get all email log entries
c.execute("SELECT date, sent, sent_time FROM email_log ORDER BY date DESC")
entries = c.fetchall()

if entries:
    print(f"\nTotal daily summary emails logged: {len(entries)}\n")
    print(f"{'Date':<15} {'Sent':<10} {'Time Sent':<25}")
    print("-" * 80)
    
    for date_val, sent, sent_time in entries:
        sent_status = "YES" if sent == 1 else "NO"
        time_display = sent_time if sent_time else "N/A"
        print(f"{date_val:<15} {sent_status:<10} {time_display:<25}")
    
    # Show summary stats
    print("\n" + "=" * 80)
    print("SUMMARY:")
    print("=" * 80)
    
    # Most recent
    if entries[0][2]:
        print(f"Most recent daily summary: {entries[0][0]} at {entries[0][2]}")
    else:
        print(f"Most recent daily summary: {entries[0][0]} (no timestamp)")
    
    # Oldest
    if entries[-1][2]:
        print(f"Oldest daily summary: {entries[-1][0]} at {entries[-1][2]}")
    else:
        print(f"Oldest daily summary: {entries[-1][0]} (no timestamp)")
    
    # Count by month
    from collections import defaultdict
    by_month = defaultdict(int)
    for date_val, _, _ in entries:
        try:
            month_key = date_val[:7]  # YYYY-MM
            by_month[month_key] += 1
        except:
            pass
    
    if by_month:
        print(f"\nEmails per month:")
        for month in sorted(by_month.keys(), reverse=True):
            print(f"  {month}: {by_month[month]} emails")

else:
    print("\nNo email log entries found.")
    print("\nThis means:")
    print("  - The app has never sent a daily summary email, OR")
    print("  - The email_log table was recently created/cleared")

conn.close()

print("\n" + "=" * 80)
print("NOTE: This log ONLY tracks daily summary emails sent at 8pm.")
print("It does NOT track:")
print("  - Individual shift confirmation emails")
print("  - Open shift alert emails")
print("  - Midnight refresh notification emails")
print("=" * 80)
