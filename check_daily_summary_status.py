#!/usr/bin/env python3
"""
Diagnostic script to check the current state of daily summary email sending.
This script will tell us if the app thinks the daily summary email was already sent today.
"""

import datetime
import sys
import os

# Add the current directory to Python path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    try:
        from email_db import check_email_sent
        
        now = datetime.datetime.now()
        today_str = now.strftime('%Y-%m-%d')
        
        print(f"=== Daily Summary Email Status Check ===")
        print(f"Current date/time: {now.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Today's date: {today_str}")
        print()
        
        # Check if daily summary email was sent today
        email_sent_today = check_email_sent()
        
        print(f"check_email_sent() returned: {email_sent_today}")
        
        if email_sent_today:
            print("✅ The app thinks the daily summary email was ALREADY SENT today")
            print("   This means the daily summary email logic will skip sending today")
        else:
            print("❌ The app thinks the daily summary email was NOT SENT today")
            print("   This means the daily summary email should be sent at 8:00pm or later")
        
        print()
        print("=== Schedule Analysis ===")
        
        # Check what time it is and what should happen
        if now.hour > 20 or (now.hour == 20 and now.minute >= 0):
            print(f"Current time ({now.hour:02d}:{now.minute:02d}) is after 8:00pm")
            if email_sent_today:
                print("➡️  Email already sent, so daily summary should be skipped")
            else:
                print("➡️  Email not sent yet, so daily summary should be sent NOW")
        else:
            print(f"Current time ({now.hour:02d}:{now.minute:02d}) is before 8:00pm")
            print("➡️  Daily summary should wait until 8:00pm or later")
        
        print()
        print("=== Email Database Contents ===")
        
        # Let's also check what's in the email database
        try:
            import sqlite3
            conn = sqlite3.connect('shifts.db')
            cursor = conn.cursor()
            
            # Check if email_sent table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='email_sent'")
            if cursor.fetchone():
                print("Email sent table exists. Recent entries:")
                cursor.execute("SELECT * FROM email_sent ORDER BY date_sent DESC LIMIT 5")
                rows = cursor.fetchall()
                
                if rows:
                    print("Date Sent")
                    print("-" * 20)
                    for row in rows:
                        print(f"{row[0]}")
                else:
                    print("No entries in email_sent table")
            else:
                print("Email sent table does not exist yet")
            
            conn.close()
            
        except Exception as e:
            print(f"Error checking email database: {e}")
        
        print()
        print("=== Recommendations ===")
        
        if now.hour > 20 and not email_sent_today:
            print("🚨 ISSUE: It's after 8pm and no daily summary was sent today!")
            print("   Possible causes:")
            print("   1. The daily summary timer is not running")
            print("   2. There's an error in the email sending logic")
            print("   3. The app was not running at 8pm")
            print("   4. The _start_daily_summary_timer() method has an issue")
        elif now.hour > 20 and email_sent_today:
            print("✅ Everything looks normal - email was sent today as expected")
        else:
            print("ℹ️  Too early to determine if there's an issue (before 8pm)")
        
    except ImportError as e:
        print(f"ERROR: Could not import required modules: {e}")
        print("Make sure you're running this script from the correct directory")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
