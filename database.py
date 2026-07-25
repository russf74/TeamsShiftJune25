import sqlite3
import os
import logging
from datetime import datetime

# Configure logging for database operations
logger = logging.getLogger('database')
logger.setLevel(logging.INFO)

# Create file handler for persistent logs (rotating - max 5MB, keep 2 backups)
log_file = os.path.join(os.path.dirname(__file__), 'shift_operations.log')
from logging.handlers import RotatingFileHandler
file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=2)
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
    # Legacy callers cannot tell an empty, healthy scan from a failed scan. The active
    # scanner now uses reconcile_month_observations() and passes scan health explicitly.
    # Keep this conservative behavior for old scripts and manual callers.
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
        # Check if this is a new booking (not already in DB as booked)
        c.execute("SELECT id, confirmed_email_sent FROM shifts WHERE date = ? AND shift_type = 'booked'", (date_str,))
        existing = c.fetchone()
        if not existing:
            # Not in shifts table - but check shift_history to see if we already sent a confirmation
            # This prevents duplicate emails when a booked shift is deleted and re-added
            c.execute("SELECT confirmed_email_sent FROM shift_history WHERE date = ? AND shift_type = 'booked'", (date_str,))
            history = c.fetchone()
            already_confirmed = history and history[0] == 1
            if not already_confirmed:
                is_new_booking = True
                logger.info(f"NEW BOOKING detected: {date_str} (will send confirmation email)")
            else:
                logger.info(f"RE-ADDED booked shift: {date_str} - confirmation already sent previously, skipping email")
        else:
            logger.info(f"Existing booked shift: {date_str}, confirmed_email_sent={existing[1]}")
   
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
    c.execute("SELECT count, created_at, alerted FROM shifts WHERE date = ? AND shift_type = ?", (date_str, shift_type))
    row = c.fetchone()
    now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if row:
        # CRITICAL FIX: Preserve BOTH created_at AND alerted flag during UPDATE
        old_count = row[0]
        old_alerted = row[2] if len(row) > 2 else 0  # Get existing alerted flag
        logger.info(f"UPDATING existing {shift_type} shift: {date_str}, count {old_count}->{count}, created_at={row[1]}, alerted={old_alerted}")
        # Only update count, preserve everything else
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
            import datetime as _dt
            shift_date = _dt.datetime.strptime(date_str, "%Y-%m-%d").date()
            current_date = _dt.datetime.now().date()
            if shift_date >= current_date:
                logger.info(f"SENDING confirmation email for NEW booking: {date_str}")
                # Reserve delivery, but do not claim success before SMTP completes.
                conn2 = sqlite3.connect(get_db_path())
                conn2.execute("UPDATE shifts SET email_status = 'pending' WHERE date = ? AND shift_type = 'booked'", (date_str,))
                conn2.commit()
                conn2.close()
                # Send in background thread so SMTP never blocks the scan
                import threading
                def _send(d=date_str):
                    try:
                        from email_alert import send_shift_confirmation_email
                        send_shift_confirmation_email(d)
                    except Exception as ex:
                        logger.error(f"Confirmation email failed for {d}: {ex}")
                threading.Thread(target=_send, daemon=True).start()
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
        confirmed_email_sent INTEGER DEFAULT 0,
        details TEXT,
        created_at TEXT,
        last_seen_at TEXT,
        missing_scan_count INTEGER DEFAULT 0,
        email_status TEXT DEFAULT 'not_required',
        UNIQUE(date, shift_type)
    )''')
    # Migration: add confirmed_email_sent if it doesn't exist (for existing DBs)
    try:
        c.execute("ALTER TABLE shifts ADD COLUMN confirmed_email_sent INTEGER DEFAULT 0")
    except Exception:
        pass  # Column already exists
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
        confirmed_email_sent INTEGER DEFAULT 0,
        UNIQUE(date, shift_type)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS booked_shift_candidates (
        date TEXT PRIMARY KEY,
        first_seen_at TEXT NOT NULL,
        last_seen_at TEXT NOT NULL,
        detection_count INTEGER NOT NULL DEFAULT 1,
        details TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS shift_corrections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        shift_type TEXT NOT NULL,
        reason TEXT NOT NULL,
        corrected_at TEXT NOT NULL
    )''')
    # Migration: add confirmed_email_sent to shift_history if it doesn't exist (for existing DBs)
    try:
        c.execute("ALTER TABLE shift_history ADD COLUMN confirmed_email_sent INTEGER DEFAULT 0")
    except Exception:
        pass  # Column already exists
    for column, definition in (
        ("created_at", "TEXT"),
        ("last_seen_at", "TEXT"),
        ("missing_scan_count", "INTEGER DEFAULT 0"),
        ("email_status", "TEXT DEFAULT 'not_required'"),
    ):
        try:
            c.execute(f"ALTER TABLE shifts ADD COLUMN {column} {definition}")
        except sqlite3.OperationalError:
            pass  # Column already exists
    c.execute("UPDATE shifts SET last_seen_at = COALESCE(last_seen_at, created_at)")
    c.execute("UPDATE shifts SET email_status = CASE WHEN shift_type = 'booked' AND confirmed_email_sent = 1 THEN 'sent' ELSE COALESCE(email_status, 'not_required') END")
    conn.commit()
    conn.close()

