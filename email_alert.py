import yagmail
from config import load_config
from datetime import datetime, timedelta
from email_db import mark_email_sent, check_email_sent, get_last_email_sent_time
import logging

# Configure logging for email operations
logger = logging.getLogger('email_alert')
logger.setLevel(logging.INFO)

# Create file handler for persistent logs
import os
log_file = os.path.join(os.path.dirname(__file__), 'shift_operations.log')
file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.INFO)

# Create console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Create formatter
formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] [EMAIL] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add handlers
logger.addHandler(file_handler)
logger.addHandler(console_handler)

def check_whatsapp_quick():
    """Quick WhatsApp connectivity check for daily summary."""
    import psutil
    import pywinauto
    
    try:
        # Check if WhatsApp is running
        whatsapp_running = False
        for proc in psutil.process_iter(['pid', 'name']):
            if 'whatsapp' in proc.info['name'].lower():
                whatsapp_running = True
                break
        
        if not whatsapp_running:
            return {'status': 'WARN', 'message': 'WhatsApp not running'}
        
        # Try to connect to WhatsApp window
        app = pywinauto.Application().connect(title_re=".*WhatsApp.*")
        if not app.windows():
            return {'status': 'WARN', 'message': 'WhatsApp window not accessible'}
            
        return {'status': 'OK', 'message': 'WhatsApp ready'}
        
    except Exception as e:
        return {'status': 'ERROR', 'message': f'WhatsApp check failed: {str(e)[:50]}...'}

def send_email_alert(subject, body, to_email):
    config = load_config()
    user = config.get('gmail_user')
    app_password = config.get('gmail_app_password')
    if not user or not app_password:
        raise Exception("Gmail user or app password not set in config.")
    yag = yagmail.SMTP(user=user, password=app_password)
    yag.send(to=to_email, subject=subject, contents=body)

def send_availability_alert(matched_dates_with_counts):
    """
    Sends an email alert when open shifts are found that match the user's availability.
    
    Args:
        matched_dates_with_counts: List of tuples (date_str, count) where open shifts match availability
    """
    
    # CRITICAL SAFETY CHECK: Double-check that none of these shifts have already been alerted
    from database import is_shift_alerted
    
    filtered_dates = []
    skipped_dates = []
    
    for item in matched_dates_with_counts:
        # Handle both tuple and string formats
        if isinstance(item, tuple):
            date_str, count = item
        else:
            date_str = item
            count = 1
        
        # Double-check the alerted flag before sending
        if is_shift_alerted(date_str, 'open'):
            logger.warning(f"BLOCKED: Skipping alert for {date_str} - already alerted (alerted=1)")
            skipped_dates.append(date_str)
        else:
            filtered_dates.append((date_str, count))
    
    if skipped_dates:
        logger.info(f"Skipped {len(skipped_dates)} already-alerted shifts: {skipped_dates}")
    
    if not filtered_dates:
        logger.info("No unalerted shifts to send - all were already alerted")
        return
    
    # Update the variable to use filtered list
    matched_dates_with_counts = filtered_dates
    
    # Log the alert attempt
    logger.info(f"SENDING availability alert for {len(matched_dates_with_counts)} shifts: {[d[0] for d in matched_dates_with_counts]}")
    
    if not matched_dates_with_counts:
        return
        
    config = load_config()
    to_email = config.get('alert_email')
    
    if not to_email:
        raise Exception("Alert email not set in config.")
    
    # Format the dates for display in a more readable format
    formatted_dates = []
    for date_str, count in matched_dates_with_counts:
        year, month, day = map(int, date_str.split('-'))
        date_obj = datetime(year, month, day)
        formatted_date = date_obj.strftime("%A, %B %d, %Y")  # e.g. "Monday, June 5, 2025"
        formatted_dates.append(f"{formatted_date} ({count} shift{'s' if count > 1 else ''})")
    
    # Build the email
    subject = f"Teams Shift Alert: {len(matched_dates_with_counts)} Open Shifts Match Your Availability"
    
    body = [
        f"<h2>Open Shifts Matching Your Availability</h2>",
        "<p>The following open shifts match days you marked as available:</p>",
        "<ul>"
    ]
    
    for date in formatted_dates:
        body.append(f"<li>{date}</li>")
    
    body.extend([
        "</ul>",
        "<p>Log into Microsoft Teams to book these shifts before they are taken.</p>",
        "<p>This is an automated alert from your Teams Shift Database and Alert application.</p>"
    ])
    
    # Send the email
    logger.info(f"About to send email alert to {to_email} for shifts: {[d[0] for d in matched_dates_with_counts]}")
    send_email_alert(subject, "\n".join(body), to_email)
    logger.info(f"SUCCESS: Email alert sent for {len(matched_dates_with_counts)} shifts")

