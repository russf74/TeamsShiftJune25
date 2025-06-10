import yagmail
from config import load_config

def send_email_alert(subject, body, to_email):
    config = load_config()
    user = config.get('gmail_user')
    app_password = config.get('gmail_app_password')
    if not user or not app_password:
        raise Exception("Gmail user or app password not set in config.")
    yag = yagmail.SMTP(user=user, password=app_password)
    yag.send(to=to_email, subject=subject, contents=body)

def send_availability_alert(matched_dates):
    """
    Sends an email alert when open shifts are found that match the user's availability.
    
    Args:
        matched_dates: List of date strings (YYYY-MM-DD) where open shifts match availability
    """
    import calendar
    from datetime import datetime
    
    if not matched_dates:
        return
        
    config = load_config()
    to_email = config.get('alert_email')
    
    if not to_email:
        raise Exception("Alert email not set in config.")
    
    # Format the dates for display in a more readable format
    formatted_dates = []
    for date_str in matched_dates:
        year, month, day = map(int, date_str.split('-'))
        date_obj = datetime(year, month, day)
        formatted_date = date_obj.strftime("%A, %B %d, %Y")  # e.g. "Monday, June 5, 2025"
        formatted_dates.append(formatted_date)
    
    # Build the email
    subject = f"Teams Shift Alert: {len(matched_dates)} Open Shifts Match Your Availability"
    
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
