import tkinter as tk
from tkinter import ttk, messagebox
import calendar
from database import get_shifts_for_month
from datetime import timedelta
from database import get_shifts_for_month, get_availability_for_month, set_availability_for_date
import datetime as pydatetime

# Fluent-inspired palette for the docked monitor strip under Teams.
UI = {
    "bg": "#E9EEF5",
    "surface": "#FFFFFF",
    "border": "#C9D4E0",
    "text": "#1F2937",
    "muted": "#5B6B7C",
    "accent": "#0F6CBD",
    "accent_hover": "#115EA3",
    "danger": "#C50F1F",
    "past": "#B6C2D0",
    "past_text": "#111827",
    "booked": "#93C5FD",
    "open_avail": "#86EFAC",
    "open_busy": "#FDBA74",
    "empty": "#FFFFFF",
    "empty_alt": "#F8FAFC",
    "header": "#F3F6FA",
    "today": "#0F6CBD",
    "shadow": "#D5DEE8",
}


def _ui_font(size=9, weight="normal"):
    # Prefer Segoe UI on Windows for a native professional look.
    family = "Segoe UI"
    if weight == "bold":
        return (family, size, "bold")
    return (family, size)


class CalendarView(tk.Frame):
    """
    Canvas-drawn monthly grid.

    Drawing on a single Canvas guarantees every week row scales into the
    short docked strip under Teams (no clipped final weeks from widget packing).
    Click a day cell to toggle availability (except past/booked days).
    """

    def __init__(self, master, year, month, *args, **kwargs):
        super().__init__(master, bg=UI["bg"], *args, **kwargs)
        self.year = year
        self.month = month
        self._hit = []  # list of (x1,y1,x2,y2,date_str,locked)
        self._data = None

        self.canvas = tk.Canvas(self, bg=UI["surface"], highlightthickness=1, highlightbackground=UI["border"], bd=0)
        self.canvas.pack(fill="both", expand=True, padx=1, pady=1)
        self.canvas.bind("<Configure>", self._on_resize)
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<Motion>", self._on_motion)
        self._load_data()
        self.after_idle(self.redraw)

    def _load_data(self):
        shifts = get_shifts_for_month(self.year, self.month)
        availability = get_availability_for_month(self.year, self.month)
        shift_info = {
            s["date"]: {
                "type": s["shift_type"],
                "alerted": s.get("alerted", 0),
                "count": s.get("count", 1),
            }
            for s in shifts
        }
        available_dates = set(a["date"] for a in availability)
        month_days = calendar.Calendar().monthdayscalendar(self.year, self.month)
        self._data = {
            "shift_info": shift_info,
            "available_dates": available_dates,
            "month_days": month_days,
            "today": pydatetime.date.today(),
        }

    def build_widgets(self):
        # Compatibility with older refresh path that called build_widgets().
        self._load_data()
        self.redraw()

    def _on_resize(self, _event=None):
        self.redraw()

    def _on_motion(self, event):
        for x1, y1, x2, y2, _date_str, locked in self._hit:
            if x1 <= event.x <= x2 and y1 <= event.y <= y2:
                self.canvas.configure(cursor="arrow" if locked else "hand2")
                return
        self.canvas.configure(cursor="arrow")

    def _on_click(self, event):
        for x1, y1, x2, y2, date_str, locked in self._hit:
            if x1 <= event.x <= x2 and y1 <= event.y <= y2:
                if locked:
                    return
                is_avail = date_str in self._data["available_dates"]
                new_val = not is_avail
                try:
                    set_availability_for_date(date_str, new_val)
                except Exception as e:
                    print(f"[CalendarView] Failed saving availability for {date_str}: {e}")
                    return
                self._load_data()
                self.redraw()
                return

    def redraw(self):
        if not self._data:
            return
        c = self.canvas
        w = max(c.winfo_width(), 10)
        h = max(c.winfo_height(), 10)
        c.delete("all")
        self._hit = []

        # Layout metrics — compact enough for the short docked strip.
        pad = 2
        header_h = 18
        dow_h = 14
        grid_top = pad + header_h + dow_h
        grid_bottom = h - pad
        grid_left = pad
        grid_right = w - pad
        grid_w = max(10, grid_right - grid_left)
        grid_h = max(10, grid_bottom - grid_top)

        month_days = self._data["month_days"]
        weeks = len(month_days) if month_days else 5
        weeks = max(4, weeks)
        cell_w = grid_w / 7.0
        cell_h = grid_h / float(weeks)

        # Card background + header
        c.create_rectangle(0, 0, w, h, fill=UI["surface"], outline="")
        c.create_rectangle(0, 0, w, grid_top - 1, fill=UI["header"], outline="")
        c.create_text(
            pad + 8,
            pad + header_h / 2,
            anchor="w",
            text=f"{calendar.month_name[self.month]} {self.year}",
            fill=UI["text"],
            font=_ui_font(10, "bold"),
        )
        # Weekday labels aligned to columns
        for i, name in enumerate(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]):
            cx = grid_left + cell_w * i + cell_w / 2
            c.create_text(
                cx,
                pad + header_h + dow_h / 2 - 1,
                text=name,
                fill=UI["muted"],
                font=_ui_font(8, "bold"),
            )

        shift_info = self._data["shift_info"]
        available_dates = self._data["available_dates"]
        today = self._data["today"]

        for r, week in enumerate(month_days):
            for col, day in enumerate(week):
                x1 = grid_left + cell_w * col + 0.5
                y1 = grid_top + cell_h * r + 0.5
                x2 = grid_left + cell_w * (col + 1) - 1.5
                y2 = grid_top + cell_h * (r + 1) - 1.5

                if day == 0:
                    c.create_rectangle(x1, y1, x2, y2, fill=UI["header"], outline=UI["border"])
                    continue

                date_str = f"{self.year}-{self.month:02d}-{day:02d}"
                shift = shift_info.get(date_str)
                is_available = date_str in available_dates
                if shift and shift["type"] == "booked":
                    is_available = False
                cell_date = pydatetime.date(self.year, self.month, day)
                is_past = cell_date < today
                is_today = cell_date == today
                locked = bool(is_past or (shift and shift["type"] == "booked"))

                if is_past:
                    bg, fg = UI["past"], UI["past_text"]
                    badge = ""
                elif shift and shift["type"] == "booked":
                    bg, fg = UI["booked"], "#0B1F33"
                    badge = "BOOKED"
                elif shift and shift["type"] == "open":
                    count = int(shift.get("count", 1) or 1)
                    if is_available:
                        bg, fg = UI["open_avail"], "#14532D"
                        badge = f"OPEN x{count}" if count > 1 else "OPEN + AVAIL"
                    else:
                        bg, fg = UI["open_busy"], "#7C2D12"
                        badge = f"OPEN x{count}" if count > 1 else "OPEN"
                else:
                    bg = UI["empty"] if (r + col) % 2 == 0 else UI["empty_alt"]
                    fg = UI["text"]
                    badge = "AVAIL" if is_available else ""

                border = UI["today"] if is_today else UI["border"]
                width = 2 if is_today else 1
                # Soft fill
                c.create_rectangle(x1, y1, x2, y2, fill=bg, outline=border, width=width)
                if is_today:
                    c.create_line(x1 + 1, y1 + 1, x2 - 1, y1 + 1, fill=UI["today"], width=2)

                # Day number
                c.create_text(
                    x1 + 7,
                    y1 + 4,
                    anchor="nw",
                    text=str(day),
                    fill=fg,
                    font=_ui_font(11, "bold"),
                )
                # Availability tick
                if is_available and not is_past and not (shift and shift["type"] == "booked"):
                    c.create_oval(x2 - 16, y1 + 4, x2 - 5, y1 + 15, fill=UI["accent"], outline="")
                    c.create_text(
                        x2 - 10.5,
                        y1 + 9.5,
                        text="✓",
                        fill="white",
                        font=_ui_font(7, "bold"),
                    )
                # Status badge
                if badge and cell_h >= 26:
                    c.create_text(
                        x1 + 7,
                        y2 - 5,
                        anchor="sw",
                        text=badge,
                        fill=fg,
                        font=_ui_font(7, "bold"),
                    )

                self._hit.append((x1, y1, x2, y2, date_str, locked))

    def get_calendar_cell_for_date(self, day):
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

        style = ttk.Style()
        try:
            style.theme_use("vista")
        except Exception:
            pass
        style.configure("App.TFrame", background=UI["bg"])
        style.configure("Toolbar.TFrame", background=UI["surface"])
        style.configure("App.TLabel", background=UI["surface"], foreground=UI["text"], font=_ui_font(9))
        style.configure("Muted.TLabel", background=UI["surface"], foreground=UI["muted"], font=_ui_font(8))
        style.configure("Countdown.TLabel", background=UI["surface"], foreground=UI["accent"], font=_ui_font(9, "bold"))
        style.configure("Tool.TButton", font=_ui_font(8), padding=(6, 1))
        style.configure("Accent.TButton", font=_ui_font(8, "bold"), padding=(8, 1))
        style.configure("Orange.TFrame", background=UI["open_busy"])
        style.configure("Orange.TLabel", background=UI["open_busy"])
        style.configure("Orange.TCheckbutton", background=UI["open_busy"])
        style.configure("Green.TFrame", background=UI["open_avail"])
        style.configure("Green.TLabel", background=UI["open_avail"])
        style.configure("Green.TCheckbutton", background=UI["open_avail"])
        style.configure("Blue.TFrame", background=UI["booked"])
        style.configure("Blue.TLabel", background=UI["booked"])
        style.configure("Blue.TCheckbutton", background=UI["booked"])
        style.configure("Purple.TFrame", background="#B266FF")
        style.configure("Purple.TLabel", background="#B266FF")
        style.configure("Purple.TCheckbutton", background="#B266FF")

        self.configure(style="App.TFrame")
        self.pack(fill="both", expand=True)
        self.current_date = pydatetime.datetime.today().replace(day=1)

        from config import load_config, save_config
        self.config = load_config()

        # Outer chrome - one slim toolbar row so Canvas month grid gets max height.
        outer = tk.Frame(self, bg=UI["bg"])
        outer.pack(fill="both", expand=True)

        self.toolbar = tk.Frame(outer, bg=UI["surface"], highlightbackground=UI["border"], highlightthickness=1)
        self.toolbar.pack(side="top", fill="x", padx=3, pady=(3, 2))
        self.left_panel = self.toolbar
        self.timer_frame = self.toolbar
        self.nav_frame = self.toolbar

        bar = tk.Frame(self.toolbar, bg=UI["surface"])
        bar.pack(side="top", fill="x", padx=6, pady=3)

        def _sep():
            tk.Frame(bar, bg=UI["border"], width=1, height=14).pack(side="left", padx=5, fill="y")

        tk.Label(bar, text="SHIFT MONITOR", font=_ui_font(8, "bold"), bg=UI["surface"], fg=UI["accent"]).pack(side="left", padx=(0, 6))
        tk.Label(bar, text="Interval", font=_ui_font(8), bg=UI["surface"], fg=UI["muted"]).pack(side="left")
        self.interval_var = tk.StringVar(value=str(self.config.get("scan_interval_seconds", 600)))
        self.interval_entry = ttk.Entry(bar, textvariable=self.interval_var, width=4, font=_ui_font(9))
        self.interval_entry.pack(side="left", padx=(3, 2))
        self.save_btn = ttk.Button(bar, text="Store", command=self.save_interval, style="Tool.TButton", width=5)
        self.save_btn.pack(side="left", padx=1)

        _sep()
        self.scanning_on = True
        self.toggle_btn = ttk.Button(bar, text="Stop", command=self.toggle_scanning, style="Accent.TButton", width=5)
        self.toggle_btn.pack(side="left", padx=1)
        self.scan_btn = ttk.Button(bar, text="Scan", command=self.manual_scan, style="Tool.TButton", width=5)
        self.scan_btn.pack(side="left", padx=1)
        self.clear_btn = ttk.Button(bar, text="Clear", command=self.clear_all_shifts, style="Tool.TButton", width=5)
        self.clear_btn.pack(side="left", padx=1)
        self.test_email_btn = ttk.Button(bar, text="Test", command=self.send_test_msg, style="Tool.TButton", width=5)
        self.test_email_btn.pack(side="left", padx=1)
        self.reset_btn = ttk.Button(
            bar,
            text="Reset",
            command=lambda: self.trigger_shift_app_reset(run_scan_after_reset=True),
            style="Tool.TButton",
            width=6,
        )
        self.reset_btn.pack(side="left", padx=1)

        _sep()
        self.prev_btn = ttk.Button(bar, text="<", command=self.prev_month, style="Tool.TButton", width=3)
        self.prev_btn.pack(side="left", padx=1)
        self.current_btn = ttk.Button(bar, text="Today", command=self.move_to_current_month, style="Tool.TButton", width=6)
        self.current_btn.pack(side="left", padx=1)
        self.next_btn = ttk.Button(bar, text=">", command=self.next_month, style="Tool.TButton", width=3)
        self.next_btn.pack(side="left", padx=1)

        _sep()
        self.countdown_var = tk.StringVar(value="")
        self.countdown_label = tk.Label(
            bar, textvariable=self.countdown_var, font=_ui_font(9, "bold"), bg=UI["surface"], fg=UI["accent"]
        )
        self.countdown_label.pack(side="left", padx=(0, 2))
        self.minus10_btn = ttk.Button(bar, text="-10s", command=self.subtract_ten_seconds, style="Tool.TButton", width=4)
        self.minus10_btn.pack(side="left", padx=1)

        self.quit_btn = tk.Button(
            bar,
            text="Quit",
            command=self.force_quit,
            bg=UI["danger"],
            fg="white",
            activebackground="#A50D1A",
            activeforeground="white",
            font=_ui_font(8, "bold"),
            relief="flat",
            bd=0,
            padx=10,
            pady=1,
            cursor="hand2",
        )
        self.quit_btn.pack(side="right")

        legend = tk.Frame(bar, bg=UI["surface"])
        legend.pack(side="right", padx=(4, 8))
        for text, color in (
            ("Booked", UI["booked"]),
            ("Open+Avail", UI["open_avail"]),
            ("Open", UI["open_busy"]),
            ("Past", UI["past"]),
        ):
            tk.Label(
                legend,
                text=" " + text + " ",
                font=_ui_font(7, "bold"),
                bg=color,
                fg=UI["text"],
                highlightbackground=UI["border"],
                highlightthickness=1,
            ).pack(side="left", padx=2)

        self.scan_status_var = tk.StringVar(value="Ready")
        self.scan_status_label = tk.Label(
            bar,
            textvariable=self.scan_status_var,
            font=_ui_font(8),
            bg=UI["surface"],
            fg=UI["muted"],
            anchor="w",
            justify="left",
        )
        self.scan_status_label.pack(side="left", fill="x", expand=True, padx=8)

        self.timer_running = True
        try:
            self.remaining = int(self.interval_var.get())
        except Exception:
            self.remaining = 120
        self._scanning = False
        self._scan_thread_running = False
        self._restart_countdown_when_done = False

        self.right_panel = tk.Frame(outer, bg=UI["bg"])
        self.right_panel.pack(side="top", fill="both", expand=True, padx=3, pady=(0, 3))
        self.header = tk.Frame(self.right_panel, bg=UI["bg"])
        self.header.pack_forget()

        try:
            self.cal_frame = CalendarView(self.right_panel, self.current_date.year, self.current_date.month)
            self.cal_frame.pack(fill="both", expand=True, side="top")
        except Exception as e:
            print("[GUI] Error initializing calendar:", e)
            self.cal_frame = ttk.Label(self.right_panel, text="Calendar loading...")
            self.cal_frame.pack(fill="both", expand=True, side="top")
            self.after(500, self.ensure_calendar_visible)

        self.after(1000, self.start_countdown)
        self.toggle_btn.config(text="Stop" if self.scanning_on else "Start")

    def trigger_shift_app_reset(self, run_scan_after_reset=False):
        import threading
        threading.Thread(
            target=self.refresh_teams_shifts,
            args=(run_scan_after_reset,),
            daemon=True
        ).start()

    def force_quit(self):
        """Force quit the application"""
        print("[INFO] Application is shutting down forcefully.")
        import os
        os._exit(0)

    def _record_screen_video(self, duration_seconds=300, fps=5, filename="midnight_reset_recording.mp4"):
        """
        Record screen during midnight reset process
        Args:
            duration_seconds: How long to record (default 5 minutes)
            fps: Frames per second (default 5 for small file size)
            filename: Output filename (overwrites each day)
        """
        import cv2
        import numpy as np
        import pyautogui
        import time
        
        try:
            # Get screen dimensions
            screen_size = pyautogui.size()
            
            # Calculate scaling to achieve 1280x720 resolution
            target_width, target_height = 1280, 720
            scale_x = target_width / screen_size.width
            scale_y = target_height / screen_size.height
            scale = min(scale_x, scale_y)  # Maintain aspect ratio
            
            # Calculate actual output dimensions
            output_width = int(screen_size.width * scale)
            output_height = int(screen_size.height * scale)
            
            # Define codec and create VideoWriter object
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            out = cv2.VideoWriter(filename, fourcc, fps, (output_width, output_height))
            
            if not out.isOpened():
                print(f"[Recording] Failed to open video writer for {filename}")
                return
            
            start_time = time.time()
            frame_interval = 1.0 / fps  # Time between frames
            next_frame_time = start_time
            
            print(f"[Recording] Starting screen recording: {filename} at {output_width}x{output_height}, {fps} FPS")
            
            while time.time() - start_time < duration_seconds:
                current_time = time.time()
                
                # Only capture frame if it's time for the next one
                if current_time >= next_frame_time:
                    # Capture screenshot
                    screenshot = pyautogui.screenshot()
                    frame = np.array(screenshot)
                    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                    
                    # Resize frame to target resolution
                    if scale != 1.0:
                        frame = cv2.resize(frame, (output_width, output_height), interpolation=cv2.INTER_AREA)
                    
                    # Write frame to video
                    out.write(frame)
                    
                    # Calculate next frame time
                    next_frame_time += frame_interval
                else:
                    # Small sleep to prevent excessive CPU usage
                    time.sleep(0.1)
                    
        except Exception as e:
            print(f"[Recording] Error during screen recording: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if 'out' in locals():
                out.release()
            print(f"[Recording] Screen recording completed: {filename}")

    def _raw_click(self, x, y):
        """Click at exact screen coordinates using ctypes SendInput (works on modern Windows)."""
        import ctypes
        import ctypes.wintypes

        x, y = int(x), int(y)
        ctypes.windll.user32.SetCursorPos(x, y)
        print(f"[RawClick] SetCursorPos({x},{y})")

        # Use SendInput for reliable clicking on modern Windows
        PUL = ctypes.POINTER(ctypes.c_ulong)
        class MouseInput(ctypes.Structure):
            _fields_ = [("dx", ctypes.c_long), ("dy", ctypes.c_long),
                        ("mouseData", ctypes.c_ulong), ("dwFlags", ctypes.c_ulong),
                        ("time", ctypes.c_ulong), ("dwExtraInfo", PUL)]
        class Input_I(ctypes.Union):
            _fields_ = [("mi", MouseInput)]
        class Input(ctypes.Structure):
            _fields_ = [("type", ctypes.c_ulong), ("ii", Input_I)]

        def click_event(flags):
            extra = ctypes.c_ulong(0)
            ii = Input_I()
            ii.mi = MouseInput(0, 0, 0, flags, 0, ctypes.pointer(extra))
            inp = Input(0, ii)  # type 0 = INPUT_MOUSE
            ctypes.windll.user32.SendInput(1, ctypes.pointer(inp), ctypes.sizeof(inp))

        click_event(0x0002)  # MOUSEEVENTF_LEFTDOWN
        import time; time.sleep(0.05)
        click_event(0x0004)  # MOUSEEVENTF_LEFTUP
        print(f"[RawClick] SendInput click fired at ({x},{y})")

    def _show_click_marker(self, x, y, duration_ms=2000):
        """Show a red dot at (x,y) - must be called via self.after() to run on main thread."""
        def _draw():
            try:
                size = 30
                dot = tk.Toplevel(self.master)
                dot.overrideredirect(True)
                dot.wm_attributes('-topmost', True)
                dot.wm_attributes('-transparentcolor', 'white')
                dot.geometry(f"{size}x{size}+{int(x) - size//2}+{int(y) - size//2}")
                c = tk.Canvas(dot, width=size, height=size, bg='white', highlightthickness=0)
                c.pack()
                c.create_oval(2, 2, size-2, size-2, fill='red', outline='darkred', width=3)
                dot.after(duration_ms, dot.destroy)
            except Exception as e:
                print(f"[Marker] {e}")
        self.after(0, _draw)

    def refresh_teams_shifts(self, run_scan_after_reset=False):
        import time
        import threading
        from datetime import datetime
        from email_alert import send_email_alert
        from automation import refresh_teams_shifts_view

        # Start screen recording in background thread
        video_filename = "midnight_reset.mp4"  # Single filename that overwrites each day

        self.scan_status_var.set("Starting screen recording and refreshing Teams Shifts app...")

        # Start recording in background thread
        recording_thread = threading.Thread(
            target=self._record_screen_video,
            args=(180, 5, video_filename),  # 3 minutes is enough for the revised reset path
            daemon=True
        )
        recording_thread.start()

        self.scan_status_var.set("Pausing scanning and refreshing Teams Shifts app...")
        # Pause scanning AND mark reset in progress so any concurrent scan aborts immediately
        self._midnight_reset_in_progress = True
        self.timer_running = False
        self.scanning_on = False
        self._scanning = False
        try:
            self.scan_status_var.set("[Reset] Opening Teams Shifts monthly view...")
            if not refresh_teams_shifts_view():
                raise RuntimeError("Could not refresh Microsoft Teams Shifts monthly view")

            self.scan_status_var.set("Teams Shifts app refreshed successfully. Will resume scanning at 5am.")
            try:
                send_email_alert(
                    "Teams Shifts app reset successful",
                    "Teams Shifts app was successfully refreshed at midnight. Scanning will resume at 5:00 AM.",
                    "russfray74@gmail.com"
                )
                print("[Reset] Success confirmation email sent")
            except Exception as e:
                print(f"[Reset] Failed to send success email: {e}")

            if run_scan_after_reset:
                self.scan_status_var.set("Teams Shifts app refreshed successfully. Starting test scan...")
                self.timer_running = True
                self.scanning_on = True
                self._scanning = False
                self.after(0, lambda: self.manual_scan(silent=True))
                return

            now = datetime.now()
            next_5am = now.replace(hour=5, minute=0, second=0, microsecond=0)
            if now >= next_5am:
                from datetime import timedelta
                next_5am += timedelta(days=1)

            delay_seconds = int((next_5am - now).total_seconds())
            print(f"[Reset] Scheduling scan resumption at 5:00 AM (in {delay_seconds} seconds)")
            self.scan_status_var.set("Midnight reset complete. Resuming at 5:00 AM.")

            def resume_at_5am():
                print("[Reset] Resuming scanning at 5:00 AM")
                self.timer_running = True
                self.scanning_on = True
                self._scanning = False
                self.start_countdown()

            self.after(delay_seconds * 1000, resume_at_5am)
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.scan_status_var.set(f"Teams refresh failed: {e}. Emailing admin.")
            try:
                send_email_alert(
                    "Teams refresh failed",
                    f"Teams Shifts app could not be refreshed: {e}",
                    "russfray74@gmail.com"
                )
            except Exception as email_error:
                print(f"[Reset] Failed to send failure email: {email_error}")
        finally:
            self._midnight_reset_in_progress = False

    def _start_daily_summary_timer(self):
        import threading, datetime
        from email_db import check_email_sent

        def schedule_midnight_refresh(force_next_day=False):
            now = datetime.datetime.now()
            midnight_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
            if not force_next_day and midnight_today <= now < midnight_today + datetime.timedelta(minutes=5):
                next_midnight = now
            else:
                next_midnight = (now + datetime.timedelta(days=1)).replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
            delay_seconds = (next_midnight - now).total_seconds()

            def run_midnight_refresh():
                print(f"[INFO] Triggering midnight Teams Shifts refresh at {datetime.datetime.now():%Y-%m-%d %H:%M:%S}")
                self.trigger_shift_app_reset()
                schedule_midnight_refresh(force_next_day=True)

            midnight_timer = threading.Timer(delay_seconds, run_midnight_refresh)
            midnight_timer.daemon = True
            midnight_timer.start()
        
        def check_and_send_summary():
            import traceback
            now = datetime.datetime.now()
            try:
                # If it's after 8:00pm and we haven't sent today's summary, send it
                if now.hour >= 20:  # 8:00pm or later
                    # Check database to see if email was already sent today
                    if not check_email_sent():
                        print(f"[INFO] Attempting to send daily summary email at {now.strftime('%Y-%m-%d %H:%M:%S')}")
                        try:
                            self.send_daily_summary_email()
                            self._summary_email_sent_date = now.date()
                            print(f"[INFO] Daily summary email sent at {now.strftime('%Y-%m-%d %H:%M:%S')}")
                        except Exception as e:
                            print(f"[ERROR] Failed to send daily summary email: {e}")
                            traceback.print_exc()
                    else:
                        print(f"[INFO] Daily summary email already sent today, skipping at {now.strftime('%Y-%m-%d %H:%M:%S')}")
                
            except Exception as e:
                print(f"[ERROR] Exception in summary email scheduler: {e}")
                traceback.print_exc()
            # Schedule next check in 5 minutes
            summary_timer = threading.Timer(300, check_and_send_summary)
            summary_timer.daemon = True
            summary_timer.start()

        schedule_midnight_refresh()
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
        
        # Check if WhatsApp is enabled for status message
        from config import load_config
        config = load_config()
        if config.get('whatsapp_enabled', True):
            self.scan_status_var.set("Sending test email and WhatsApp focus...")
        else:
            self.scan_status_var.set("Sending test email (WhatsApp disabled)...")
            
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
        # Check if WhatsApp is enabled in config
        from config import load_config
        config = load_config()
        if config.get('whatsapp_enabled', True):  # Default to True for backward compatibility
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
        else:
            print("[WhatsApp] WhatsApp testing disabled in config - skipping WhatsApp test")
            whatsapp_focus_success = True  # Mark as success so email-only mode works

        # SMS test
        sms_success = False
        try:
            from sms_alert import sms_alert
            sms_success = sms_alert.test_sms()
            if sms_success:
                print("[SMS] Test SMS sent successfully")
            else:
                print("[SMS] SMS test failed or disabled")
        except Exception as e:
            print(f"[SMS] Error testing SMS: {e}")

        # Status update
        if config.get('whatsapp_enabled', True):
            if email_success and whatsapp_focus_success and sms_success:
                self.scan_status_var.set("Test email, WhatsApp, and SMS all succeeded.")
            elif email_success and whatsapp_focus_success:
                self.scan_status_var.set("Test email sent to russfray74@gmail.com and WhatsApp focus/type succeeded.")
            elif email_success:
                self.scan_status_var.set("Test email sent to russfray74@gmail.com, but WhatsApp focus/type failed.")
            elif whatsapp_focus_success:
                self.scan_status_var.set("WhatsApp focus/type succeeded, but test email failed.")
        else:
            if email_success and sms_success:
                self.scan_status_var.set("Test email and SMS sent successfully (WhatsApp disabled).")
            elif email_success:
                self.scan_status_var.set("Test email sent to russfray74@gmail.com (WhatsApp disabled, SMS failed/disabled).")
            elif sms_success:
                self.scan_status_var.set("Test SMS sent successfully (WhatsApp disabled, email failed).")
            else:
                self.scan_status_var.set("Test email and SMS failed (WhatsApp disabled in config).")
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
                self.cal_frame = CalendarView(self.right_panel, self.current_date.year, self.current_date.month)
                self.cal_frame.pack(fill="both", expand=True, side="top")
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
                self.cal_frame = CalendarView(self.right_panel, self.current_date.year, self.current_date.month)
                self.cal_frame.pack(fill="both", expand=True, side="top")
                self.update()  # Force a complete update of the window
                
        except Exception as e:
            print(f"[GUI] Error ensuring calendar visibility: {e}")
            # Force recreation as last resort
            try:
                # Make sure we're using the current month when recreating
                self.current_date = pydatetime.datetime(self.current_date.year, self.current_date.month, 1)
                
                self.cal_frame = CalendarView(self.right_panel, self.current_date.year, self.current_date.month)
                self.cal_frame.pack(fill="both", expand=True)
                self.update()  # Force a complete update of the window
            except Exception as e2:
                print(f"[GUI] Failed to recreate calendar: {e2}")

    def clear_all_shifts(self):
        from database import clear_all_shifts
        clear_all_shifts()
        self.scan_status_var.set("Shifts cleared.")
        self.refresh_calendar(force=True)
        
    def manual_scan(self, silent=False, restart_countdown_when_done=False):
        """
        Performs a full automation scan for open shifts in Teams (4 months).
        Runs the heavy work in a background thread to keep the GUI responsive.
        If silent=True, suppresses any popups/dialogs (for auto-scan).
        If restart_countdown_when_done=True, the next interval countdown starts
        only after this scan fully finishes (not when it begins).
        """
        if getattr(self, '_scan_thread_running', False):
            self.scan_status_var.set("Scan already in progress...")
            return

        import threading
        self._scan_thread_running = True
        # Always resume the interval countdown after any scan finishes when
        # auto-scanning is enabled. Explicit flag still forces resume.
        self._restart_countdown_when_done = bool(restart_countdown_when_done) or bool(self.scanning_on)
        # Pause countdown while a scan is running so the interval does not
        # overlap with an in-progress scan.
        self.timer_running = False
        self.countdown_var.set("Scanning... countdown paused")
        t = threading.Thread(target=self._manual_scan_worker, args=(silent,), daemon=True)
        t.start()

    def _manual_scan_worker(self, silent=False):
        """
        Background-thread worker for manual_scan. All GUI updates go via self.after().
        """
        try:
            self._run_manual_scan(silent=silent)
        finally:
            self._scan_thread_running = False
            restart = getattr(self, '_restart_countdown_when_done', False)
            self._restart_countdown_when_done = False
            if restart and self.scanning_on:
                self.after(0, self._start_countdown_after_scan)
            elif self.scanning_on:
                # Safety net if flags got out of sync.
                self.after(0, self._start_countdown_after_scan)
            else:
                self.after(0, lambda: self.countdown_var.set("Countdown: paused"))

    def _start_countdown_after_scan(self):
        """Begin the next scan-interval countdown after a scan has finished."""
        if not self.scanning_on:
            return
        try:
            self.remaining = int(self.interval_var.get())
        except Exception:
            self.remaining = int(self.config.get("scan_interval_seconds", 120) or 120)
        self.timer_running = True
        self.update_countdown_label()
        self.after(1000, self.start_countdown)

    def _run_manual_scan(self, silent=False):
        """
        The actual scan implementation, called from a background thread.
        """
        # Hard abort if a midnight reset is in progress — scanning during a reload
        # is what caused false October alerts at 00:04 (Teams showing stale data).
        if getattr(self, '_midnight_reset_in_progress', False):
            print("[Scan] Midnight reset in progress — aborting scan to avoid false detections.")
            return

        from automation import scan_four_months_with_automation
        from ocr_processing import extract_shifts_from_image
        from database import get_availability_for_date, is_shift_alerted
        # get_shift_count import removed (function does not exist)
        import os
        import glob
        import shutil
        import datetime

        # --- Clear screenshots directory at the very start of scan ---
        screenshot_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'screenshots')
        if os.path.exists(screenshot_dir):
            files = glob.glob(os.path.join(screenshot_dir, '*'))
            for f in files:
                try:
                    os.remove(f)
                except Exception as e:
                    print(f"[Cleanup] Could not delete {f}: {e}")

        def set_status(msg):
            self.after(0, lambda m=msg: self.scan_status_var.set(m))

        total_new_shifts = 0
        matched_dates = []  # List of (date_str, shift_type)
        matched_dates_set = set()

        original_year = self.current_date.year
        original_month = self.current_date.month
        self._first_scan_year = None
        self._first_scan_month = None

        # Track all found shifts per (year, month)
        found_open_shifts_by_month = {}
        found_booked_shifts_by_month = {}

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
            open_dates_this_month = set()     # Track open shifts found in current scan
            booked_dates_this_month = set()   # Track booked shifts found in current scan
            for date_str, shift_info in all_shifts_map.items():
                shift_type = shift_info['type'] # 'open' or 'booked'
                shift_count = shift_info.get('count', 1)  # Get the count from OCR detection
                # coords = shift_info['coords'] # Available if needed

                # Validate date format before processing
                try:
                    import datetime
                    datetime.datetime.strptime(date_str, "%Y-%m-%d")
                except ValueError:
                    print(f"[GUI] Skipping invalid date format: {date_str}")
                    continue

                processed_dates_this_month.add(date_str)

                if shift_type == 'open':
                    open_dates_this_month.add(date_str)
                elif shift_type == 'booked':
                    booked_dates_this_month.add(date_str)

            # Update status message
            scan_time = pydatetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            status_msg = f"Scanned: {calendar.month_name[month]} {year} at {scan_time} : "
            if new_open_shifts_this_month > 0:
                status_msg += f"{new_open_shifts_this_month} new open shifts. "
            if new_booked_shifts_this_month > 0:
                status_msg += f"{new_booked_shifts_this_month} new booked shifts. "
            if new_open_shifts_this_month == 0 and new_booked_shifts_this_month == 0:
                status_msg += "No new shifts found."
            self.after(0, lambda s=status_msg.strip(): self.scan_status_var.set(s))
            
            # Track open shifts for this month for later cleanup (this might need adjustment)
            # Store both open and booked shifts found during current scan for cleanup
            found_open_shifts_by_month[(year, month)] = open_dates_this_month
            found_booked_shifts_by_month[(year, month)] = booked_dates_this_month

            # Use the top-level import for pydatetime (do not re-import locally)
            _status = status_msg.strip()
            def _update_calendar_ui(y=year, m=month, s=_status):
                self.current_date = pydatetime.datetime(y, m, 1)
                try:
                    if hasattr(self, 'cal_frame') and isinstance(self.cal_frame, CalendarView):
                        self.cal_frame.destroy()
                    self.cal_frame = CalendarView(self.right_panel, y, m)
                    self.cal_frame.pack(fill="both", expand=True, side="top")
                    self.update()
                except Exception as e:
                    print(f"[PATCH] Error recreating calendar: {e}")
                    self.refresh_calendar(force=True)
                self.ensure_calendar_visible()
                self.scan_status_var.set(s)
                self.update_idletasks()
            self.after(0, _update_calendar_ui)

        def send_availability_alert(matched_dates):
            if not matched_dates:
                return
            import json
            import smtplib
            from email.mime.text import MIMEText
            from email.utils import formataddr
            import os
            try:
                smtp_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'smtp_settings.json')
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
                # Mark all emailed shifts as alerted IN A SINGLE ATOMIC TRANSACTION

                # This prevents race conditions where a new scan starts while flags are being set

                from database import mark_multiple_shifts_alerted

                mark_multiple_shifts_alerted(matched_dates)
                self.scan_status_var.set(f"Alert email sent for {len(matched_dates)} new matched shifts.")
            except Exception as e:
                self.scan_status_var.set(f"Alert email failed: {e}")
                import traceback
                traceback.print_exc()
            # --- WhatsApp automation: send message after emailing ---
            # Check if WhatsApp is enabled in config
            from config import load_config
            config = load_config()
            if config.get('whatsapp_enabled', True):  # Default to True for backward compatibility
                try:
                    from automation import send_whatsapp_message
                    # You can change the group name here if needed
                    group_name = "Manor Shift Alerts"
                    send_whatsapp_message(group_name, matched_dates)
                except Exception as e:
                    print(f"[WhatsApp] Error sending WhatsApp message: {e}")
            else:
                print("[WhatsApp] WhatsApp messaging disabled in config - skipping WhatsApp alert")
            
            # --- SMS automation: send text message after emailing ---
            try:
                from sms_alert import sms_alert
                sms_success = sms_alert.send_shift_alert_sms(matched_dates)
                if sms_success:
                    print(f"[SMS] Text message sent for {len(matched_dates)} new shifts")
                else:
                    print("[SMS] Text message failed or disabled")
            except Exception as e:
                print(f"[SMS] Error sending SMS: {e}")

        try:
            set_status("Running full Teams automation scan (4 months)...")
            import datetime as pydatetime
            now = pydatetime.datetime.now()
            self._first_scan_year = None
            self._first_scan_month = None
            self._scanning = True

            scan_four_months_with_automation(ocr_and_store, now.year, now.month)

            self._scanning = False

            # Reconcile only months whose OCR callback completed. This distinguishes a
            # healthy empty scan from a capture/navigation failure, so failed scans
            # cannot remove existing shifts.
            from database import reconcile_month_observations
            import datetime as pydatetime
            
            # Generate list of all months that were scanned (4 months starting from current)
            scan_start_date = pydatetime.datetime(now.year, now.month, 1)
            scanned_months = []
            for i in range(4):
                scan_year = scan_start_date.year
                scan_month = scan_start_date.month + i
                # Handle year rollover
                while scan_month > 12:
                    scan_month -= 12
                    scan_year += 1
                scanned_months.append((scan_year, scan_month))
            
            # Apply each complete month as one state transition.
            for year, month in scanned_months:
                if (year, month) not in found_open_shifts_by_month or (year, month) not in found_booked_shifts_by_month:
                    print(f"[Scan] Skipping reconciliation for {calendar.month_name[month]} {year}: no completed OCR result.")
                    continue
                open_shifts_found = found_open_shifts_by_month.get((year, month), set())
                booked_shifts_found = found_booked_shifts_by_month.get((year, month), set())
                reconciliation = reconcile_month_observations(year, month, open_shifts_found, booked_shifts_found)
                new_open_dates = reconciliation.get('new_open', [])
                total_new_shifts += len(new_open_dates) + len(reconciliation.get('new_bookings', []))
                for date_str in new_open_dates:
                    availability = get_availability_for_date(date_str)
                    if availability and availability.get('is_available') and not is_shift_alerted(date_str, 'open') and date_str not in matched_dates_set:
                        matched_dates.append(date_str)
                        matched_dates_set.add(date_str)
                for date_str in reconciliation.get('new_bookings', []):
                    import threading
                    from email_alert import send_shift_confirmation_email
                    threading.Thread(target=send_shift_confirmation_email, args=(date_str,), daemon=True).start()

            current_datetime = pydatetime.datetime.now()

            def _final_ui_update(md=list(matched_dates), ns=total_new_shifts, cd=current_datetime):
                self.current_date = pydatetime.datetime(cd.year, cd.month, 1)
                self.refresh_calendar(force=True)
                self.ensure_calendar_visible()
                self.update()
                self.scan_status_var.set("")
                scan_time = pydatetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                if md:
                    summary = f"New matched shifts found: {len(md)}\n" + ", ".join(md)
                    self.scan_status_var.set(summary)
                    print(f"[ALERT] Attempting to send availability alert for {len(md)} shifts: {md}")
                    import threading
                    threading.Thread(target=send_availability_alert, args=(md,), daemon=True).start()
                else:
                    self.scan_status_var.set(f"Last scan run: {scan_time} : {ns} new shifts found. No new matched shifts.")
                self._log_scan(new_shifts=ns, alert_count=len(md), scan_status=self.scan_status_var.get())
            self.after(0, _final_ui_update)

        except Exception as e:
            self._scanning = False
            def _error_ui(err=str(e)):
                self.scan_status_var.set(f"Scan error: {err}")
                self._log_error(err)
                self.refresh_calendar(force=True)
                self.ensure_calendar_visible()
            self.after(0, _error_ui)
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
            self.toggle_btn.config(text="Stop")
            # Removed popup box on start
        else:
            # Stop scanning
            self.scanning_on = False
            self.timer_running = False
            self.remaining = int(self.interval_var.get())
            self.update_countdown_label()
            self.toggle_btn.config(text="Start")
            # Removed popup box on stop

    def start_countdown(self):
        """
        Countdown timer for automated scanning.
        The next countdown begins only after an auto-scan finishes.
        """
        if not self.timer_running or not self.scanning_on:
            return
        if getattr(self, '_scan_thread_running', False):
            # Do not tick while a scan is in progress.
            self.countdown_var.set("Scanning... countdown paused")
            return

        self.update_countdown_label()

        # Periodically check calendar visibility (every 30 seconds)
        if self.remaining % 30 == 0:
            self.ensure_calendar_visible()

        if self.remaining > 0:
            self.remaining -= 1
            self.after(1000, self.start_countdown)
        else:
            # When countdown reaches zero, perform a scan. Countdown restarts
            # only after that scan completes (_manual_scan_worker callback).
            print(f"[Scheduler] Auto-scan triggered")
            self.timer_running = False
            try:
                self.auto_scan()
            except Exception as e:
                print(f"[Scheduler] Auto-scan error: {e}")
                import traceback
                traceback.print_exc()
                if self.scanning_on:
                    self.after(1000, self._start_countdown_after_scan)

    def auto_scan(self):
        """
        Performs an automated scan without UI dialogs (calls manual_scan with silent=True).
        Interval countdown resumes only when the scan thread finishes.
        """
        self.countdown_var.set("Auto-scanning...")
        try:
            self.master.update_idletasks()
        except Exception:
            pass
        try:
            self.manual_scan(silent=True, restart_countdown_when_done=True)
        except Exception as e:
            self._log_error(f"Auto-scan error: {e}")
            if self.scanning_on:
                self.after(0, self._start_countdown_after_scan)

    def subtract_ten_seconds(self):
        """Knock 10 seconds off the countdown timer (only when >= 10s remain)."""
        if getattr(self, '_scan_thread_running', False):
            return
        if self.remaining >= 10:
            self.remaining -= 10
            self.update_countdown_label()

    def update_countdown_label(self):
        if getattr(self, '_scan_thread_running', False):
            self.countdown_var.set("Scanning... countdown paused")
        else:
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
        
    def move_to_current_month(self):
        self.current_date = pydatetime.datetime.today().replace(day=1)
        # Force refresh to show current month
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
                self.cal_frame = CalendarView(self.right_panel, self.current_date.year, self.current_date.month)
                self.cal_frame.pack(fill="both", expand=True, side="top")
                self.update()  # Force a complete update of the window
                return            # If cal_frame is missing or not a CalendarView, create it
            self.cal_frame = CalendarView(self.right_panel, self.current_date.year, self.current_date.month)
            self.cal_frame.pack(fill="both", expand=True, side="top")
            self.update()  # Force a complete update of the window
        except Exception as e:
            print(f"[GUI] Error refreshing calendar: {e}")
            import traceback
            traceback.print_exc()
            # Try to restore a basic calendar on error
            try:
                self.cal_frame = CalendarView(self.right_panel, self.current_date.year, self.current_date.month)
                self.cal_frame.pack(fill="both", expand=True)
            except Exception as e2:
                print(f"[GUI] Failed to restore calendar: {e2}")