def send_summary_email(stats=None):
    from config import load_config
    from datetime import datetime, timedelta
    import calendar
    import sqlite3
    from database import get_shifts_for_month, get_availability_for_month
    config = load_config()
    user = config.get('gmail_user')
    app_password = config.get('gmail_app_password')
    to_email = "russfray74@gmail.com"
    if not user or not app_password or not to_email:
        print("[ERROR] Gmail user, app password, or alert email not set in config.")
        raise Exception("Gmail user, app password, or alert email not set in config.")
    now = datetime.now()
    subject = f"Teams Shift Daily Summary: {now.strftime('%A, %d %B %Y')}"
    body = [
        f"<h2>Daily Summary for {now.strftime('%A, %d %B %Y')}</h2>",
        f"<ul>"
    ]
    def fmt_short(dt):
        return dt.strftime('%a %d %b %H:%M')
    if stats:
        body.append(f"<li>Number of successful scans: <b>{stats.get('scan_count', 0)}</b></li>")
        body.append(f"<li>Number of errors: <b>{stats.get('error_count', 0)}</b></li>")
        body.append(f"<li>Emails sent: <b>{stats.get('emails_sent', 0)}</b></li>")
        body.append(f"<li>SMS Text messages sent: <b>{stats.get('sms_sent', 0)}</b></li>")
        if stats.get('last_scan_time'):
            try:
                dt = datetime.strptime(stats['last_scan_time'], '%Y-%m-%d %H:%M:%S')
                body.append(f"<li>Last scan time: <b>{fmt_short(dt)}</b></li>")
            except Exception:
                body.append(f"<li>Last scan time: <b>{stats['last_scan_time']}</b></li>")
        if stats.get('errors'):
            body.append("<li>Error log:<ul>")
            for err in stats['errors']:
                body.append(f"<li>{err}</li>")
            body.append("</ul></li>")
    else:
        body.append("<li>No scan statistics available for today.</li>")
    body.append("</ul>")
    # --- Shift Status Section ---
    body.append("<h3>Shift Status</h3>")
    # Get last email sent time for filtering
    last_email_time = get_last_email_sent_time()
    # Get all future shifts (not just this/next month)
    today = now.date()
    conn = sqlite3.connect(config.get('db_path', 'shifts.db'))
    c = conn.cursor()
    c.execute("SELECT date, shift_type, count, created_at FROM shifts WHERE date > ? ORDER BY date ASC", (today.isoformat(),))
    shifts = c.fetchall()
    conn.close()
    # Get all future availability
    conn = sqlite3.connect(config.get('db_path', 'shifts.db'))
    c = conn.cursor()
    c.execute("SELECT date FROM availability WHERE date > ?", (today.isoformat(),))
    availability = set(row[0] for row in c.fetchall())
    conn.close()
    def readable_date(date_str):
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.strftime("%a %d %b")
    shift_lines = []
    booked_dates = set()  # Track dates you're already booked
    
    # First pass: collect all booked dates
    for date_str, shift_type, count, created_at in shifts:
        if shift_type == 'booked':
            booked_dates.add(date_str)
    
    # Second pass: generate lines, skipping open shifts for booked dates
    for date_str, shift_type, count, created_at in shifts:
        # SAFETY CHECK: Never show open shifts for dates you're already booked
        if shift_type == 'open' and date_str in booked_dates:
            print(f"[EMAIL] Skipping open shift for {date_str} - already booked")
            continue
            
        tag = ""
        count_str = f"(Open : {count})" if shift_type == 'open' else f"(Booked : {count})"
        is_new = False
        if created_at and last_email_time:
            try:
                created_dt = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")
                if created_dt > last_email_time:
                    is_new = True
            except Exception:
                pass
        if shift_type == 'booked':
            tag = f"(Booked : {count})"
            line = f"<li><b style='color:blue'>{readable_date(date_str)} {tag}</b>"
        elif shift_type == 'open':
            if date_str in availability:
                tag = f"(Matched : {count})"
                line = f"<li><b>{readable_date(date_str)} {tag}</b>"
            else:
                tag = f"(Open : {count})"
                line = f"<li>{readable_date(date_str)} {tag}"
        else:
            line = f"<li>{readable_date(date_str)} {tag}"
        if is_new:
            line += " <span style='color:green'>(NEW!)</span>"
        line += "</li>"
        shift_lines.append(line)
    if shift_lines:
        body.append("<ul>")
        body.extend(shift_lines)
        body.append("</ul>")
    else:
        body.append("<p>No future shifts found.</p>")
    
    body.append("<p>This is an automated daily summary from your Teams Shift Database and Alert application.</p>")
    import yagmail
    try:
        yag = yagmail.SMTP(user=user, password=app_password)
        yag.send(to=to_email, subject=subject, contents=''.join(body))
        print(f"[INFO] Daily summary email sent to {to_email} at {now.strftime('%Y-%m-%d %H:%M:%S')}")
    except Exception as e:
        print(f"[ERROR] Failed to send daily summary email: {e}")
        import traceback
        traceback.print_exc()
        return False
    mark_email_sent()
    return True

