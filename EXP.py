import customtkinter as ctk
import tkinter as tk
from datetime import datetime, timedelta
import calendar
import re
import json
import os
import threading

# NOTE: matplotlib is intentionally NOT imported here. Importing it (and
# building a Figure/canvas) is one of the biggest contributors to a slow
# startup, so it's deferred until the user actually opens the Analytics tab
# (see setup_analytics_tab). This lets the main window appear immediately.

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Ensure DATA_FILE is saved in the exact folder where Run.py resides
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "runs.json")

# Shared color palette so plain-tk "fast" widgets match the CTk dark theme
COL_BG = "#1a1a1a"
COL_BG_ALT = "#242424"
COL_ROW_A = "#2b2b2b"
COL_ROW_B = "#242424"
COL_FIELD = "#2b2b2b"
COL_TEXT = "#ffffff"
COL_MUTED = "#9ca3af"
COL_ACCENT = "#1f6aa5"
COL_ACCENT_HOVER = "#144870"
COL_DANGER = "#b91c1c"
COL_DANGER_HOVER = "#991b1b"
COL_TODAY = "#1d4ed8"


# ==================== HIGH-PERFORMANCE CALENDAR POPUP ====================
# Built entirely from plain tkinter widgets (instead of CTk widgets) because
# this popup is created and destroyed every time the user clicks the date
# picker button. Plain tk.Toplevel/tk.Button construction is dramatically
# cheaper than CTkToplevel/CTkButton, so open/close feels instant.
class FastCalendarPopup(tk.Toplevel):
    def __init__(self, master, target_entry):
        super().__init__(master)
        self.target_entry = target_entry
        self.configure(bg=COL_BG)

        self.title("Select Date")
        self.transient(master)
        self.grab_set()

        self.today = datetime.now()
        self.current_year = self.today.year
        self.current_month = self.today.month

        # Navigation Header
        header_frame = tk.Frame(self, bg=COL_BG)
        header_frame.pack(fill="x", padx=10, pady=(10, 5))

        self.btn_prev = tk.Button(
            header_frame, text="<", width=3, bd=0, relief="flat",
            bg=COL_ROW_A, fg=COL_TEXT, activebackground="#374151", activeforeground=COL_TEXT,
            font=("Helvetica", 10, "bold"), cursor="hand2", command=self.prev_month
        )
        self.btn_prev.pack(side="left")

        self.lbl_month_year = tk.Label(header_frame, text="", bg=COL_BG, fg=COL_TEXT, font=("Helvetica", 13, "bold"))
        self.lbl_month_year.pack(side="left", expand=True)

        self.btn_next = tk.Button(
            header_frame, text=">", width=3, bd=0, relief="flat",
            bg=COL_ROW_A, fg=COL_TEXT, activebackground="#374151", activeforeground=COL_TEXT,
            font=("Helvetica", 10, "bold"), cursor="hand2", command=self.next_month
        )
        self.btn_next.pack(side="right")

        # Grid Container
        days_frame = tk.Frame(self, bg=COL_BG)
        days_frame.pack(fill="both", expand=True, padx=10, pady=5)

        days = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
        for col, day in enumerate(days):
            lbl = tk.Label(days_frame, text=day, bg=COL_BG, fg=COL_MUTED, font=("Helvetica", 11, "bold"), width=4)
            lbl.grid(row=0, column=col, padx=2, pady=2)

        # Pre-allocate Grid Matrix
        self.day_buttons = []
        for r in range(1, 7):
            row_btns = []
            for c in range(7):
                btn = tk.Button(
                    days_frame,
                    text="",
                    width=3,
                    height=1,
                    bd=0,
                    relief="flat",
                    font=("Helvetica", 10),
                    cursor="hand2"
                )
                btn.grid(row=r, column=c, padx=2, pady=2)
                row_btns.append(btn)
            self.day_buttons.append(row_btns)

        self.render_calendar()

        # Size the window to what it actually needs (character-based widget
        # widths render differently across fonts/systems, so a hardcoded
        # pixel guess was clipping Saturday/Sunday off the right edge).
        self.update_idletasks()
        req_w = self.winfo_reqwidth() + 16
        req_h = self.winfo_reqheight() + 16
        self.geometry(f"{req_w}x{req_h}")
        self.minsize(req_w, req_h)
        self.resizable(False, False)

    def prev_month(self):
        if self.current_month == 1:
            self.current_month = 12
            self.current_year -= 1
        else:
            self.current_month -= 1
        self.render_calendar()

    def next_month(self):
        if self.current_month == 12:
            self.current_month = 1
            self.current_year += 1
        else:
            self.current_month += 1
        self.render_calendar()

    def render_calendar(self):
        month_name = calendar.month_name[self.current_month]
        self.lbl_month_year.configure(text=f"{month_name} {self.current_year}")

        month_cal = calendar.monthcalendar(self.current_year, self.current_month)

        for r in range(6):
            for c in range(7):
                btn = self.day_buttons[r][c]
                if r < len(month_cal) and month_cal[r][c] != 0:
                    day_num = month_cal[r][c]
                    is_today = (
                        day_num == self.today.day and
                        self.current_month == self.today.month and
                        self.current_year == self.today.year
                    )
                    btn.config(
                        text=str(day_num),
                        state="normal",
                        bg=COL_TODAY if is_today else COL_ROW_A,
                        fg="white",
                        activebackground="#2563eb",
                        activeforeground="white",
                        command=lambda d=day_num: self.select_date(d)
                    )
                else:
                    btn.config(
                        text="",
                        state="disabled",
                        bg=COL_BG,
                        fg=COL_BG,
                        activebackground=COL_BG,
                        command=lambda: None
                    )

    def select_date(self, day):
        month_name = calendar.month_name[self.current_month]
        selected_str = f"{day} {month_name}"
        self.target_entry.delete(0, "end")
        self.target_entry.insert(0, selected_str)
        self.destroy()