def reconcile_month_observations(year, month, observed_open_dates, observed_booked_dates, scan_healthy=True):
    """Reconcile one successfully scanned month against the current shift state.

    A booked result needs two healthy observations before it is promoted from a
    candidate to a confirmed booking. Confirmed bookings are removed only after
    two consecutive healthy scans miss them. This prevents a transient OCR issue
    from either creating a permanent booking or deleting a genuine one.
    """
    if not scan_healthy:
        logger.warning("Skipping reconciliation for %04d-%02d because the scan was not healthy", year, month)
        return {"new_open": [], "new_bookings": [], "deleted": [], "candidates": []}

    start = f"{year:04d}-{month:02d}-01"
    end = f"{year + 1:04d}-01-01" if month == 12 else f"{year:04d}-{month + 1:02d}-01"
    observed_open_dates = set(observed_open_dates)
    observed_booked_dates = set(observed_booked_dates)
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn = sqlite3.connect(get_db_path())
    c = conn.cursor()
    new_bookings = []
    new_open = []
    deleted = []
    candidates = []

    # Open shifts remain immediate because their alerts already have independent
    # atomic suppression. Do not add an open shift where a confirmed booking exists.
    for date_str in observed_open_dates:
        c.execute("SELECT 1 FROM shifts WHERE date = ? AND shift_type = 'booked'", (date_str,))
        if c.fetchone() is None:
            c.execute("SELECT 1 FROM shifts WHERE date = ? AND shift_type = 'open'", (date_str,))
            if c.fetchone() is None:
                history = c.execute("SELECT first_seen, last_alerted FROM shift_history WHERE date = ? AND shift_type = 'open'", (date_str,)).fetchone()
                if history is None:
                    c.execute("INSERT INTO shifts(date, shift_type, count, created_at, last_seen_at, missing_scan_count, email_status) VALUES (?, 'open', 1, ?, ?, 0, 'not_required')", (date_str, now_str, now_str))
                    c.execute("INSERT INTO shift_history(date, shift_type, first_seen, last_alerted) VALUES (?, 'open', ?, 0)", (date_str, now_str))
                    new_open.append(date_str)
                else:
                    c.execute("INSERT INTO shifts(date, shift_type, count, alerted, created_at, last_seen_at, missing_scan_count, email_status) VALUES (?, 'open', 1, ?, ?, ?, 0, 'not_required')", (date_str, history[1], history[0], now_str))
            else:
                c.execute("UPDATE shifts SET last_seen_at = ?, missing_scan_count = 0 WHERE date = ? AND shift_type = 'open'", (now_str, date_str))

    # A single booked OCR read is retained as evidence only. It cannot suppress an
    # open shift or send a confirmation until independently observed again.
    for date_str in observed_booked_dates:
        c.execute("SELECT 1 FROM shifts WHERE date = ? AND shift_type = 'booked'", (date_str,))
        if c.fetchone() is not None:
            c.execute("UPDATE shifts SET last_seen_at = ?, missing_scan_count = 0 WHERE date = ? AND shift_type = 'booked'", (now_str, date_str))
            continue
        c.execute("SELECT detection_count FROM booked_shift_candidates WHERE date = ?", (date_str,))
        candidate = c.fetchone()
        if candidate is None:
            c.execute("INSERT INTO booked_shift_candidates(date, first_seen_at, last_seen_at, detection_count) VALUES (?, ?, ?, 1)", (date_str, now_str, now_str))
            candidates.append(date_str)
        else:
            detection_count = candidate[0] + 1
            if detection_count >= 2:
                c.execute("DELETE FROM booked_shift_candidates WHERE date = ?", (date_str,))
                c.execute("DELETE FROM shifts WHERE date = ? AND shift_type = 'open'", (date_str,))
                history = c.execute("SELECT confirmed_email_sent FROM shift_history WHERE date = ? AND shift_type = 'booked'", (date_str,)).fetchone()
                previously_confirmed = history is not None and history[0] == 1
                c.execute("INSERT INTO shifts(date, shift_type, count, created_at, last_seen_at, missing_scan_count, email_status, confirmed_email_sent) VALUES (?, 'booked', 1, ?, ?, 0, ?, ?)", (date_str, now_str, now_str, 'sent' if previously_confirmed else 'pending', 1 if previously_confirmed else 0))
                c.execute("INSERT OR IGNORE INTO shift_history(date, shift_type, first_seen, last_alerted) VALUES (?, 'booked', ?, 0)", (date_str, now_str))
                if not previously_confirmed:
                    new_bookings.append(date_str)
            else:
                c.execute("UPDATE booked_shift_candidates SET detection_count = ?, last_seen_at = ? WHERE date = ?", (detection_count, now_str, date_str))

    # A candidate absent from the next healthy scan was not corroborated.
    candidate_rows = c.execute("SELECT date FROM booked_shift_candidates WHERE date >= ? AND date < ?", (start, end)).fetchall()
    for (date_str,) in candidate_rows:
        if date_str not in observed_booked_dates:
            c.execute("DELETE FROM booked_shift_candidates WHERE date = ?", (date_str,))

    rows = c.execute("SELECT date, shift_type, missing_scan_count FROM shifts WHERE date >= ? AND date < ?", (start, end)).fetchall()
    for date_str, shift_type, missing_count in rows:
        observed_dates = observed_open_dates if shift_type == 'open' else observed_booked_dates
        if date_str in observed_dates:
            continue
        if shift_type == 'booked':
            next_missing_count = (missing_count or 0) + 1
            if next_missing_count < 2:
                c.execute("UPDATE shifts SET missing_scan_count = ? WHERE date = ? AND shift_type = 'booked'", (next_missing_count, date_str))
                logger.warning("Keeping booked shift %s after one healthy missed scan", date_str)
            else:
                c.execute("DELETE FROM shifts WHERE date = ? AND shift_type = 'booked'", (date_str,))
                deleted.append((date_str, shift_type))
        else:
            c.execute("DELETE FROM shifts WHERE date = ? AND shift_type = 'open'", (date_str,))
            deleted.append((date_str, shift_type))

    conn.commit()
    conn.close()
    logger.info("Reconciled %04d-%02d: %d booked candidate(s), %d new booking(s), %d stale row(s) removed", year, month, len(candidates), len(new_bookings), len(deleted))
    return {"new_open": new_open, "new_bookings": new_bookings, "deleted": deleted, "candidates": candidates}