def _work_area():
    """Return Windows work area (screen minus taskbar) as left, top, right, bottom."""
    import ctypes
    from ctypes import wintypes

    class RECT(ctypes.Structure):
        _fields_ = [
            ("left", ctypes.c_long),
            ("top", ctypes.c_long),
            ("right", ctypes.c_long),
            ("bottom", ctypes.c_long),
        ]

    rect = RECT()
    # SPI_GETWORKAREA = 0x0030
    if ctypes.windll.user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(rect), 0):
        return rect.left, rect.top, rect.right, rect.bottom
    import pyautogui
    sw, sh = pyautogui.size()
    return 0, 0, sw, sh


def _docked_rect_under_teams():
    """
    Return (x, y, w, h) for a full-width strip under the Teams scan window,
    filling the remaining Windows work area so the month calendar fits.
    """
    try:
        from automation import TEAMS_SCAN_HEIGHT_RATIO, get_teams_window
        teams_ratio = float(TEAMS_SCAN_HEIGHT_RATIO)
    except Exception:
        teams_ratio = 0.65
        get_teams_window = None

    left, top, right, bottom = _work_area()
    work_w = max(800, right - left)

    teams_bottom = None
    try:
        if get_teams_window:
            tw = get_teams_window()
            if tw is not None:
                tr = tw.rectangle()
                teams_bottom = int(tr.bottom)
    except Exception:
        teams_bottom = None

    import pyautogui
    screen_w, screen_h = pyautogui.size()
    if teams_bottom is None:
        teams_bottom = max(360, int(screen_h * teams_ratio))

    # Sit just under Teams; never climb above the work area top.
    y = max(top, min(teams_bottom + 2, bottom - 180))
    height = max(180, bottom - y)
    return left, y, work_w, height


