import tkinter as tk
from tkinter import ttk, messagebox
import calendar
from database import get_shifts_for_month
from datetime import timedelta
from database import get_shifts_for_month, get_availability_for_month, set_availability_for_date
import datetime as pydatetime

class CalendarView(ttk.Frame):
    def __init__(self, master, year, month, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.year = year
        self.month = month
        self.build_widgets()

    def build_widgets(self):
        style = ttk.Style()
        # Remove all children widgets to clear previous month's content
        for widget in self.winfo_children():
            widget.destroy()
        self.update_idletasks()
        cal = calendar.Calendar()
        month_days = cal.monthdayscalendar(self.year, self.month)
        header = f"{calendar.month_name[self.month]} {self.year}"
        ttk.Label(self, text=header, font=("Arial", 16)).grid(row=0, column=0, columnspan=7, pady=5)
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for idx, day in enumerate(days):
            ttk.Label(self, text=day, font=("Arial", 10, "bold")).grid(row=1, column=idx)
        # Fetch DB info
        shifts = get_shifts_for_month(self.year, self.month)
        availability = get_availability_for_month(self.year, self.month)
        # Build shift info dict: {date: {type, alerted, count}}
        shift_info = {}
        for s in shifts:
            shift_info[s['date']] = {'type': s['shift_type'], 'alerted': s.get('alerted', 0), 'count': s.get('count', 1)}
        available_dates = set(a['date'] for a in availability)
        for r, week in enumerate(month_days):
            for c, day in enumerate(week):
                if day == 0:
                    ttk.Label(self, text="").grid(row=r+2, column=c)
                else:
                    date_str = f"{self.year}-{self.month:02d}-{day:02d}"
                    shift = shift_info.get(date_str)
                    is_available = date_str in available_dates
                    # If the shift is booked, force is_available to False (untick)
                    if shift and shift['type'] == 'booked':
                        is_available = False
                    # Check if date is in the past
                    today = pydatetime.date.today()
                    cell_date = pydatetime.date(self.year, self.month, day)
                    is_past = cell_date < today
                    # Color logic:
                    # Booked: blue
                    # Open+available+not emailed: green
                    # Open+available+emailed: purple
                    # Open+not available: orange
                    # Past: dark grey
                    if is_past:
                        frame_style = None
                        label_style = None
                        cb_style = None
                        frame = tk.Frame(self, bg="#888888", highlightbackground="#888", highlightthickness=1)
                        frame.grid(row=r+2, column=c, padx=1, pady=1, sticky="nsew")
                        label = tk.Label(frame, text=str(day), bg="#888888", fg="#cccccc")
                        label.pack()
                        spacer = tk.Label(frame, text=" ", width=9, bg="#888888")
                        spacer.pack()
                        cb = ttk.Checkbutton(frame, text="", state="disabled")
                        cb.pack(anchor="center")
                        continue
                    elif shift and shift['type'] == 'booked':
                        frame_style = "Blue.TFrame"
                        label_style = "Blue.TLabel"
                        cb_style = "Blue.TCheckbutton"
                    elif shift and shift['type'] == 'open':
                        if is_available:
                            # Always green for open+available, regardless of alerted status
                            frame_style = "Green.TFrame"
                            label_style = "Green.TLabel"
                            cb_style = "Green.TCheckbutton"
                        else:
                            # Open shift exists, but not available: always orange
                            frame_style = "Orange.TFrame"
                            label_style = "Orange.TLabel"
                            cb_style = "Orange.TCheckbutton"
                    else:
                        frame_style = None
                        label_style = None
                        cb_style = None

                    # Use tk.Frame for colored backgrounds to avoid ttk style bleed-through
                    if frame_style:
                        frame = tk.Frame(self, bg=style.lookup(frame_style, 'background'), highlightbackground="#888", highlightthickness=1)
                    else:
                        frame = ttk.Frame(self, borderwidth=1, relief="solid")
                    frame.grid(row=r+2, column=c, padx=1, pady=1, sticky="nsew")
                    # Use tk.Label for colored backgrounds
                    if label_style:
                        label = tk.Label(frame, text=str(day), bg=style.lookup(label_style, 'background'))
                    else:
                        label = ttk.Label(frame, text=str(day))
                    label.pack()
                    var = tk.BooleanVar(value=is_available)
                    # --- Show open shift count in the middle spacer ---
                    count_text = " "
                    if shift and shift['type'] == 'open':
                        count = shift.get('count', 1)
                        if count > 0:
                            count_text = f"({count})"
                    spacer = tk.Label(frame, text=count_text, width=9, bg=style.lookup(label_style, 'background') if label_style else None, fg="#333", font=("Arial", 9))
                    spacer.pack()
                    if cb_style:
                        cb = ttk.Checkbutton(frame, text="", variable=var,
                            command=lambda d=date_str, v=var: set_availability_for_date(d, v.get()), style=cb_style)
                        cb.pack(anchor="center")
                    else:
                        cb = ttk.Checkbutton(frame, text="", variable=var,
                            command=lambda d=date_str, v=var: set_availability_for_date(d, v.get()))
                        cb.pack(anchor="center")

        # --- Display shift counts in calendar cells ---
        # Use self.year and self.month, and use the top-level import
        shift_counts = {}
        for shift in shifts:
            if shift['shift_type'] == 'open':
                if shift['date'] not in shift_counts:
                    shift_counts[shift['date']] = shift.get('count', 1)
                else:
                    shift_counts[shift['date']] += shift.get('count', 1)
        # Update calendar cells with shift counts (placeholder logic)
        for day in range(1, calendar.monthrange(self.year, self.month)[1] + 1):
            date_str = f"{self.year}-{self.month:02d}-{day:02d}"
            count = shift_counts.get(date_str, 0)
            if count > 1:
                # Draw the count in the cell (e.g., as a label or overlay)
                # This is a placeholder; actual drawing depends on your calendar widget
                cell = self.get_calendar_cell_for_date(day)
                if cell:
                    cell.set_shift_count(count)

    def get_calendar_cell_for_date(self, day):
        # Placeholder: return the widget or cell object for the given day
        # You must implement this according to your calendar widget
        # For now, return None to avoid errors
        return None

class MainApp(ttk.Frame):
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        # --- Daily summary tracking ---
        self.scan_count_today = 0
        self.error_log_today = []
        self.last_scan_time = None
        self.last_alert_count = 0
        self.last_new_shifts = 0
        self.last_scan_status = ""
        self._summary_email_sent_date = None
        self._start_daily_summary_timer()

        # Add orange style for open shifts (after root exists)
        style = ttk.Style()
        style.configure("Orange.TFrame", background="#FFA500")
        style.configure("Orange.TLabel", background="#FFA500")
        style.configure("Orange.TCheckbutton", background="#FFA500")

        style.configure("Green.TFrame", background="#90EE90")  # light green
        style.configure("Green.TLabel", background="#90EE90")
        style.configure("Green.TCheckbutton", background="#90EE90")

        style.configure("Blue.TFrame", background="#3399FF")  # blue for booked
        style.configure("Blue.TLabel", background="#3399FF")
        style.configure("Blue.TCheckbutton", background="#3399FF")

        style.configure("Purple.TFrame", background="#B266FF")  # purple for emailed open
        style.configure("Purple.TLabel", background="#B266FF")
        style.configure("Purple.TCheckbutton", background="#B266FF")
        self.pack(fill="both", expand=True)
        self.current_date = pydatetime.datetime.today().replace(day=1)

        # --- Scan Timer Controls ---
        from config import load_config, save_config
        self.config = load_config()

        # Place timer_frame and scan_status_label at the top, then calendar below
        self.timer_frame = ttk.Frame(self)
        self.timer_frame.pack(fill="x", pady=10, side="top", anchor="n")

        # --- Top row: Scan interval controls ---
        ttk.Label(self.timer_frame, text="Scan Interval (seconds):").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.interval_var = tk.StringVar(value=str(self.config.get("scan_interval_seconds", 600)))
        self.interval_entry = ttk.Entry(self.timer_frame, textvariable=self.interval_var, width=8)
        self.interval_entry.grid(row=0, column=1, padx=2, pady=2, sticky="w")
        self.save_btn = ttk.Button(self.timer_frame, text="Store", command=self.save_interval)
        self.save_btn.grid(row=0, column=2, padx=5, pady=2, sticky="w")
        # Replace checkbox with a toggle button (on/off)
        self.scanning_on = False
        self.toggle_btn = ttk.Button(self.timer_frame, text="Start Scanning", command=self.toggle_scanning, width=14)
        self.toggle_btn.grid(row=0, column=3, padx=10, pady=2, sticky="w")
        self.countdown_var = tk.StringVar(value="")
        # Place countdown label on a new row, smaller font
        self.countdown_label = ttk.Label(self.timer_frame, textvariable=self.countdown_var, font=("Arial", 9))
        self.countdown_label.grid(row=2, column=0, columnspan=5, padx=5, pady=(2, 0), sticky="w")
        self.timer_running = False
        self.remaining = int(self.interval_var.get())
        self._scanning = False  # Flag to prevent calendar updates during scanning

        # --- Second row: Action buttons ---
        self.scan_btn = ttk.Button(self.timer_frame, text="Scan", command=self.manual_scan)
        self.scan_btn.grid(row=1, column=0, padx=5, pady=4, sticky="w")
        self.clear_btn = ttk.Button(self.timer_frame, text="Clear All Shifts", command=self.clear_all_shifts)
        self.clear_btn.grid(row=1, column=1, padx=5, pady=4, sticky="w")
        self.test_email_btn = ttk.Button(self.timer_frame, text="Test Msg", command=self.send_test_msg)
        self.test_email_btn.grid(row=1, column=2, padx=5, pady=4, sticky="w")

        # Scan status label always just below timer_frame
        self.scan_status_var = tk.StringVar(value="")
        self.scan_status_label = ttk.Label(self, textvariable=self.scan_status_var, font=("Arial", 10))
        self.scan_status_label.pack(fill="x", pady=5, side="top", anchor="n")
        # Header and calendar below controls
        self.header = ttk.Frame(self)
        self.header.pack(fill="x", side="top", anchor="n")
        self.prev_btn = ttk.Button(self.header, text="<", width=3, command=self.prev_month)
        self.prev_btn.pack(side="left", padx=5, pady=5)
        self.next_btn = ttk.Button(self.header, text=">", width=3, command=self.next_month)
        self.next_btn.pack(side="right", padx=5, pady=5)

        # Initialize calendar frame with error handling
        try:
            self.cal_frame = CalendarView(self, self.current_date.year, self.current_date.month)
            self.cal_frame.pack(fill="both", expand=True, side="top", anchor="n")
        except Exception as e:
            print(f"[GUI] Error initializing calendar: {e}")
            # Create a simple fallback calendar
            self.cal_frame = ttk.Label(self, text="Calendar loading...")
            self.cal_frame.pack(fill="both", expand=True, side="top", anchor="n")
            # Try to recreate the calendar after a short delay
            self.after(500, self.ensure_calendar_visible)
    def _start_daily_summary_timer(self):
        import threading, datetime
        from email_db import check_email_sent
        
        def check_and_send_summary():
            now = datetime.datetime.now()
            # If it's after 6:00pm and we haven't sent today's summary, send it
            if now.hour > 18 or (now.hour == 18 and now.minute >= 0):
                # Check database to see if email was already sent today
                if not check_email_sent():
                    self.send_daily_summary_email()
                    self._summary_email_sent_date = now.date()
            # Schedule next check in 5 minutes
            threading.Timer(300, check_and_send_summary).start()
        check_and_send_summary()

    def _log_scan(self, new_shifts, alert_count, scan_status):
        import datetime
        self.scan_count_today += 1
        self.last_scan_time = datetime.datetime.now()
        self.last_new_shifts = new_shifts
        self.last_alert_count = alert_count
        self.last_scan_status = scan_status
        # Track new shifts for summary
        if not hasattr(self, 'new_shifts_today'):
            self.new_shifts_today = []
        if isinstance(new_shifts, list):
            self.new_shifts_today.extend(new_shifts)
        elif isinstance(new_shifts, int) and new_shifts > 0:
            self.new_shifts_today.append(f"{new_shifts} new shifts")
        # Track emails/whatsapp sent
        if not hasattr(self, 'emails_sent_today'):
            self.emails_sent_today = 0
        self.emails_sent_today += alert_count
        if not hasattr(self, 'whatsapp_sent_today'):
            self.whatsapp_sent_today = 0
        self.whatsapp_sent_today += alert_count

    def _log_error(self, error_msg):
        import datetime
        ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.error_log_today.append(f"[{ts}] {error_msg}")

    def send_daily_summary_email(self):
        from email_alert import send_summary_email
        from email_db import check_email_sent
        if not check_email_sent():
            stats = {
                'scan_count': self.scan_count_today,
                'error_count': len(self.error_log_today),
                'new_shifts': getattr(self, 'new_shifts_today', []),
                'emails_sent': getattr(self, 'emails_sent_today', 0),
                'whatsapp_sent': getattr(self, 'whatsapp_sent_today', 0),
                'last_scan_time': self.last_scan_time.strftime('%Y-%m-%d %H:%M:%S') if self.last_scan_time else None,
                'last_status': self.last_scan_status,
                'errors': self.error_log_today,
            }
            was_sent = send_summary_email(stats)
            if was_sent:
                print("[INFO] Daily summary email sent.")
        else:
            print("[INFO] Daily summary email already sent today.")

    def send_test_msg(self):
        import json
        import smtplib
        from email.mime.text import MIMEText
        from email.utils import formataddr
        import os
        import time
        self.scan_status_var.set("Sending test email and WhatsApp focus...")
        self.update_idletasks()
        email_success = False
        whatsapp_focus_success = False
        try:
            smtp_path = os.path.join(os.getcwd(), 'smtp_settings.json')
            with open(smtp_path, 'r') as f:
                smtp_settings = json.load(f)
            host = smtp_settings.get('SmtpHost')
            port = smtp_settings.get('SmtpPort')
            user = smtp_settings.get('FromAddress')
            password = smtp_settings.get('FromPassword')
            # Only send to Russ for test
            test_recipient = "russfray74@gmail.com"
            from_name = smtp_settings.get('FromName', user)
            to_name = smtp_settings.get('ToName', test_recipient)
            enable_ssl = smtp_settings.get('EnableSsl', True)
            if not (host and port and user and password):
                self.scan_status_var.set("SMTP settings missing or incomplete.")
                return
            msg = MIMEText("This is a test email from the Teams Shift Database and Alert application.", "plain", "utf-8")
            msg['Subject'] = "Test Email from TeamsDB"
            msg['From'] = formataddr((from_name, user))
            msg['To'] = test_recipient
            server = smtplib.SMTP(host, port, timeout=10)
            if enable_ssl:
                server.starttls()
            server.login(user, password)
            server.sendmail(user, [test_recipient], msg.as_string())
            server.quit()
            email_success = True
        except Exception as e:
            self.scan_status_var.set(f"Test email failed: {e}")
            import traceback
            traceback.print_exc()

        # WhatsApp focus and type test (do not send)
        try:
            import pyautogui
            import pywinauto
            from pywinauto.application import Application
            # Try to focus WhatsApp window
            app = None
            try:
                app = Application(backend="uia").connect(title_re=".*WhatsApp.*", timeout=3)
            except Exception:
                # Try to start WhatsApp if not running
                try:
                    app = Application(backend="uia").start("WhatsApp.exe")
                    time.sleep(2)
                    app = Application(backend="uia").connect(title_re=".*WhatsApp.*", timeout=5)
                except Exception as e:
                    print(f"[WhatsApp] Could not start or connect: {e}")
            if app:
                win = app.top_window()
                win.set_focus()
                time.sleep(0.5)
                pyautogui.typewrite("test", interval=0.05)
                whatsapp_focus_success = True
            else:
                print("[WhatsApp] WhatsApp window not found.")
        except Exception as e:
            print(f"[WhatsApp] Error focusing and typing: {e}")

        # Status update
        if email_success and whatsapp_focus_success:
            self.scan_status_var.set("Test email sent to russfray74@gmail.com and WhatsApp focus/type succeeded.")
        elif email_success:
            self.scan_status_var.set("Test email sent to russfray74@gmail.com, but WhatsApp focus/type failed.")
        elif whatsapp_focus_success:
            self.scan_status_var.set("WhatsApp focus/type succeeded, but test email failed.")
        # If both failed, the error message is already set above.
            
    def ensure_calendar_visible(self):
        """
        Ensures the calendar frame is visible and properly displayed.
        Call this method when there might be display issues.
        """
        try:
            # Check if calendar frame exists and is properly displayed
            if not hasattr(self, 'cal_frame') or self.cal_frame is None:
                print("[GUI] Calendar frame missing, recreating...")
                self.cal_frame = CalendarView(self, self.current_date.year, self.current_date.month)
                self.cal_frame.pack(fill="both", expand=True, side="top", anchor="n")
                self.update()  # Force a complete update of the window
                return
            
            # Check if calendar frame still exists in Tkinter
            try:
                # This will raise TclError if the widget was destroyed
                self.cal_frame.winfo_exists()
                if not self.cal_frame.winfo_viewable():
                    print("[GUI] Calendar frame not viewable, refreshing...")
                    self.refresh_calendar(force=True)  # Force refresh even during scanning
                    self.update()  # Force a complete update of the window
            except tk.TclError:
                print("[GUI] Calendar frame was destroyed, recreating...")
                self.cal_frame = CalendarView(self, self.current_date.year, self.current_date.month)
                self.cal_frame.pack(fill="both", expand=True, side="top", anchor="n")
                self.update()  # Force a complete update of the window
                
        except Exception as e:
            print(f"[GUI] Error ensuring calendar visibility: {e}")
            # Force recreation as last resort
            try:
                # Make sure we're using the current month when recreating
                self.current_date = pydatetime.datetime(self.current_date.year, self.current_date.month, 1)
                
                self.cal_frame = CalendarView(self, self.current_date.year, self.current_date.month)
                self.cal_frame.pack(fill="both", expand=True)
                self.update()  # Force a complete update of the window
            except Exception as e2:
                print(f"[GUI] Failed to recreate calendar: {e2}")

    def clear_all_shifts(self):
        from database import clear_all_shifts
        clear_all_shifts()
        self.scan_status_var.set("Shifts cleared.")
        self.refresh_calendar(force=True)
        
    def manual_scan(self, silent=False):
        """
        Performs a full automation scan for open shifts in Teams (4 months)
        1. Runs the full UI automation workflow
        2. Detects open shifts for each month and adds them to the database
        3. Shows results and refreshes the calendar
        4. If new open shifts are found and you are available (not already booked),
           show them on screen and send a single email with all new matched shifts.
        If silent=True, suppresses any popups/dialogs (for auto-scan).
        """
        from automation import scan_four_months_with_automation
        from ocr_processing import extract_shifts_from_image
        from database import shift_exists, add_shift, get_availability_for_date
        # get_shift_count import removed (function does not exist)
        import os
        import glob
        import shutil
        import datetime

        # --- Clear screenshots directory at the very start of scan ---
        screenshot_dir = os.path.join(os.getcwd(), 'screenshots')
        if os.path.exists(screenshot_dir):
            files = glob.glob(os.path.join(screenshot_dir, '*'))
            for f in files:
                try:
                    os.remove(f)
                except Exception as e:
                    print(f"[Cleanup] Could not delete {f}: {e}")

        def set_status(msg):
            self.scan_status_var.set(msg)
            self.update_idletasks()

        total_new_shifts = 0
        matched_dates = []  # List of (date_str, shift_type)
        matched_dates_set = set()

        original_year = self.current_date.year
        original_month = self.current_date.month
        self._first_scan_year = None
        self._first_scan_month = None

        # Track all found open shifts per (year, month)
        found_open_shifts_by_month = {}

        def ocr_and_store(image_path, year, month):
            # (Screenshot cleanup is now handled at the start of manual_scan, not here)

            nonlocal total_new_shifts
            if self._first_scan_year is None or self._first_scan_month is None:
                self._first_scan_year = year
                self._first_scan_month = month
            set_status(f"Analyzing {calendar.month_name[month]} {year} for shifts...") # Generalize status
            all_shifts_map = extract_shifts_from_image(image_path, year, month) # Renamed for clarity
            new_open_shifts_this_month = 0
            new_booked_shifts_this_month = 0
            processed_dates_this_month = set()
            for date_str, shift_info in all_shifts_map.items():
                shift_type = shift_info['type'] # 'open' or 'booked'
                shift_count = shift_info.get('count', 1)  # Get the count from OCR detection
                # coords = shift_info['coords'] # Available if needed

                processed_dates_this_month.add(date_str)

                if shift_type == 'open':
                    if not shift_exists(date_str, 'open'):
                        # Check if it's already booked, if so, don't add as open
                        if shift_exists(date_str, 'booked'):
                            print(f"[GUI] Shift on {date_str} is already booked, not adding as open.")
                            continue
                        add_shift(date_str, 'open', shift_count)
                        new_open_shifts_this_month += 1
                        total_new_shifts += 1 # This counts all new shifts (open or booked)
                        # Availability check for open shifts
                        availability = get_availability_for_date(date_str)
                        # booked check here is for a *different* type of booking, not the one we just found
                        # if it was booked by this scan, it would be shift_type == 'booked'
                        is_already_booked_in_db = shift_exists(date_str, 'booked') 
                        if availability and availability.get('is_available') and not is_already_booked_in_db:
                            if date_str not in matched_dates_set: # matched_dates_set is for availability matches
                                matched_dates.append(date_str)
                                matched_dates_set.add(date_str)
                elif shift_type == 'booked':
                    # If an open shift for this date was previously added in this scan session from a different screenshot,
                    # we might need to remove it or update its type.
                    # For now, just add as booked if not already booked.
                    if not shift_exists(date_str, 'booked'):
                        add_shift(date_str, 'booked', shift_count)
                        new_booked_shifts_this_month += 1
                        total_new_shifts += 1 # Count new booked shifts
                        # If it was previously marked as 'open' in the DB from a *prior* scan, update it.
                        if shift_exists(date_str, 'open'):
                            print(f"[GUI] Updating shift on {date_str} from open to booked.")
                            # This might require a specific update_shift_type function in database.py
                            # For now, we assume add_shift handles conflicts or we add a new one.
                            # If add_shift overwrites, it's fine. If not, we might have duplicates or need an update function.
                            # Let's assume add_shift can handle this by either updating or ignoring if same type.
                            # If it was added as 'open' in *this current scan run* and now found as 'booked',
                            # the 'open' entry should ideally be removed or updated.
                            # This logic can get complex depending on how `add_shift` and `shift_exists` are implemented.
                            pass # Current add_shift will add a new 'booked' entry. 
                                 # We might need to remove the 'open' one if it exists from a previous iteration of this scan.

            # Update status message
            scan_time = pydatetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            status_msg = f"Scanned: {calendar.month_name[month]} {year} at {scan_time} : "
            if new_open_shifts_this_month > 0:
                status_msg += f"{new_open_shifts_this_month} new open shifts. "
            if new_booked_shifts_this_month > 0:
                status_msg += f"{new_booked_shifts_this_month} new booked shifts. "
            if new_open_shifts_this_month == 0 and new_booked_shifts_this_month == 0:
                status_msg += "No new shifts found."
            self.scan_status_var.set(status_msg.strip())
            
            # Track open shifts for this month for later cleanup (this might need adjustment)
            # found_open_shifts_by_month[(year, month)] = open_dates_this_month # This was for open shifts only
            # We need to decide how to handle cleanup if a date is now booked.
            # For now, let's keep track of all processed dates for potential cleanup logic later.
            found_open_shifts_by_month[(year, month)] = processed_dates_this_month # Store all processed dates for this month

            # Use the top-level import for pydatetime (do not re-import locally)
            self.current_date = pydatetime.datetime(year, month, 1)
            try:
                if hasattr(self, 'cal_frame') and isinstance(self.cal_frame, CalendarView):
                    self.cal_frame.destroy()
                self.cal_frame = CalendarView(self, year, month)
                self.cal_frame.pack(fill="both", expand=True, side="top", anchor="n")
                self.update()
            except Exception as e:
                print(f"[PATCH] Error recreating calendar: {e}")
                self.refresh_calendar(force=True)
            self.ensure_calendar_visible()
            scan_time = pydatetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            # Remove or update the following line to use the correct variables
            # self.scan_status_var.set(f"Scanned: {calendar.month_name[month]} {year} at {scan_time} : {new_shifts_this_month} new shifts found.")
            # Instead, use the status_msg already built above:
            self.scan_status_var.set(status_msg.strip())
            self.update_idletasks()

        def send_availability_alert(matched_dates):
            if not matched_dates:
                return
            import json
            import smtplib
            from email.mime.text import MIMEText
            from email.utils import formataddr
            import os
            try:
                smtp_path = os.path.join(os.getcwd(), 'smtp_settings.json')
                with open(smtp_path, 'r') as f:
                    smtp_settings = json.load(f)
                host = smtp_settings.get('SmtpHost')
                port = smtp_settings.get('SmtpPort')
                user = smtp_settings.get('FromAddress')
                password = smtp_settings.get('FromPassword')
                to_addr = smtp_settings.get('ToAddress')
                extra_recipients = ["laurafray74@gmail.com", "russfray74@gmail.com"]
                all_recipients = set([to_addr] + extra_recipients)
                from_name = smtp_settings.get('FromName', user)
                to_name = smtp_settings.get('ToName', to_addr)
                enable_ssl = smtp_settings.get('EnableSsl', True)
                if not (host and port and user and password and to_addr):
                    self.scan_status_var.set("SMTP settings missing or incomplete.")
                    return
                subject = "New Open Shifts Matching Your Availability"
                body = "The following new open shifts were found that match your availability:\n\n"
                for date_str in matched_dates:
                    try:
                        dt = datetime.datetime.strptime(date_str, "%Y-%m-%d")
                        date_fmt = dt.strftime("%A, %B %d, %Y")
                    except Exception:
                        date_fmt = date_str
                    body += f"- {date_fmt}\n"
                body += "\nPlease log in to Teams to book your shifts as soon as possible.\n"
                msg = MIMEText(body, "plain", "utf-8")
                msg['Subject'] = subject
                msg['From'] = formataddr((from_name, user))
                msg['To'] = ", ".join(all_recipients)
                server = smtplib.SMTP(host, port, timeout=10)
                if enable_ssl:
                    server.starttls()
                server.login(user, password)
                server.sendmail(user, list(all_recipients), msg.as_string())
                server.quit()
                # Mark all emailed shifts as alerted
                from database import mark_shift_alerted
                for date_str in matched_dates:
                    mark_shift_alerted(date_str)
                self.scan_status_var.set(f"Alert email sent for {len(matched_dates)} new matched shifts.")
            except Exception as e:
                self.scan_status_var.set(f"Alert email failed: {e}")
                import traceback
                traceback.print_exc()
            # --- WhatsApp automation: send message after emailing ---
            try:
                from automation import send_whatsapp_message
                # You can change the group name here if needed
                group_name = "Manor Shift Alerts"
                send_whatsapp_message(group_name, matched_dates)
            except Exception as e:
                print(f"[WhatsApp] Error sending WhatsApp message: {e}")

        try:
            set_status("Running full Teams automation scan (4 months)...")
            import datetime as pydatetime
            now = pydatetime.datetime.now()
            self._first_scan_year = None
            self._first_scan_month = None
            self._scanning = True

            scan_four_months_with_automation(ocr_and_store, now.year, now.month)

            self._scanning = False

            # --- Remove obsolete open shifts from DB for each scanned month ---
            from database import delete_shifts_not_in_list
            for (year, month), valid_dates in found_open_shifts_by_month.items():
                delete_shifts_not_in_list(year, month, valid_dates, shift_type='open')

            current_datetime = pydatetime.datetime.now()
            self.current_date = pydatetime.datetime(current_datetime.year, current_datetime.month, 1)

            self.refresh_calendar(force=True)
            self.ensure_calendar_visible()
            self.update()
            set_status("")

            scan_time = pydatetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            if matched_dates:
                summary = f"New matched shifts found: {len(matched_dates)}\n" + ", ".join(matched_dates)
                self.scan_status_var.set(summary)
                send_availability_alert(matched_dates)
            else:
                self.scan_status_var.set(f"Last scan run: {scan_time} : {total_new_shifts} new shifts found. No new matched shifts.")
            # Log scan for summary
            self._log_scan(new_shifts=total_new_shifts, alert_count=len(matched_dates), scan_status=self.scan_status_var.get())

        except Exception as e:
            self._scanning = False
            set_status("")
            self.scan_status_var.set(f"Scan error: {str(e)}")
            self._log_error(str(e))
            self.refresh_calendar(force=True)
            self.ensure_calendar_visible()
            import traceback
            traceback.print_exc()

    def save_interval(self):
        try:
            val = int(self.interval_var.get())
            self.config["scan_interval_seconds"] = val
            from config import save_config
            save_config(self.config)
            self.remaining = val
            self.update_countdown_label()
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid number of seconds.")
            
    def toggle_scanning(self):
        """
        Toggle the automatic scanning functionality on/off using a button.
        """
        if not self.scanning_on:
            # Start scanning
            self.scanning_on = True
            self.timer_running = True
            self.remaining = int(self.interval_var.get())
            self.start_countdown()
            self.toggle_btn.config(text="Stop Scanning")
            # Removed popup box on start
        else:
            # Stop scanning
            self.scanning_on = False
            self.timer_running = False
            self.remaining = int(self.interval_var.get())
            self.update_countdown_label()
            self.toggle_btn.config(text="Start Scanning")
            # Removed popup box on stop

    def start_countdown(self):
        """
        Countdown timer for automated scanning
        """
        if not self.timer_running:
            return
            
        self.update_countdown_label()
        
        # Periodically check calendar visibility (every 30 seconds)
        if self.remaining % 30 == 0:
            self.ensure_calendar_visible()
        
        if self.timer_running:
            if self.remaining > 0:
                self.remaining -= 1
                self.after(1000, self.start_countdown)
            else:
                # When countdown reaches zero, perform a scan
                print(f"[Scheduler] Auto-scan triggered")
                try:
                    # Run scan silently without UI dialogs
                    self.auto_scan()
                except Exception as e:
                    print(f"[Scheduler] Auto-scan error: {e}")
                    import traceback
                    traceback.print_exc()
                # Reset countdown
                self.remaining = int(self.interval_var.get())
                self.after(1000, self.start_countdown)
                
    def auto_scan(self):
        """
        Performs an automated scan without UI dialogs (calls manual_scan with silent=True)
        """
        self.countdown_var.set(f"Auto-scanning...")
        self.master.update()
        try:
            self.manual_scan(silent=True)
        except Exception as e:
            self._log_error(f"Auto-scan error: {e}")
        # Reset countdown display after a few seconds
        self.after(3000, lambda: self.update_countdown_label())
            
    def update_countdown_label(self):
        self.countdown_var.set(f"Countdown: {self.remaining}s")
        
    def prev_month(self):
        prev = self.current_date - timedelta(days=1)
        self.current_date = prev.replace(day=1)        # Force refresh even during scanning to prevent disappearing calendar
        self.refresh_calendar(force=True)
        # Ensure calendar is visible after month change
        self.ensure_calendar_visible()
        
    def next_month(self):
        year = self.current_date.year + (self.current_date.month // 12)
        month = self.current_date.month % 12 + 1
        self.current_date = self.current_date.replace(year=year, month=month, day=1)
        # Force refresh even during scanning to prevent disappearing calendar
        self.refresh_calendar(force=True)
        # Ensure calendar is visible after month change
        self.ensure_calendar_visible()
        
    def refresh_calendar(self, force=False):
        """
        Safely refresh the calendar display.
        If force=True, refresh even during scanning.
        Instead of destroying/recreating the frame, update its contents in place if possible.
        """
        try:
            # We'll refresh calendar even during scanning to fix disappearing issue
            # Just check if we should skip based on force flag (backwards compatibility)
            if hasattr(self, '_scanning') and self._scanning and not force:
                # Instead of returning, we'll continue to update the calendar
                pass
                
            # If cal_frame exists and is a CalendarView, just update its contents for the new month/year
            if hasattr(self, 'cal_frame') and isinstance(self.cal_frame, CalendarView):                # Always create a new CalendarView for the new month to ensure a clean state
                self.cal_frame.destroy()
                self.cal_frame = CalendarView(self, self.current_date.year, self.current_date.month)
                self.cal_frame.pack(fill="both", expand=True, side="top", anchor="n")
                self.update()  # Force a complete update of the window
                return            # If cal_frame is missing or not a CalendarView, create it
            self.cal_frame = CalendarView(self, self.current_date.year, self.current_date.month)
            self.cal_frame.pack(fill="both", expand=True, side="top")
            self.update()  # Force a complete update of the window
        except Exception as e:
            print(f"[GUI] Error refreshing calendar: {e}")
            import traceback
            traceback.print_exc()
            # Try to restore a basic calendar on error
            try:
                self.cal_frame = CalendarView(self, self.current_date.year, self.current_date.month)
                self.cal_frame.pack(fill="both", expand=True)
            except Exception as e2:
                print(f"[GUI] Failed to restore calendar: {e2}")


def launch_gui(root, config):
    root.title("Teams Shift Database and Alert")
    # Restore window size and position if available
    import sqlite3
    DB_PATH = "shifts.db"
    TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS window_geometry (
        id INTEGER PRIMARY KEY,
        geometry TEXT
    )
    """
    def get_last_geometry():
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute(TABLE_SQL)
            c.execute("SELECT geometry FROM window_geometry WHERE id=1")
            row = c.fetchone()
            conn.close()
            if row:
                return row[0]
        except Exception:
            pass
        return None

    def save_geometry(geom):
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute(TABLE_SQL)
            c.execute("INSERT OR REPLACE INTO window_geometry (id, geometry) VALUES (1, ?)", (geom,))
            conn.commit()
            conn.close()
        except Exception:
            pass

    # Set geometry from DB if available, else default, and ensure on-screen
    geom = get_last_geometry()
    fixed_height = 750
    fixed_width = 600
    import re
    def is_geometry_onscreen(geom_str):
        m = re.match(r"(\d+)x(\d+)([+-]\d+)([+-]\d+)", geom_str or "")
        if not m:
            return False
        w, h, x, y = int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4))
        screen_w = root.winfo_screenwidth()
        screen_h = root.winfo_screenheight()
        # Consider window visible if at least top-left is on screen
        return (0 <= x < screen_w - 50) and (0 <= y < screen_h - 50)

    # Default geometry string
    default_geom = f"{fixed_width}x{fixed_height}+64+64"
    use_geom = default_geom
    if geom:
        m = re.match(r"(\d+)x(\d+)([+-]\d+)([+-]\d+)", geom)
        if m and is_geometry_onscreen(geom):
            use_geom = geom
    root.geometry(use_geom)

    def save_window_geometry():
        geom = root.geometry()
        save_geometry(geom)
        root.destroy()

    def on_configure(event):
        # Save geometry on every move/resize
        geom = root.geometry()
        save_geometry(geom)

    root.bind('<Configure>', on_configure)
    app = MainApp(root)
    root.protocol("WM_DELETE_WINDOW", save_window_geometry)

    # Ensure the Quit button is at the top center and performs a forced shutdown
    import os
    import sys

    def force_quit():
        print("[INFO] Application is shutting down forcefully.")
        # Use os._exit to force immediate termination without cleanup
        os._exit(0)

    # Create a frame at the top to hold the quit button
    top_frame = tk.Frame(root)
    top_frame.pack(side=tk.TOP, fill=tk.X)
    
    # Place the quit button in the center of the top frame
    quit_button = tk.Button(top_frame, text="Quit", command=force_quit, bg="red", fg="white")
    quit_button.pack(pady=10)
