import sqlite3
from datetime import date, datetime

def get_db_path():
    import os
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'shifts.db')

def check_email_sent():
    """Check if the summary email has already been sent today"""
    conn = sqlite3.connect(get_db_path())
    c = conn.cursor()
    
    # Make sure the table exists
    c.execute('''CREATE TABLE IF NOT EXISTS email_log 
                 (date TEXT PRIMARY KEY, sent INTEGER)''')
    
    today = date.today().isoformat()
    c.execute("SELECT sent FROM email_log WHERE date = ?", (today,))
    result = c.fetchone()
    conn.close()
    
    return result is not None and result[0] == 1

def get_last_email_sent_time():
    import os
    import sqlite3
    db_path = get_db_path() if 'get_db_path' in globals() else os.path.join(os.path.dirname(__file__), 'shifts.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS email_log (date TEXT PRIMARY KEY, sent INTEGER, sent_time TEXT)''')
    c.execute("SELECT sent_time FROM email_log ORDER BY sent_time DESC LIMIT 1")
    result = c.fetchone()
    conn.close()
    if result and result[0]:
        try:
            return datetime.strptime(result[0], "%Y-%m-%d %H:%M:%S")
        except Exception:
            return None
    return None

def mark_email_sent():
    """Mark that the summary email has been sent today, with timestamp"""
    import os
    import sqlite3
    from datetime import datetime
    db_path = get_db_path() if 'get_db_path' in globals() else os.path.join(os.path.dirname(__file__), 'shifts.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS email_log (date TEXT PRIMARY KEY, sent INTEGER, sent_time TEXT)''')
    today = date.today().isoformat()
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute("INSERT OR REPLACE INTO email_log (date, sent, sent_time) VALUES (?, 1, ?)", (today, now_str))
    conn.commit()
    conn.close()

def migrate_email_log_add_sent_time():
    import os
    import sqlite3
    db_path = get_db_path() if 'get_db_path' in globals() else os.path.join(os.path.dirname(__file__), 'shifts.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS email_log (date TEXT PRIMARY KEY, sent INTEGER)''')
    # Check if 'sent_time' column exists
    c.execute("PRAGMA table_info(email_log)")
    columns = [row[1] for row in c.fetchall()]
    if "sent_time" not in columns:
        print("[DB] Migrating: adding 'sent_time' column to email_log table...")
        c.execute("ALTER TABLE email_log ADD COLUMN sent_time TEXT")
        conn.commit()
    conn.close()

# Always run migration on import
migrate_email_log_add_sent_time()