def send_shift_confirmation_email(date_str):
    """
    Send immediate confirmation email when a shift is booked/confirmed.
    
    Args:
        date_str: Date string in YYYY-MM-DD format of the confirmed shift
    """
    import sqlite3
    from datetime import datetime
    from config import load_config
    
    logger.info(f"send_shift_confirmation_email() called for {date_str}")
    
    # CRITICAL SAFETY CHECK: Never send confirmation emails for past dates
    try:
        shift_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        current_date = datetime.now().date()
        
        if shift_date < current_date:
            days_ago = (current_date - shift_date).days
            logger.warning(f"BLOCKED: Refusing to send confirmation email for PAST date {date_str} (completed {days_ago} days ago)")
            return
    except ValueError:
        logger.error(f"BLOCKED: Invalid date format {date_str}, skipping confirmation email")
        return
    
    config = load_config()
    user = config.get('gmail_user')
    app_password = config.get('gmail_app_password')
    
    if not user or not app_password:
        logger.error("Gmail credentials not set in config")
        raise Exception("Gmail user or app password not set in config.")
    
    # Atomically claim pending delivery. A sent flag represents actual SMTP success,
    # not merely that a background worker was scheduled.
    conn = sqlite3.connect(config.get('db_path', 'shifts.db'))
    c = conn.cursor()
    c.execute("SELECT confirmed_email_sent, COALESCE(email_status, 'not_required') FROM shifts WHERE date = ? AND shift_type = 'booked'", (date_str,))
    result = c.fetchone()
    
    if not result:
        logger.warning(f"BLOCKED: No current booked shift exists for {date_str}")
        conn.close()
        return
    if result[0] == 1 or result[1] == 'sent':
        logger.warning(f"BLOCKED: Confirmation email already sent for {date_str}")
        conn.close()
        return
    if result[1] == 'sending':
        logger.warning(f"BLOCKED: Confirmation email delivery is already in progress for {date_str}")
        conn.close()
        return
    c.execute("UPDATE shifts SET email_status = 'sending' WHERE date = ? AND shift_type = 'booked' AND COALESCE(email_status, 'not_required') != 'sending'", (date_str,))
    conn.commit()
    
    logger.info(f"Proceeding to send confirmation email for {date_str} (status={result[1]})")
    
    # Format the date for display
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        formatted_date = date_obj.strftime("%A, %B %d, %Y")  # e.g. "Monday, June 5, 2025"
        short_date = date_obj.strftime("%a %d %b")  # e.g. "Mon 05 Jun"
    except ValueError:
        formatted_date = date_str
        short_date = date_str
    
    # Email recipients
    recipients = ["russfray74@gmail.com", "laurafray74@gmail.com"]
    
    # Build the email
    subject = f"Shift Confirmed: {short_date}"
    
    body = [
        f"<h2 style='color:blue'>✅ Shift Confirmed</h2>",
        f"<p>Your shift has been confirmed for:</p>",
        f"<p><b style='color:blue; font-size:18px'>{formatted_date}</b></p>",
        f"<p>This confirmation was detected automatically by your Teams Shift monitoring system.</p>",
        f"<p>No further action is required.</p>",
        f"<hr>",
        f"<p><small>This is an automated notification from your Teams Shift Database and Alert application.</small></p>"
    ]
    
    # Send the email
    import yagmail
    try:
        logger.info(f"SENDING email to {', '.join(recipients)} - Subject: '{subject}'")
        yag = yagmail.SMTP(user=user, password=app_password)
        yag.send(to=recipients, subject=subject, contents=''.join(body))
        
        # Mark confirmation email as sent
        c.execute("UPDATE shifts SET confirmed_email_sent = 1, email_status = 'sent' WHERE date = ? AND shift_type = 'booked'", (date_str,))
        c.execute("UPDATE shift_history SET confirmed_email_sent = 1 WHERE date = ? AND shift_type = 'booked'", (date_str,))
        conn.commit()
        
        logger.info(f"SUCCESS: Confirmation email sent for {date_str}, flag set to 1")
        
    except Exception as e:
        c.execute("UPDATE shifts SET email_status = 'failed' WHERE date = ? AND shift_type = 'booked'", (date_str,))
        conn.commit()
        logger.error(f"FAILED to send confirmation email for {date_str}: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        conn.close()
