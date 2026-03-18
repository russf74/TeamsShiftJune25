import sqlite3
from datetime import datetime

conn = sqlite3.connect('shifts.db')
c = conn.cursor()

# Check March 27 shift status
c.execute("SELECT * FROM shifts WHERE date='2026-03-27'")
rows = c.fetchall()

print("=" * 80)
print("MARCH 27, 2026 SHIFT STATUS")
print("=" * 80)

if rows:
    for row in rows:
        print(f"\nDate: {row[1]}")
        print(f"Type: {row[2]}")
        print(f"Count: {row[3]}")
        print(f"Alerted: {row[4]}")
        print(f"Created At: {row[5]}")
        if len(row) > 6:
            print(f"Confirmed Email Sent: {row[6]}")
else:
    print("\nNo shifts found for 2026-03-27")

# Check availability for March 27
c.execute("SELECT * FROM availability WHERE date='2026-03-27'")
avail = c.fetchall()

print("\n" + "=" * 80)
print("AVAILABILITY STATUS")
print("=" * 80)

if avail:
    for a in avail:
        print(f"Date: {a[0]}, Available: {a[1]}")
else:
    print("No availability set for 2026-03-27")

# Check when alerts were sent in the last 24 hours
print("\n" + "=" * 80)
print("RECENT ACTIVITY (Last 48 Hours)")
print("=" * 80)

conn.close()

# Now check log file for actual email sends
import re
from datetime import datetime, timedelta

now = datetime.now()
cutoff = now - timedelta(hours=48)

print(f"\nSearching logs from {cutoff.strftime('%Y-%m-%d %H:%M:%S')} onwards...")

try:
    with open('shift_operations.log', 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
 
    # Look for lines mentioning March 27 email alerts
    march27_alerts = []
    for line in lines:
        if '2026-03-27' in line and any(x in line for x in ['Alert email', 'matched', 'send_availability_alert', 'EMAIL']):
            march27_alerts.append(line.strip())
    
    if march27_alerts:
        print(f"\nFound {len(march27_alerts)} log entries mentioning March 27 alerts:")
        for entry in march27_alerts[-20:]:  # Last 20 entries
            print(f"  {entry}")
    else:
        print("\nNo alert log entries found for March 27")
        
except Exception as e:
    print(f"\nError reading log file: {e}")

print("\n" + "=" * 80)
