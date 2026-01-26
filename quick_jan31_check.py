import sqlite3

conn = sqlite3.connect('shifts.db')
c = conn.cursor()

print("\nJan 31st Booked Shift Status:")
print("=" * 60)

c.execute("SELECT date, shift_type, count, confirmed_email_sent, created_at FROM shifts WHERE date = '2026-01-31' AND shift_type = 'booked'")
row = c.fetchone()

if row:
    print(f"Date: {row[0]}")
    print(f"Type: {row[1]}")
    print(f"Count: {row[2]}")
    print(f"Email Sent Flag: {row[3]}")
    print(f"Created: {row[4]}")
    
    if row[3] == 1:
        print("\nSTATUS: Email flag IS set - should prevent duplicates")
        print("BUG: Shift is likely being deleted and re-added by scans")
    else:
        print("\nSTATUS: Email flag NOT set - explains duplicate emails")
else:
    print("NO SHIFT FOUND - It was deleted!")
    print("This proves the delete/re-add cycle theory")

print("\n" + "=" * 60)
print("All January 2026 Shifts:")
c.execute("SELECT date, shift_type, confirmed_email_sent FROM shifts WHERE date >= '2026-01-01' AND date < '2026-02-01' ORDER BY date")
for r in c.fetchall():
    flag = "SET" if r[2] == 1 else "NOT SET"
    print(f"  {r[0]} ({r[1]}): email_flag={flag}")

conn.close()