def remove_incorrect_bookings(date_list, reason):
    """Remove verified false bookings and preserve an audit trail for the correction."""
    if not date_list:
        return []
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn = sqlite3.connect(get_db_path())
    c = conn.cursor()
    corrected = []
    for date_str in date_list:
        c.execute("SELECT 1 FROM shifts WHERE date = ? AND shift_type = 'booked'", (date_str,))
        if c.fetchone() is None:
            continue
        c.execute("DELETE FROM shifts WHERE date = ? AND shift_type = 'booked'", (date_str,))
        c.execute("DELETE FROM booked_shift_candidates WHERE date = ?", (date_str,))
        # A correction reverses a false delivery marker, allowing a genuine future
        # booking on the date to be confirmed rather than permanently suppressed.
        c.execute("UPDATE shift_history SET confirmed_email_sent = 0 WHERE date = ? AND shift_type = 'booked'", (date_str,))
        c.execute("INSERT INTO shift_corrections(date, shift_type, reason, corrected_at) VALUES (?, 'booked', ?, ?)", (date_str, reason, now_str))
        corrected.append(date_str)
    conn.commit()
    conn.close()
    if corrected:
        logger.warning("Removed verified incorrect booked shift(s): %s. Reason: %s", ", ".join(corrected), reason)
    return corrected

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
    deleted = c.rowcount
    conn.commit()
    conn.close()
    if deleted > 0:
        logger.info(f"remove_past_shifts: removed {deleted} past shift(s) (before {today})")

def cleanup_erroneous_open_shifts(erroneous_dates):
    """
    Removes specific open shift entries that are known to be erroneous because
    they were incorrectly detected from 'U' (unavailable) shift tiles in Teams.

    Only removes shifts that have NOT yet been alerted (alerted=0), so no
    previously-sent email alerts are affected.

    Args:
        erroneous_dates: list of date strings (YYYY-MM-DD) to remove as open shifts
    Returns:
        Number of rows actually deleted.
    """
    if not erroneous_dates:
        return 0
    conn = sqlite3.connect(get_db_path())
    c = conn.cursor()
    deleted_count = 0
    for date_str in erroneous_dates:
        c.execute(
            "DELETE FROM shifts WHERE date = ? AND shift_type = 'open' AND alerted = 0",
            (date_str,)
        )
        if c.rowcount > 0:
            logger.warning(
                f"[Cleanup] Removed erroneous open shift {date_str} "
                f"(was incorrectly detected from an unavailable shift block)"
            )
            deleted_count += 1
    conn.commit()
    conn.close()
    if deleted_count > 0:
        logger.info(f"[Cleanup] Erroneous shift cleanup complete: {deleted_count} incorrect open shift(s) removed.")
    return deleted_count
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
