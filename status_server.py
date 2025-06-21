import threading
import os
from flask import Flask, render_template_string, send_from_directory
from datetime import datetime
from database import get_shifts_for_month, get_availability_for_month
from config import load_config
import logging

app = Flask(__name__)

# Suppress Flask's default request logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# HTML template for status page (responsive for desktop/mobile)
STATUS_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Teams Shift Scanner Status</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 0; background: #f4f4f4; }
        .container { max-width: 600px; margin: 20px auto; background: #fff; border-radius: 8px; box-shadow: 0 2px 8px #ccc; padding: 20px; }
        h1 { font-size: 1.5em; margin-bottom: 0.5em; }
        .status { margin-bottom: 1em; }
        .screenshots { display: flex; flex-wrap: wrap; gap: 10px; justify-content: center; }
        .screenshots img { max-width: 48%; height: auto; border-radius: 4px; box-shadow: 0 1px 4px #aaa; }
        ul { padding-left: 1.2em; }
        li { margin-bottom: 0.2em; }
        @media (max-width: 600px) {
            .container { max-width: 98vw; padding: 8px; }
            .screenshots img { max-width: 98vw; }
        }
    </style>
</head>
<body>
<div class="container">
    <h1>Teams Shift Scanner Status</h1>
    <div class="status">
        <b>Status:</b> {{ status }}<br>
        <b>Last Scan:</b> {{ last_scan }}<br>
        <b>Last Result:</b> {{ last_result }}
    </div>
    <div class="screenshots">
        {% for img in screenshots %}
        <div><img src="/screenshot/{{ img }}" alt="Screenshot"></div>
        {% endfor %}
    </div>
    <h2>Upcoming Shifts</h2>
    <ul>
    {% for line in shift_lines %}
        {{ line|safe }}
    {% endfor %}
    </ul>
</div>
</body>
</html>
'''

def get_latest_screenshots(n=4):
    folder = os.path.join(os.path.dirname(__file__), 'screenshots')
    if not os.path.exists(folder):
        return []
    files = [f for f in os.listdir(folder) if f.lower().endswith('.png')]
    files.sort(reverse=True)
    return files[:n]

def get_shift_summary():
    from datetime import date, timedelta
    today = date.today()
    # Get all future shifts
    import sqlite3
    config = load_config()
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
    return shift_lines

@app.route('/')
def status_page():
    # Example status and scan info (replace with real values if available)
    status = "Running"
    # For demo, try to get last scan info from a file or log (customize as needed)
    last_scan = "Unknown"
    last_result = "Unknown"
    scan_log = os.path.join(os.path.dirname(__file__), 'scan.log')
    if os.path.exists(scan_log):
        with open(scan_log, 'r') as f:
            lines = f.readlines()
            if lines:
                last = lines[-1].strip().split('|')
                if len(last) >= 3:
                    last_scan = last[1].strip()
                    last_result = last[2].strip()
    screenshots = get_latest_screenshots()
    shift_lines = get_shift_summary()
    return render_template_string(STATUS_TEMPLATE, status=status, last_scan=last_scan, last_result=last_result, screenshots=screenshots, shift_lines=shift_lines)

@app.route('/screenshot/<path:filename>')
def screenshot_file(filename):
    folder = os.path.join(os.path.dirname(__file__), 'screenshots')
    return send_from_directory(folder, filename)

def run_status_server():
    # Run Flask in a thread so it doesn't block the main app
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False), daemon=True).start()

# ...existing code...
