import yagmail
from config import load_config
from datetime import datetime, timedelta
from email_db import mark_email_sent, check_email_sent

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
    send_email_alert(subject, "\n".join(body), to_email)

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
        body.append(f"<li>WhatsApp messages sent: <b>{stats.get('whatsapp_sent', 0)}</b></li>")
        if stats.get('last_scan_time'):
            try:
                dt = datetime.strptime(stats['last_scan_time'], '%Y-%m-%d %H:%M:%S')
                body.append(f"<li>Last scan time: <b>{fmt_short(dt)}</b></li>")
            except Exception:
                body.append(f"<li>Last scan time: <b>{stats['last_scan_time']}</b></li>")
        if stats.get('last_status'):
            try:
                dt = datetime.strptime(stats['last_status'], '%Y-%m-%d %H:%M:%S')
                body.append(f"<li>Last scan result: <b>{fmt_short(dt)}</b></li>")
            except Exception:
                body.append(f"<li>Last scan result: <b>{stats['last_status']}</b></li>")
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
    # Get all future shifts (not just this/next month)
    today = now.date()
    conn = sqlite3.connect(config.get('db_path', 'shifts.db'))
    c = conn.cursor()
    c.execute("SELECT date, shift_type FROM shifts WHERE date > ? ORDER BY date ASC", (today.isoformat(),))
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
    for date_str, shift_type in shifts:
        tag = ""
        if shift_type == 'booked':
            tag = "(Booked)"
            shift_lines.append(f"<li>{readable_date(date_str)} {tag}</li>")
        elif shift_type == 'open':
            if date_str in availability:
                tag = "(Matched)"
                shift_lines.append(f"<li><b>{readable_date(date_str)} {tag}</b></li>")
            else:
                tag = "(Open)"
                shift_lines.append(f"<li>{readable_date(date_str)} {tag}</li>")
    if shift_lines:
        body.append("<ul>")
        body.extend(shift_lines)
        body.append("</ul>")
    else:
        body.append("<p>No future shifts found.</p>")
    body.append("<p>This is an automated daily summary from your Teams Shift Database and Alert application.</p>")
    from email_db import mark_email_sent
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
