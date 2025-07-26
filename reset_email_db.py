#!/usr/bin/env python3
"""
Reset Email Database Script
This script clears today's email log entry so the app will think no daily summary email has been sent today.
Run this before restarting the app to test the 8pm email functionality.
"""

import sqlite3
import os
from datetime import date

def get_db_path():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'shifts.db')

def reset_email_log():
    """Clear today's email log entry"""
    conn = sqlite3.connect(get_db_path())
    c = conn.cursor()
    
    # Make sure the table exists
    c.execute('''CREATE TABLE IF NOT EXISTS email_log 
                 (date TEXT PRIMARY KEY, sent INTEGER, sent_time TEXT)''')
    
    today = date.today().isoformat()
    
    # Check if entry exists for today
    c.execute("SELECT * FROM email_log WHERE date = ?", (today,))
    result = c.fetchone()
    
    if result:
        print(f"Found email log entry for {today}: {result}")
        # Delete today's entry
        c.execute("DELETE FROM email_log WHERE date = ?", (today,))
        conn.commit()
        print(f"✅ Deleted email log entry for {today}")
        print("The app will now think no daily summary email has been sent today.")
    else:
        print(f"No email log entry found for {today}")
        print("The app already thinks no daily summary email has been sent today.")
    
    # Show remaining entries
    c.execute("SELECT * FROM email_log ORDER BY date DESC LIMIT 5")
    recent_entries = c.fetchall()
    if recent_entries:
        print("\nRecent email log entries:")
        for entry in recent_entries:
            print(f"  {entry}")
    else:
        print("\nNo email log entries found.")
    
    conn.close()

if __name__ == "__main__":
    print("Resetting email database...")
    reset_email_log()
    print("\n✅ Done! You can now restart the app and it should send the daily summary at 8pm.")
