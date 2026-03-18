#!/usr/bin/env python3
"""
Comprehensive diagnostic for March 27 duplicate alert issue
"""
import sqlite3
from datetime import datetime, timedelta

print("=" * 80)
print("MARCH 27 DUPLICATE ALERT DIAGNOSIS")
print("=" * 80)

# 1. Check current database state
print("\n1. DATABASE STATE FOR MARCH 27:")
print("-" * 80)
conn = sqlite3.connect('shifts.db')
c = conn.cursor()

c.execute("SELECT * FROM shifts WHERE date='2026-03-27'")
rows = c.fetchall()

if rows:
    c.execute("PRAGMA table_info(shifts)")
    cols = [col[1] for col in c.fetchall()]
    
    for row in rows:
        print(f"\nShift ID: {row[0]}")
        for i, val in enumerate(row[1:], 1):  # Skip ID
            print(f"  {cols[i]}: {val}")
else:
    print("No shifts found for 2026-03-27")

# 2. Check availability
print("\n2. AVAILABILITY FOR MARCH 27:")
print("-" * 80)
c.execute("SELECT * FROM availability WHERE date='2026-03-27'")
avail = c.fetchall()
if avail:
    print(f"User IS AVAILABLE on 2026-03-27")
else:
    print("User is NOT available on 2026-03-27")

# 3. Check shift history
print("\n3. SHIFT HISTORY FOR MARCH 27:")
print("-" * 80)
c.execute("SELECT * FROM shift_history WHERE date='2026-03-27'")
history = c.fetchall()
if history:
  for h in history:
        print(f"Date: {h[1]}, Type: {h[2]}, First Seen: {h[3]}")
else:
    print("No shift history for 2026-03-27")

conn.close()

# 4. Search logs for actual email sends
print("\n4. SEARCHING LOGS FOR MARCH 27 EMAIL ALERTS:")
print("-" * 80)

try:
    with open('shift_operations.log', 'r', encoding='utf-8', errors='ignore') as f:
 lines = f.readlines()
    
    # Search for any line mentioning March 27 and email/alert keywords
    email_lines = []
    for line in lines:
        if '2026-03-27' in line:
            if any(keyword in line.lower() for keyword in ['email', 'alert', 'send', 'mail', 'smtp', 'yagmail']):
  email_lines.append(line.strip())
    
    if email_lines:
        print(f"Found {len(email_lines)} log entries mentioning March 27 and emails:")
   for line in email_lines[-20:]:  # Last 20 entries
     print(f"  {line}")
    else:
 print("No log entries found mentioning March 27 and email keywords")
        
    # Also search for generic "matched" logs around midnight
    print("\n5. SEARCHING FOR MATCHED DATES LOGS (Last 48 hours):")
    print("-" * 80)

    # Get recent date range
    now = datetime.now()
    cutoff = now - timedelta(hours=48)
    cutoff_str = cutoff.strftime('%Y-%m-%d')
    
    matched_logs = []
 for line in lines:
   if 'matched_dates' in line.lower() or 'alert email' in line.lower() or 'new matched shifts' in line.lower():
        # Extract timestamp
       import re
            match = re.search(r'\[(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2}:\d{2})\]', line)
            if match:
             line_date = match.group(1)
    if line_date >= cutoff_str:
        matched_logs.append(line.strip())
    
    if matched_logs:
        print(f"Found {len(matched_logs)} recent matched/alert logs:")
        for log in matched_logs[-30:]:
      print(f"  {log}")
    else:
        print("No recent matched/alert logs found")
        
except Exception as e:
  print(f"Error reading logs: {e}")
    import traceback
    traceback.print_exc()

# 6. Check for email log entries
print("\n6. EMAIL LOG TABLE:")
print("-" * 80)
try:
    conn = sqlite3.connect('shifts.db')
    c = conn.cursor()
    c.execute("SELECT * FROM email_log ORDER BY date DESC LIMIT 10")
    email_logs = c.fetchall()
    if email_logs:
        print("Recent email log entries:")
        for log in email_logs:
            print(f"  Date: {log[0]}, Sent: {log[1]}, Sent Time: {log[2] if len(log) > 2 else 'N/A'}")
    else:
      print("No email log entries found")
    conn.close()
except Exception as e:
    print(f"Error checking email log: {e}")

print("\n" + "=" * 80)
print("DIAGNOSIS SUMMARY:")
print("=" * 80)
print("""
Based on the above data:
1. If 'alerted' = 1 and user IS available, no alerts should be sent
2. If emails are being sent despite alerted=1, the bug is in gui.py not checking the flag
3. If alerted keeps resetting to 0, the bug is in database.py UPDATE logic
4. Check timestamps to see when the duplicate occurred relative to midnight reset
""")
