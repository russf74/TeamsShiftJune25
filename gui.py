import tkinter as tk
from tkinter import ttk, messagebox
import calendar
from database import get_shifts_for_month
from datetime import timedelta
from database import get_shifts_for_month, get_availability_for_month, set_availability_for_date
import datetime as pydatetime

# Professional palette for the docked multi-month monitor under Teams.
UI = {
    "bg": "#E8EDF5",
    "surface": "#FFFFFF",
    "surface2": "#F7F9FC",
    "border": "#D0D7E2",
    "border_strong": "#A8B3C4",
    "text": "#111827",
    "muted": "#64748B",
    "accent": "#0B5CAB",
    "accent_soft": "#DCEBFA",
    "accent_hover": "#094A8A",
    "danger": "#B10E1E",
    "danger_hover": "#8F0B18",
    "success": "#0F7B3A",
    "past": "#E2E8F0",
    "past_text": "#475569",
    "booked": "#3B82F6",
    "booked_soft": "#DBEAFE",
    "booked_text": "#1E3A8A",
    "open_avail": "#16A34A",
    "open_avail_soft": "#DCFCE7",
    "open_avail_text": "#14532D",
    "open_busy": "#F59E0B",
    "open_busy_soft": "#FEF3C7",
    "open_busy_text": "#92400E",
    "empty": "#FFFFFF",
    "empty_alt": "#F8FAFC",
    "header": "#F1F5F9",
    "today": "#0B5CAB",
    "shadow": "#C5D0DE",
    "btn": "#EEF2F7",
    "btn_text": "#0F172A",
    "btn_border": "#C5CEDA",
}


def _ui_font(size=9, weight="normal"):
    family = "Segoe UI"
    if weight == "bold":
        return (family, size, "bold")
    return (family, size)


def _estimate_text_width(text, font):
    """Approximate canvas text width so month titles do not collide with counts."""
    size = 9
    if isinstance(font, (tuple, list)) and len(font) >= 2:
        try:
            size = int(font[1])
        except (TypeError, ValueError):
            size = 9
    return max(0, int(len(text or "") * size * 0.62))


def _add_months(year, month, delta):
    idx = year * 12 + (month - 1) + delta
    return idx // 12, idx % 12 + 1


class PillButton(tk.Frame):
    """Compact coloured button that looks intentional, not default-white."""

    def __init__(
        self,
        master,
        text,
        command=None,
        bg=None,
        fg=None,
        hover=None,
        width=None,
        padx=10,
        pady=3,
        **kwargs,
    ):
        super().__init__(master, bg=master.cget("bg") if hasattr(master, "cget") else UI["surface"], **kwargs)
        self._command = command
        self._bg = bg or UI["btn"]
        self._fg = fg or UI["btn_text"]
        self._hover = hover or UI["accent_soft"]
        self._enabled = True
        self.lbl = tk.Label(
            self,
            text=text,
            bg=self._bg,
            fg=self._fg,
            font=_ui_font(8, "bold"),
            padx=padx,
            pady=pady,
            cursor="hand2",
            highlightthickness=1,
            highlightbackground=UI["btn_border"],
            highlightcolor=UI["accent"],
        )
        if width is not None:
            self.lbl.configure(width=width)
        self.lbl.pack()
        for w in (self, self.lbl):
            w.bind("<Enter>", self._on_enter)
            w.bind("<Leave>", self._on_leave)
            w.bind("<Button-1>", self._on_click)

    def config(self, **kwargs):
        # ttk.Button-compatible subset
        if "text" in kwargs:
            self.lbl.configure(text=kwargs.pop("text"))
        if "state" in kwargs:
            st = kwargs.pop("state")
            self._enabled = st not in ("disabled", tk.DISABLED)
            self.lbl.configure(cursor="hand2" if self._enabled else "arrow")
            self.lbl.configure(fg=self._fg if self._enabled else UI["muted"])
        if kwargs:
            super().config(**kwargs)

    configure = config

    def _on_enter(self, _e=None):
        if self._enabled:
            self.lbl.configure(bg=self._hover)

    def _on_leave(self, _e=None):
        self.lbl.configure(bg=self._bg)

    def _on_click(self, _e=None):
        if self._enabled and callable(self._command):
            self._command()


