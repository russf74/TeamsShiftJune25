import sqlite3

# Connect to the database
conn = sqlite3.connect('shifts.db')
cursor = conn.cursor()

# Check the schema first
cursor.execute("PRAGMA table_info(shifts)")
columns = cursor.fetchall()
print("Database schema:")
for col in columns:
    print(f"  {col[1]} ({col[2]})")

print("\n" + "="*50)

# Check July 2025 shifts
cursor.execute("SELECT * FROM shifts WHERE date LIKE '2025-07-%' ORDER BY date")
rows = cursor.fetchall()

print(f"\nShifts for July 2025 ({len(rows)} total):")
print("-" * 60)
for row in rows:
    if len(row) >= 5:
        print(f"Date: {row[1]}, Type: {row[2]}, Count: {row[3]}, Alerted: {row[4]}")
    elif len(row) >= 4:
        print(f"Date: {row[1]}, Type: {row[2]}, Count: {row[3]}")
    else:
        print(f"Date: {row[1]}, Type: {row[2]}")

# Check for multiple entries for the same date
print("\n" + "="*50)
cursor.execute("SELECT date, COUNT(*) as entry_count FROM shifts WHERE date LIKE '2025-07-%' GROUP BY date HAVING COUNT(*) > 1")
duplicate_dates = cursor.fetchall()

if duplicate_dates:
    print(f"\nDates with multiple entries:")
    for date, count in duplicate_dates:
        print(f"  {date}: {count} entries")
        
        # Show details for each duplicate date
        cursor.execute("SELECT * FROM shifts WHERE date = ? ORDER BY shift_type", (date,))
        details = cursor.fetchall()
        for detail in details:
            if len(detail) >= 5:
                print(f"    -> Type: {detail[2]}, Count: {detail[3]}, Alerted: {detail[4]}")
            else:
                print(f"    -> Type: {detail[2]}, Count: {detail[3] if len(detail) > 3 else 'N/A'}")
else:
    print("\nNo dates with multiple entries found.")

# Check July 7th specifically
print("\n" + "="*50)
cursor.execute("SELECT * FROM shifts WHERE date = '2025-07-07'")
july_7_shifts = cursor.fetchall()

print(f"\nJuly 7th, 2025 shifts ({len(july_7_shifts)} entries):")
for shift in july_7_shifts:
    if len(shift) >= 5:
        print(f"  Type: {shift[2]}, Count: {shift[3]}, Alerted: {shift[4]}")
    else:
        print(f"  Type: {shift[2]}, Count: {shift[3] if len(shift) > 3 else 'N/A'}")

conn.close()
