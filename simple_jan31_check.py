import sqlite3
from datetime import datetime

conn = sqlite3.connect('shifts.db')
c = conn.cursor()

print("JANUARY 31ST ANALYSIS")
print("=" * 60)

c.execute("SELECT date, shift_type, count, confirmed_email_sent, created_at FROM shifts WHERE date = '2025-01-31'")
shift = c.fetchone()

if shift:
    print(f"Date: {shift[0]}")
    print(f"Type: {shift[1]}")
    print(f"Count: {shift[2]}")
    print(f"Confirmed Email Sent: {shift[3]}")
    print(f"Created At: {shift[4]}")
    
    shift_date = datetime.strptime(shift[0], "%Y-%m-%d").date()
    today = datetime.now().date()
    days_ago = (today - shift_date).days
    
    print(f"\nThis shift was {days_ago} days AGO (in the past)")
    print(f"Confirmation email sent flag: {shift[3]}")
    
    if shift[3] == 1:
        print("\nWARNING: Confirmation flag is SET - email was already sent")
    else:
        print("\nINFO: Confirmation flag is NOT SET")
else:
    print("No shift found for Jan 31st")

print("\n" + "=" * 60)
print("ALL JANUARY SHIFTS:")
c.execute("SELECT date, shift_type, confirmed_email_sent FROM shifts WHERE date LIKE '2025-01%' ORDER BY date")
for s in c.fetchall():
    print(f"  {s[0]} - {s[1]} - Confirmed: {s[2]}")

conn.close()
