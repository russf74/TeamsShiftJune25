import sqlite3
import os
import logging
from datetime import datetime

# Configure logging for database operations
logger = logging.getLogger('database')
logger.setLevel(logging.INFO)

# Create file handler for persistent logs
log_file = os.path.join(os.path.dirname(__file__), 'shift_operations.log')
file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.INFO)

# Create console handler for real-time monitoring
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Create formatter
formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] [%(funcName)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add handlers to logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

def delete_shifts_not_in_list(year, month, valid_dates, shift_type='open'):
    """
    Delete all shifts of a given type for the specified month/year that are NOT in valid_dates.
    valid_dates: set of date strings (YYYY-MM-DD) to keep.
    
    CRITICAL SAFETY: Never deletes booked shifts with confirmed_email_sent=1 to prevent
    duplicate confirmation emails from OCR failures causing delete/re-add cycles.
    """
    # CRITICAL SAFETY CHECK: Never delete if no valid dates found - could be scanning failure
    if not valid_dates:
        # Only show message for current/past months where we'd expect to find shifts
        from datetime import datetime
        current_date = datetime.now()
        scan_date = datetime(year, month, 1)

        # Only warn for months that are current or in the recent past
        if scan_date.year == current_date.year and scan_date.month <= current_date.month + 1:
            logger.warning(f"Skipping cleanup for {year}-{month:02d} {shift_type} shifts - no shifts found in scan")
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
    
    # Get all shifts for this month/type with email status
    if shift_type == 'booked':
        c.execute("SELECT date, confirmed_email_sent FROM shifts WHERE date >= ? AND date < ? AND shift_type = ?", (start, end, shift_type))
    else:
        c.execute("SELECT date, alerted FROM shifts WHERE date >= ? AND date < ? AND shift_type = ?", (start, end, shift_type))
    
    rows = c.fetchall()
    deleted_count = 0
    protected_count = 0
    deleted_dates = []
    protected_dates = []
    
    for row in rows:
        date_str = row[0]
        email_flag = row[1] if len(row) > 1 else 0
        
        if date_str not in valid_dates:
            # CRITICAL SAFETY: Never delete booked shifts that have been confirmed via email
            if shift_type == 'booked' and email_flag == 1:
                logger.warning(f"PROTECTED: Keeping booked shift {date_str} despite not in scan (confirmation email already sent)")
                protected_count += 1
                protected_dates.append(date_str)
                continue  # Don't delete this shift
            
            # Safe to delete
            logger.warning(f"DELETING {shift_type} shift: {date_str} (not found in scan results)")
            c.execute("DELETE FROM shifts WHERE date = ? AND shift_type = ?", (date_str, shift_type))
            deleted_count += 1
            deleted_dates.append(date_str)
 
    if deleted_count > 0:
        logger.info(f"Cleanup complete: Removed {deleted_count} stale {shift_type} shifts for {year}-{month:02d}: {', '.join(deleted_dates)}")
    
    if protected_count > 0:
        logger.info(f"Protected {protected_count} confirmed booked shifts from deletion: {', '.join(protected_dates)}")
  
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
        logger.error(f"Rejecting invalid date format: {date_str}")
        return  # Don't add malformed dates to database
    
    conn = sqlite3.connect(get_db_path())
    c = conn.cursor()
    
    # CRITICAL FIX: Prevent conflicting shift types on same date
    is_new_booking = False
    if shift_type == 'booked':
        # Check if this is a new booking (not already booked)
        c.execute("SELECT confirmed_email_sent FROM shifts WHERE date = ? AND shift_type = 'booked'", (date_str,))
        existing = c.fetchone()
        if not existing:
            is_new_booking = True
            logger.info(f"NEW BOOKING detected: {date_str} (will send confirmation email)")
        else:
            logger.info(f"Existing booked shift: {date_str}, confirmed_email_sent={existing[0]}")
   
        # If adding a booked shift, remove any existing open shifts for this date
        c.execute("DELETE FROM shifts WHERE date = ? AND shift_type = 'open'", (date_str,))
        logger.info(f"Removed any open shifts for {date_str} (now booked)")
    elif shift_type == 'open':
        # If adding an open shift, check if date is already booked
        c.execute("SELECT 1 FROM shifts WHERE date = ? AND shift_type = 'booked'", (date_str,))
        if c.fetchone():
            logger.info(f"Skipping open shift for {date_str} - already booked")
            conn.close()
            return  # Don't add open shift for dates you're already booked
    
    # Check if this shift already exists - FETCH alerted flag too!
    c.execute("SELECT count, created_at, confirmed_email_sent, alerted FROM shifts WHERE date = ? AND shift_type = ?", (date_str, shift_type))
    row = c.fetchone()
    now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    if row:
        # CRITICAL FIX: Preserve BOTH created_at AND alerted flag during UPDATE
        old_count = row[0]
        old_alerted = row[3] if len(row) > 3 else 0  # Get existing alerted flag
        logger.info(f"UPDATING existing {shift_type} shift: {date_str}, count {old_count}->{count}, created_at={row[1]}, email_sent={row[2]}, alerted={old_alerted}")
        # Only update count, preserve everything else by not touching other columns
        c.execute("UPDATE shifts SET count = ? WHERE date = ? AND shift_type = ?", (count, date_str, shift_type))
        # The alerted flag is preserved because we don't update it
    else:
        # New shift - check if we have a record of when this shift was first discovered
        # This prevents false NEW! alerts from delete/re-add cycles
        c.execute("SELECT first_seen, last_alerted FROM shift_history WHERE date = ? AND shift_type = ?", (date_str, shift_type))
        history_row = c.fetchone()
        
        if history_row:
            # CRITICAL FIX: Restore BOTH original timestamp AND alerted flag to prevent duplicate alerts
            original_created_at = history_row[0]
            original_alerted = history_row[1] if len(history_row) > 1 else 0
            logger.warning(f"RE-ADDING {shift_type} shift: {date_str} with original timestamp {original_created_at} and alerted={original_alerted} (was previously deleted!)")
            c.execute("INSERT INTO shifts(date, shift_type, count, created_at, alerted) VALUES (?, ?, ?, ?, ?)", (date_str, shift_type, count, original_created_at, original_alerted))
        else:
            # Truly new shift - record first time seeing it
            logger.info(f"ADDING NEW {shift_type} shift: {date_str} with timestamp {now_str}")
            c.execute("INSERT INTO shifts(date, shift_type, count, created_at) VALUES (?, ?, ?, ?)", (date_str, shift_type, count, now_str))
            c.execute("INSERT INTO shift_history(date, shift_type, first_seen, last_alerted) VALUES (?, ?, ?, ?)", (date_str, shift_type, now_str, 0))
    
    conn.commit()
    conn.close()
    
    # Send confirmation email for new bookings - BUT ONLY for future dates
    if is_new_booking and shift_type == 'booked':
        # CRITICAL: Never send confirmation emails for past dates
        try:
            shift_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
            current_date = datetime.datetime.now().date()
            
            if shift_date >= current_date:
                logger.info(f"SENDING confirmation email for NEW booking: {date_str}")
                from email_alert import send_shift_confirmation_email
                send_shift_confirmation_email(date_str)
            else:
                logger.info(f"Skipping confirmation email for past date: {date_str} (completed {(current_date - shift_date).days} days ago)")
        except Exception as e:
            logger.error(f"Failed to send confirmation email for {date_str}: {e}")

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
    c.execute('''CREATE TABLE IF NOT EXISTS shift_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        shift_type TEXT NOT NULL,
        first_seen TEXT NOT NULL,
        last_alerted INTEGER DEFAULT 0,
        UNIQUE(date, shift_type)
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
    """Mark a single shift as alerted (legacy function - use mark_multiple_shifts_alerted for batch operations)"""
    conn = sqlite3.connect(get_db_path())
    c = conn.cursor()
    c.execute("UPDATE shifts SET alerted = 1 WHERE date = ? AND shift_type = 'open'", (date_str,))
    conn.commit()
    conn.close()
    logger.info(f"Marked {date_str} as alerted")

def mark_multiple_shifts_alerted(date_list):
    """
    Mark multiple shifts as alerted in a single atomic transaction.
    This prevents race conditions where a new scan starts while flags are being set.
    
    Args:
date_list: List of date strings (YYYY-MM-DD) to mark as alerted
    """
    if not date_list:
        return
    
    conn = sqlite3.connect(get_db_path())
    c = conn.cursor()
    
    for date_str in date_list:
        c.execute("UPDATE shifts SET alerted = 1 WHERE date = ? AND shift_type = 'open'", (date_str,))
        # CRITICAL FIX: Also update shift_history to preserve flag across delete/re-add cycles
        c.execute("UPDATE shift_history SET last_alerted = 1 WHERE date = ? AND shift_type = 'open'", (date_str,))
    
    conn.commit()  # Single commit for ALL updates - atomic operation
    conn.close()
    logger.info(f"Atomically marked {len(date_list)} shifts as alerted: {', '.join(date_list)}")
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
    Ensures the 'count', 'created_at', 'confirmed_email_sent' columns exist in the shifts table and shift_history table exists.
    Adds them if missing and populates shift_history with existing data.
    """
    db_path = get_db_path() if 'get_db_path' in globals() else os.path.join(os.path.dirname(__file__), 'shifts.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Check if 'count' column exists
    c.execute("PRAGMA table_info(shifts)")
    columns = [row[1] for row in c.fetchall()]
    if "count" not in columns:
        logger.info("[DB] Migrating: adding 'count' column to shifts table...")
        c.execute("ALTER TABLE shifts ADD COLUMN count INTEGER DEFAULT 1")
        conn.commit()
    if "created_at" not in columns:
        logger.info("[DB] Migrating: adding 'created_at' column to shifts table...")
        c.execute("ALTER TABLE shifts ADD COLUMN created_at TEXT")
        conn.commit()
    if "confirmed_email_sent" not in columns:
        logger.info("[DB] Migrating: adding 'confirmed_email_sent' column to shifts table...")
        c.execute("ALTER TABLE shifts ADD COLUMN confirmed_email_sent INTEGER DEFAULT 0")
        conn.commit()
    
    # Create shift_history table if it doesn't exist
    c.execute('''CREATE TABLE IF NOT EXISTS shift_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        shift_type TEXT NOT NULL,
        first_seen TEXT NOT NULL,
        last_alerted INTEGER DEFAULT 0,
        UNIQUE(date, shift_type)
    )''')
    
    # Check if last_alerted column exists in shift_history
    c.execute("PRAGMA table_info(shift_history)")
    history_columns = [row[1] for row in c.fetchall()]
    if "last_alerted" not in history_columns:
        logger.info("[DB] Migrating: adding 'last_alerted' column to shift_history table...")
        c.execute("ALTER TABLE shift_history ADD COLUMN last_alerted INTEGER DEFAULT 0")
        # Backfill with current alerted status from shifts table
        c.execute("""
   UPDATE shift_history 
  SET last_alerted = (
       SELECT alerted FROM shifts 
           WHERE shifts.date = shift_history.date 
    AND shifts.shift_type = shift_history.shift_type
   )
        """)
        conn.commit()
        logger.info("[DB] Migration complete: last_alerted column added and backfilled")
    
    # Populate shift_history with existing shifts to prevent false NEW! alerts
    c.execute("SELECT COUNT(*) FROM shift_history")
    if c.fetchone()[0] == 0:
        logger.info("[DB] Migrating: populating shift_history with existing shifts...")
        c.execute("INSERT OR IGNORE INTO shift_history(date, shift_type, first_seen, last_alerted) SELECT date, shift_type, COALESCE(created_at, '2025-01-01 00:00:00'), COALESCE(alerted, 0) FROM shifts")
        conn.commit()
        logger.info("[DB] Migration complete: shift_history populated with existing shifts")
    
    conn.close()

# Always run migration on import