class MonthCard:
    """Draw one month card. Board supplies near-square cell size."""

    def __init__(self, canvas, year, month, x, y, w, h, cell_w, cell_h, compact=None):
        self.canvas = canvas
        self.year = year
        self.month = month
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.cell_w = cell_w
        self.cell_h = cell_h
        # Board may force compact chrome so title/grid metrics stay aligned.
        if compact is None:
            compact = min(cell_w, cell_h) < 20
        self.compact = bool(compact)
        self.hits = []
        self._load()

    def _load(self):
        shifts = get_shifts_for_month(self.year, self.month)
        availability = get_availability_for_month(self.year, self.month)
        self.shift_info = {
            s["date"]: {
                "type": s["shift_type"],
                "alerted": s.get("alerted", 0),
                "count": s.get("count", 1),
            }
            for s in shifts
        }
        self.available_dates = set(a["date"] for a in availability)
        self.month_days = calendar.Calendar().monthdayscalendar(self.year, self.month)
        self.today = pydatetime.date.today()

    def draw(self):
        c = self.canvas
        x, y, w, h = self.x, self.y, self.w, self.h
        cell_w, cell_h = self.cell_w, self.cell_h
        self.hits = []
        compact = self.compact

        # Card chrome (lighter shadow when many cards share the strip)
        if not compact:
            c.create_rectangle(x + 2, y + 3, x + w + 1, y + h + 1, fill=UI["shadow"], outline="")
        c.create_rectangle(x, y, x + w, y + h, fill=UI["surface"], outline=UI["border"], width=1)

        pad_x = 5 if compact else 8
        pad_y = 3 if compact else 6
        title_h = 14 if compact else 18
        dow_h = 11 if compact else 14
        title_font = _ui_font(8 if compact else 11, "bold")
        meta_font = _ui_font(6 if compact else 7, "bold")
        dow_font = _ui_font(6 if compact else 7, "bold")
        day_font = _ui_font(6 if compact else 8, "bold")

        # Title — abbreviate month name when cards are narrow
        month_label = calendar.month_name[self.month]
        if compact and w < 160:
            month_label = calendar.month_abbr[self.month]
        title_text = f"{month_label} {self.year}"
        n_open = sum(1 for v in self.shift_info.values() if v.get("type") == "open")
        n_booked = sum(1 for v in self.shift_info.values() if v.get("type") == "booked")
        bits = []
        if n_booked:
            bits.append(f"{n_booked}b" if compact else f"{n_booked} booked")
        if n_open:
            bits.append(f"{n_open}o" if compact else f"{n_open} open")
        meta_text = " · ".join(bits)
        title_px = _estimate_text_width(title_text, title_font)
        meta_px = _estimate_text_width(meta_text, meta_font) if meta_text else 0
        # Keep title and counts on one line only when both fit with a gap.
        stack_meta = bool(meta_text) and (title_px + meta_px + (pad_x * 2) + 16 > w)
        if stack_meta:
            title_h += 10 if compact else 12
        c.create_text(
            x + pad_x,
            y + pad_y + (5 if compact else 7),
            anchor="w",
            text=title_text,
            fill=UI["accent"],
            font=title_font,
        )
        if meta_text:
            if stack_meta:
                c.create_text(
                    x + pad_x,
                    y + pad_y + (15 if compact else 19),
                    anchor="w",
                    text=meta_text,
                    fill=UI["muted"],
                    font=meta_font,
                )
            else:
                c.create_text(
                    x + w - pad_x,
                    y + pad_y + (5 if compact else 7),
                    anchor="e",
                    text=meta_text,
                    fill=UI["muted"],
                    font=meta_font,
                )

        # Grid origin (centered horizontally inside card)
        weeks = max(5, len(self.month_days))
        grid_w = cell_w * 7
        ox = x + (w - grid_w) / 2.0
        oy = y + pad_y + title_h + dow_h

        for i, name in enumerate(["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]):
            cx = ox + cell_w * i + cell_w / 2
            c.create_text(
                cx,
                y + pad_y + title_h + dow_h / 2 - 1,
                text=name[0] if compact and cell_w < 16 else name,
                fill=UI["muted"],
                font=dow_font,
            )

        for r, week in enumerate(self.month_days):
            for col, day in enumerate(week):
                x1 = ox + cell_w * col + 0.5
                y1 = oy + cell_h * r + 0.5
                x2 = ox + cell_w * (col + 1) - 1.2
                y2 = oy + cell_h * (r + 1) - 1.2
                if day == 0:
                    c.create_rectangle(x1, y1, x2, y2, fill=UI["surface2"], outline=UI["border"])
                    continue

                date_str = f"{self.year}-{self.month:02d}-{day:02d}"
                shift = self.shift_info.get(date_str)
                is_available = date_str in self.available_dates
                stype = (shift or {}).get("type")
                if stype == "booked":
                    is_available = False
                cell_date = pydatetime.date(self.year, self.month, day)
                is_past = cell_date < self.today
                is_today = cell_date == self.today
                locked = bool(is_past or stype == "booked")

                badge = ""
                badge_bg = None
                if stype == "booked":
                    bg, fg = UI["booked"], "white"
                    badge, badge_bg = "BOOKED", UI["booked_text"]
                elif stype == "open":
                    count = int(shift.get("count", 1) or 1)
                    if is_available:
                        bg, fg = UI["open_avail"], "white"
                        badge = f"OPEN×{count}" if count > 1 else "OPEN"
                        badge_bg = UI["open_avail_text"]
                    else:
                        bg, fg = UI["open_busy"], "white"
                        badge = f"OPEN×{count}" if count > 1 else "OPEN"
                        badge_bg = UI["open_busy_text"]
                elif is_past:
                    bg, fg = UI["past"], UI["past_text"]
                else:
                    bg = UI["empty"] if ((r + col) % 2 == 0) else UI["empty_alt"]
                    fg = UI["text"]

                border = UI["today"] if is_today else UI["border"]
                bw = 2 if is_today and not compact else 1
                c.create_rectangle(x1, y1, x2, y2, fill=bg, outline=border, width=bw)

                day_pad = 1 if compact else 3
                c.create_text(
                    x1 + day_pad,
                    y1 + (1 if compact else 2),
                    anchor="nw",
                    text=str(day),
                    fill=fg,
                    font=day_font,
                )

                if is_available and not is_past and stype != "booked":
                    mark_r = 3.0 if compact else 4.5
                    cx = x2 - (5 if compact else 7)
                    cy = y1 + (6 if compact else 8)
                    c.create_oval(cx - mark_r, cy - mark_r, cx + mark_r, cy + mark_r, fill=UI["accent"], outline="")
                    if not compact:
                        c.create_text(cx, cy + 0.5, text="✓", fill="white", font=_ui_font(6, "bold"))

                if badge and (y2 - y1) >= 22:
                    chip_h = 10 if compact else 11
                    bx1 = x1 + 2
                    bx2 = x2 - 2
                    by2 = y2 - 2
                    by1 = by2 - chip_h
                    c.create_rectangle(bx1, by1, bx2, by2, fill=badge_bg or fg, outline="")
                    label = badge
                    if (bx2 - bx1) < 42 or compact:
                        label = "BK" if "BOOK" in badge else ("OP" if "OPEN" in badge else badge[:3])
                    c.create_text(
                        (bx1 + bx2) / 2,
                        (by1 + by2) / 2,
                        text=label,
                        fill="white",
                        font=_ui_font(5 if compact else 6, "bold"),
                    )
                elif badge and (y2 - y1) >= 14:
                    c.create_rectangle(x1 + 1, y2 - 3, x2 - 1, y2 - 1.2, fill=badge_bg or fg, outline="")

                self.hits.append((x1, y1, x2, y2, date_str, locked))


class MultiMonthBoard(tk.Frame):
    """
    Up to 6–7 month cards packed into the dock strip (1–2 rows) so less
    horizontal scrolling is needed. Cell size is derived from available space.
    """

    # Prefer denser boards; fall back if the dock strip is too small.
    TARGET_MONTHS = 7
    MIN_MONTHS = 2
    MIN_CELL = 11.0
    MAX_CELL = 36.0

    def __init__(self, master, year, month, *args, **kwargs):
        super().__init__(master, bg=UI["bg"], *args, **kwargs)
        self.year = year
        self.month = month
        self._cards = []
        self._hits = []
        self.visible_months = 3
        self._scan_highlight = None
        self.canvas = tk.Canvas(self, bg=UI["bg"], highlightthickness=0, bd=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda e: self.redraw())
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<Motion>", self._on_motion)
        self.after_idle(self.redraw)

    def build_widgets(self):
        self.redraw()

    def set_month(self, year, month):
        self.year = year
        self.month = month
        self.redraw()

    def set_scan_highlight(self, year=None, month=None):
        """Glow the month currently being scanned; clear when scan ends."""
        if year and month:
            self._scan_highlight = (int(year), int(month))
        else:
            self._scan_highlight = None
        self.redraw()

    def _on_motion(self, event):
        for x1, y1, x2, y2, _d, locked in self._hits:
            if x1 <= event.x <= x2 and y1 <= event.y <= y2:
                self.canvas.configure(cursor="arrow" if locked else "hand2")
                return
        self.canvas.configure(cursor="")

    def _on_click(self, event):
        for x1, y1, x2, y2, date_str, locked in self._hits:
            if x1 <= event.x <= x2 and y1 <= event.y <= y2:
                if locked:
                    return
                y = int(date_str[0:4])
                m = int(date_str[5:7])
                avail = {a["date"] for a in get_availability_for_month(y, m)}
                new_val = date_str not in avail
                try:
                    set_availability_for_date(date_str, new_val)
                except Exception as e:
                    print(f"[MultiMonthBoard] availability save failed {date_str}: {e}")
                    return
                self.redraw()
                return

    def _pick_layout(self, usable_w, usable_h):
        """
        Choose (n_months, cols, rows, cell, title_block, card_pad_bottom, hgap, vgap)
        packing as many months as will still keep readable day cells.
        """
        weeks = 6
        best = None  # higher n wins; then larger cell

        for n in range(self.TARGET_MONTHS, self.MIN_MONTHS - 1, -1):
            # Prefer two rows once we show 5+ months; still try one row first for wide strips.
            row_options = (1, 2) if n <= 4 else (2, 1)
            for rows in row_options:
                cols = (n + rows - 1) // rows
                for compact in (False, True):
                    if compact:
                        title_block = 3 + 14 + 11  # pad_y + title + dow
                        card_pad_bottom = 4
                        hgap, vgap = 8, 6
                        side_chrome = 10  # pad_x*2 inside card
                    else:
                        title_block = 6 + 18 + 14
                        card_pad_bottom = 6
                        hgap, vgap = 10, 8
                        side_chrome = 16

                    cell_h = (
                        (usable_h - (rows - 1) * vgap) / float(rows)
                        - title_block
                        - card_pad_bottom
                    ) / float(weeks)
                    cell_w = (
                        (usable_w - (cols - 1) * hgap) / float(cols) - side_chrome
                    ) / 7.0
                    cell = min(cell_h, cell_w, self.MAX_CELL)
                    if cell < self.MIN_CELL:
                        continue
                    # Prefer more months, then non-compact chrome, then larger cells.
                    score = (n, 0 if compact else 1, cell)
                    candidate = (
                        score,
                        n,
                        cols,
                        rows,
                        cell,
                        title_block,
                        card_pad_bottom,
                        hgap,
                        vgap,
                        side_chrome,
                        compact,
                    )
                    if best is None or candidate[0] > best[0]:
                        best = candidate
            if best is not None and best[1] == n:
                # Largest n that fits; stop searching smaller counts.
                break

        if best is None:
            # Absolute fallback: two tiny months.
            n, cols, rows = 2, 2, 1
            title_block, card_pad_bottom, hgap, vgap, side_chrome = 3 + 14 + 11, 4, 6, 6, 8
            compact = True
            cell = max(
                9.0,
                min(
                    (usable_h - title_block - card_pad_bottom) / float(weeks),
                    (usable_w - hgap - side_chrome * cols) / float(cols * 7),
                    self.MAX_CELL,
                ),
            )
            return n, cols, rows, cell, title_block, card_pad_bottom, hgap, vgap, side_chrome, compact

        (
            _score,
            n,
            cols,
            rows,
            cell,
            title_block,
            card_pad_bottom,
            hgap,
            vgap,
            side_chrome,
            compact,
        ) = best
        return n, cols, rows, cell, title_block, card_pad_bottom, hgap, vgap, side_chrome, compact

    def redraw(self):
        c = self.canvas
        w = max(int(c.winfo_width()), 20)
        h = max(int(c.winfo_height()), 20)
        c.delete("all")
        self._hits = []
        self._cards = []
        if w < 20 or h < 20:
            return

        c.create_rectangle(0, 0, w, h, fill=UI["bg"], outline="")

        top_pad = 3
        bottom_pad = 3
        side_pad = 8
        weeks = 6

        usable_h = max(40.0, h - top_pad - bottom_pad)
        usable_w = max(40.0, w - side_pad * 2)

        (
            n,
            cols,
            rows,
            cell,
            title_block,
            card_pad_bottom,
            hgap,
            vgap,
            side_chrome,
            compact,
        ) = self._pick_layout(usable_w, usable_h)
        self.visible_months = n
        cell_w = cell_h = float(cell)
        card_w = side_chrome + cell_w * 7
        card_h = title_block + card_pad_bottom + cell_h * weeks

        grid_w = cols * card_w + (cols - 1) * hgap
        grid_h = rows * card_h + (rows - 1) * vgap
        origin_x = max(side_pad, (w - grid_w) / 2.0)
        origin_y = top_pad + max(0.0, (usable_h - grid_h) / 2.0)

        tray_pad = 6
        c.create_rectangle(
            origin_x - tray_pad,
            origin_y - 3,
            origin_x + grid_w + tray_pad,
            origin_y + grid_h + 5,
            fill=UI["surface2"],
            outline=UI["border"],
            width=1,
        )

        for i in range(n):
            yy, mm = _add_months(self.year, self.month, i)
            r = i // cols
            items_before = r * cols
            items_in_row = min(cols, n - items_before)
            col_in_row = i - items_before
            # Center a short final row (e.g. 7 months as 4 + 3).
            row_width = items_in_row * card_w + max(0, items_in_row - 1) * hgap
            row_origin_x = origin_x + max(0.0, (grid_w - row_width) / 2.0)
            cx = row_origin_x + col_in_row * (card_w + hgap)
            cy = origin_y + r * (card_h + vgap)
            card = MonthCard(c, yy, mm, cx, cy, card_w, card_h, cell_w, cell_h, compact=compact)
            card.draw()
            if self._scan_highlight == (yy, mm):
                glow = ("#93C5FD", "#3B82F6", "#1D4ED8")
                for idx, color in enumerate(glow, start=1):
                    pad = 2 + idx * 2
                    c.create_rectangle(
                        cx - pad,
                        cy - pad,
                        cx + card_w + pad,
                        cy + card_h + pad,
                        outline=color,
                        width=2,
                    )
            self._cards.append(card)
            self._hits.extend(card.hits)


class CalendarView(MultiMonthBoard):
    """Alias so existing MainApp code keeps working."""

    def __init__(self, master, year, month, *args, **kwargs):
        super().__init__(master, year, month, *args, **kwargs)


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
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("App.TFrame", background=UI["bg"])
        style.configure("Tool.TEntry", fieldbackground=UI["surface"], foreground=UI["text"], padding=3)
        style.configure("Orange.TFrame", background=UI["open_busy_soft"])
        style.configure("Orange.TLabel", background=UI["open_busy_soft"])
        style.configure("Orange.TCheckbutton", background=UI["open_busy_soft"])
        style.configure("Green.TFrame", background=UI["open_avail_soft"])
        style.configure("Green.TLabel", background=UI["open_avail_soft"])
        style.configure("Green.TCheckbutton", background=UI["open_avail_soft"])
        style.configure("Blue.TFrame", background=UI["booked_soft"])
        style.configure("Blue.TLabel", background=UI["booked_soft"])
        style.configure("Blue.TCheckbutton", background=UI["booked_soft"])
        style.configure("Purple.TFrame", background="#E9D5FF")
        style.configure("Purple.TLabel", background="#E9D5FF")
        style.configure("Purple.TCheckbutton", background="#E9D5FF")

        self.configure(style="App.TFrame")
        self.pack(fill="both", expand=True)
        self.current_date = pydatetime.datetime.today().replace(day=1)
        self._display_anchor = self.current_date

        from config import load_config, save_config
        self.config = load_config()

        outer = tk.Frame(self, bg=UI["bg"])
        outer.pack(fill="both", expand=True)

        # ---- Toolbar card -------------------------------------------------
        self.toolbar = tk.Frame(outer, bg=UI["surface"], highlightbackground=UI["border"], highlightthickness=1)
        self.toolbar.pack(side="top", fill="x", padx=6, pady=(5, 3))
        self.left_panel = self.toolbar
        self.timer_frame = self.toolbar
        self.nav_frame = self.toolbar

        bar = tk.Frame(self.toolbar, bg=UI["surface"])
        bar.pack(side="top", fill="x", padx=8, pady=5)

        def _sep(parent=bar):
            tk.Frame(parent, bg=UI["border"], width=1, height=16).pack(side="left", padx=5, fill="y")

        brand = tk.Frame(bar, bg=UI["accent"])
        brand.pack(side="left", padx=(0, 8))
        tk.Label(
            brand,
            text="  SHIFTS  ",
            font=_ui_font(8, "bold"),
            bg=UI["accent"],
            fg="white",
            pady=3,
        ).pack()

        tk.Label(bar, text="Interval", font=_ui_font(8), bg=UI["surface"], fg=UI["muted"]).pack(side="left")
        self.interval_var = tk.StringVar(value=str(self.config.get("scan_interval_seconds", 600)))
        self.interval_entry = ttk.Entry(bar, textvariable=self.interval_var, width=4, style="Tool.TEntry", font=_ui_font(9))
        self.interval_entry.pack(side="left", padx=(3, 2))
        self.save_btn = PillButton(bar, "Store", command=self.save_interval, bg=UI["btn"], hover=UI["accent_soft"], padx=8, pady=2)
        self.save_btn.pack(side="left", padx=1)

        _sep()
        self.scanning_on = True
        self.toggle_btn = PillButton(
            bar, "Stop", command=self.toggle_scanning, bg=UI["accent"], fg="white", hover=UI["accent_hover"], padx=10, pady=2
        )
        self.toggle_btn.pack(side="left", padx=1)
        self.scan_btn = PillButton(bar, "Scan", command=self.manual_scan, bg="#0F766E", fg="white", hover="#0D9488", padx=10, pady=2)
        self.scan_btn.pack(side="left", padx=1)
        self.clear_btn = PillButton(bar, "Clear", command=self.clear_all_shifts, bg=UI["btn"], hover="#FDE68A", padx=8, pady=2)
        self.clear_btn.pack(side="left", padx=1)
        self.test_email_btn = PillButton(bar, "Test", command=self.send_test_msg, bg=UI["btn"], hover=UI["accent_soft"], padx=8, pady=2)
        self.test_email_btn.pack(side="left", padx=1)
        self.reset_btn = PillButton(
            bar,
            "Reset",
            command=lambda: self.trigger_shift_app_reset(run_scan_after_reset=True),
            bg="#7C3AED",
            fg="white",
            hover="#6D28D9",
            padx=10,
            pady=2,
        )
        self.reset_btn.pack(side="left", padx=1)

        _sep()
        self.prev_btn = PillButton(bar, "◀", command=self.prev_month, bg=UI["btn"], hover=UI["accent_soft"], padx=7, pady=2)
        self.prev_btn.pack(side="left", padx=1)
        self.current_btn = PillButton(bar, "Today", command=self.move_to_current_month, bg=UI["btn"], hover=UI["accent_soft"], padx=8, pady=2)
        self.current_btn.pack(side="left", padx=1)
        self.next_btn = PillButton(bar, "▶", command=self.next_month, bg=UI["btn"], hover=UI["accent_soft"], padx=7, pady=2)
        self.next_btn.pack(side="left", padx=1)

        _sep()
        self.countdown_var = tk.StringVar(value="")
        self.countdown_label = tk.Label(
            bar, textvariable=self.countdown_var, font=_ui_font(9, "bold"), bg=UI["surface"], fg=UI["accent"]
        )
        self.countdown_label.pack(side="left", padx=(0, 2))
        self.minus10_btn = PillButton(bar, "−10s", command=self.subtract_ten_seconds, bg=UI["btn"], hover=UI["accent_soft"], padx=7, pady=2)
        self.minus10_btn.pack(side="left", padx=1)

        self.quit_btn = PillButton(
            bar, "Quit", command=self.force_quit, bg=UI["danger"], fg="white", hover=UI["danger_hover"], padx=12, pady=2
        )
        self.quit_btn.pack(side="right", padx=(6, 0))

        legend = tk.Frame(bar, bg=UI["surface"])
        legend.pack(side="right", padx=(4, 4))
        for text, bg, fg in (
            ("Booked", UI["booked"], "white"),
            ("Open+Avail", UI["open_avail"], "white"),
            ("Open", UI["open_busy"], "white"),
            ("Past", UI["past"], UI["past_text"]),
        ):
            tk.Label(
                legend,
                text=f" {text} ",
                font=_ui_font(7, "bold"),
                bg=bg,
                fg=fg,
                pady=2,
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
        self._midnight_reset_in_progress = False
        self._scan_invalidated = False
        self._active_scan_token = None

        # ---- Multi-month board --------------------------------------------
        self.right_panel = tk.Frame(outer, bg=UI["bg"])
        self.right_panel.pack(side="top", fill="both", expand=True, padx=6, pady=(0, 6))
        self.header = tk.Frame(self.right_panel, bg=UI["bg"])
        self.header.pack_forget()

        try:
            self.cal_frame = CalendarView(self.right_panel, self.current_date.year, self.current_date.month)
            self.cal_frame.pack(fill="both", expand=True, side="top")
        except Exception as e:
            print(f"[GUI] Error initializing calendar: {e}")
            self.cal_frame = ttk.Label(self.right_panel, text="Calendar loading...")
            self.cal_frame.pack(fill="both", expand=True, side="top")
            self.after(500, self.ensure_calendar_visible)

        self.after(1000, self.start_countdown)
        self.toggle_btn.config(text="Stop" if self.scanning_on else "Start")
        # Quiet ready-check after dock geometry settles: refresh Teams into month view,
        # no emails / no video / no 5am hold — just arm the scanner.
        # If midnight was missed because the app was down, catch up once.
        self.after(2800, self._run_startup_ready_reset)

    def _run_startup_ready_reset(self):
        """Semi-midnight reset on first load: refresh Teams month view, stay ready to scan."""
        import datetime as _dt
        from email_db import check_midnight_reset_sent

        now = _dt.datetime.now()
        missed_midnight = now.hour < 5 and not check_midnight_reset_sent(now.date())
        try:
            if missed_midnight:
                print("[INFO] Missed midnight reset detected — catching up with confirmation email.")
                self.scan_status_var.set("Catching up missed midnight Teams refresh...")
            else:
                print("[INFO] Startup ready-check: refreshing Teams Shifts month view (no email).")
                self.scan_status_var.set("Startup ready-check: refreshing Teams Shifts...")
        except Exception:
            pass
        if missed_midnight:
            self.trigger_shift_app_reset(
                run_scan_after_reset=False,
                notify=True,
                record_video=False,
                resume_scanning="5am",
            )
            return
        self.trigger_shift_app_reset(
            run_scan_after_reset=False,
            notify=False,
            record_video=False,
            resume_scanning="now",
        )

    def trigger_shift_app_reset(
        self,
        run_scan_after_reset=False,
        notify=True,
        record_video=None,
        resume_scanning=None,
    ):
        """
        Kick off a Teams Shifts refresh on a background thread.

        resume_scanning:
          - "5am": midnight behaviour (hold until 5:00 AM)
          - "now": restore countdown/ready state immediately (startup)
          - "scan": run a silent scan after refresh (Reset button)
        """
        import threading

        if resume_scanning is None:
            resume_scanning = "scan" if run_scan_after_reset else "5am"
        if record_video is None:
            record_video = bool(notify)

        threading.Thread(
            target=self.refresh_teams_shifts,
            kwargs={
                "run_scan_after_reset": run_scan_after_reset,
                "notify": notify,
                "record_video": record_video,
                "resume_scanning": resume_scanning,
            },
            daemon=True,
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

    def refresh_teams_shifts(
        self,
        run_scan_after_reset=False,
        notify=True,
        record_video=True,
        resume_scanning="5am",
    ):
        import threading
        from datetime import datetime
        from automation import refresh_teams_shifts_view

        if resume_scanning is None:
            resume_scanning = "scan" if run_scan_after_reset else "5am"
        if run_scan_after_reset:
            resume_scanning = "scan"

        was_scanning = bool(getattr(self, "scanning_on", True))

        if record_video:
            # Start screen recording in background thread (midnight path).
            video_filename = "midnight_reset.mp4"  # Single filename that overwrites each day
            self.scan_status_var.set("Starting screen recording and refreshing Teams Shifts app...")
            recording_thread = threading.Thread(
                target=self._record_screen_video,
                args=(180, 5, video_filename),  # 3 minutes is enough for the revised reset path
                daemon=True,
            )
            recording_thread.start()
        else:
            self.scan_status_var.set("Refreshing Teams Shifts app (startup ready-check)...")

        self.scan_status_var.set("Pausing scanning and refreshing Teams Shifts app...")
        # Pause scanning and invalidate any in-flight scan so it cannot reconcile
        # stale/partial Teams UI captured while midnight refresh is rewriting the view.
        self._midnight_reset_in_progress = True
        self._scan_invalidated = True
        self._active_scan_token = None
        self.timer_running = False
        self.scanning_on = False
        self._scanning = False

        # Wait for an in-flight scan thread to exit before touching Teams.
        # Without this wait, midnight refresh races the scanner and produces
        # false open-shift tiles (e.g. phantom Nov 7 / Nov 13 after 00:00).
        import time as _time
        wait_deadline = _time.time() + 180
        while getattr(self, "_scan_thread_running", False) and _time.time() < wait_deadline:
            print("[Reset] Waiting for in-flight scan to abort before Teams refresh...")
            _time.sleep(0.5)
        if getattr(self, "_scan_thread_running", False):
            print("[Reset] WARNING: scan thread still running after wait; proceeding carefully.")

        clear_midnight_guard = True

        def _clear_midnight_guard():
            self._midnight_reset_in_progress = False
            self._scan_invalidated = False

        def _resume_ready(status_msg, force_on=False):
            def _ui():
                _clear_midnight_guard()
                self.timer_running = True
                self.scanning_on = True if (force_on or was_scanning) else False
                self._scanning = False
                try:
                    self.toggle_btn.config(text="Stop" if self.scanning_on else "Start")
                except Exception:
                    pass
                self.scan_status_var.set(status_msg)
                if self.scanning_on:
                    self.start_countdown()

            self.after(0, _ui)

        try:
            self.after(0, lambda: self.scan_status_var.set("[Reset] Opening Teams Shifts monthly view..."))
            refresh_ok = False
            try:
                refresh_ok = bool(refresh_teams_shifts_view(max_attempts=3))
            except TypeError:
                # Backward compatibility if an older automation module is imported.
                refresh_ok = bool(refresh_teams_shifts_view())
            if not refresh_ok:
                raise RuntimeError(
                    "Could not refresh Microsoft Teams Shifts into calendar Month view "
                    "after retries (see automation logs / screenshots/refresh_*.png)"
                )

            if notify:
                try:
                    from email_alert import send_email_alert
                    from email_db import check_midnight_reset_sent, mark_midnight_reset_sent

                    if check_midnight_reset_sent():
                        print("[Reset] Midnight confirmation email already sent today, skipping.")
                    else:
                        send_email_alert(
                            "Teams Shifts app reset successful",
                            "Teams Shifts app was successfully refreshed at midnight and locked to "
                            "calendar Month view. Scanning will resume at 5:00 AM.",
                            "russfray74@gmail.com",
                        )
                        mark_midnight_reset_sent()
                        print("[Reset] Success confirmation email sent")
                except Exception as e:
                    print(f"[Reset] Failed to send success email: {e}")

            if resume_scanning == "scan":
                clear_midnight_guard = False

                def _start_scan_ui():
                    _clear_midnight_guard()
                    self.scan_status_var.set("Teams Shifts app refreshed successfully. Starting test scan...")
                    self.timer_running = True
                    self.scanning_on = True
                    self._scanning = False
                    try:
                        self.toggle_btn.config(text="Stop")
                    except Exception:
                        pass
                    self.manual_scan(silent=True)

                self.after(0, _start_scan_ui)
                return

            if resume_scanning == "now":
                print("[Reset] Startup/semi-midnight reset complete — ready to scan.")
                clear_midnight_guard = False
                _resume_ready("Startup reset complete. Teams Shifts month view ready.", force_on=True)
                return

            # Default midnight behaviour: hold until 5:00 AM and keep the
            # midnight guard active so no scan can reconcile before resume.
            clear_midnight_guard = False
            now = datetime.now()
            next_5am = now.replace(hour=5, minute=0, second=0, microsecond=0)
            if now >= next_5am:
                from datetime import timedelta

                next_5am += timedelta(days=1)

            delay_seconds = int((next_5am - now).total_seconds())
            print(f"[Reset] Scheduling scan resumption at 5:00 AM (in {delay_seconds} seconds)")
            self.after(0, lambda: self.scan_status_var.set("Midnight reset complete. Resuming at 5:00 AM."))

            def resume_at_5am():
                print("[Reset] Resuming scanning at 5:00 AM")
                _clear_midnight_guard()
                self.timer_running = True
                self.scanning_on = True
                self._scanning = False
                try:
                    self.toggle_btn.config(text="Stop")
                except Exception:
                    pass
                self.start_countdown()

            self.after(delay_seconds * 1000, resume_at_5am)
        except Exception as e:
            import traceback

            traceback.print_exc()
            if notify:
                self.after(0, lambda: self.scan_status_var.set(f"Teams refresh failed: {e}. Emailing admin."))
                try:
                    from email_alert import send_email_alert

                    send_email_alert(
                        "Teams refresh failed",
                        (
                            "Teams Shifts app could not be refreshed into calendar Month view.\n\n"
                            f"Error: {e}\n\n"
                            "The refresh path now retries navigation, Ctrl+R reload, and Month-view "
                            "selection using multi-signal confirmation. Check the latest "
                            "screenshots/refresh_*.png capture and automation console output."
                        ),
                        "russfray74@gmail.com",
                    )
                except Exception as email_error:
                    print(f"[Reset] Failed to send failure email: {email_error}")
                clear_midnight_guard = True
            else:
                print(f"[Reset] Quiet refresh failed (no email): {e}")
                # Still unlock the monitor so normal scanning can continue.
                clear_midnight_guard = False
                _resume_ready(f"Startup reset failed: {e}. Scanner still armed.", force_on=True)
        finally:
            if clear_midnight_guard:
                _clear_midnight_guard()

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
            if not hasattr(self, "cal_frame") or self.cal_frame is None:
                print("[GUI] Calendar frame missing, recreating...")
                self.cal_frame = CalendarView(self.right_panel, self.current_date.year, self.current_date.month)
                self.cal_frame.pack(fill="both", expand=True, side="top")
                self.update_idletasks()
                return

            try:
                if not self.cal_frame.winfo_exists():
                    raise tk.TclError("calendar missing")
                # A not-yet-mapped board is normal during dock/startup. Redraw
                # in place instead of destroying it, which left a blank strip.
                self.cal_frame.set_month(self.current_date.year, self.current_date.month)
                self.update_idletasks()
            except tk.TclError:
                print("[GUI] Calendar frame was destroyed, recreating...")
                self.cal_frame = CalendarView(self.right_panel, self.current_date.year, self.current_date.month)
                self.cal_frame.pack(fill="both", expand=True, side="top")
                self.update_idletasks()
        except Exception as e:
            print(f"[GUI] Error ensuring calendar visibility: {e}")
            try:
                self.current_date = pydatetime.datetime(self.current_date.year, self.current_date.month, 1)
                self.cal_frame = CalendarView(self.right_panel, self.current_date.year, self.current_date.month)
                self.cal_frame.pack(fill="both", expand=True)
                self.update_idletasks()
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
        if getattr(self, '_midnight_reset_in_progress', False) or getattr(self, '_scan_invalidated', False):
            print("[Scan] Midnight reset/invalidation in progress — aborting scan to avoid false detections.")
            return

        from automation import scan_four_months_with_automation
        from ocr_processing import extract_shifts_from_image
        from database import get_availability_for_date, is_shift_alerted
        # get_shift_count import removed (function does not exist)
        import os
        import glob
        import shutil
        import datetime

        scan_token = object()
        self._active_scan_token = scan_token
        self._scan_invalidated = False

        def scan_aborted():
            return (
                getattr(self, "_midnight_reset_in_progress", False)
                or getattr(self, "_scan_invalidated", False)
                or getattr(self, "_active_scan_token", None) is not scan_token
            )

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
            if scan_aborted():
                print(f"[Scan] Aborting OCR for {calendar.month_name[month]} {year}: scan invalidated.")
                return
            if self._first_scan_year is None or self._first_scan_month is None:
                self._first_scan_year = year
                self._first_scan_month = month
            set_status(f"Analyzing {calendar.month_name[month]} {year} for shifts...") # Generalize status
            all_shifts_map = extract_shifts_from_image(image_path, year, month) # Renamed for clarity
            if scan_aborted():
                print(f"[Scan] Discarding OCR for {calendar.month_name[month]} {year}: scan invalidated mid-OCR.")
                return
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
            def _update_calendar_ui(s=_status, y=year, m=month):
                # Keep the board pinned to the current month. Mid-scan months
                # get a glow instead of becoming the visible starting card.
                today = pydatetime.datetime.today().replace(day=1)
                self.current_date = today
                self._display_anchor = today
                try:
                    if hasattr(self, "cal_frame") and hasattr(self.cal_frame, "set_scan_highlight"):
                        if (self.cal_frame.year, self.cal_frame.month) != (today.year, today.month):
                            self.cal_frame.set_month(today.year, today.month)
                        self.cal_frame.set_scan_highlight(y, m)
                    else:
                        self.refresh_calendar(force=True)
                except Exception as e:
                    print(f"[PATCH] Error refreshing calendar: {e}")
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

            if scan_aborted():
                print("[Scan] Aborting before automation: scan invalidated.")
                return

            scan_four_months_with_automation(
                ocr_and_store,
                now.year,
                now.month,
                should_abort=scan_aborted,
            )

            self._scanning = False

            if scan_aborted():
                print("[Scan] Discarding scan results after midnight reset/invalidation — no reconcile or alerts.")
                self.after(0, lambda: self.scan_status_var.set(
                    "Scan discarded: midnight reset invalidated in-flight results."
                ))
                return

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
                if scan_aborted():
                    print("[Scan] Aborting reconciliation: scan invalidated.")
                    matched_dates.clear()
                    matched_dates_set.clear()
                    return
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

            if scan_aborted():
                print("[Scan] Discarding alerts after post-reconcile invalidation.")
                return

            current_datetime = pydatetime.datetime.now()

            def _final_ui_update(md=list(matched_dates), ns=total_new_shifts, cd=current_datetime):
                today = pydatetime.datetime.today().replace(day=1)
                self.current_date = today
                self._display_anchor = today
                if hasattr(self, "cal_frame") and hasattr(self.cal_frame, "set_scan_highlight"):
                    self.cal_frame.set_scan_highlight(None, None)
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
                if hasattr(self, "cal_frame") and hasattr(self.cal_frame, "set_scan_highlight"):
                    self.cal_frame.set_scan_highlight(None, None)
                self.scan_status_var.set(f"Scan error: {err}")
                self._log_error(err)
                self.refresh_calendar(force=True)
                self.ensure_calendar_visible()
            self.after(0, _error_ui)
            import traceback
            traceback.print_exc()
        finally:
            if getattr(self, "_active_scan_token", None) is scan_token:
                self._active_scan_token = None

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
        self._display_anchor = self.current_date
        # Force refresh to show current month
        self.refresh_calendar(force=True)
        # Ensure calendar is visible after month change
        self.ensure_calendar_visible()
        
    def refresh_calendar(self, force=False):
        """Refresh the multi-month board in place when possible."""
        try:
            if hasattr(self, "cal_frame") and isinstance(self.cal_frame, CalendarView):
                highlight = getattr(self.cal_frame, "_scan_highlight", None)
                if hasattr(self.cal_frame, "set_month"):
                    self.cal_frame.set_month(self.current_date.year, self.current_date.month)
                    if highlight and hasattr(self.cal_frame, "set_scan_highlight"):
                        self.cal_frame.set_scan_highlight(*highlight)
                else:
                    self.cal_frame.destroy()
                    self.cal_frame = CalendarView(self.right_panel, self.current_date.year, self.current_date.month)
                    self.cal_frame.pack(fill="both", expand=True, side="top")
                try:
                    self.update_idletasks()
                except Exception:
                    pass
                return
            self.cal_frame = CalendarView(self.right_panel, self.current_date.year, self.current_date.month)
            self.cal_frame.pack(fill="both", expand=True, side="top")
        except Exception as e:
            print(f"[GUI] Error refreshing calendar: {e}")
            import traceback
            traceback.print_exc()
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


def _work_area_split():
    """
    Split the Windows work area into a full-width Teams band on top and a
    full-width monitor band underneath. The two bands meet with no gap.
    """
    try:
        from automation import TEAMS_SCAN_HEIGHT_RATIO

        teams_ratio = float(TEAMS_SCAN_HEIGHT_RATIO)
    except Exception:
        teams_ratio = 0.62

    left, top, right, bottom = _work_area()
    work_w = max(800, right - left)
    work_h = max(600, bottom - top)
    min_monitor_h = 260
    teams_h = max(360, int(work_h * teams_ratio))
    if teams_h > work_h - min_monitor_h:
        teams_h = max(360, work_h - min_monitor_h)
    monitor_h = max(min_monitor_h, work_h - teams_h)
    teams_h = work_h - monitor_h
    return {
        "left": left,
        "top": top,
        "right": right,
        "bottom": bottom,
        "width": work_w,
        "teams_h": teams_h,
        "monitor_y": top + teams_h,
        "monitor_h": monitor_h,
    }


def _docked_rect_under_teams():
    """Return (x, y, w, h) for the full-width monitor strip under Teams."""
    split = _work_area_split()
    return split["left"], split["monitor_y"], split["width"], split["monitor_h"]


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
            elif hasattr(app, "cal_frame") and hasattr(app.cal_frame, "redraw"):
                app.cal_frame.redraw()
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

    def _size_teams_async():
        try:
            from automation import configure_teams_window

            configure_teams_window()
        except Exception:
            pass
        try:
            root.after(0, lambda: apply_docked_geometry(True))
        except Exception:
            pass

    # Re-assert dock after the widget tree is realized so the full remaining
    # work-area height is used for the month grid (no clipped final weeks).
    root.after(50, lambda: apply_docked_geometry(False))
    root.after(250, lambda: apply_docked_geometry(True))
    import threading
    threading.Thread(target=_size_teams_async, daemon=True).start()

    import os

    def force_quit():
        print("[INFO] Application is shutting down forcefully.")
        os._exit(0)