def _docked_geometry_under_teams(root=None):
    x, y, w, h = _docked_rect_under_teams()
    return f"{w}x{h}+{x}+{y}"


def _force_dock_window(root):
    """Apply dock geometry via Tk and win32 for pixel-accurate placement."""
    x, y, w, h = _docked_rect_under_teams()
    geom = f"{w}x{h}+{x}+{y}"
    try:
        root.minsize(800, 180)
        root.maxsize(root.winfo_screenwidth(), root.winfo_screenheight())
    except Exception:
        pass
    root.geometry(geom)
    try:
        root.update_idletasks()
        hwnd = int(root.winfo_id())
        # Climb to the top-level owner HWND.
        import ctypes
        user32 = ctypes.windll.user32
        GA_ROOT = 2
        root_hwnd = user32.GetAncestor(hwnd, GA_ROOT) or hwnd
        # SWP_SHOWWINDOW | SWP_NOZORDER
        user32.SetWindowPos(root_hwnd, 0, int(x), int(y), int(w), int(h), 0x0040 | 0x0004)
    except Exception:
        pass
    return geom


def launch_gui(root, config):
    root.title("Teams Shift Monitor")
    # Always dock full-width under the Teams scan window for a neat stacked layout.
    import sqlite3
    import os as _os
    DB_PATH = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), 'shifts.db')
    TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS window_geometry (
        id INTEGER PRIMARY KEY,
        geometry TEXT
    )
    """

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

    def apply_docked_geometry(refresh_cal=False):
        use_geom = _force_dock_window(root)
        try:
            root.update_idletasks()
            if hasattr(app, "scan_status_label"):
                app.scan_status_label.configure(wraplength=max(180, root.winfo_width() - 980))
            if refresh_cal and hasattr(app, "refresh_calendar"):
                app.refresh_calendar(force=True)
        except Exception:
            pass
        save_geometry(use_geom)
        return use_geom

    # Apply before widgets so first paint is already docked.
    try:
        root.configure(bg=UI["bg"])
    except Exception:
        pass
    _force_dock_window(root)

    def save_window_geometry():
        geom = root.geometry()
        save_geometry(geom)
        root.destroy()

    app = MainApp(root)
    root.protocol("WM_DELETE_WINDOW", save_window_geometry)

    # Re-assert dock after the widget tree is realized so the full remaining
    # work-area height is used for the month grid (no clipped final weeks).
    root.after(50, lambda: apply_docked_geometry(False))
    root.after(250, lambda: apply_docked_geometry(True))
    root.after(900, lambda: apply_docked_geometry(True))

    import os

    def force_quit():
        print("[INFO] Application is shutting down forcefully.")
        os._exit(0)


