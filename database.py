def delete_shifts_not_in_list(year, month, valid_dates, shift_type='open'):
    """
    Delete all shifts of a given type for the specified month/year that are NOT in valid_dates.
    valid_dates: set of date strings (YYYY-MM-DD) to keep.
    """
    # CRITICAL SAFETY CHECK: Never delete if no valid dates found - could be scanning failure
    if not valid_dates:
        # Only show message for current/past months where we'd expect to find shifts
        from datetime import datetime
        current_date = datetime.now()
        scan_date = datetime(year, month, 1)
        
        # Only warn for months that are current or in the recent past
        if scan_date.year == current_date.year and scan_date.month <= current_date.month + 1:
            print(f"[SAFETY] Skipping cleanup for {year}-{month:02d} {shift_type} shifts - no shifts found")
        # For future months, this is normal - no message needed
        return
    
    import sqlite3
    conn = sqlite3.connect(get_db_path())
    c = conn.cursor()
    start = f"{year}-{month:02d}-01"
    if month == 12:
        end = f"{year+1}-01-01"
    else:
        end = f"{year}-{month+1:02d}-01"
    # Get all shifts for this month/type
    c.execute("SELECT date FROM shifts WHERE date >= ? AND date < ? AND shift_type = ?", (start, end, shift_type))
    rows = c.fetchall()
    deleted_count = 0
    for row in rows:
        date_str = row[0]
        if date_str not in valid_dates:
            c.execute("DELETE FROM shifts WHERE date = ? AND shift_type = ?", (date_str, shift_type))
            deleted_count += 1
    
    if deleted_count > 0:
        print(f"[CLEANUP] Removed {deleted_count} stale {shift_type} shifts for {year}-{month:02d}")
    
    conn.commit()
    conn.close()
def clear_all_shifts():
    """Delete all shifts from the database."""
    import sqlite3
    conn = sqlite3.connect(get_db_path())
    c = conn.cursor()
    c.execute("DELETE FROM shifts")
    conn.commit()
    conn.close()
def shift_exists(date_str, shift_type='open', count=None):
    conn = sqlite3.connect(get_db_path())
    c = conn.cursor()
    if count is not None:
        c.execute("SELECT count FROM shifts WHERE date = ? AND shift_type = ?", (date_str, shift_type))
        row = c.fetchone()
        conn.close()
        return row is not None and row[0] >= count
    else:
        c.execute("SELECT 1 FROM shifts WHERE date = ? AND shift_type = ?", (date_str, shift_type))
        exists = c.fetchone() is not None
        conn.close()
        return exists

def add_shift(date_str, shift_type='open', count=1):
    import datetime
    
    # Validate date format before adding to database
    try:
        datetime.datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        print(f"[DATABASE] Rejecting invalid date format: {date_str}")
        return  # Don't add malformed dates to database
    
    conn = sqlite3.connect(get_db_path())
    c = conn.cursor()
    
    # CRITICAL FIX: Prevent conflicting shift types on same date
    if shift_type == 'booked':
        # If adding a booked shift, remove any existing open shifts for this date
        c.execute("DELETE FROM shifts WHERE date = ? AND shift_type = 'open'", (date_str,))
        print(f"[DATABASE] Removed any open shifts for {date_str} (now booked)")
    elif shift_type == 'open':
        # If adding an open shift, check if date is already booked
        c.execute("SELECT 1 FROM shifts WHERE date = ? AND shift_type = 'booked'", (date_str,))
        if c.fetchone():
            print(f"[DATABASE] Skipping open shift for {date_str} - already booked")
            conn.close()
            return  # Don't add open shift for dates you're already booked
    
    # Upsert: always set count to the new value, but preserve alerted status
    c.execute("SELECT count FROM shifts WHERE date = ? AND shift_type = ?", (date_str, shift_type))
    row = c.fetchone()
    now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if row:
        # Update existing shift but preserve the alerted status
        c.execute("UPDATE shifts SET count = ? WHERE date = ? AND shift_type = ?", (count, date_str, shift_type))
    else:
        # Insert new shift with alerted = 0
        c.execute("INSERT INTO shifts(date, shift_type, count, created_at) VALUES (?, ?, ?, ?)", (date_str, shift_type, count, now_str))
    conn.commit()
    conn.close()
import sqlite3
import os

