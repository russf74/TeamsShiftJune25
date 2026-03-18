import sqlite3
from datetime import datetime
import re

conn = sqlite3.connect('shifts.db')
c = conn.cursor()

# Check schema of shifts table
c.execute("PRAGMA table_info(shifts)")
schema = c.fetchall()

print("=" * 80)
print("SHIFTS TABLE SCHEMA")
print("=" * 80)
for col in schema:
    print(f"{col[0]}: {col[1]} ({col[2]})")

print("\n" + "=" * 80)
print("MARCH 27, 2026 RAW DATA")
print("=" * 80)

c.execute("SELECT * FROM shifts WHERE date='2026-03-27'")
rows = c.fetchall()

for row in rows:
    print(f"\nRaw row: {row}")
    for i, val in enumerate(row):
        if i < len(schema):
            print(f"  {schema[i][1]}: {val}")
        else:
            print(f"  [col{i}]: {val}")

conn.close()

# Check the logs for March 27 mentions today
print("\n" + "=" * 80)
print("RECENT LOGS WITH MARCH 27 MENTIONS (Today)")
print("=" * 80)

try:
    with open('shift_operations.log', 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()

    today = datetime.now().date().isoformat()
    relevant_lines = []
    
    for line in lines:
        if '2026-03-27' in line:
            match = re.search(r'\[(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2}:\d{2})\]', line)
            if match:
                line_date = match.group(1)
                if line_date >= today:
                    relevant_lines.append(line.strip())
    
    if relevant_lines:
        print(f"\nFound {len(relevant_lines)} mentions of March 27 from today:")
        for line in relevant_lines[-30:]:
            print(line)
    else:
        print("\nNo mentions of March 27 from today")
      
except Exception as e:
    print(f"Error reading log: {e}")
    import traceback
    traceback.print_exc()