# ==================== MAIN APPLICATION ====================
class RunningTrackerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("🏃 Running Tracker & Analytics")
        self.geometry("1200x820")
        self.minsize(1080, 650)
        self.resizable(True, True)

        self.rows_ui = []
        self.row_pool = []  # reusable plain-tk table row widgets (avoids destroy/recreate churn)
        self.plot_elements = []
        self.analytics_built = False  # analytics tab (and matplotlib) is built lazily, on first visit
        self.runs = self.load_runs()

        # Tab System Creation. The command callback lets us build the heavy
        # Analytics tab (and import matplotlib) only when the user actually
        # switches to it, instead of paying that cost on every startup.
        self.tabview = ctk.CTkTabview(self, command=self.on_tab_changed)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_history = self.tabview.add("Log & History")
        self.tab_analytics = self.tabview.add("Analytics Dashboard")

        self.setup_history_tab()
        self.tabview.set("Log & History")

    def on_tab_changed(self):
        if self.tabview.get() == "Analytics Dashboard" and not self.analytics_built:
            self.analytics_built = True
            self.setup_analytics_tab()

    def report_callback_exception(self, exc, val, tb):
        """Tkinter routes exceptions from deferred/idle callbacks (like
        matplotlib's canvas redraw) through here rather than letting them
        propagate normally. We use this to quietly handle a known
        matplotlib/FreeType bug ('FT_Render_Glyph ... raster overflow')
        instead of spamming a full traceback on every redraw."""
        if isinstance(val, RuntimeError) and "raster overflow" in str(val):
            if not getattr(self, "_ft_bug_warned", False):
                self._ft_bug_warned = True
                print(
                    "Note: chart text rendering hit a matplotlib/FreeType bug "
                    "(raster overflow) in this Python environment. The rest of "
                    "the app is unaffected. Try: pip install --upgrade matplotlib "
                    "(or pip install \"matplotlib==3.8.4\" as a known-working fallback)."
                )
            return
        super().report_callback_exception(exc, val, tb)

    # ==================== DATA PERSISTENCE & SORTING ====================
    def parse_run_date(self, date_str):
        now = datetime.now()
        clean_str = str(date_str).strip()

        # 1. Try formats that already include a year
        for fmt in ("%d %B %Y", "%d %b %Y", "%Y-%m-%d"):
            try:
                return datetime.strptime(clean_str, fmt)
            except ValueError:
                pass

        # 2. For formats without a year, append current year BEFORE parsing
        for fmt in ("%d %B", "%d %b"):
            try:
                return datetime.strptime(f"{clean_str} {now.year}", f"{fmt} %Y")
            except ValueError:
                pass

        return now

    def sort_runs(self):
        """Sorts the runs array chronologically by parsed date."""
        self.runs.sort(key=lambda r: self.parse_run_date(r.get("date", "")))

    def load_runs(self):
        loaded_data = []
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r") as f:
                    loaded_data = json.load(f)
            except Exception:
                pass

        if not loaded_data:
            loaded_data = [
                {"date": "17 July", "distance": "2km", "time": "17min 25sec", "incline": "1%", "calories": "130 kcal"},
                {"date": "18 July", "distance": "2.5km", "time": "19min 10sec", "incline": "2%", "calories": "175 kcal"},
                {"date": "19 July", "distance": "3km", "time": "22min 15sec", "incline": "1.5%", "calories": "210 kcal"},
                {"date": "20 July", "distance": "2km", "time": "14min 45sec", "incline": "3%", "calories": "150 kcal"}
            ]

        loaded_data.sort(key=lambda r: self.parse_run_date(r.get("date", "")))
        return loaded_data

    def save_runs(self):
        """Writes the run log to disk on a background thread so add/edit/delete
        never has to wait on file I/O before the UI updates."""
        data_snapshot = list(self.runs)

        def _write():
            try:
                with open(DATA_FILE, "w") as f:
                    json.dump(data_snapshot, f, indent=4)
            except Exception as e:
                print(f"Error saving runs: {e}")

        threading.Thread(target=_write, daemon=True).start()

    # ==================== HELPER PARSERS ====================
    def extract_numeric(self, text_val, default=0.0):
        digits = re.findall(r"[-+]?\d*\.\d+|\d+", str(text_val))
        return float(digits[0]) if digits else default

    def compute_run_speed_num(self, run):
        km_val = self.extract_numeric(run.get("distance", "0"))
        min_match = re.search(r"(\d+)\s*min", run.get("time", ""))
        sec_match = re.search(r"(\d+)\s*sec", run.get("time", ""))
        m = int(min_match.group(1)) if min_match else 0
        s = int(sec_match.group(1)) if sec_match else 0
        total_seconds = m * 60 + s

        if km_val > 0 and total_seconds > 0:
            hours = total_seconds / 3600.0
            return km_val / hours
        return 0.0

    def filter_runs_by_period(self, period):
        now = datetime.now()
        filtered = []

        if period == "All Time":
            filtered = list(self.runs)
        else:
            for run in self.runs:
                run_dt = self.parse_run_date(run.get("date", ""))
                if period == "This Week":
                    if run_dt.isocalendar()[:2] == now.isocalendar()[:2]:
                        filtered.append(run)
                elif period == "This Month":
                    if run_dt.year == now.year and run_dt.month == now.month:
                        filtered.append(run)

        filtered.sort(key=lambda r: self.parse_run_date(r.get("date", "")))
        return filtered

    # ==================== TAB 1: LOG & HISTORY ====================
    def setup_history_tab(self):
        container = ctk.CTkFrame(self.tab_history, fg_color="transparent")
        container.pack(fill="both", expand=True)

        # Left Panel: Data Entry
        self.input_frame = ctk.CTkFrame(container, width=260)
        self.input_frame.pack(side="left", fill="y", padx=(0, 15))
        self.input_frame.pack_propagate(False)

        lbl_title = ctk.CTkLabel(self.input_frame, text="Log a New Run", font=ctk.CTkFont(size=16, weight="bold"))
        lbl_title.pack(pady=(12, 8))

        # Date Entry with Fast Calendar Picker
        self.lbl_date = ctk.CTkLabel(self.input_frame, text="Date:")
        self.lbl_date.pack(anchor="w", padx=15)

        date_box_frame = ctk.CTkFrame(self.input_frame, fg_color="transparent")
        date_box_frame.pack(fill="x", padx=15, pady=(0, 8))

        self.entry_date = ctk.CTkEntry(date_box_frame)
        self.entry_date.pack(side="left", fill="x", expand=True)

        btn_cal_picker = ctk.CTkButton(
            date_box_frame,
            text="📅",
            width=36,
            command=lambda: FastCalendarPopup(self, self.entry_date)
        )
        btn_cal_picker.pack(side="left", padx=(6, 0))

        # Distance Entry + Unit
        self.lbl_dist = ctk.CTkLabel(self.input_frame, text="Distance:")
        self.lbl_dist.pack(anchor="w", padx=15)
        dist_box_frame = ctk.CTkFrame(self.input_frame, fg_color="transparent")
        dist_box_frame.pack(fill="x", padx=15, pady=(0, 8))
        self.entry_dist = ctk.CTkEntry(dist_box_frame, placeholder_text="e.g., 2.5")
        self.entry_dist.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(dist_box_frame, text="km", font=ctk.CTkFont(weight="bold"), text_color="#9ca3af").pack(side="left", padx=(6, 0))

        # Time Entry
        self.lbl_time = ctk.CTkLabel(self.input_frame, text="Time Taken:")
        self.lbl_time.pack(anchor="w", padx=15)
        time_box_frame = ctk.CTkFrame(self.input_frame, fg_color="transparent")
        time_box_frame.pack(fill="x", padx=15, pady=(0, 8))

        self.entry_time_min = ctk.CTkEntry(time_box_frame, placeholder_text="16", width=65)
        self.entry_time_min.pack(side="left")
        ctk.CTkLabel(time_box_frame, text="min", font=ctk.CTkFont(weight="bold"), text_color="#9ca3af").pack(side="left", padx=(4, 10))

        self.entry_time_sec = ctk.CTkEntry(time_box_frame, placeholder_text="15", width=65)
        self.entry_time_sec.pack(side="left")
        ctk.CTkLabel(time_box_frame, text="sec", font=ctk.CTkFont(weight="bold"), text_color="#9ca3af").pack(side="left", padx=(4, 0))

        # Incline Entry
        self.lbl_incline = ctk.CTkLabel(self.input_frame, text="Incline:")
        self.lbl_incline.pack(anchor="w", padx=15)
        inc_box_frame = ctk.CTkFrame(self.input_frame, fg_color="transparent")
        inc_box_frame.pack(fill="x", padx=15, pady=(0, 8))
        self.entry_incline = ctk.CTkEntry(inc_box_frame, placeholder_text="e.g., 2")
        self.entry_incline.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(inc_box_frame, text="%", font=ctk.CTkFont(weight="bold"), text_color="#9ca3af").pack(side="left", padx=(6, 0))

        # Calories Entry
        self.lbl_cal = ctk.CTkLabel(self.input_frame, text="Calories Burnt:")
        self.lbl_cal.pack(anchor="w", padx=15)
        cal_box_frame = ctk.CTkFrame(self.input_frame, fg_color="transparent")
        cal_box_frame.pack(fill="x", padx=15, pady=(0, 15))
        self.entry_cal = ctk.CTkEntry(cal_box_frame, placeholder_text="e.g., 180")
        self.entry_cal.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(cal_box_frame, text="kcal", font=ctk.CTkFont(weight="bold"), text_color="#9ca3af").pack(side="left", padx=(6, 0))

        # Action Buttons
        self.btn_add = ctk.CTkButton(self.input_frame, text="Save Run Log", font=ctk.CTkFont(weight="bold"), command=self.add_run)
        self.btn_add.pack(fill="x", padx=15, pady=5)

        self.lbl_status = ctk.CTkLabel(self.input_frame, text="", text_color="green")
        self.lbl_status.pack(pady=5)

        self.reset_date_field()

        # Right Panel: Data Table Display
        self.table_frame = ctk.CTkFrame(container)
        self.table_frame.pack(side="right", fill="both", expand=True)

        # Month Filter Dropdown Bar
        filter_bar = ctk.CTkFrame(self.table_frame, fg_color="transparent")
        filter_bar.pack(fill="x", padx=5, pady=(5, 0))

        lbl_filter_month = ctk.CTkLabel(filter_bar, text="Filter by Month:", font=ctk.CTkFont(weight="bold", size=13))
        lbl_filter_month.pack(side="left", padx=(5, 10))

        self.option_month_filter = ctk.CTkOptionMenu(
            filter_bar,
            values=["All Months"],
            command=lambda selected: self.rebuild_table()
        )
        self.option_month_filter.set("All Months")
        self.option_month_filter.pack(side="left")

        self.create_table_headers()

        self.scroll_data_frame = ctk.CTkScrollableFrame(self.table_frame, fg_color="transparent")
        self.scroll_data_frame.pack(fill="both", expand=True, padx=5, pady=(0, 5))
        self.scroll_data_frame.grid_columnconfigure(0, weight=1)

        self.update_month_dropdown()
        self.rebuild_table()

    def reset_date_field(self):
        self.entry_date.delete(0, "end")
        self.entry_date.insert(0, datetime.now().strftime("%d %B"))

    def create_table_headers(self):
        header_bar = ctk.CTkFrame(self.table_frame, fg_color="#1f293d", height=35)
        header_bar.pack(fill="x", padx=5, pady=5)
        header_bar.pack_propagate(False)
        ctk.CTkLabel(header_bar, text="Date", font=ctk.CTkFont(weight="bold")).place(relx=0.02, rely=0.5, anchor="w")
        ctk.CTkLabel(header_bar, text="Run", font=ctk.CTkFont(weight="bold")).place(relx=0.14, rely=0.5, anchor="w")
        ctk.CTkLabel(header_bar, text="Time (km/h)", font=ctk.CTkFont(weight="bold")).place(relx=0.26, rely=0.5, anchor="w")
        ctk.CTkLabel(header_bar, text="Incline", font=ctk.CTkFont(weight="bold")).place(relx=0.48, rely=0.5, anchor="w")
        ctk.CTkLabel(header_bar, text="Calories", font=ctk.CTkFont(weight="bold")).place(relx=0.62, rely=0.5, anchor="w")
        ctk.CTkLabel(header_bar, text="Actions", font=ctk.CTkFont(weight="bold")).place(relx=0.995, rely=0.5, anchor="e")

    # ---- Row pooling: plain-tk row widgets are built once and reused. ----
    # Instead of destroying and rebuilding every row on every add/edit/delete
    # (the original behavior), rows are grid-placed by index and just have
    # their text/colors/commands reconfigured. This turns an O(n) widget
    # creation storm into cheap O(n) text updates on already-live widgets.
    def _build_pool_row(self):
        frame = tk.Frame(self.scroll_data_frame, height=44, bg=COL_ROW_A)
        frame.grid_propagate(False)

        lbl_date = tk.Label(frame, bg=COL_ROW_A, fg=COL_TEXT, anchor="w")
        lbl_date.place(relx=0.02, rely=0.5, anchor="w")

        lbl_dist = tk.Label(frame, bg=COL_ROW_A, fg=COL_TEXT, anchor="w")
        lbl_dist.place(relx=0.14, rely=0.5, anchor="w")

        lbl_time = tk.Label(frame, bg=COL_ROW_A, fg=COL_TEXT, anchor="w")
        lbl_time.place(relx=0.26, rely=0.5, anchor="w")

        lbl_incline = tk.Label(frame, bg=COL_ROW_A, fg=COL_TEXT, anchor="w")
        lbl_incline.place(relx=0.48, rely=0.5, anchor="w")

        lbl_cal = tk.Label(frame, bg=COL_ROW_A, fg=COL_TEXT, anchor="w")
        lbl_cal.place(relx=0.62, rely=0.5, anchor="w")

        actions_frame = tk.Frame(frame, bg=COL_ROW_A)
        actions_frame.place(relx=1.0, rely=0.5, anchor="e", x=-8)

        btn_edit = tk.Button(
            actions_frame, text="Edit", width=6, bd=0, relief="flat",
            bg=COL_ACCENT, fg="white", activebackground=COL_ACCENT_HOVER, activeforeground="white",
            cursor="hand2"
        )
        btn_edit.pack(side="left", padx=3)

        btn_del = tk.Button(
            actions_frame, text="Delete", width=6, bd=0, relief="flat",
            bg=COL_DANGER, fg="white", activebackground=COL_DANGER_HOVER, activeforeground="white",
            cursor="hand2"
        )
        btn_del.pack(side="left", padx=3)

        return {
            "frame": frame,
            "lbl_date": lbl_date,
            "lbl_dist": lbl_dist,
            "lbl_time": lbl_time,
            "lbl_incline": lbl_incline,
            "lbl_cal": lbl_cal,
            "actions_frame": actions_frame,
            "btn_edit": btn_edit,
            "btn_del": btn_del
        }

    def _get_pool_row(self, pool_index):
        if pool_index >= len(self.row_pool):
            self.row_pool.append(self._build_pool_row())
        return self.row_pool[pool_index]

    def _update_pool_row(self, row, row_index, log, original_index):
        bg = COL_ROW_A if row_index % 2 == 0 else COL_ROW_B

        speed_num = self.compute_run_speed_num(log)
        speed_str = f"{speed_num:.1f} km/h" if speed_num > 0 else "N/A"

        row["frame"].configure(bg=bg)
        row["lbl_date"].configure(bg=bg, text=log.get("date", ""))
        row["lbl_dist"].configure(bg=bg, text=log.get("distance", ""))
        row["lbl_time"].configure(bg=bg, text=f"{log.get('time', '')} ({speed_str})")
        row["lbl_incline"].configure(bg=bg, text=log.get("incline", "0%"))
        row["lbl_cal"].configure(bg=bg, text=log.get("calories", "0 kcal"))
        row["actions_frame"].configure(bg=bg)

        row["btn_edit"].configure(command=lambda i=original_index: self.edit_run(i))
        row["btn_del"].configure(command=lambda i=original_index: self.delete_run(i))

        row["frame"].grid(row=row_index, column=0, sticky="ew", pady=2)

    def update_month_dropdown(self):
        """Extracts available month/year combinations from logged runs and populates dropdown."""
        month_set = set()
        for run in self.runs:
            dt = self.parse_run_date(run.get("date", ""))
            month_set.add((dt.year, dt.month, dt.strftime("%B %Y")))

        sorted_months = sorted(list(month_set), key=lambda x: (x[0], x[1]))
        month_options = ["All Months"] + [m[2] for m in sorted_months]

        current_selection = self.option_month_filter.get()
        self.option_month_filter.configure(values=month_options)

        if current_selection in month_options:
            self.option_month_filter.set(current_selection)
        else:
            self.option_month_filter.set("All Months")

    def rebuild_table(self):
        """Refreshes the data table for the selected month filter using the
        pooled row widgets (no destroy/recreate)."""
        selected_month = self.option_month_filter.get()

        display_index = 0
        for original_index, log in enumerate(self.runs):
            run_dt = self.parse_run_date(log.get("date", ""))
            run_month_str = run_dt.strftime("%B %Y")

            if selected_month == "All Months" or run_month_str == selected_month:
                row = self._get_pool_row(display_index)
                self._update_pool_row(row, display_index, log, original_index)
                display_index += 1

        # Hide any previously-used rows that aren't needed this time round.
        for j in range(display_index, len(self.row_pool)):
            self.row_pool[j]["frame"].grid_remove()

        self.rows_ui = self.row_pool[:display_index]

    # ==================== TAB 2: ANALYTICS DASHBOARD ====================
    def setup_analytics_tab(self):
        # Deferred import: matplotlib is one of the heaviest imports in this
        # app, so it's only pulled in once the user actually opens this tab.
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        from matplotlib.figure import Figure
        import matplotlib
        # Works around a known matplotlib/FreeType bug ("FT_Render_Glyph ...
        # raster overflow") seen on some FreeType builds (notably with very
        # new Python/matplotlib combos). Disabling hinting and antialiasing
        # routes text through FreeType's plain rasterizer, which avoids the
        # buggy code path.
        matplotlib.rcParams["text.hinting"] = "none"
        matplotlib.rcParams["text.antialiased"] = False

        top_bar = ctk.CTkFrame(self.tab_analytics, fg_color="transparent")
        top_bar.pack(fill="x", pady=(5, 5))

        lbl_filter = ctk.CTkLabel(top_bar, text="View Period:", font=ctk.CTkFont(weight="bold", size=13))
        lbl_filter.pack(side="left", padx=(5, 10))

        self.seg_period = ctk.CTkSegmentedButton(
            top_bar,
            values=["All Time", "This Month", "This Week"],
            command=lambda selected: self.refresh_analytics_display()
        )
        self.seg_period.set("All Time")
        self.seg_period.pack(side="left")

        # Summary Cards
        self.summary_frame = ctk.CTkFrame(self.tab_analytics, fg_color="#18181b", corner_radius=8)
        self.summary_frame.pack(fill="x", pady=(5, 10), padx=2)

        self.lbl_sum_week = ctk.CTkLabel(self.summary_frame, text="", font=ctk.CTkFont(size=12))
        self.lbl_sum_week.pack(side="left", expand=True, pady=8)

        self.lbl_sum_month = ctk.CTkLabel(self.summary_frame, text="", font=ctk.CTkFont(size=12))
        self.lbl_sum_month.pack(side="left", expand=True, pady=8)

        self.lbl_sum_all = ctk.CTkLabel(self.summary_frame, text="", font=ctk.CTkFont(size=12))
        self.lbl_sum_all.pack(side="left", expand=True, pady=8)

        # Main KPI Cards
        self.kpi_frame = ctk.CTkFrame(self.tab_analytics, fg_color="transparent", height=75)
        self.kpi_frame.pack(fill="x", pady=(0, 10))
        self.kpi_frame.pack_propagate(False)

        self.card_runs = self.create_kpi_card(self.kpi_frame, "Runs Count", "0", 0)
        self.card_dist = self.create_kpi_card(self.kpi_frame, "Total Distance", "0.0 km", 1)
        self.card_pace = self.create_kpi_card(self.kpi_frame, "Avg Pace", "0'00\" /km", 2)
        self.card_calories = self.create_kpi_card(self.kpi_frame, "Total Calories", "0 kcal", 3)

        # Charts Canvas
        self.chart_frame = ctk.CTkFrame(self.tab_analytics, fg_color="#121212")
        self.chart_frame.pack(fill="both", expand=True, pady=2)

        self.fig = Figure(figsize=(8, 4.2), dpi=100, facecolor="#121212")

        self.ax_dist = self.fig.add_subplot(221)
        self.ax_speed = self.fig.add_subplot(222)
        self.ax_cal = self.fig.add_subplot(223)
        self.ax_incline = self.fig.add_subplot(224)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.chart_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=8)

        # Bind hover mouse movement to dynamic tooltips
        self.canvas.mpl_connect("motion_notify_event", self.on_hover)

        self.refresh_analytics_display()

    def create_kpi_card(self, parent, label_text, initial_value, column_index):
        card = ctk.CTkFrame(parent, fg_color="#1e1e1e", corner_radius=10)
        card.grid(row=0, column=column_index, padx=6, sticky="nsew")
        parent.grid_columnconfigure(column_index, weight=1)

        lbl_title = ctk.CTkLabel(card, text=label_text, font=ctk.CTkFont(size=11), text_color="#9ca3af")
        lbl_title.pack(pady=(6, 1))

        lbl_val = ctk.CTkLabel(card, text=initial_value, font=ctk.CTkFont(size=17, weight="bold"))
        lbl_val.pack(pady=(0, 6))
        return lbl_val

    def calculate_metrics_for_set(self, dataset):
        total_runs = len(dataset)
        total_km = 0.0
        total_seconds = 0
        total_calories = 0.0

        for run in dataset:
            total_km += self.extract_numeric(run.get("distance", "0"))
            total_calories += self.extract_numeric(run.get("calories", "0"))

            min_match = re.search(r"(\d+)\s*min", run.get("time", ""))
            sec_match = re.search(r"(\d+)\s*sec", run.get("time", ""))

            m = int(min_match.group(1)) if min_match else 0
            s = int(sec_match.group(1)) if sec_match else 0
            total_seconds += (m * 60 + s)

        if total_km > 0 and total_seconds > 0:
            sec_per_km = total_seconds / total_km
            pace_minutes = int(sec_per_km // 60)
            pace_seconds = int(sec_per_km % 60)
            pace_string = f"{pace_minutes}m {pace_seconds:02d}s /km"
        else:
            pace_string = "N/A"

        return str(total_runs), f"{total_km:.2f} km", pace_string, f"{int(total_calories)} kcal"

    def format_subplot(self, ax, title, main_color):
        ax.set_facecolor("#1a1a1a")
        ax.set_title(title, color="#e5e7eb", fontname="DejaVu Sans", fontsize=9, pad=6, weight="bold", loc="left")
        ax.grid(True, which='major', linestyle=':', alpha=0.08, color="#ffffff")

        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#374151')
        ax.spines['bottom'].set_color('#374151')
        ax.spines['left'].set_linewidth(0.8)
        ax.spines['bottom'].set_linewidth(0.8)

        ax.tick_params(colors='#9ca3af', labelsize=8, length=3)

    def plot_metric_series(self, ax, dates, values, title, color, unit=""):
        self.format_subplot(ax, title, color)
        if not dates or not values:
            return None

        line, = ax.plot(dates, values, color=color, linewidth=2.2, zorder=3)
        ax.fill_between(dates, values, color=color, alpha=0.12, zorder=2)
        scat = ax.scatter(dates, values, color=color, s=35, zorder=4, edgecolors='#ffffff', linewidth=1.2)

        annot = ax.annotate(
            "",
            xy=(0, 0),
            xytext=(15, 15),
            textcoords="offset points",
            bbox=dict(boxstyle="round,pad=0.5", fc="#1e1e1e", ec=color, lw=1.5),
            arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=0", color=color, lw=1.2),
            fontsize=8,
            color="white",
            weight="bold"
        )
        annot.set_visible(False)

        return {
            "ax": ax,
            "line": line,
            "scat": scat,
            "annot": annot,
            "dates": dates,
            "values": values,
            "unit": unit
        }

    def draw_chart(self, dataset):
        axes = [self.ax_dist, self.ax_speed, self.ax_cal, self.ax_incline]
        for ax in axes:
            ax.clear()

        self.plot_elements.clear()

        if dataset:
            dates = [run.get("date", "") for run in dataset]
            distances = [self.extract_numeric(r.get("distance", "0")) for r in dataset]
            speeds = [self.compute_run_speed_num(r) for r in dataset]
            calories = [self.extract_numeric(r.get("calories", "0")) for r in dataset]
            inclines = [self.extract_numeric(r.get("incline", "0")) for r in dataset]

            p1 = self.plot_metric_series(self.ax_dist, dates, distances, "Distance (km)", "#00F0FF", "km")
            p2 = self.plot_metric_series(self.ax_speed, dates, speeds, "Avg Speed (km/h)", "#00FF88", "km/h")
            p3 = self.plot_metric_series(self.ax_cal, dates, calories, "Calories Burnt (kcal)", "#FF3366", "kcal")
            p4 = self.plot_metric_series(self.ax_incline, dates, inclines, "Incline Level (%)", "#A855F7", "%")

            for p in (p1, p2, p3, p4):
                if p:
                    self.plot_elements.append(p)

        self.fig.tight_layout(pad=1.5, h_pad=2.0, w_pad=1.5)
        self.canvas.draw_idle()

    # ==================== INTERACTIVE HOVER EVENT ====================
    def on_hover(self, event):
        vis_changed = False

        if event.inaxes:
            for elem in self.plot_elements:
                annot = elem["annot"]
                if elem["ax"] != event.inaxes:
                    if annot.get_visible():
                        annot.set_visible(False)
                        vis_changed = True
                    continue

                scat = elem["scat"]
                cont, ind = scat.contains(event)

                if cont:
                    idx = ind["ind"][0]
                    pos = scat.get_offsets()[idx]
                    annot.xy = pos

                    date_str = elem["dates"][idx]
                    val = elem["values"][idx]
                    unit = elem["unit"]

                    val_str = f"{val:.1f}" if isinstance(val, float) and val % 1 != 0 else f"{val:.1f}" if isinstance(val, float) else str(val)

                    annot.set_text(f"{date_str}\n{val_str} {unit}")
                    if not annot.get_visible():
                        annot.set_visible(True)
                        vis_changed = True
                else:
                    if annot.get_visible():
                        annot.set_visible(False)
                        vis_changed = True
        else:
            for elem in self.plot_elements:
                annot = elem["annot"]
                if annot.get_visible():
                    annot.set_visible(False)
                    vis_changed = True

        if vis_changed:
            self.canvas.draw_idle()

    def refresh_analytics_display(self):
        week_runs = self.filter_runs_by_period("This Week")
        month_runs = self.filter_runs_by_period("This Month")

        w_cnt, w_dist, _, _ = self.calculate_metrics_for_set(week_runs)
        m_cnt, m_dist, _, _ = self.calculate_metrics_for_set(month_runs)
        a_cnt, a_dist, _, _ = self.calculate_metrics_for_set(self.runs)

        self.lbl_sum_week.configure(text=f"🗓️  This Week:  {w_dist}  ({w_cnt} runs)")
        self.lbl_sum_month.configure(text=f"📅  This Month:  {m_dist}  ({m_cnt} runs)")
        self.lbl_sum_all.configure(text=f"🏆  All Time:  {a_dist}  ({a_cnt} runs)")

        selected_period = self.seg_period.get()
        active_runs = self.filter_runs_by_period(selected_period)

        runs_count, distance_str, pace_str, calories_str = self.calculate_metrics_for_set(active_runs)

        self.card_runs.configure(text=runs_count)
        self.card_dist.configure(text=distance_str)
        self.card_pace.configure(text=pace_str)
        self.card_calories.configure(text=calories_str)

        self.draw_chart(active_runs)

    # ==================== DATA ACTIONS ====================
    def add_run(self):
        date_val = self.entry_date.get().strip()
        dist_val = self.entry_dist.get().strip()
        min_val = self.entry_time_min.get().strip() or "0"
        sec_val = self.entry_time_sec.get().strip() or "0"
        inc_val = self.entry_incline.get().strip() or "0"
        cal_val = self.entry_cal.get().strip() or "0"

        if not dist_val or (min_val == "0" and sec_val == "0"):
            self.lbl_status.configure(text="Missing required fields!", text_color="#ef4444")
            return

        if not date_val:
            date_val = datetime.now().strftime("%d %B")

        formatted_dist = dist_val if "km" in dist_val.lower() else f"{dist_val}km"
        formatted_time = f"{min_val}min {sec_val}sec"
        formatted_inc = inc_val if "%" in inc_val else f"{inc_val}%"
        formatted_cal = cal_val if "kcal" in cal_val.lower() else f"{cal_val} kcal"

        new_run = {
            "date": date_val,
            "distance": formatted_dist,
            "time": formatted_time,
            "incline": formatted_inc,
            "calories": formatted_cal
        }

        self.runs.append(new_run)
        self.sort_runs()
        self.save_runs()

        self.update_month_dropdown()
        self.rebuild_table()
        if self.analytics_built:
            self.refresh_analytics_display()

        self.entry_dist.delete(0, "end")
        self.entry_time_min.delete(0, "end")
        self.entry_time_sec.delete(0, "end")
        self.entry_incline.delete(0, "end")
        self.entry_cal.delete(0, "end")
        self.reset_date_field()

        self.lbl_status.configure(text="Run logged successfully!", text_color="#10b981")
        self.after(2500, lambda: self.lbl_status.configure(text=""))

    def delete_run(self, index):
        if index < 0 or index >= len(self.runs):
            return

        self.runs.pop(index)
        self.save_runs()

        self.update_month_dropdown()
        self.rebuild_table()
        if self.analytics_built:
            self.refresh_analytics_display()

    def edit_run(self, index):
        if index < 0 or index >= len(self.runs):
            return

        run = self.runs[index]

        # Plain tk.Toplevel (instead of CTkToplevel) so the edit dialog opens
        # and closes instantly rather than paying CTk's extra setup cost.
        dlg = tk.Toplevel(self)
        dlg.configure(bg=COL_BG)
        dlg.title("Edit Run")
        dlg.geometry("360x420")
        dlg.resizable(False, False)
        dlg.transient(self)
        dlg.grab_set()

        min_match = re.search(r"(\d+)\s*min", run.get("time", ""))
        sec_match = re.search(r"(\d+)\s*sec", run.get("time", ""))
        curr_min = min_match.group(1) if min_match else "0"
        curr_sec = sec_match.group(1) if sec_match else "0"

        def make_label(text, top_pad=6):
            lbl = tk.Label(dlg, text=text, bg=COL_BG, fg=COL_TEXT)
            lbl.pack(anchor="w", padx=15, pady=(top_pad, 0))
            return lbl

        def make_entry(parent, width=None):
            kwargs = dict(bg=COL_FIELD, fg=COL_TEXT, insertbackground=COL_TEXT, relief="flat", bd=6)
            if width:
                kwargs["width"] = width
            return tk.Entry(parent, **kwargs)

        def make_unit_label(parent, text):
            return tk.Label(parent, text=text, bg=COL_BG, fg=COL_MUTED, font=("Helvetica", 10, "bold"))

        # Date Field
        make_label("Date:", top_pad=10)
        date_frame = tk.Frame(dlg, bg=COL_BG)
        date_frame.pack(fill="x", padx=15, pady=(2, 0))

        entry_date = make_entry(date_frame)
        entry_date.pack(side="left", fill="x", expand=True)
        entry_date.insert(0, run.get("date", ""))

        btn_edit_cal = tk.Button(
            date_frame, text="📅", width=3, bd=0, relief="flat",
            bg=COL_ROW_A, fg=COL_TEXT, activebackground="#374151", activeforeground=COL_TEXT,
            cursor="hand2", command=lambda: FastCalendarPopup(dlg, entry_date)
        )
        btn_edit_cal.pack(side="left", padx=(6, 0))

        # Distance Field
        make_label("Distance:")
        dist_frame = tk.Frame(dlg, bg=COL_BG)
        dist_frame.pack(fill="x", padx=15, pady=(2, 0))
        entry_dist = make_entry(dist_frame)
        entry_dist.pack(side="left", fill="x", expand=True)
        entry_dist.insert(0, str(self.extract_numeric(run.get("distance", "0"))))
        make_unit_label(dist_frame, "km").pack(side="left", padx=(6, 0))

        # Time Field
        make_label("Time Taken:")
        time_frame = tk.Frame(dlg, bg=COL_BG)
        time_frame.pack(fill="x", padx=15, pady=(2, 0))

        entry_min = make_entry(time_frame, width=6)
        entry_min.pack(side="left")
        entry_min.insert(0, curr_min)
        make_unit_label(time_frame, "min").pack(side="left", padx=(4, 12))

        entry_sec = make_entry(time_frame, width=6)
        entry_sec.pack(side="left")
        entry_sec.insert(0, curr_sec)
        make_unit_label(time_frame, "sec").pack(side="left", padx=(4, 0))

        # Incline Field
        make_label("Incline:")
        inc_frame = tk.Frame(dlg, bg=COL_BG)
        inc_frame.pack(fill="x", padx=15, pady=(2, 0))
        entry_inc = make_entry(inc_frame)
        entry_inc.pack(side="left", fill="x", expand=True)
        entry_inc.insert(0, str(self.extract_numeric(run.get("incline", "0"))))
        make_unit_label(inc_frame, "%").pack(side="left", padx=(6, 0))

        # Calories Field
        make_label("Calories:")
        cal_frame = tk.Frame(dlg, bg=COL_BG)
        cal_frame.pack(fill="x", padx=15, pady=(2, 0))
        entry_cal = make_entry(cal_frame)
        entry_cal.pack(side="left", fill="x", expand=True)
        entry_cal.insert(0, str(int(self.extract_numeric(run.get("calories", "0")))))
        make_unit_label(cal_frame, "kcal").pack(side="left", padx=(6, 0))

        def save_edit():
            d = entry_date.get().strip()
            dv = entry_dist.get().strip()
            mv = entry_min.get().strip() or "0"
            sv = entry_sec.get().strip() or "0"
            iv = entry_inc.get().strip() or "0"
            cv = entry_cal.get().strip() or "0"

            if not dv:
                return

            updated_run = {
                "date": d or run.get("date", ""),
                "distance": dv if "km" in dv.lower() else f"{dv}km",
                "time": f"{mv}min {sv}sec",
                "incline": iv if "%" in iv else f"{iv}%",
                "calories": cv if "kcal" in cv.lower() else f"{cv} kcal"
            }
            self.runs[index] = updated_run
            self.sort_runs()
            self.save_runs()

            dlg.destroy()
            self.update_month_dropdown()
            self.rebuild_table()
            if self.analytics_built:
                self.refresh_analytics_display()

        btn_frame = tk.Frame(dlg, bg=COL_BG)
        btn_frame.pack(fill="x", padx=15, pady=(20, 10))

        tk.Button(
            btn_frame, text="Save", bd=0, relief="flat",
            bg=COL_ACCENT, fg="white", activebackground=COL_ACCENT_HOVER, activeforeground="white",
            cursor="hand2", command=save_edit
        ).pack(side="left", expand=True, fill="x", padx=(0, 4), ipady=4)

        tk.Button(
            btn_frame, text="Cancel", bd=0, relief="flat",
            bg=COL_ROW_A, fg="white", activebackground="#374151", activeforeground="white",
            cursor="hand2", command=dlg.destroy
        ).pack(side="right", expand=True, fill="x", padx=(4, 0), ipady=4)


if __name__ == "__main__":
    app = RunningTrackerApp()
    app.mainloop()