def get_db_path():
    return os.path.join(os.path.dirname(__file__), 'shifts.db')

def init_db():
    conn = sqlite3.connect(get_db_path())
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS shifts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        shift_type TEXT NOT NULL,
        count INTEGER DEFAULT 1,
        alerted INTEGER DEFAULT 0,
        details TEXT,
        UNIQUE(date, shift_type)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS availability (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS config (
        key TEXT PRIMARY KEY,
        value TEXT
    )''')
    conn.commit()
    conn.close()

# --- Calendar/Shift/Availability helpers ---
def get_shifts_for_month(year, month):
    conn = sqlite3.connect(get_db_path())
    c = conn.cursor()
    start = f"{year}-{month:02d}-01"
    if month == 12:
        end = f"{year+1}-01-01"
    else:
        end = f"{year}-{month+1:02d}-01"
    c.execute("SELECT date, shift_type, count, alerted FROM shifts WHERE date >= ? AND date < ?", (start, end))
    rows = c.fetchall()
    conn.close()
    return [{"date": row[0], "shift_type": row[1], "count": row[2], "alerted": row[3]} for row in rows]

def mark_shift_alerted(date_str):
    conn = sqlite3.connect(get_db_path())
    c = conn.cursor()
    c.execute("UPDATE shifts SET alerted = 1 WHERE date = ? AND shift_type = 'open'", (date_str,))
    conn.commit()
    conn.close()

def is_shift_alerted(date_str, shift_type='open'):
    """Check if a shift has already been alerted."""
    conn = sqlite3.connect(get_db_path())
    c = conn.cursor()
    c.execute("SELECT alerted FROM shifts WHERE date = ? AND shift_type = ?", (date_str, shift_type))
    row = c.fetchone()
    conn.close()
    return row is not None and row[0] == 1
def get_availability_for_month(year, month):
    conn = sqlite3.connect(get_db_path())
    c = conn.cursor()
    start = f"{year}-{month:02d}-01"
    if month == 12:
        end = f"{year+1}-01-01"
    else:
        end = f"{year}-{month+1:02d}-01"
    c.execute("SELECT date FROM availability WHERE date >= ? AND date < ?", (start, end))
    rows = c.fetchall()
    conn.close()
    return [{"date": row[0]} for row in rows]

def set_availability_for_date(date_str, available):
    conn = sqlite3.connect(get_db_path())
    c = conn.cursor()
    if available:
        # Insert if not exists
        c.execute("INSERT OR IGNORE INTO availability(date) VALUES (?)", (date_str,))
    else:
        c.execute("DELETE FROM availability WHERE date = ?", (date_str,))
    conn.commit()
    conn.close()

def get_availability_for_date(date_str):
    """
    Checks if a specific date is marked as available.
    Returns a dict with the date and availability status.
    """
    conn = sqlite3.connect(get_db_path())
    c = conn.cursor()
    c.execute("SELECT 1 FROM availability WHERE date = ?", (date_str,))
    is_available = c.fetchone() is not None
    conn.close()
    return {"date": date_str, "is_available": is_available}

def remove_past_shifts():
    import sqlite3
    from datetime import date
    conn = sqlite3.connect(get_db_path())
    c = conn.cursor()
    today = date.today().isoformat()
    c.execute("DELETE FROM shifts WHERE date < ?", (today,))
    conn.commit()
    conn.close()
def migrate_shifts_table_add_count_and_created_at():
    """
    Ensures the 'count' and 'created_at' columns exist in the shifts table. Adds them if missing.
    """
    db_path = get_db_path() if 'get_db_path' in globals() else os.path.join(os.path.dirname(__file__), 'shifts.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    # Check if 'count' column exists
    c.execute("PRAGMA table_info(shifts)")
    columns = [row[1] for row in c.fetchall()]
    if "count" not in columns:
        print("[DB] Migrating: adding 'count' column to shifts table...")
        c.execute("ALTER TABLE shifts ADD COLUMN count INTEGER DEFAULT 1")
        conn.commit()
    if "created_at" not in columns:
        print("[DB] Migrating: adding 'created_at' column to shifts table...")
        c.execute("ALTER TABLE shifts ADD COLUMN created_at TEXT")
        conn.commit()
    conn.close()

# Always run migration on import
migrate_shifts_table_add_count_and_created_at()
