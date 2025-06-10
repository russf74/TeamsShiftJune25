def delete_shifts_not_in_list(year, month, valid_dates, shift_type='open'):
    """
    Delete all shifts of a given type for the specified month/year that are NOT in valid_dates.
    valid_dates: set of date strings (YYYY-MM-DD) to keep.
    """
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
    for row in rows:
        date_str = row[0]
        if date_str not in valid_dates:
            c.execute("DELETE FROM shifts WHERE date = ? AND shift_type = ?", (date_str, shift_type))
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
def shift_exists(date_str, shift_type='open'):
    conn = sqlite3.connect(get_db_path())
    c = conn.cursor()
    c.execute("SELECT 1 FROM shifts WHERE date = ? AND shift_type = ?", (date_str, shift_type))
    exists = c.fetchone() is not None
    conn.close()
    return exists

def add_shift(date_str, shift_type='open'):
    conn = sqlite3.connect(get_db_path())
    c = conn.cursor()
    c.execute("INSERT INTO shifts(date, shift_type) VALUES (?, ?)", (date_str, shift_type))
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
        alerted INTEGER DEFAULT 0,
        details TEXT
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
    c.execute("SELECT date, shift_type, alerted FROM shifts WHERE date >= ? AND date < ?", (start, end))
    rows = c.fetchall()
    conn.close()
    return [{"date": row[0], "shift_type": row[1], "alerted": row[2]} for row in rows]

def mark_shift_alerted(date_str):
    conn = sqlite3.connect(get_db_path())
    c = conn.cursor()
    c.execute("UPDATE shifts SET alerted = 1 WHERE date = ? AND shift_type = 'open'", (date_str,))
    conn.commit()
    conn.close()
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
