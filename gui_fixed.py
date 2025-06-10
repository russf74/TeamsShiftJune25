import tkinter as tk
from tkinter import ttk, messagebox
import calendar
from datetime import datetime, timedelta
from database import get_shifts_for_month, get_availability_for_month, set_availability_for_date

class CalendarView(ttk.Frame):
    def __init__(self, master, year, month, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.year = year
        self.month = month
        self.build_widgets()

    def build_widgets(self):
        for widget in self.winfo_children():
            widget.destroy()
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
        shift_dates = {s['date']: s['shift_type'] for s in shifts}
        available_dates = set(a['date'] for a in availability)
        for r, week in enumerate(month_days):
            for c, day in enumerate(week):
                if day == 0:
                    ttk.Label(self, text="").grid(row=r+2, column=c)
                else:
                    date_str = f"{self.year}-{self.month:02d}-{day:02d}"
                    shift = shift_dates.get(date_str)
                    # Use orange style for the whole cell if open shift
                    frame_style = "Orange.TFrame" if shift == 'open' else None
                    frame = ttk.Frame(self, borderwidth=1, relief="solid", style=frame_style)
                    frame.grid(row=r+2, column=c, padx=1, pady=1, sticky="nsew")

                    # Use orange label and checkbox if open shift
                    label_style = "Orange.TLabel" if shift == 'open' else None
                    cb_style = "Orange.TCheckbutton" if shift == 'open' else None

                    label = ttk.Label(frame, text=str(day), style=label_style) if label_style else ttk.Label(frame, text=str(day))
                    label.pack()
                    if shift == 'booked':
                        ttk.Label(frame, text="Booked", foreground="green").pack()
                    # Availability checkbox
                    var = tk.BooleanVar(value=date_str in available_dates)
                    cb = ttk.Checkbutton(frame, text="Available", variable=var,
                        command=lambda d=date_str, v=var: set_availability_for_date(d, v.get()), style=cb_style) if cb_style else ttk.Checkbutton(frame, text="Available", variable=var,
                        command=lambda d=date_str, v=var: set_availability_for_date(d, v.get()))
                    cb.pack()

class MainApp(ttk.Frame):
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        # Add orange style for open shifts (after root exists)
        style = ttk.Style()
        style.configure("Orange.TFrame", background="#FFA500")
        style.configure("Orange.TLabel", background="#FFA500")
        style.configure("Orange.TCheckbutton", background="#FFA500")
        self.pack(fill="both", expand=True)
        self.current_date = datetime.today().replace(day=1)

        # --- Scan Timer Controls ---
        from config import load_config, save_config
        self.config = load_config()

        # Place timer_frame and scan_status_label at the top, then calendar below
        self.timer_frame = ttk.Frame(self)
        self.timer_frame.pack(fill="x", pady=10, side="top", anchor="n")

        ttk.Label(self.timer_frame, text="Scan Interval (seconds):").pack(side="left", padx=5)
        self.interval_var = tk.StringVar(value=str(self.config.get("scan_interval_seconds", 600)))
        self.interval_entry = ttk.Entry(self.timer_frame, textvariable=self.interval_var, width=8)
        self.interval_entry.pack(side="left")
        self.save_btn = ttk.Button(self.timer_frame, text="Save", command=self.save_interval)
        self.save_btn.pack(side="left", padx=5)
        self.toggle_var = tk.BooleanVar(value=False)
        self.toggle_btn = ttk.Checkbutton(self.timer_frame, text="Start Scanning", variable=self.toggle_var, command=self.toggle_scanning, style="Switch.TCheckbutton")
        self.toggle_btn.pack(side="left", padx=10)
        self.countdown_var = tk.StringVar(value="")
        self.countdown_label = ttk.Label(self.timer_frame, textvariable=self.countdown_var, font=("Arial", 12, "bold"))
        self.countdown_label.pack(side="left", padx=10)
        self.timer_running = False
        self.remaining = int(self.interval_var.get())
        self._scanning = False  # Flag to prevent calendar updates during scanning

        # Manual Scan Button
        self.scan_btn = ttk.Button(self.timer_frame, text="Scan", command=self.manual_scan)
        self.scan_btn.pack(side="left", padx=10)

        # --- Clear All Shifts Button ---
        self.clear_btn = ttk.Button(self.timer_frame, text="Clear All Shifts", command=self.clear_all_shifts)
        self.clear_btn.pack(side="left", padx=10)

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
                return
            
            # Check if calendar frame still exists in Tkinter
            try:
                # This will raise TclError if the widget was destroyed
                self.cal_frame.winfo_exists()
                if not self.cal_frame.winfo_viewable():
                    print("[GUI] Calendar frame not viewable, refreshing...")
                    self.refresh_calendar()
            except tk.TclError:
                print("[GUI] Calendar frame was destroyed, recreating...")
                self.cal_frame = CalendarView(self, self.current_date.year, self.current_date.month)
                self.cal_frame.pack(fill="both", expand=True, side="top", anchor="n")
                
        except Exception as e:
            print(f"[GUI] Error ensuring calendar visibility: {e}")
            # Force recreation as last resort
            try:
                self.cal_frame = CalendarView(self, self.current_date.year, self.current_date.month)
                self.cal_frame.pack(fill="both", expand=True)
            except Exception as e2:
                print(f"[GUI] Failed to recreate calendar: {e2}")

    def clear_all_shifts(self):
        from database import clear_all_shifts
        if messagebox.askyesno("Confirm", "Are you sure you want to delete ALL shifts from the database?"):
            clear_all_shifts()
            messagebox.showinfo("Shifts Cleared", "All shifts have been deleted from the database.")
            self.refresh_calendar()
        
    def manual_scan(self):
        """
        Performs a full automation scan for open shifts in Teams (4 months)
        1. Runs the full UI automation workflow
        2. Detects open shifts for each month and adds them to the database
        3. Shows results and refreshes the calendar
        """
        from automation import scan_four_months_with_automation
        from ocr_processing import extract_shifts_from_image
        from database import shift_exists, add_shift, get_availability_for_date
        import os
        import datetime

        # Always create scan_status_var and scan_status_label once, and place it in a fixed location
        if not hasattr(self, 'scan_status_var'):
            self.scan_status_var = tk.StringVar(value="")
            self.scan_status_label = ttk.Label(self, textvariable=self.scan_status_var, font=("Arial", 12, "bold"), foreground="blue")
            # Place the scan status label just below the timer_frame, always
            self.scan_status_label.pack_forget()  # In case it was packed elsewhere
            self.scan_status_label.pack(after=self.timer_frame, fill="x", pady=5)

        def set_status(msg):
            self.scan_status_var.set(msg)
            self.update_idletasks()

        # Store all found shifts across all months
        found_shifts = {}
        matched_dates = []

        # Store the first scanned month/year so we can return to it at the end
        self._first_scan_year = None
        self._first_scan_month = None
        
        # Keep track of the original month to return to after scan
        original_year = self.current_date.year
        original_month = self.current_date.month

        def ocr_and_store(image_path, year, month):
            set_status(f"Analyzing {calendar.month_name[month]} {year} for open shifts...")
            date_map = extract_shifts_from_image(image_path, year, month)
            new_shifts_this_month = 0
            for date_str in date_map:
                found_shifts[date_str] = True
                if not shift_exists(date_str, 'open'):
                    add_shift(date_str, 'open')
                    new_shifts_this_month += 1
                    # Check if user is available on this date
                    availability = get_availability_for_date(date_str)
                    if availability and availability.get('is_available'):
                        matched_dates.append(date_str)
            # Store the first scanned month/year so we can return to it at the end
            if self._first_scan_year is None:
                self._first_scan_year = year
                self._first_scan_month = month
            
            # Update status but DON'T update calendar during scan to avoid visual issues
            scan_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.scan_status_var.set(f"Scanned: {calendar.month_name[month]} {year} at {scan_time} : {new_shifts_this_month} new shifts found.")
            
            # --- Clean up old screenshots, keep only the latest set ---
            import glob, os
            screenshot_dir = os.path.join(os.getcwd(), 'screenshots')
            all_files = glob.glob(os.path.join(screenshot_dir, 'shifts_screenshot_*.png'))
            import re
            timestamps = set()
            for f in all_files:
                m = re.search(r'shifts_screenshot_(\d{8}_\d{6})', f)
                if m:
                    timestamps.add(m.group(1))
            if len(timestamps) > 1:
                latest = sorted(timestamps)[-1]
                for ts in timestamps:
                    if ts == latest:
                        continue
                    for f in glob.glob(os.path.join(screenshot_dir, f'shifts_screenshot_{ts}*')):
                        try:
                            os.remove(f)
                        except Exception as e:
                            print(f"[Cleanup] Could not delete {f}: {e}")

        try:
            set_status("Running full Teams automation scan (4 months)...")
            import datetime as pydatetime
            now = pydatetime.datetime.now()
            self._first_scan_year = None
            self._first_scan_month = None
            
            # Disable calendar updates during scanning to prevent disappearing
            self._scanning = True
            
            scan_four_months_with_automation(ocr_and_store, now.year, now.month)
            
            # Re-enable calendar updates
            self._scanning = False
            set_status("")

            # After scan, return to original month in the GUI and refresh once
            self.current_date = pydatetime.datetime(original_year, original_month, 1)
            self.refresh_calendar()

            # Show results in the on-screen label only (no popups)
            scan_time = pydatetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            new_shifts = len(found_shifts)
            self.scan_status_var.set(f"Last scan run: {scan_time} : {new_shifts} new shifts found.")

        except Exception as e:
            # Re-enable calendar updates on error
            self._scanning = False
            set_status("")
            self.scan_status_var.set(f"Scan error: {str(e)}")
            # Refresh calendar to ensure it's visible after error
            self.refresh_calendar()
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
        Toggle the automatic scanning functionality on/off
        """
        if self.toggle_var.get():
            # Start scanning
            self.timer_running = True
            self.remaining = int(self.interval_var.get())
            self.start_countdown()
            self.toggle_btn.config(text="Stop Scanning")
            messagebox.showinfo("Auto-Scanning", f"Auto-scanning enabled. First scan will occur in {self.remaining} seconds.")
        else:
            # Stop scanning
            self.timer_running = False
            self.remaining = int(self.interval_var.get())
            self.update_countdown_label()
            self.toggle_btn.config(text="Start Scanning")
            messagebox.showinfo("Auto-Scanning", "Auto-scanning disabled.")

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
        Performs an automated scan without UI dialogs
        """
        from automation import focus_teams_window, capture_shifts_screen
        from ocr_processing import extract_shifts_from_image
        from database import shift_exists, add_shift, get_availability_for_date
        import os
        
        # Update status
        self.countdown_var.set(f"Auto-scanning...")
        self.master.update()
        
        # Preserve current calendar state
        original_year = self.current_date.year
        original_month = self.current_date.month
        
        try:
            # 1. Focus Teams window
            if not focus_teams_window():
                print("[Auto-scan] Could not focus Teams window")
                self.countdown_var.set(f"Error: Teams not found")
                self.after(3000, lambda: self.update_countdown_label())
                return
                
            # 2. Capture screenshot
            screenshot_path = capture_shifts_screen()
            if not screenshot_path or not os.path.exists(screenshot_path):
                print("[Auto-scan] Failed to capture screenshot")
                self.countdown_var.set(f"Error: Screenshot failed")
                self.after(3000, lambda: self.update_countdown_label())
                return
                
            # 3. Detect open shifts for current month only (to avoid calendar issues)
            year, month = self.current_date.year, self.current_date.month
            date_map = extract_shifts_from_image(screenshot_path, year, month)
            
            # 4. Process results
            added = 0
            matched_dates = []
            
            for date_str in date_map:
                if not shift_exists(date_str, 'open'):
                    add_shift(date_str, 'open')
                    added += 1
                    
                    # Check for availability match
                    availability = get_availability_for_date(date_str)
                    if availability and availability.get('is_available'):
                        matched_dates.append(date_str)
                        
            # 5. Update status with results
            if added > 0:
                if matched_dates:
                    # Found matches
                    self.countdown_var.set(f"Found {len(matched_dates)} matches!")
                else:
                    self.countdown_var.set(f"Found {added} shifts")
            else:
                self.countdown_var.set(f"No new shifts found")
                
            # 6. Refresh calendar only if we found new shifts to avoid unnecessary updates
            if added > 0:
                # Ensure we're still on the same month before refreshing
                if self.current_date.year == original_year and self.current_date.month == original_month:
                    self.refresh_calendar()
            else:
                # Even if no new shifts, ensure calendar is still visible
                self.ensure_calendar_visible()
            
            # Reset countdown display after a few seconds
            self.after(3000, lambda: self.update_countdown_label())
            
        except Exception as e:
            print(f"[Auto-scan] Error: {e}")
            import traceback
            traceback.print_exc()
            self.countdown_var.set(f"Scan error")
            # Ensure calendar is still visible after error
            self.ensure_calendar_visible()
            self.after(3000, lambda: self.update_countdown_label())

    def update_countdown_label(self):
        self.countdown_var.set(f"Countdown: {self.remaining}s")

    def prev_month(self):
        prev = self.current_date - timedelta(days=1)
        self.current_date = prev.replace(day=1)
        self.refresh_calendar()

    def next_month(self):
        year = self.current_date.year + (self.current_date.month // 12)
        month = self.current_date.month % 12 + 1
        self.current_date = self.current_date.replace(year=year, month=month, day=1)
        self.refresh_calendar()

    def refresh_calendar(self):
        """
        Safely refresh the calendar display
        """
        try:
            # Don't refresh if we're in the middle of scanning to avoid visual issues
            if hasattr(self, '_scanning') and self._scanning:
                return
                
            # Destroy existing calendar frame if it exists
            if hasattr(self, 'cal_frame') and self.cal_frame is not None:
                try:
                    self.cal_frame.destroy()
                except tk.TclError:
                    # Calendar frame was already destroyed
                    pass
            
            # Create new calendar frame with proper positioning
            self.cal_frame = CalendarView(self, self.current_date.year, self.current_date.month)
            self.cal_frame.pack(fill="both", expand=True, side="top", anchor="n")
            
            # Force update to ensure visibility
            self.update_idletasks()
            
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
    geom = config.get("window_geometry")
    if geom:
        root.geometry(geom)
    else:
        root.geometry("800x600")
    def save_window_geometry():
        config["window_geometry"] = root.geometry()
        from config import save_config
        save_config(config)
        root.quit()
    app = MainApp(root)
    root.protocol("WM_DELETE_WINDOW", save_window_geometry)
