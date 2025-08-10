# School Timetable Planner - Optimized for Fast Loading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import sqlite3
import json
import os
import calendar
from datetime import datetime
import socket
import urllib.request

# Lazy imports - load only when needed
def lazy_import_pandas():
    try:
        import pandas as pd
        return pd
    except ImportError:
        messagebox.showerror("Missing Dependency", "pandas is not installed. Please run: pip install pandas")
        return None

def lazy_import_reportlab():
    try:
        from reportlab.lib.pagesizes import letter, landscape
        from reportlab.pdfgen import canvas
        return canvas, letter, landscape
    except ImportError:
        messagebox.showerror("Missing Dependency", "reportlab is not installed. Please run: pip install reportlab")
        return None, None, None

DB_FILE = 'timetable.db'
CONFIG_FILE = 'config.json'

# Default config
DEFAULT_CONFIG = {
    "classes": [f"Class {i+1}" for i in range(10)],
    "sections": ["A", "B", "C", "D"],
    "subjects": ["Math", "Science", "English", "History", "Geography"],
    "teachers": ["Teacher 1", "Teacher 2", "Teacher 3", "Teacher 4"],
    "periods_per_day": 7,
    "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
}

class TimetableApp:
    def __init__(self, root):
        self.root = root
        # Set basic properties first
        self._set_theme()
        self.root.title("Class Flow v1.3")
        self.root.geometry("1200x700")
        
        # Initialize essential variables
        now = datetime.now()
        # Calculate academic week (assuming academic year starts in August)
        # For August 10, 2025, this should be week 2 of academic year
        if now.month >= 8:  # August or later in academic year
            academic_start = datetime(now.year, 8, 1)  # August 1st
        else:  # January to July, previous academic year
            academic_start = datetime(now.year - 1, 8, 1)  # Previous August 1st
        
        days_since_start = (now - academic_start).days
        self.current_week = (days_since_start // 7) + 1  # Academic week
        
        self.selected_week = tk.IntVar(value=self.current_week)
        self.selected_year = tk.IntVar(value=datetime.now().year)
        self.current_date_str = now.strftime("%B %d, %Y")  # e.g., "August 10, 2025"
        self.current_time_str = now.strftime("%I:%M %p")    # e.g., "2:30 PM"
        self.impacted_cells = set()
        self.resolved_cells = set()
        self.entries = {}
        self.teacher_cbs = {}
        self.cell_frames = {}
        self.current_impacted_periods = []
        
        # Show loading message
        loading_label = tk.Label(self.root, text="Loading Class Flow...", 
                               font=("Segoe UI", 16), fg="#2d6cdf")
        loading_label.pack(expand=True)
        
        # Schedule the heavy initialization for after the window is shown
        self.root.after(50, self._complete_initialization)
        
    def _complete_initialization(self):
        """Complete the heavy initialization after window is shown"""
        # Remove loading message
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Load config (fast)
        self.config = self.load_config()
        
        # Setup database (optimized)
        self.setup_db()
        
        # Setup UI (fast)
        self.setup_ui()
        
        # Check internet in background (non-blocking)
        self.root.after(100, self.check_internet_connection)
        
        # Load timetable data in background
        self.root.after(200, self.load_timetable)

    def check_internet_connection(self):
        """Quick internet connectivity check - non-blocking"""
        try:
            # Quick DNS check with very short timeout
            socket.create_connection(("8.8.8.8", 53), timeout=1)
            return True
        except OSError:
            # Show warning but don't block startup
            self.root.after(100, lambda: messagebox.showwarning(
                "Limited Connectivity", 
                "Internet connection may be limited.\n\n"
                "Some features may not work:\n"
                "• Online help resources\n"
                "• Update checks\n\n"
                "The application will continue to work offline."
            ))
            return False

    def _set_theme(self):
        self.style = ttk.Style()
        self.root.configure(bg="#f0f4f8")
        self.style.theme_use('clam')
        self.style.configure('TFrame', background="#f0f4f8")
        self.style.configure('TLabel', background="#f0f4f8", font=("Segoe UI", 10))
        self.style.configure('Header.TLabel', background="#2d6cdf", foreground="#fff", font=("Segoe UI", 11, "bold"), anchor="center")
        self.style.configure('TButton', font=("Segoe UI", 10, "bold"), background="#2d6cdf", foreground="#fff")
        self.style.map('TButton', background=[('active', '#1b4e91')], foreground=[('active', '#fff')])
        self.style.configure('Warning.TButton', font=("Segoe UI", 10, "bold"), background="#ff9800", foreground="#fff")
        self.style.map('Warning.TButton', background=[('active', '#e65100')], foreground=[('active', '#fff')])
        self.style.configure('Green.TButton', font=("Segoe UI", 10, "bold"), background="#43a047", foreground="#fff")
        self.style.map('Green.TButton', background=[('active', '#2e7031')], foreground=[('active', '#fff')])
        self.style.configure('TCombobox', font=("Segoe UI", 10))
        self.style.configure('RedCell.TFrame', background="#ffcccc", borderwidth=2, relief="solid")
        self.style.configure('GreenCell.TFrame', background="#ccffcc", borderwidth=2, relief="solid")
        self.style.configure('FancyCell.TFrame', background="#eaf0fa", borderwidth=1, relief="solid")
        self.style.configure('FancyCell.TLabel', background="#eaf0fa", font=("Segoe UI", 9))

    def load_config(self):
        """Optimized config loading with caching"""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
        
        # Create default config if needed
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(DEFAULT_CONFIG, f, indent=2)
        except IOError:
            pass
        return DEFAULT_CONFIG.copy()

    def setup_db(self):
        """Optimized database setup with faster connection"""
        self.conn = sqlite3.connect(DB_FILE, check_same_thread=False)
        self.conn.execute('PRAGMA journal_mode=WAL')  # Faster writes
        self.conn.execute('PRAGMA synchronous=NORMAL')  # Better performance
        self.c = self.conn.cursor()
        
        # Quick table existence check
        self.c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='timetable'")
        if not self.c.fetchone():
            # Create table only if it doesn't exist
            self.c.execute('''CREATE TABLE timetable (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                year INTEGER,
                week INTEGER,
                class TEXT,
                section TEXT,
                day TEXT,
                period INTEGER,
                subject TEXT,
                teacher TEXT
            )''')
        else:
            # Quick column existence check
            self.c.execute('PRAGMA table_info(timetable)')
            columns = [row[1] for row in self.c.fetchall()]
            if 'year' not in columns:
                self.c.execute('ALTER TABLE timetable ADD COLUMN year INTEGER')
            if 'week' not in columns:
                self.c.execute('ALTER TABLE timetable ADD COLUMN week INTEGER')
        
        # Create teacher restrictions table for class-section limitations
        self.c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='teacher_restrictions'")
        if not self.c.fetchone():
            self.c.execute('''CREATE TABLE teacher_restrictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                teacher TEXT,
                class TEXT,
                section TEXT,
                UNIQUE(teacher, class, section)
            )''')
        
        self.conn.commit()

    def get_teacher_restrictions(self, teacher):
        """Get list of (class, section) tuples that a teacher can teach"""
        self.c.execute("SELECT class, section FROM teacher_restrictions WHERE teacher = ?", (teacher,))
        return self.c.fetchall()
    
    def can_teacher_teach_class_section(self, teacher, class_name, section):
        """Check if a teacher can teach a specific class-section combination"""
        self.c.execute(
            "SELECT COUNT(*) FROM teacher_restrictions WHERE teacher = ? AND class = ? AND section = ?",
            (teacher, class_name, section)
        )
        count = self.c.fetchone()[0]
        
        # If no restrictions exist for this teacher, they can teach any class-section
        self.c.execute("SELECT COUNT(*) FROM teacher_restrictions WHERE teacher = ?", (teacher,))
        total_restrictions = self.c.fetchone()[0]
        
        if total_restrictions == 0:
            return True  # No restrictions means can teach anywhere
        
        return count > 0  # Can teach if specifically allowed

    def filter_teachers_by_restrictions(self, teachers, class_name, section):
        """Filter teachers based on class-section restrictions"""
        filtered_teachers = []
        for teacher in teachers:
            if self.can_teacher_teach_class_section(teacher, class_name, section):
                filtered_teachers.append(teacher)
        return filtered_teachers

    def setup_ui(self):
        # Header with app name and beta label, improved alignment and color
        header_frame = tk.Frame(self.root, bg="#2d6cdf")
        header_frame.pack(fill='x', padx=0, pady=(0, 5))
        header_label = tk.Label(header_frame, text="Class Flow v1.3", font=("Segoe UI", 26, "bold"), bg="#2d6cdf", fg="#fff", anchor="center")
        header_label.pack(side='left', expand=True, fill='x', pady=(10, 0), padx=(20, 0))
        
        # Date and time info frame
        datetime_frame = tk.Frame(header_frame, bg="#2d6cdf")
        datetime_frame.pack(side='right', padx=(10, 20), pady=(10, 0))
        
        # Current date display
        date_label = tk.Label(datetime_frame, text=f"{self.current_date_str}", 
                             font=("Segoe UI", 12, "bold"), bg="#2d6cdf", fg="#ffe082", anchor="e")
        date_label.pack(anchor='e')
        
        # Current time display  
        self.time_label = tk.Label(datetime_frame, text=f"{self.current_time_str}", 
                                  font=("Segoe UI", 10), bg="#2d6cdf", fg="#ffffff", anchor="e")
        self.time_label.pack(anchor='e')
        
        # Academic week display
        week_label = tk.Label(datetime_frame, text=f"Academic Week: {self.current_week}", 
                             font=("Segoe UI", 10), bg="#2d6cdf", fg="#ffe082", anchor="e")
        week_label.pack(anchor='e')
        
        beta_label = tk.Label(header_frame, text="beta release", font=("Segoe UI", 12, "italic"), bg="#2d6cdf", fg="#ffe082", anchor="w")
        beta_label.pack(side='left', pady=(18, 0), padx=(10, 20))
        
        # Start time update loop
        self.update_time()

        # Top controls
        controls = ttk.Frame(self.root)
        controls.pack(fill='x', padx=10, pady=5)

        ttk.Label(controls, text="Year:").pack(side='left')
        ttk.Entry(controls, textvariable=self.selected_year, width=6).pack(side='left', padx=5)
        
        ttk.Label(controls, text="Week:").pack(side='left')
        ttk.Entry(controls, textvariable=self.selected_week, width=4).pack(side='left', padx=5)
        
        ttk.Button(controls, text="Load", command=self.load_timetable).pack(side='left', padx=5)
        ttk.Button(controls, text="Save", command=self.save_timetable).pack(side='left', padx=5)
        ttk.Button(controls, text="Edit Classes", command=self.edit_classes).pack(side='right', padx=5)
        ttk.Button(controls, text="Edit Sections", command=self.edit_sections).pack(side='right', padx=5)
        ttk.Button(controls, text="Edit Teachers", command=self.edit_teachers).pack(side='right', padx=5)
        
        # Action buttons
        actions = ttk.Frame(self.root)
        actions.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(actions, text="Auto-Assign", command=self.auto_assign).pack(side='left', padx=5)
        ttk.Button(actions, text="Smart Match", command=self.smart_match, style='Green.TButton').pack(side='left', padx=5)
        ttk.Button(actions, text="Teacher Mapping", command=self.show_teacher_subject_mapping).pack(side='left', padx=5)
        ttk.Button(actions, text="Teacher Restrictions", command=self.show_teacher_restrictions).pack(side='left', padx=5)
        ttk.Button(actions, text="Teacher Leave", command=self.mark_leave).pack(side='left', padx=5)
        ttk.Button(actions, text="Export Excel", command=self.export_excel).pack(side='left', padx=5)
        ttk.Button(actions, text="Export PDF", command=self.export_pdf).pack(side='left', padx=5)
        ttk.Button(actions, text="Refresh", command=self.refresh_grid).pack(side='left', padx=5)

        # Grid with scrollbars
        self.grid_container = ttk.Frame(self.root)
        self.grid_container.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create canvas and scrollbars for the grid
        self.grid_canvas = tk.Canvas(self.grid_container, highlightthickness=0)
        self.v_scrollbar = ttk.Scrollbar(self.grid_container, orient="vertical", command=self.grid_canvas.yview)
        self.h_scrollbar = ttk.Scrollbar(self.grid_container, orient="horizontal", command=self.grid_canvas.xview)
        
        self.grid_frame = ttk.Frame(self.grid_canvas)
        
        # Configure scrollbars
        self.grid_canvas.configure(yscrollcommand=self.v_scrollbar.set, xscrollcommand=self.h_scrollbar.set)
        
        # Pack scrollbars and canvas
        self.v_scrollbar.pack(side="right", fill="y")
        self.h_scrollbar.pack(side="bottom", fill="x")
        self.grid_canvas.pack(side="left", fill="both", expand=True)
        
        # Create window in canvas
        self.canvas_frame = self.grid_canvas.create_window((0, 0), window=self.grid_frame, anchor="nw")
        
        # Bind events for scrolling
        self.grid_frame.bind("<Configure>", self._on_frame_configure)
        self.grid_canvas.bind("<Configure>", self._on_canvas_configure)
        self.grid_canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        
        # Add additional scroll event bindings
        self._bind_scroll_events()
        
        # Add Hypersync footer at the bottom
        footer_frame = ttk.Frame(self.root)
        footer_frame.pack(fill='x', pady=(5, 0))
        
        footer_label = ttk.Label(footer_frame, text="Hypersync - An AI based education startup", 
                                font=("Segoe UI", 9), foreground="#666666")
        footer_label.pack(anchor='center')
        
        # Initial grid draw
        self.draw_grid()

    def update_time(self):
        """Update the time display every minute"""
        now = datetime.now()
        new_time_str = now.strftime("%I:%M %p")
        if hasattr(self, 'time_label'):
            self.time_label.config(text=new_time_str)
        # Schedule next update in 60 seconds
        self.root.after(60000, self.update_time)

    def _on_frame_configure(self, event):
        """Reset the scroll region to encompass the inner frame"""
        self.grid_canvas.configure(scrollregion=self.grid_canvas.bbox("all"))
        # Ensure both horizontal and vertical scrolling work properly
        canvas_width = self.grid_canvas.winfo_width()
        canvas_height = self.grid_canvas.winfo_height()
        frame_width = self.grid_frame.winfo_reqwidth()
        frame_height = self.grid_frame.winfo_reqheight()
        
        # Configure canvas item size for proper scrolling
        if frame_width > canvas_width or frame_height > canvas_height:
            self.grid_canvas.itemconfig(self.canvas_frame, width=max(frame_width, canvas_width), height=max(frame_height, canvas_height))

    def _on_canvas_configure(self, event):
        """Reset the canvas window to encompass inner frame when required"""
    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling with shift for horizontal scroll"""
        if event.state & 0x1:  # Shift key pressed
            # Horizontal scrolling
            self.grid_canvas.xview_scroll(int(-1 * (event.delta / 120)), "units")
        else:
            # Vertical scrolling
            self.grid_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas_width = event.width
        frame_width = self.grid_frame.winfo_reqwidth()
        # Only resize if frame is smaller than canvas
        if frame_width < canvas_width:
            self.grid_canvas.itemconfig(self.canvas_frame, width=canvas_width)

    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling"""
        # Check if we need horizontal scroll (Shift key or if vertical scroll isn't needed)
        if event.state & 0x1:  # Shift key pressed
            self.grid_canvas.xview_scroll(int(-1*(event.delta/120)), "units")
        else:
            self.grid_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def _bind_scroll_events(self):
        """Bind additional scroll events for better navigation"""
        # Bind arrow keys for keyboard navigation
        self.root.bind("<Left>", lambda e: self.grid_canvas.xview_scroll(-1, "units"))
        self.root.bind("<Right>", lambda e: self.grid_canvas.xview_scroll(1, "units"))
        self.root.bind("<Up>", lambda e: self.grid_canvas.yview_scroll(-1, "units"))
        self.root.bind("<Down>", lambda e: self.grid_canvas.yview_scroll(1, "units"))
        
        # Bind Page Up/Down for faster vertical scrolling
        self.root.bind("<Prior>", lambda e: self.grid_canvas.yview_scroll(-1, "pages"))
        self.root.bind("<Next>", lambda e: self.grid_canvas.yview_scroll(1, "pages"))
        
        # Bind Home/End for horizontal scrolling
        self.root.bind("<Home>", lambda e: self.grid_canvas.xview_moveto(0))
        self.root.bind("<End>", lambda e: self.grid_canvas.xview_moveto(1))
        
        # Make canvas focusable for keyboard events
        self.grid_canvas.focus_set()
        self.grid_canvas.bind("<Button-1>", lambda e: self.grid_canvas.focus_set())

    def export_pdf(self):
        # Lazy load reportlab only when needed
        canvas_module, letter, landscape = lazy_import_reportlab()
        if canvas_module is None:
            return
        
        file = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        if not file:
            return
            
        try:
            data = []
            for (class_, section, day, period), (subj_var, teacher_var) in self.entries.items():
                if subj_var.get() or teacher_var.get():
                    data.append([
                        class_, section, day, str(period + 1), 
                        subj_var.get() or "", teacher_var.get() or ""
                    ])
            
            if not data:
                messagebox.showinfo("No Data", "No timetable data to export.")
                return
            
            c = canvas_module.Canvas(file, pagesize=landscape(letter))
            width, height = landscape(letter)
            
            # Title
            c.setFont("Helvetica-Bold", 16)
            c.drawString(30, height - 40, "Class Flow - Timetable Export")
            
            # Headers
            c.setFont("Helvetica-Bold", 10)
            headers = ["Class", "Section", "Day", "Period", "Subject", "Teacher"]
            x = 30
            y = height - 70
            for i, h in enumerate(headers):
                c.drawString(x + i*100, y, h)
            
            # Data
            c.setFont("Helvetica", 9)
            y -= 20
            for row in data:
                for i, val in enumerate(row):
                    c.drawString(x + i*100, y, str(val))
                y -= 15
                if y < 40:  # Start new page if running out of space
                    c.showPage()
                    c.setFont("Helvetica", 9)
                    y = height - 40
            
            # Add Hypersync footer at bottom of page
            c.setFont("Helvetica", 8)
            footer_text = "Hypersync - An AI based education startup"
            footer_width = c.stringWidth(footer_text, "Helvetica", 8)
            c.drawString((width - footer_width) / 2, 30, footer_text)
            
            c.save()
            messagebox.showinfo("Success", f"PDF exported successfully to:\n{file}")
            
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export PDF:\n{str(e)}")
            return

        # Grid
        self.grid_frame = ttk.Frame(self.root)
        self.grid_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Initial grid draw
        self.draw_grid()

    def draw_grid(self):
        """Optimized grid drawing with batched operations"""
        # Clear grid efficiently
        for widget in self.grid_frame.winfo_children():
            widget.destroy()
        
        # Disable updates during grid creation for faster rendering
        self.grid_frame.update_idletasks()
        
        # Headers - create in batch
        header_widgets = []
        header_widgets.append(ttk.Label(self.grid_frame, text="Class", style='Header.TLabel', borderwidth=1, relief="solid", width=10, anchor='center', justify='center'))
        header_widgets.append(ttk.Label(self.grid_frame, text="Section", style='Header.TLabel', borderwidth=1, relief="solid", width=8, anchor='center', justify='center'))
        
        # Grid headers
        header_widgets[0].grid(row=0, column=0, sticky='nsew')
        header_widgets[1].grid(row=0, column=1, sticky='nsew')
        
        col = 2
        for day in self.config['days']:
            for p in range(self.config['periods_per_day']):
                header = ttk.Label(self.grid_frame, text=f"{day}\nP{p+1}", style='Header.TLabel', borderwidth=1, relief="solid", width=10)
                header.grid(row=0, column=col, sticky='nsew')
                col += 1

        # Cells
        row = 1
        for class_ in self.config['classes']:
            for section in self.config['sections']:
                ttk.Label(self.grid_frame, text=class_, style='TLabel', borderwidth=1, relief="solid", width=10, anchor='center', justify='center').grid(row=row, column=0, sticky='nsew')
                ttk.Label(self.grid_frame, text=section, style='TLabel', borderwidth=1, relief="solid", width=8, anchor='center', justify='center').grid(row=row, column=1, sticky='nsew')
                col = 2
                for day in self.config['days']:
                    for period in range(self.config['periods_per_day']):
                        cell_key = (class_, section, day, period)
                        highlight = None
                        if cell_key in self.impacted_cells:
                            highlight = 'RedCell.TFrame'
                        elif cell_key in self.resolved_cells:
                            highlight = 'GreenCell.TFrame'
                        else:
                            highlight = 'FancyCell.TFrame'
                        frame = ttk.Frame(self.grid_frame, style=highlight)
                        frame.grid(row=row, column=col, sticky='nsew')
                        subj_var = tk.StringVar()
                        teacher_var = tk.StringVar()
                        
                        # Subject dropdown with blank option
                        subject_values = [""] + self.config['subjects']  # Add blank option
                        subj_cb = ttk.Combobox(frame, textvariable=subj_var, values=subject_values, width=8)
                        subj_cb.pack(side='top', fill='x', padx=1, pady=1)
                        
                        # Teacher dropdown - initially with all teachers, will be filtered by subject
                        # Filter initial teacher values by class-section restrictions
                        allowed_teachers = self.filter_teachers_by_restrictions(self.config['teachers'], class_, section)
                        teacher_values = [""] + allowed_teachers  # Add blank option
                        teacher_cb = ttk.Combobox(frame, textvariable=teacher_var, values=teacher_values, width=12)
                        teacher_cb.pack(side='top', fill='x', padx=1, pady=(0,2))
                        
                        self.entries[cell_key] = (subj_var, teacher_var)
                        self.teacher_cbs[cell_key] = teacher_cb
                        self.cell_frames[cell_key] = frame
                        
                        def on_subject_change(event=None, key=cell_key, t_cb=teacher_cb, t_var=teacher_var):
                            """Update teacher dropdown based on selected subject"""
                            selected_subject = subj_var.get()
                            current_teacher = t_var.get()
                            
                            if selected_subject and selected_subject != "":
                                # Get teachers who can teach this subject
                                teacher_subjects = self.config.get('teacher_subjects', {})
                                if teacher_subjects:
                                    available_teachers = [teacher for teacher, subjects in teacher_subjects.items() 
                                                        if selected_subject in subjects]
                                else:
                                    # If no mapping exists, show all teachers
                                    available_teachers = self.config['teachers']
                                
                                # Further filter by class-section restrictions
                                available_teachers = self.filter_teachers_by_restrictions(
                                    available_teachers, class_, section
                                )
                                
                                # Update teacher dropdown with filtered teachers
                                filtered_values = [""] + available_teachers
                                t_cb['values'] = filtered_values
                                
                                # Only clear teacher selection if current teacher can't teach this subject
                                # BUT preserve blank entries and manual entries
                                if current_teacher and current_teacher != "" and current_teacher not in available_teachers:
                                    # Check if it's a custom/manual entry not in the original teacher list
                                    if current_teacher not in self.config['teachers']:
                                        # Keep custom entries as they might be substitutes or special assignments
                                        pass
                                    else:
                                        # Only clear if it's a standard teacher who can't teach this subject
                                        t_var.set("")
                            else:
                                # If no subject selected, show teachers allowed for this class-section
                                all_allowed_teachers = self.filter_teachers_by_restrictions(
                                    self.config['teachers'], class_, section
                                )
                                t_cb['values'] = [""] + all_allowed_teachers
                        
                        def on_teacher_change(event=None, key=cell_key):
                            self.resolved_cells.add(key)
                            self.impacted_cells.discard(key)
                            if key in self.cell_frames:
                                self.cell_frames[key].configure(style='GreenCell.TFrame')
                        
                        # Bind events
                        subj_cb.bind('<<ComboboxSelected>>', on_subject_change)
                        subj_cb.bind('<KeyRelease>', on_subject_change)  # For manual typing
                        teacher_cb.bind('<FocusOut>', on_teacher_change)
                        teacher_cb.bind('<Return>', on_teacher_change)
                        teacher_cb.bind('<<ComboboxSelected>>', on_teacher_change)
                        col += 1
                row += 1

    def refresh_grid(self):
        # Update the display and scrollbars
        self.grid_frame.update_idletasks()
        self.grid_canvas.configure(scrollregion=self.grid_canvas.bbox("all"))
        
        # Ensure proper canvas sizing for scrolling
        frame_width = self.grid_frame.winfo_reqwidth()
        frame_height = self.grid_frame.winfo_reqheight()
        canvas_width = self.grid_canvas.winfo_width()
        canvas_height = self.grid_canvas.winfo_height()
        
        # Configure scrolling based on content size
        if frame_width > canvas_width or frame_height > canvas_height:
            self.grid_canvas.itemconfig(self.canvas_frame, 
                                       width=max(frame_width, canvas_width),
                                       height=max(frame_height, canvas_height))
        if frame_height > canvas_height:
            self.grid_canvas.itemconfig(self.canvas_frame, height=frame_height)

    def mark_leave(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Teacher Leave Management")
        dialog.geometry("600x500")
        dialog.configure(bg="#f0f4f8")
        
        # Main frame
        main_frame = ttk.Frame(dialog)
        main_frame.pack(fill='both', expand=True, padx=15, pady=15)
        
        # Step 1: Teacher and Day Selection
        selection_frame = ttk.LabelFrame(main_frame, text="Step 1: Select Teacher and Day", padding=15)
        selection_frame.pack(fill='x', pady=(0, 15))
        
        teacher_var = tk.StringVar()
        day_var = tk.StringVar()
        
        ttk.Label(selection_frame, text="Teacher on Leave:", font=('Segoe UI', 10, 'bold')).grid(row=0, column=0, padx=10, pady=8, sticky='w')
        teacher_cb = ttk.Combobox(selection_frame, textvariable=teacher_var, 
                    values=self.config['teachers'], width=25, font=('Segoe UI', 10))
        teacher_cb.grid(row=0, column=1, padx=10, pady=8, sticky='ew')
        
        ttk.Label(selection_frame, text="Day of Leave:", font=('Segoe UI', 10, 'bold')).grid(row=1, column=0, padx=10, pady=8, sticky='w')
        day_cb = ttk.Combobox(selection_frame, textvariable=day_var, 
                    values=self.config['days'], width=25, font=('Segoe UI', 10))
        day_cb.grid(row=1, column=1, padx=10, pady=8, sticky='ew')
        
        # Step 2: Impact Analysis and Teacher Assignment
        impact_frame = ttk.LabelFrame(main_frame, text="Step 2: Impact Analysis & Teacher Assignment", padding=15)
        impact_frame.pack(fill='both', expand=True, pady=(0, 15))
        
        # Impact analysis display
        impact_text = tk.Text(impact_frame, height=8, width=60, wrap=tk.WORD, font=('Consolas', 9))
        impact_scrollbar = ttk.Scrollbar(impact_frame, orient="vertical", command=impact_text.yview)
        impact_text.configure(yscrollcommand=impact_scrollbar.set)
        impact_text.grid(row=0, column=0, columnspan=3, padx=(0, 10), pady=(0, 15), sticky='nsew')
        impact_scrollbar.grid(row=0, column=3, pady=(0, 15), sticky='ns')
        
        # Teacher assignment section
        ttk.Label(impact_frame, text="Assign Substitute Teacher:", font=('Segoe UI', 10, 'bold')).grid(row=1, column=0, padx=5, pady=5, sticky='w')
        substitute_var = tk.StringVar()
        substitute_cb = ttk.Combobox(impact_frame, textvariable=substitute_var, 
                    values=['[Leave Blank]'] + self.config['teachers'], width=25, font=('Segoe UI', 10))
        substitute_cb.set('[Leave Blank]')
        substitute_cb.grid(row=1, column=1, padx=10, pady=5, sticky='ew')
        
        # Store impacted periods for processing
        self.current_impacted_periods = []
        
        def analyze_and_show_impact():
            teacher = teacher_var.get()
            day = day_var.get()
            
            if not teacher or not day:
                impact_text.delete(1.0, tk.END)
                impact_text.insert(tk.END, "⚠️  Please select both teacher and day to see impact analysis.")
                impact_text.configure(fg='orange')
                self.current_impacted_periods = []
                # Reset substitute dropdown to all teachers
                substitute_cb['values'] = ['[Leave Blank]'] + self.config['teachers']
                return
            
            # Find all periods where this teacher is assigned on this day
            impacted_periods = []
            required_subjects = set()
            for (class_, section, d, period), (subj_var, teacher_var_entry) in self.entries.items():
                if d == day and teacher_var_entry.get().strip().lower() == teacher.strip().lower():
                    subject = subj_var.get()
                    if subject:
                        required_subjects.add(subject)
                    impacted_periods.append({
                        'class': class_,
                        'section': section,
                        'day': d,
                        'period': period,
                        'period_num': period + 1,
                        'subject': subject,
                        'key': (class_, section, d, period)
                    })
            
            self.current_impacted_periods = impacted_periods
            
            # Update substitute teacher dropdown - include all teachers for maximum flexibility
            # Don't filter by subject mapping in leave management to allow for emergency assignments
            substitute_cb['values'] = ['[Leave Blank]'] + [t for t in self.config['teachers'] if t != teacher]
            
            # Display impact analysis
            impact_text.delete(1.0, tk.END)
            impact_text.configure(fg='black')
            
            if impacted_periods:
                impact_text.insert(tk.END, f"🔍 IMPACT ANALYSIS\n")
                impact_text.insert(tk.END, "="*50 + "\n\n")
                impact_text.insert(tk.END, f"👨‍🏫 Teacher: {teacher}\n")
                impact_text.insert(tk.END, f"📅 Day: {day}\n")
                impact_text.insert(tk.END, f"⚠️  Total Periods Affected: {len(impacted_periods)}\n")
                if required_subjects:
                    impact_text.insert(tk.END, f"📚 Subjects to Cover: {', '.join(sorted(required_subjects))}\n")
                impact_text.insert(tk.END, "\n📋 AFFECTED PERIODS:\n")
                impact_text.insert(tk.END, "-" * 40 + "\n")
                
                for i, period_info in enumerate(impacted_periods, 1):
                    impact_text.insert(tk.END, f"{i:2d}. {period_info['class']:8s} - {period_info['section']:3s} | "
                                             f"Period {period_info['period_num']} | {period_info['subject']}\n")
                
                impact_text.insert(tk.END, "\n" + "="*50 + "\n")
                impact_text.insert(tk.END, f"💡 ACTION REQUIRED:\n")
                impact_text.insert(tk.END, f"   • Select a substitute teacher from dropdown below\n")
                impact_text.insert(tk.END, f"   • OR leave blank to mark periods as unassigned\n")
                impact_text.insert(tk.END, f"   • Click 'Process Leave' to apply changes\n")
            else:
                impact_text.insert(tk.END, f"✅ NO IMPACT FOUND\n\n")
                impact_text.insert(tk.END, f"👨‍🏫 Teacher: {teacher}\n")
                impact_text.insert(tk.END, f"📅 Day: {day}\n\n")
                impact_text.insert(tk.END, f"ℹ️  {teacher} is not assigned to any periods on {day}.\n")
                impact_text.insert(tk.END, f"   No action needed.")
                impact_text.configure(fg='green')
        
        # Bind change events to update impact analysis
        teacher_cb.bind('<<ComboboxSelected>>', lambda e: analyze_and_show_impact())
        day_cb.bind('<<ComboboxSelected>>', lambda e: analyze_and_show_impact())
        teacher_cb.bind('<KeyRelease>', lambda e: dialog.after(500, analyze_and_show_impact))
        day_cb.bind('<KeyRelease>', lambda e: dialog.after(500, analyze_and_show_impact))
        
        # Step 3: Action Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=(10, 0))
        
        def process_teacher_leave():
            teacher = teacher_var.get()
            day = day_var.get()
            substitute = substitute_var.get()
            
            if not teacher or not day:
                messagebox.showerror("Error", "Please select both teacher and day")
                return
            
            if not self.current_impacted_periods:
                messagebox.showinfo("No Changes", f"{teacher} is not assigned to any periods on {day}")
                dialog.destroy()
                return
            
            # Process the leave
            substitute_teacher = substitute if substitute != '[Leave Blank]' else ""
            processed_assignments = []
            
            for period_info in self.current_impacted_periods:
                key = period_info['key']
                if key in self.entries:
                    subj_var, teacher_var_entry = self.entries[key]
                    
                    # Update teacher assignment
                    old_assignment = f"{period_info['class']}-{period_info['section']} P{period_info['period_num']} ({period_info['subject']})"
                    teacher_var_entry.set(substitute_teacher)
                    
                    # Mark cell as impacted (red color)
                    self.impacted_cells.add(key)
                    self.resolved_cells.discard(key)
                    if key in self.cell_frames:
                        self.cell_frames[key].configure(style='RedCell.TFrame')
                    
                    new_teacher_text = substitute_teacher if substitute_teacher else "[UNASSIGNED]"
                    processed_assignments.append(f"{old_assignment} → {new_teacher_text}")
            
            # Show confirmation
            result_message = f"✅ Teacher leave processed successfully!\n\n"
            result_message += f"👨‍🏫 Teacher on Leave: {teacher}\n"
            result_message += f"📅 Day: {day}\n"
            result_message += f"🔄 Periods Updated: {len(processed_assignments)}\n\n"
            
            if substitute_teacher:
                result_message += f"🆕 Substitute Teacher: {substitute_teacher}\n\n"
            else:
                result_message += f"⚠️  Periods marked as UNASSIGNED\n\n"
            
            result_message += "📋 CHANGES MADE:\n"
            for assignment in processed_assignments[:8]:  # Show first 8 changes
                result_message += f"  • {assignment}\n"
            
            if len(processed_assignments) > 8:
                result_message += f"  ... and {len(processed_assignments) - 8} more"
            
            messagebox.showinfo("Leave Processed", result_message)
            dialog.destroy()
        
        # Buttons
        ttk.Button(button_frame, text="🔍 Refresh Analysis", command=analyze_and_show_impact).pack(side='left', padx=5)
        ttk.Button(button_frame, text="✅ Process Leave", command=process_teacher_leave, 
                  style='Accent.TButton').pack(side='left', padx=10)
        ttk.Button(button_frame, text="❌ Cancel", command=dialog.destroy).pack(side='right', padx=5)
        
        # Add Hypersync footer
        footer_frame = ttk.Frame(main_frame)
        footer_frame.pack(fill='x', pady=(10, 0))
        
        footer_label = ttk.Label(footer_frame, text="Hypersync - An AI based education startup", 
                                font=("Segoe UI", 9), foreground="#666666")
        footer_label.pack(anchor='center')
        
        # Configure grid weights for responsive design
        selection_frame.columnconfigure(1, weight=1)
        impact_frame.columnconfigure(0, weight=1)
        impact_frame.rowconfigure(0, weight=1)
        
        # Initial focus and analysis
        teacher_cb.focus_set()
        dialog.after(100, analyze_and_show_impact)

    def save_timetable(self):
        year = self.selected_year.get()
        week = self.selected_week.get()
        
        # Clear old data
        self.c.execute("DELETE FROM timetable WHERE year=? AND week=?", (year, week))
        
        # Save current grid
        for (class_, section, day, period), (subj_var, teacher_var) in self.entries.items():
            if subj_var.get() and teacher_var.get():  # Only save filled cells
                self.c.execute('''
                    INSERT INTO timetable (year, week, class, section, day, period, subject, teacher)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (year, week, class_, section, day, period, subj_var.get(), teacher_var.get()))
                
        self.conn.commit()
        messagebox.showinfo("Success", "Timetable saved")

    def load_timetable(self):
        year = self.selected_year.get()
        week = self.selected_week.get()
        
        # Ensure grid is drawn first
        if not hasattr(self, 'entries') or not self.entries:
            self.draw_grid()
        
        # Clear grid
        for _, (subj_var, teacher_var) in self.entries.items():
            subj_var.set('')
            teacher_var.set('')
            
        # Load saved data
        try:
            self.c.execute('''
                SELECT class, section, day, period, subject, teacher 
                FROM timetable 
                WHERE year=? AND week=?
            ''', (year, week))
            
            rows_loaded = 0
            for row in self.c.fetchall():
                class_, section, day, period, subject, teacher = row
                key = (class_, section, day, period)
                if key in self.entries:
                    self.entries[key][0].set(subject or '')
                    self.entries[key][1].set(teacher or '')
                    
                    # Update teacher dropdown based on loaded subject
                    if key in self.teacher_cbs and subject:
                        teacher_cb = self.teacher_cbs[key]
                        teacher_subjects = self.config.get('teacher_subjects', {})
                        if teacher_subjects:
                            available_teachers = [t for t, subjs in teacher_subjects.items() if subject in subjs]
                        else:
                            available_teachers = self.config['teachers']
                        teacher_cb['values'] = [""] + available_teachers
                    
                    rows_loaded += 1
            
            if rows_loaded > 0:
                messagebox.showinfo("Success", f"Loaded timetable for Year {year}, Week {week}\n{rows_loaded} entries loaded.")
            else:
                messagebox.showinfo("No Data", f"No saved timetable found for Year {year}, Week {week}")
                
        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load timetable:\n{str(e)}")
            print(f"Load error: {e}")

    def auto_assign(self):
        # Auto-assign both subjects and teachers for all periods
        teacher_subjects = self.config.get('teacher_subjects', {})
        subjects = self.config['subjects']
        teachers = self.config['teachers']
        
        # Get all available teachers (combine main list with teacher_subjects keys)
        all_teachers = list(set(teachers + list(teacher_subjects.keys())))
        
        # If no teacher mapping exists, create default mapping where all teachers can teach all subjects
        if not teacher_subjects:
            teacher_subjects = {teacher: subjects for teacher in all_teachers}
        
        filled_count = 0
        total_cells = len(self.config['classes']) * len(self.config['sections']) * len(self.config['days']) * self.config['periods_per_day']
        
        # Ensure entries exist first
        if not hasattr(self, 'entries') or not self.entries:
            self.draw_grid()
            
        for day in self.config['days']:
            for period in range(self.config['periods_per_day']):
                used_teachers = set()
                class_section_index = 0
                for idx_class, class_ in enumerate(self.config['classes']):
                    for idx_section, section in enumerate(self.config['sections']):
                        key = (class_, section, day, period)
                        if key in self.entries:
                            subj_var, teacher_var = self.entries[key]
                            
                            # Assign subject in a round-robin way
                            subject = subjects[(period + idx_class + idx_section) % len(subjects)]
                            subj_var.set(subject)
                            
                            # Update teacher dropdown for this subject
                            if key in self.teacher_cbs:
                                teacher_cb = self.teacher_cbs[key]
                                # Filter teachers based on subject
                                available_teachers_for_subject = [t for t in all_teachers if subject in teacher_subjects.get(t, [])]
                                if not available_teachers_for_subject:
                                    available_teachers_for_subject = all_teachers  # Fallback to all teachers
                                
                                # Further filter by class-section restrictions
                                available_teachers_for_subject = self.filter_teachers_by_restrictions(
                                    available_teachers_for_subject, class_, section
                                )
                                
                                # Update dropdown values
                                teacher_cb['values'] = [""] + available_teachers_for_subject
                            
                            # Find available teacher for this subject not already used in this period
                            available_teachers = [t for t in all_teachers if subject in teacher_subjects.get(t, []) and t not in used_teachers]
                            
                            # Further filter by class-section restrictions
                            available_teachers = self.filter_teachers_by_restrictions(
                                available_teachers, class_, section
                            )
                            
                            # If no mapped teacher available, use any available teacher
                            if not available_teachers:
                                all_available_for_class = self.filter_teachers_by_restrictions(
                                    [t for t in all_teachers if t not in used_teachers], class_, section
                                )
                                available_teachers = all_available_for_class
                            
                            # If still no teacher available, reuse teachers with better distribution
                            if not available_teachers:
                                # Use teachers allowed for this class-section in round-robin fashion
                                allowed_teachers = self.filter_teachers_by_restrictions(all_teachers, class_, section)
                                if not allowed_teachers:
                                    allowed_teachers = all_teachers  # Ultimate fallback
                                teacher_index = class_section_index % len(allowed_teachers)
                                assigned_teacher = allowed_teachers[teacher_index]
                            else:
                                # Use first available teacher
                                assigned_teacher = available_teachers[0]
                            
                            teacher_var.set(assigned_teacher)
                            if assigned_teacher:
                                used_teachers.add(assigned_teacher)
                            filled_count += 1
                            class_section_index += 1
        
        # Update the display
        self.grid_frame.update_idletasks()
        self.grid_canvas.configure(scrollregion=self.grid_canvas.bbox("all"))
        messagebox.showinfo("Success", f"Auto-assign completed!\nFilled {filled_count} out of {total_cells} timetable slots")

    def smart_match(self):
        # Validate that no teacher is assigned to more than one subject at the same time (case-insensitive)
        periods = self.config['periods_per_day']
        days = self.config['days']
        classes = self.config['classes']
        sections = self.config['sections']
        conflicts = []
        for day in days:
            for period in range(periods):
                teacher_slots = {}
                for class_ in classes:
                    for section in sections:
                        key = (class_, section, day, period)
                        if key in self.entries:
                            subj_var, teacher_var = self.entries[key]
                            teacher = teacher_var.get().strip().lower()
                            subject = subj_var.get().strip()
                            if teacher:
                                if teacher not in teacher_slots:
                                    teacher_slots[teacher] = []
                                teacher_slots[teacher].append((class_, section, subject))
                for teacher, slots in teacher_slots.items():
                    if len(slots) > 1:
                        conflict_str = f"Teacher '{teacher}' assigned to multiple subjects on {day} Period {period+1}: "
                        conflict_str += ", ".join([f"{c} {s} ({subj})" for c, s, subj in slots])
                        conflicts.append(conflict_str)
        if conflicts:
            messagebox.showerror("Smart Match - Conflicts Found", "\n".join(conflicts))
        else:
            messagebox.showinfo("Smart Match", "No teacher is assigned to more than one subject at the same time. All good!")

    def edit_classes(self):
        self.edit_list('classes', 'Edit Classes (comma separated):')

    def edit_sections(self):
        self.edit_list('sections', 'Edit Sections (comma separated):')

    def edit_teachers(self):
        self.edit_list('teachers', 'Edit Teachers (comma separated):')

    def edit_list(self, key, prompt):
        current = ', '.join(self.config[key])
        result = simpledialog.askstring('Edit', prompt, initialvalue=current)
        if result is not None:
            self.config[key] = [x.strip() for x in result.split(',') if x.strip()]
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=2)
            self.draw_grid()

    def export_excel(self):
        # Lazy load pandas only when needed
        pd = lazy_import_pandas()
        if pd is None:
            return
            
        file = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
        )
        if not file:
            return
        
        try:
            # Create Excel writer object
            with pd.ExcelWriter(file, engine='openpyxl') as writer:
                # Create a worksheet for each class
                for class_ in self.config['classes']:
                    # Create timetable data for this class
                    periods = list(range(1, self.config['periods_per_day'] + 1))
                    days = self.config['days']
                    sections = self.config['sections']
                    
                    # Create a DataFrame with days as rows and periods as columns
                    class_data = {}
                    
                    # Initialize the structure
                    for day in days:
                        class_data[day] = {}
                        for period in periods:
                            class_data[day][f'Period {period}'] = []
                    
                    # Fill data for all sections of this class
                    for section in sections:
                        for day in days:
                            for period_idx in range(self.config['periods_per_day']):
                                key = (class_, section, day, period_idx)
                                if key in self.entries:
                                    subj_var, teacher_var = self.entries[key]
                                    subject = subj_var.get() or ""
                                    teacher = teacher_var.get() or ""
                                    entry = f"{section}: {subject}"
                                    if teacher:
                                        entry += f" ({teacher})"
                                    class_data[day][f'Period {period_idx + 1}'].append(entry)
                                else:
                                    class_data[day][f'Period {period_idx + 1}'].append(f"{section}: -")
                    
                    # Convert to DataFrame format
                    df_data = []
                    for day in days:
                        row = {'Day': day}
                        for period in periods:
                            period_key = f'Period {period}'
                            # Join all sections for this period
                            row[period_key] = '\n'.join(class_data[day][period_key])
                        df_data.append(row)
                    
                    df = pd.DataFrame(df_data)
                    
                    # Write to Excel with proper formatting
                    sheet_name = class_.replace('/', '_').replace('\\', '_')[:31]  # Excel sheet name limit
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
                    
                    # Get the worksheet to apply formatting
                    worksheet = writer.sheets[sheet_name]
                    
                    # Auto-adjust column widths
                    for column in worksheet.columns:
                        max_length = 0
                        column = [cell for cell in column]
                        for cell in column:
                            try:
                                if len(str(cell.value)) > max_length:
                                    max_length = len(str(cell.value))
                            except:
                                pass
                        adjusted_width = min(max_length + 2, 50)
                        worksheet.column_dimensions[column[0].column_letter].width = adjusted_width
                    
                    # Set row height for better readability
                    for row in worksheet.iter_rows():
                        worksheet.row_dimensions[row[0].row].height = 60
            
            messagebox.showinfo("Success", f"Excel exported successfully!\nEach class has its own worksheet.\nFile: {file}")
            
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export Excel:\n{str(e)}")
            return

    def show_teacher_subject_mapping(self):
        # Show a dialog to edit teacher-subject mapping
        mapping = self.config.get('teacher_subjects', {})
        win = tk.Toplevel(self.root)
        win.title("Edit Teacher-Subject Mapping")
        win.geometry("600x500")
        win.resizable(True, True)
        
        # Main frame
        main_frame = ttk.Frame(win)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Instructions
        instruction_label = ttk.Label(main_frame, 
            text="Enter subjects each teacher can teach (comma separated):", 
            font=("Segoe UI", 10, "bold"))
        instruction_label.pack(anchor='w', pady=(0, 10))
        
        # Create scrollable frame
        canvas = tk.Canvas(main_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Teacher entries
        teacher_vars = {}
        row = 0
        for teacher in self.config['teachers']:
            # Teacher name label
            teacher_label = ttk.Label(scrollable_frame, text=f"{teacher}:", 
                                    font=("Segoe UI", 10, "bold"))
            teacher_label.grid(row=row, column=0, sticky='w', padx=5, pady=5)
            
            # Subjects entry
            subjects_var = tk.StringVar(value=','.join(mapping.get(teacher, [])))
            teacher_vars[teacher] = subjects_var
            entry = ttk.Entry(scrollable_frame, textvariable=subjects_var, width=50)
            entry.grid(row=row, column=1, padx=5, pady=5, sticky='ew')
            
            # Configure grid weights
            scrollable_frame.grid_columnconfigure(1, weight=1)
            
            row += 1
        
        # Button frame at bottom
        button_frame = ttk.Frame(win)
        button_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        # Add Hypersync footer
        footer_frame = ttk.Frame(win)
        footer_frame.pack(fill='x', padx=10, pady=(5, 0))
        
        footer_label = ttk.Label(footer_frame, text="Hypersync - An AI based education startup", 
                                font=("Segoe UI", 9), foreground="#666666")
        footer_label.pack(anchor='center')
        
        def save_and_close():
            # Update mapping from all teacher variables
            for teacher, var in teacher_vars.items():
                mapping[teacher] = [s.strip() for s in var.get().split(',') if s.strip()]
            
            self.config['teacher_subjects'] = mapping
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=2)
            win.destroy()
            messagebox.showinfo("Success", "Teacher-subject mapping saved successfully!")
        
        def cancel():
            win.destroy()
        
        # Buttons
        ttk.Button(button_frame, text="Save & Close", command=save_and_close, 
                  style='Green.TButton').pack(side='right', padx=5)
        ttk.Button(button_frame, text="Cancel", command=cancel).pack(side='right', padx=5)
        
        # Enable mouse wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Focus on window
        win.focus_set()
        win.grab_set()  # Make window modal

    def show_teacher_restrictions(self):
        """Show a dialog to manage teacher class-section restrictions"""
        win = tk.Toplevel(self.root)
        win.title("Teacher Class-Section Restrictions")
        win.geometry("900x700")
        win.resizable(True, True)
        
        # Main frame
        main_frame = ttk.Frame(win)
        main_frame.pack(fill='both', expand=True, padx=15, pady=15)
        
        # Title header
        title_label = ttk.Label(main_frame, 
            text="🎯 Teacher Class-Section Restrictions", 
            font=("Segoe UI", 16, "bold"),
            foreground="#2d6cdf")
        title_label.pack(anchor='w', pady=(0, 10))
        
        # Instructions
        instruction_label = ttk.Label(main_frame, 
            text="Configure which classes and sections each teacher can teach. Click on teacher tabs below:", 
            font=("Segoe UI", 11),
            foreground="#555555")
        instruction_label.pack(anchor='w', pady=(0, 15))
        
        # Create notebook for teachers with better styling
        style = ttk.Style()
        style.configure('Teacher.TNotebook.Tab', padding=[20, 8])
        
        notebook = ttk.Notebook(main_frame, style='Teacher.TNotebook')
        notebook.pack(fill='both', expand=True, pady=(0, 15))
        
        # Store teacher restriction data
        teacher_restrictions = {}
        
        # Load existing restrictions from database
        self.c.execute("SELECT teacher, class, section FROM teacher_restrictions")
        existing_restrictions = {}
        for teacher, class_name, section in self.c.fetchall():
            if teacher not in existing_restrictions:
                existing_restrictions[teacher] = []
            existing_restrictions[teacher].append((class_name, section))
        
        # Create tab for each teacher
        for teacher in self.config['teachers']:
            # Check if teacher has existing restrictions
            has_restrictions = teacher in existing_restrictions and len(existing_restrictions[teacher]) > 0
            tab_text = f"👨‍🏫 {teacher}" if has_restrictions else f"🆕 {teacher}"
            
            # Teacher frame
            teacher_frame = ttk.Frame(notebook)
            notebook.add(teacher_frame, text=tab_text)
            
            # Create scrollable frame for this teacher
            canvas = tk.Canvas(teacher_frame, highlightthickness=0)
            scrollbar = ttk.Scrollbar(teacher_frame, orient="vertical", command=canvas.yview)
            scrollable_frame = ttk.Frame(canvas)
            
            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            
            # Pack canvas and scrollbar
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
            # Teacher name header - make it prominent
            teacher_header = ttk.Label(scrollable_frame, 
                text=f"🧑‍🏫 Teacher: {teacher}",
                font=("Segoe UI", 14, "bold"),
                foreground="#2d6cdf")
            teacher_header.pack(anchor='w', pady=(10, 5), padx=10)
            
            # Status indicator
            existing_for_teacher = existing_restrictions.get(teacher, [])
            if existing_for_teacher:
                status_text = f"✅ Current Status: {len(existing_for_teacher)} class-section combinations allowed"
                status_color = "#28a745"
            else:
                status_text = "ℹ️ Current Status: No restrictions (can teach any class-section)"
                status_color = "#6c757d"
            
            status_label = ttk.Label(scrollable_frame,
                text=status_text,
                font=("Segoe UI", 9),
                foreground=status_color)
            status_label.pack(anchor='w', pady=(0, 5), padx=10)
            
            # Separator line
            separator = ttk.Separator(scrollable_frame, orient='horizontal')
            separator.pack(fill='x', pady=(5, 10), padx=10)
            
            # Instructions for this teacher
            teacher_instruction = ttk.Label(scrollable_frame, 
                text=f"Select the classes and sections that {teacher} is allowed to teach:",
                font=("Segoe UI", 10),
                foreground="#333333")
            teacher_instruction.pack(anchor='w', pady=(0, 15), padx=10)
            
            # Create checkboxes for each class-section combination
            teacher_restrictions[teacher] = {}
            existing_for_teacher = existing_restrictions.get(teacher, [])
            
            for class_name in self.config['classes']:
                # Class frame with better styling
                class_frame = ttk.LabelFrame(scrollable_frame, 
                    text=f"📚 {class_name}", 
                    padding=10)
                class_frame.pack(fill='x', pady=8, padx=15)
                
                # Section checkboxes with better layout
                section_frame = ttk.Frame(class_frame)
                section_frame.pack(fill='x')
                
                # Add a label for sections
                section_label = ttk.Label(section_frame, 
                    text="Allowed Sections:", 
                    font=("Segoe UI", 9, "bold"))
                section_label.pack(anchor='w', pady=(0, 5))
                
                # Create a grid layout for sections
                checkbox_frame = ttk.Frame(section_frame)
                checkbox_frame.pack(fill='x')
                
                col = 0
                for section in self.config['sections']:
                    var = tk.BooleanVar()
                    # Check if this combination exists in restrictions
                    if (class_name, section) in existing_for_teacher:
                        var.set(True)
                    
                    cb = ttk.Checkbutton(checkbox_frame, 
                        text=f"Section {section}", 
                        variable=var,
                        style='TCheckbutton')
                    cb.grid(row=0, column=col, sticky='w', padx=15, pady=2)
                    col += 1
                    
                    # Store the variable
                    if class_name not in teacher_restrictions[teacher]:
                        teacher_restrictions[teacher][class_name] = {}
                    teacher_restrictions[teacher][class_name][section] = var
            
            # Enable mouse wheel scrolling for this canvas
            def make_scroll_handler(canvas):
                def _on_mousewheel(event):
                    canvas.yview_scroll(int(-1*(event.delta/120)), "units")
                return _on_mousewheel
            
            scroll_handler = make_scroll_handler(canvas)
            canvas.bind_all("<MouseWheel>", scroll_handler)
        
        # Button frame at bottom
        button_frame = ttk.Frame(win)
        button_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        # Add Hypersync footer
        footer_frame = ttk.Frame(win)
        footer_frame.pack(fill='x', padx=10, pady=(5, 0))
        
        footer_label = ttk.Label(footer_frame, text="Hypersync - An AI based education startup", 
                                font=("Segoe UI", 9), foreground="#666666")
        footer_label.pack(anchor='center')
        
        def save_restrictions():
            """Save teacher restrictions to database"""
            try:
                # Clear existing restrictions
                self.c.execute("DELETE FROM teacher_restrictions")
                
                # Insert new restrictions
                for teacher in teacher_restrictions:
                    for class_name in teacher_restrictions[teacher]:
                        for section in teacher_restrictions[teacher][class_name]:
                            if teacher_restrictions[teacher][class_name][section].get():
                                self.c.execute(
                                    "INSERT INTO teacher_restrictions (teacher, class, section) VALUES (?, ?, ?)",
                                    (teacher, class_name, section)
                                )
                
                self.conn.commit()
                win.destroy()
                messagebox.showinfo("Success", "Teacher restrictions saved successfully!")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save restrictions: {str(e)}")
        
        def cancel():
            win.destroy()
        
        # Buttons
        ttk.Button(button_frame, text="Save & Close", command=save_restrictions, 
                  style='Green.TButton').pack(side='right', padx=5)
        ttk.Button(button_frame, text="Cancel", command=cancel).pack(side='right', padx=5)
        
        # Focus on window
        win.focus_set()
        win.grab_set()  # Make window modal

if __name__ == "__main__":
    print("Launching Timetable Planner...")
    try:
        root = tk.Tk()
        app = TimetableApp(root)
        root.mainloop()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
