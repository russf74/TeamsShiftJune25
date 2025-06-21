import sqlite3
from datetime import date

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

def mark_email_sent():
    """Mark that the summary email has been sent today"""
    conn = sqlite3.connect(get_db_path())
    c = conn.cursor()
    
    # Make sure the table exists
    c.execute('''CREATE TABLE IF NOT EXISTS email_log 
                 (date TEXT PRIMARY KEY, sent INTEGER)''')
    
    today = date.today().isoformat()
    c.execute("INSERT OR REPLACE INTO email_log (date, sent) VALUES (?, 1)", (today,))
    conn.commit()
    conn.close()
