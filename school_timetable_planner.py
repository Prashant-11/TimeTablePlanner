# School Timetable Planner
# Requirements: tkinter, sqlite3, pandas, openpyxl (for Excel export)

import sys
print("Starting application...")

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import sqlite3
import json
import os
import pandas as pd
import calendar
from datetime import datetime

DB_FILE = 'timetable.db'
CONFIG_FILE = 'config.json'

# Initialize empty sets for tracking impacted and resolved cells
IMPACTED_CELLS = set()  # (class, section, day, period)
RESOLVED_CELLS = set()  # (class, section, day, period)

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import sqlite3
import json
import os
import pandas as pd
import calendar
from datetime import datetime

DB_FILE = 'timetable.db'
CONFIG_FILE = 'config.json'

# Helper to get group for a class
def get_class_group(config, class_name):
    groups = config.get('groups', [])
    for group in groups:
        if class_name in group.get('classes', []):
            return group
    return None

# Initialize empty sets for tracking impacted and resolved cells
IMPACTED_CELLS = set()  # (class, section, day, period)
RESOLVED_CELLS = set()  # (class, section, day, period)

# Default config
DEFAULT_CONFIG = {
    "classes": [f"Class {i+1}" for i in range(10)],
    "sections": ["A", "B", "C", "D"],
    "subjects": ["Math", "Science", "English", "History", "Geography"],
    "teachers": ["Teacher 1", "Teacher 2", "Teacher 3", "Teacher 4"],
    "periods_per_day": 7,
    "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
}

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    else:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(DEFAULT_CONFIG, f, indent=2)
        return DEFAULT_CONFIG

CONFIG = load_config()

# Database setup
conn = sqlite3.connect(DB_FILE)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS timetable (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    class TEXT,
    section TEXT,
    day TEXT,
    period INTEGER,
    subject TEXT,
    teacher TEXT
)''')
conn.commit()


class TimetableApp:
    def smart_match(self):
        # Validate that no teacher is assigned to more than one subject at the same time
        periods = self.config['periods_per_day']
        days = [calendar.day_name[i] for i in range(5)]
        classes = self.config['classes']
        sections = self.config['sections']
        conflicts = []
        for d in days:
            for p in range(periods):
                teacher_slots = {}
                for class_ in classes:
                    for section in sections:
                        key = (class_, section, d, p)
                        if key in self.entries:
                            subj_var, teacher_var = self.entries[key]
                            teacher = teacher_var.get().strip()
                            subject = subj_var.get().strip()
                            if teacher:
                                if teacher not in teacher_slots:
                                    teacher_slots[teacher] = []
                                teacher_slots[teacher].append((class_, section, subject))
                for teacher, slots in teacher_slots.items():
                    if len(slots) > 1:
                        conflict_str = f"Teacher '{teacher}' assigned to multiple subjects at {d} Period {p+1}: "
                        conflict_str += ", ".join([f"{c} {s} ({subj})" for c, s, subj in slots])
                        conflicts.append(conflict_str)
        if conflicts:
            messagebox.showerror("Smart Match - Conflicts Found", "\n".join(conflicts))
        else:
            messagebox.showinfo("Smart Match", "No teacher is assigned to more than one subject at the same time. All good!")
    def auto_assign_week(self):
        # Auto-assign teachers for the week based on subject mapping and availability
        days = [calendar.day_name[i] for i in range(5)]
        periods = self.config['periods_per_day']
        subjects = self.config['subjects']
        teachers = self.config['teachers']
        teacher_subjects = self.config.get('teacher_subjects', {})
        assignments = []
        for d in days:
            for p in range(periods):
                used_teachers = set()
                for class_ in self.config['classes']:
                    for section in self.config['sections']:
                        key = (class_, section, d, p)
                        subject = subjects[p % len(subjects)]
                        available_teachers = [t for t in teachers if subject in teacher_subjects.get(t, []) and t not in used_teachers]
                        assigned_teacher = available_teachers[0] if available_teachers else ""
                        assignments.append((class_, section, d, p, subject, assigned_teacher))
                        if assigned_teacher:
                            used_teachers.add(assigned_teacher)
        # Save assignments to DB
        year = self.selected_year.get()
        week = self.selected_week.get()
        c.execute("DELETE FROM timetable WHERE day LIKE ?", (f"{year}-W{week:02d}-%",))
        for class_, section, d, p, subject, teacher in assignments:
            if subject and teacher:
                c.execute("INSERT INTO timetable (class, section, day, period, subject, teacher) VALUES (?, ?, ?, ?, ?, ?)",
                          (class_, section, f"{year}-W{week:02d}-{d}", p, subject, teacher))
        conn.commit()
        self.load_timetable()
        messagebox.showinfo("Success", "Teachers auto-assigned for the week (subject mapping enforced)")

    def edit_classes(self):
        self.edit_list('classes', 'Edit Classes (comma separated):')

    def edit_sections(self):
        self.edit_list('sections', 'Edit Sections (comma separated):')

    def edit_teachers(self):
        self.edit_list('teachers', 'Edit Teachers (comma separated):')

    def edit_subjects(self):
        self.edit_list('subjects', 'Edit Subjects (comma separated):')

    def edit_list(self, key, prompt):
        current = ', '.join(self.config[key])
        result = simpledialog.askstring('Edit', prompt, initialvalue=current)
        if result is not None:
            self.config[key] = [x.strip() for x in result.split(',') if x.strip()]
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=2)
            self.draw_grid()
    def save_week_history(self, year, week, week_data):
        import glob
        hist_dir = os.path.join(os.getcwd(), "history")
        if not os.path.exists(hist_dir):
            os.makedirs(hist_dir)
        fname = os.path.join(hist_dir, f"timetable_{year}-W{week:02d}.json")
        with open(fname, "w") as f:
            json.dump(week_data, f, indent=2)
        # Keep only last 2 weeks
        files = sorted(glob.glob(os.path.join(hist_dir, "timetable_*.json")), reverse=True)
        if len(files) > 2:
            for oldf in files[2:]:
                try:
                    os.remove(oldf)
                except Exception:
                    pass

    def export_previous_week(self):
        import glob
        hist_dir = os.path.join(os.getcwd(), "history")
        year = self.selected_year.get()
        week = self.selected_week.get()
        # Calculate previous week (handle year change)
        if week == 1:
            prev_year = year - 1
            prev_week = 52  # crude, for most years
        else:
            prev_year = year
            prev_week = week - 1
        fname = os.path.join(hist_dir, f"timetable_{prev_year}-W{prev_week:02d}.json")
        if not os.path.exists(fname):
            messagebox.showerror("Not Found", f"No history found for previous week {prev_year}-W{prev_week:02d}")
            return
        with open(fname, "r") as f:
            week_data = json.load(f)
        # Export as Excel
        df = pd.DataFrame(week_data)
        file = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")], title="Export Previous Week")
        if file:
            with pd.ExcelWriter(file) as writer:
                for (class_, section), subdf in df.groupby(["class", "section"]):
                    pivot = subdf.pivot(index="day", columns="period", values=["subject", "teacher"])
                    pivot.columns = [f"P{col[1]+1} {col[0]}" for col in pivot.columns]
                    pivot.reset_index(inplace=True)
                    pivot.to_excel(writer, sheet_name=f"{class_}-{section}", index=False)
            messagebox.showinfo("Exported", f"Previous week timetable exported to {file}")
    def __init__(self, root):
        self.root = root
        self.root.title("School Weekly Timetable Planner")
        self.root.geometry("1200x700")
        self.config = CONFIG
        self.selected_week = tk.IntVar(value=datetime.now().isocalendar()[1])
        self.selected_year = tk.IntVar(value=datetime.now().year)
        self.impacted_cells = IMPACTED_CELLS
        self.resolved_cells = RESOLVED_CELLS
        self.entries = {}
        self.style = ttk.Style()
        self._set_theme()
        self.setup_ui()
        self.load_timetable()
    def show_teacher_subject_mapping(self):
        mapping = self.config.get('teacher_subjects', {})
        all_subjects = self.config.get('subjects', [])
        win = tk.Toplevel(self.root)
        win.title("Edit Teacher-Subject Mapping")
        win.geometry("500x600")
        frame = ttk.Frame(win)
        frame.pack(fill='both', expand=True, padx=10, pady=10)
        canvas = tk.Canvas(frame)
        scroll = ttk.Scrollbar(frame, orient='vertical', command=canvas.yview)
        scroll.pack(side='right', fill='y')
        canvas.pack(side='left', fill='both', expand=True)
        inner = ttk.Frame(canvas)
        canvas.create_window((0,0), window=inner, anchor='nw')
        canvas.configure(yscrollcommand=scroll.set)
        teacher_vars = {}
        def on_configure(event):
            canvas.configure(scrollregion=canvas.bbox('all'))
        inner.bind('<Configure>', on_configure)
        row = 0
        for teacher in self.config.get('teachers', []):
            ttk.Label(inner, text=teacher, font=("Segoe UI", 10, "bold")).grid(row=row, column=0, sticky='w', pady=2)
            var = tk.StringVar(value=", ".join(mapping.get(teacher, [])))
            entry = ttk.Entry(inner, textvariable=var, width=40)
            entry.grid(row=row, column=1, sticky='w', padx=5)
            teacher_vars[teacher] = var
            row += 1
        def save_mapping():
            new_mapping = {}
            for teacher, var in teacher_vars.items():
                # Split by comma, strip whitespace, only allow valid subjects
                subjects = [s.strip() for s in var.get().split(',') if s.strip() and s.strip() in all_subjects]
                new_mapping[teacher] = subjects
            self.config['teacher_subjects'] = new_mapping
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=2)
            self.draw_grid()
            messagebox.showinfo("Saved", "Teacher-subject mapping updated.")
            win.destroy()
        btn_frame = ttk.Frame(win)
        btn_frame.pack(fill='x', pady=5)
        ttk.Button(btn_frame, text="Save", command=save_mapping).pack(side='left', padx=10)
        ttk.Button(btn_frame, text="Close", command=win.destroy).pack(side='right', padx=10)
    def mark_teacher_on_leave(self):
        # Always reload config to get latest teachers
        self.config = load_config()
        teachers = self.config.get('teachers', [])
        if not teachers:
            messagebox.showerror("Error", "No teachers found in config. Please add teachers first.")
            return
        days = [calendar.day_name[i] for i in range(5)]
        leave_win = tk.Toplevel(self.root)
        leave_win.title("Mark Teacher On Leave")
        ttk.Label(leave_win, text="Select Teacher:").grid(row=0, column=0, padx=5, pady=5)
        teacher_var = tk.StringVar()
        teacher_cb = ttk.Combobox(leave_win, textvariable=teacher_var, values=teachers, state='readonly')
        teacher_cb.grid(row=0, column=1, padx=5, pady=5)
        if teachers:
            teacher_var.set(teachers[0])
        ttk.Label(leave_win, text="Select Day:").grid(row=1, column=0, padx=5, pady=5)
        day_var = tk.StringVar()
        day_cb = ttk.Combobox(leave_win, textvariable=day_var, values=days, state='readonly')
        day_cb.grid(row=1, column=1, padx=5, pady=5)
        if days:
            day_var.set(days[0])
        def process_leave():
            teacher = teacher_var.get()
            day = day_var.get()
            if not teacher or not day:
                messagebox.showerror("Error", "Please select both teacher and day.")
                return
            self.export_impacted_classes(teacher, day)
            leave_win.destroy()
        ttk.Button(leave_win, text="Export Impacted Classes", command=process_leave).grid(row=2, column=0, columnspan=2, pady=10)

    def export_impacted_classes(self, teacher, day):
        # Find all slots for this teacher on this day, and allow manual reassignment with conflict check
        year = self.selected_year.get()
        week = self.selected_week.get()
        classes = self.config['classes']
        sections = self.config['sections']
        periods = self.config['periods_per_day']
        teacher_subjects = self.config.get('teacher_subjects', {})
        impacted = []
        for class_ in classes:
            for section in sections:
                for p in range(periods):
                    subj_var, teacher_var = self.entries[(class_, section, day, p)]
                    if teacher_var.get() == teacher:
                        subject = subj_var.get()
                        # Clear the teacher field and highlight red
                        teacher_var.set("")
                        key = (class_, section, day, p)
                        self.impacted_cells.add(key)
                        if hasattr(self, 'cell_frames') and key in self.cell_frames:
                            self.cell_frames[key].configure(bg='#ffcccc')
                        impacted.append({
                            'class': class_,
                            'section': section,
                            'period': p,
                            'subject': subject,
                            'old_teacher': teacher,
                            'subj_var': subj_var,
                            'teacher_var': teacher_var
                        })
        self.draw_grid()
        if not impacted:
            messagebox.showinfo("No Impact", f"No classes found for {teacher} on {day}.")
            return
        # Show a window to edit impacted cells
        win = tk.Toplevel(self.root)
        win.title(f"Reassign {teacher} on {day}")
        win.geometry("700x400")
        frm = ttk.Frame(win)
        frm.pack(fill='both', expand=True, padx=10, pady=10)
        canvas = tk.Canvas(frm)
        vscroll = ttk.Scrollbar(frm, orient='vertical', command=canvas.yview)
        vscroll.pack(side='right', fill='y')
        canvas.pack(side='left', fill='both', expand=True)
        inner = ttk.Frame(canvas)
        canvas.create_window((0,0), window=inner, anchor='nw')
        canvas.configure(yscrollcommand=vscroll.set)
        def on_configure(event):
            canvas.configure(scrollregion=canvas.bbox('all'))
        inner.bind('<Configure>', on_configure)
        row = 0
        teacher_entries = []
        for slot in impacted:
            class_, section, p, subject = slot['class'], slot['section'], slot['period'], slot['subject']
            ttk.Label(inner, text=f"{class_} {section} Period {p+1}", background="#ffcccc").grid(row=row, column=0, sticky='w', padx=2, pady=2)
            ttk.Label(inner, text=subject).grid(row=row, column=1, sticky='w', padx=2)
            # Dropdown for available teachers (with blank option if none available)
            available_teachers = [t for t in self.config['teachers'] if t != teacher and subject in teacher_subjects.get(t,[])]
            # Remove teachers already assigned at this period in any class/section
            busy_teachers = set()
            for c2 in classes:
                for s2 in sections:
                    tval = self.entries[(c2, s2, day, p)][1].get()
                    if tval:
                        busy_teachers.add(tval)
            available_teachers = [t for t in available_teachers if t not in busy_teachers]
            if not available_teachers:
                available_teachers = [""]  # Allow blank if no teacher is available
            tvar = tk.StringVar(value=slot['teacher_var'].get())
            cb = ttk.Combobox(inner, textvariable=tvar, values=available_teachers, width=18, state='readonly')
            cb.grid(row=row, column=2, padx=2)
            teacher_entries.append((slot, tvar, cb))
            row += 1
        def save_changes():
            # Check for conflicts
            assigned = {}
            for slot, tvar, cb in teacher_entries:
                class_, section, p = slot['class'], slot['section'], slot['period']
                new_teacher = tvar.get()
                if not new_teacher:
                    messagebox.showerror("Error", f"Please assign a teacher for {class_} {section} Period {p+1}")
                    return
                # Check if teacher is already assigned at this period in any class/section
                for c2 in classes:
                    for s2 in sections:
                        if (c2, s2, day, p) == (class_, section, day, p):
                            continue
                        tval = self.entries[(c2, s2, day, p)][1].get()
                        if tval == new_teacher:
                            messagebox.showerror("Conflict", f"Teacher {new_teacher} is already assigned at {c2} {s2} Period {p+1}")
                            return
                # Also check within this batch of changes
                key = (new_teacher, p)
                if key in assigned:
                    messagebox.showerror("Conflict", f"Teacher {new_teacher} assigned to multiple impacted slots at Period {p+1}")
                    return
                assigned[key] = True
            # If all checks pass, update the main grid
            for slot, tvar, cb in teacher_entries:
                slot['teacher_var'].set(tvar.get())
            self.draw_grid()  # Ensure grid is refreshed instantly
            messagebox.showinfo("Saved", "Impacted slots updated.")
            win.destroy()
        btn_frame = ttk.Frame(win)
        btn_frame.pack(fill='x', pady=5)
        ttk.Button(btn_frame, text="Save Changes", command=save_changes).pack(side='left', padx=10)
        ttk.Button(btn_frame, text="Cancel", command=win.destroy).pack(side='right', padx=10)


    def _set_theme(self):
        # Set a modern color theme
        self.root.configure(bg="#f0f4f8")
        self.style.theme_use('clam')
        self.style.configure('TFrame', background="#f0f4f8")
        self.style.configure('TLabel', background="#f0f4f8", font=("Segoe UI", 10))
        self.style.configure('Header.TLabel', background="#2d6cdf", foreground="#fff", font=("Segoe UI", 11, "bold"), anchor="center")
        self.style.configure('TButton', font=("Segoe UI", 10, "bold"), background="#2d6cdf", foreground="#fff")
        self.style.map('TButton', background=[('active', '#1b4e91')], foreground=[('active', '#fff')])
        # Add a warning style for the Smart Match button
        self.style.configure('Warning.TButton', font=("Segoe UI", 10, "bold"), background="#ff9800", foreground="#fff")
        self.style.map('Warning.TButton', background=[('active', '#e65100')], foreground=[('active', '#fff')])
        self.style.configure('TCombobox', font=("Segoe UI", 10))
        self.style.configure('FancyCell.TFrame', background="#eaf0fa", borderwidth=1, relief="solid")
        self.style.configure('FancyCell.TLabel', background="#eaf0fa", font=("Segoe UI", 9))

    def setup_ui(self):
        # Fancy header
        header_frame = ttk.Frame(self.root)
        header_frame.pack(fill='x', padx=0, pady=(0, 5))

        # Month label (left)
        now = datetime.now()
        month_label = ttk.Label(
            header_frame,
            text=now.strftime('%B'),
            font=("Segoe UI", 12, "bold"),
            background="#2d6cdf",
            foreground="#fff",
            anchor="w"
        )
        month_label.pack(side='left', padx=(10, 0), pady=(0, 10))

        # School name (center)
        header_label = ttk.Label(
            header_frame,
            text="Indian Heights School",
            font=("Segoe UI", 22, "bold"),
            background="#2d6cdf",
            foreground="#fff",
            anchor="center"
        )
        header_label.pack(side='left', expand=True, fill='x', pady=(0, 10))

        # Date/time (right)
        datetime_label = ttk.Label(
            header_frame,
            text=now.strftime('%d %b %Y, %I:%M %p'),
            font=("Segoe UI", 12),
            background="#2d6cdf",
            foreground="#fff",
            anchor="e"
        )
        datetime_label.pack(side='right', padx=(0, 10), pady=(0, 10))

        # Top frame for week selection and config
        # Top frame for week selection and config
        top_frame = ttk.Frame(self.root)
        top_frame.pack(fill='x', padx=10, pady=5)
        ttk.Label(top_frame, text="Year:").pack(side='left')
        year_entry = ttk.Entry(top_frame, textvariable=self.selected_year, width=6)
        year_entry.pack(side='left', padx=5)
        ttk.Label(top_frame, text="Week #: ").pack(side='left')
        week_entry = ttk.Entry(top_frame, textvariable=self.selected_week, width=4)
        week_entry.pack(side='left', padx=5)
        ttk.Button(top_frame, text="Go to Week", command=self.load_timetable).pack(side='left', padx=10)
        # Config buttons
        ttk.Button(top_frame, text="Edit Classes", command=self.edit_classes).pack(side='right', padx=5)
        ttk.Button(top_frame, text="Edit Sections", command=self.edit_sections).pack(side='right', padx=5)
        ttk.Button(top_frame, text="Edit Teachers", command=self.edit_teachers).pack(side='right', padx=5)
        ttk.Button(top_frame, text="Edit Subjects", command=self.edit_subjects).pack(side='right', padx=5)

        # Action bar for main features (inside setup_ui)
        action_frame = ttk.Frame(self.root)
        action_frame.pack(fill='x', padx=10, pady=(0, 10))
        ttk.Button(action_frame, text="Smart Match", style='Warning.TButton', command=self.smart_match).pack(side='left', padx=5)
        ttk.Button(action_frame, text="Auto Assign", command=self.auto_assign_week).pack(side='left', padx=5)
        ttk.Button(action_frame, text="Export PDF", command=self.export_pdf).pack(side='left', padx=5)
        ttk.Button(action_frame, text="Export Excel", command=self.export_excel).pack(side='left', padx=5)
        ttk.Button(action_frame, text="Teacher On Leave", command=self.mark_teacher_on_leave).pack(side='left', padx=5)
        ttk.Button(action_frame, text="Refresh", command=self.load_timetable).pack(side='left', padx=5)
        ttk.Button(action_frame, text="Edit Mapping", command=self.show_teacher_subject_mapping).pack(side='left', padx=5)
        ttk.Button(action_frame, text="Save Timetable", command=self.save_timetable).pack(side='left', padx=5)

        # Timetable grid with horizontal and vertical scrollbar
        container = ttk.Frame(self.root)
        container.pack(fill='both', expand=True, padx=10, pady=10)
        canvas = tk.Canvas(container, bg="#f0f4f8", highlightthickness=0)
        h_scroll = ttk.Scrollbar(container, orient='horizontal', command=canvas.xview)
        v_scroll = ttk.Scrollbar(container, orient='vertical', command=canvas.yview)
        self.grid_frame = ttk.Frame(canvas)
        self.grid_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=self.grid_frame, anchor='nw')
        canvas.configure(xscrollcommand=h_scroll.set, yscrollcommand=v_scroll.set)
        canvas.pack(side='left', fill='both', expand=True)
        v_scroll.pack(side='right', fill='y')
        h_scroll.pack(side='bottom', fill='x')
        self.draw_grid()
    def export_pdf(self):
        from reportlab.lib.pagesizes import landscape, A4
        from reportlab.pdfgen import canvas
        from reportlab.lib import colors
        from reportlab.platypus import Table, TableStyle
        year = self.selected_year.get()
        week = self.selected_week.get()
        days = list(calendar.day_name[0:5])  # Monday to Friday
        classes = self.config['classes']
        sections = self.config['sections']
        periods = self.config['periods_per_day']
        file = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")])
        if not file:
            return
        try:
            c = canvas.Canvas(file, pagesize=landscape(A4))
            width, height = landscape(A4)
            for class_ in classes:
                for section in sections:
                    data = [["Day/Period"] + [f"P{p+1}" for p in range(periods)]]
                    for d in days:
                        row = [d]
                        for p in range(periods):
                            subj_var, teacher_var = self.entries[(class_, section, d, p)]
                            val = f"{subj_var.get()}\n{teacher_var.get()}"
                            row.append(val)
                        data.append(row)
                    t = Table(data, repeatRows=1)
                    t.setStyle(TableStyle([
                        ('BACKGROUND', (0,0), (-1,0), colors.lightblue),
                        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0,0), (-1,-1), 8),
                        ('BOTTOMPADDING', (0,0), (-1,0), 8),
                        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                    ]))
                    w, h = t.wrapOn(c, width-40, height-80)
                    c.setFont("Helvetica-Bold", 12)
                    c.drawString(30, height-30, f"Class: {class_}  Section: {section}  Year: {year}  Week: {week}")
                    t.drawOn(c, 30, height-60-h)
                    c.showPage()
            c.save()
            messagebox.showinfo("Exported", f"Weekly timetable exported to {file}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export PDF: {e}")

        # Timetable grid with horizontal scrollbar
        container = ttk.Frame(self.root)
        container.pack(fill='both', expand=True, padx=10, pady=10)
        canvas = tk.Canvas(container, bg="#f0f4f8", highlightthickness=0)
        h_scroll = ttk.Scrollbar(container, orient='horizontal', command=canvas.xview)
        v_scroll = ttk.Scrollbar(container, orient='vertical', command=canvas.yview)
        self.grid_frame = ttk.Frame(canvas)
        self.grid_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=self.grid_frame, anchor='nw')
        canvas.configure(xscrollcommand=h_scroll.set, yscrollcommand=v_scroll.set)
        canvas.pack(side='left', fill='both', expand=True)
        v_scroll.pack(side='right', fill='y')
        h_scroll.pack(side='bottom', fill='x')
        self.draw_grid()

    def draw_grid(self):
        # Always reload config to reflect any manual changes to sections, etc.
        self.config = load_config()
        for widget in self.grid_frame.winfo_children():
            widget.destroy()
        # Weekly grid: Days x Periods x Classes x Sections
        year = self.selected_year.get()
        week = self.selected_week.get()
        periods = self.config['periods_per_day']
        days = list(calendar.day_name[0:5])  # Monday to Friday
        classes = self.config['classes']
        sections = self.config['sections']
        teacher_subjects = self.config.get('teacher_subjects', {})
        # Header row
        ttk.Label(self.grid_frame, text="Class", style='Header.TLabel', borderwidth=1, relief="solid", width=10, anchor='center', justify='center').grid(row=0, column=0, sticky='nsew')
        ttk.Label(self.grid_frame, text="Section", style='Header.TLabel', borderwidth=1, relief="solid", width=8, anchor='center', justify='center').grid(row=0, column=1, sticky='nsew')
        col = 2
        for d in days:
            for p in range(periods):
                ttk.Label(self.grid_frame, text=f"{d}\nP{p+1}", style='Header.TLabel', borderwidth=1, relief="solid", width=10).grid(row=0, column=col, sticky='nsew')
                col += 1
        # Timetable cells
        self.entries = {}
        self.teacher_cbs = {}
        self.cell_frames = {}  # NEW: Track cell frames for color update
        row = 1
        for class_ in classes:
            for section in sections:
                ttk.Label(self.grid_frame, text=class_, style='TLabel', borderwidth=1, relief="solid", width=10, anchor='center', justify='center').grid(row=row, column=0, sticky='nsew')
                ttk.Label(self.grid_frame, text=section, style='TLabel', borderwidth=1, relief="solid", width=8, anchor='center', justify='center').grid(row=row, column=1, sticky='nsew')
                col = 2
                for d in days:
                    for p in range(periods):
                        cell_key = (class_, section, d, p)
                        # Use tk.Frame for color support
                        highlight = None
                        if cell_key in getattr(self, 'impacted_cells', set()):
                            highlight = '#ffcccc'  # red
                        elif cell_key in getattr(self, 'resolved_cells', set()):
                            highlight = '#ccffcc'  # green
                        frame = tk.Frame(self.grid_frame, bg=highlight if highlight else '#eaf0fa', bd=1, relief="solid")
                        frame.grid(row=row, column=col, sticky='nsew')
                        subj_var = tk.StringVar()
                        teacher_var = tk.StringVar()
                        subj_cb = ttk.Combobox(frame, textvariable=subj_var, values=self.config['subjects'], width=8, state='readonly')
                        subj_cb.pack(side='top', fill='x', padx=1, pady=1)
                        teacher_entry = ttk.Entry(frame, textvariable=teacher_var, width=12)
                        teacher_entry.pack(side='top', fill='x', padx=1, pady=(0,2))
                        # Track frame for color update
                        self.cell_frames[cell_key] = frame
                        def on_teacher_change(event=None, key=cell_key):
                            # Mark cell as resolved (green) on teacher change
                            self.resolved_cells.add(key)
                            self.impacted_cells.discard(key)
                            self.cell_frames[key].configure(bg='#ccffcc')
                        teacher_entry.bind('<FocusOut>', on_teacher_change)
                        teacher_entry.bind('<Return>', on_teacher_change)
                        subj_cb.bind('<<ComboboxSelected>>', lambda e: None)
                        self.entries[cell_key] = (subj_var, teacher_var)
                        self.teacher_cbs[cell_key] = (teacher_entry, subj_var)
                        col += 1
                row += 1

    def save_timetable(self):
        # Remove old entries for this week
        year = self.selected_year.get()
        week = self.selected_week.get()
        days = [calendar.day_name[i] for i in range(5)]
        c.execute("DELETE FROM timetable WHERE day LIKE ?", (f"{year}-W{week:02d}-%",))
        week_data = []
        for (class_, section, d, p), (subj_var, teacher_var) in self.entries.items():
            subject = subj_var.get()
            teacher = teacher_var.get()
            if subject and teacher:
                # Check for teacher conflict
                c.execute("SELECT * FROM timetable WHERE day=? AND period=? AND teacher=? AND NOT (class=? AND section=?)", (f"{year}-W{week:02d}-{d}", p, teacher, class_, section))
                if c.fetchone():
                    messagebox.showerror("Conflict", f"Teacher {teacher} already assigned at {d} Period {p+1}")
                    return
                c.execute("INSERT INTO timetable (class, section, day, period, subject, teacher) VALUES (?, ?, ?, ?, ?, ?)", (class_, section, f"{year}-W{week:02d}-{d}", p, subject, teacher))
                week_data.append({
                    "class": class_,
                    "section": section,
                    "day": d,
                    "period": p,
                    "subject": subject,
                    "teacher": teacher
                })
        conn.commit()
        # Save week snapshot to history
        self.save_week_history(year, week, week_data)
        messagebox.showinfo("Saved", "Timetable saved successfully.")

    def load_timetable(self):
        year = self.selected_year.get()
        week = self.selected_week.get()
        days = [calendar.day_name[i] for i in range(5)]
        for (class_, section, d, p), (subj_var, teacher_var) in self.entries.items():
            subj_var.set("")
            teacher_var.set("")
        c.execute("SELECT class, section, day, period, subject, teacher FROM timetable WHERE day LIKE ?", (f"{year}-W{week:02d}-%",))
        for row in c.fetchall():
            class_, section, day, period, subject, teacher = row
            # Extract day name from day string
            d = day.split('-')[-1]
            if (class_, section, d, period) in self.entries:
                self.entries[(class_, section, d, period)][0].set(subject)
                self.entries[(class_, section, d, period)][1].set(teacher)


    def export_excel(self):
        year = self.selected_year.get()
        week = self.selected_week.get()
        days = [calendar.day_name[i] for i in range(5)]
        classes = self.config['classes']
        sections = self.config['sections']
        periods = self.config['periods_per_day']
        # Gather all data from UI, including blanks and multiple teachers
        data = []
        for class_ in classes:
            for section in sections:
                for d in days:
                    for p in range(periods):
                        subj_var, teacher_var = self.entries[(class_, section, d, p)]
                        teachers = [t.strip() for t in teacher_var.get().split(',') if t.strip()]
                        data.append({
                            "Class": class_,
                            "Section": section,
                            "Day": d,
                            "Period": p,
                            "Subject": subj_var.get(),
                            "Teachers": ', '.join(teachers)
                        })
        df = pd.DataFrame(data)
        file = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
        if file:
            with pd.ExcelWriter(file) as writer:
                for class_ in classes:
                    for section in sections:
                        subdf = df[(df['Class'] == class_) & (df['Section'] == section)]
                        if not subdf.empty:
                            pivot = subdf.pivot(index="Day", columns="Period", values=["Subject", "Teachers"])
                            pivot.columns = [f"P{col[1]+1} {col[0]}" for col in pivot.columns]
                            pivot.reset_index(inplace=True)
                            pivot.to_excel(writer, sheet_name=f"{class_}-{section}", index=False)
            messagebox.showinfo("Exported", f"Weekly timetable exported to {file}")

    def export_impacted_classes(self, teacher, day):
        # Find all slots for this teacher on this day, and allow manual reassignment with conflict check
        year = self.selected_year.get()
        week = self.selected_week.get()
        classes = self.config['classes']
        sections = self.config['sections']
        periods = self.config['periods_per_day']
        teacher_subjects = self.config.get('teacher_subjects', {})
        impacted = []
        for class_ in classes:
            for section in sections:
                for p in range(periods):
                    subj_var, teacher_var = self.entries[(class_, section, day, p)]
                    if teacher_var.get() == teacher:
                        subject = subj_var.get()
                        impacted.append({
                            'class': class_,
                            'section': section,
                            'period': p,
                            'subject': subject,
                            'old_teacher': teacher,
                            'subj_var': subj_var,
                            'teacher_var': teacher_var
                        })
        if not impacted:
            messagebox.showinfo("No Impact", f"No classes found for {teacher} on {day}.")
            return
        # Show a window to edit impacted cells
        win = tk.Toplevel(self.root)
        win.title(f"Reassign {teacher} on {day}")
        win.geometry("700x400")
        frm = ttk.Frame(win)
        frm.pack(fill='both', expand=True, padx=10, pady=10)
        canvas = tk.Canvas(frm)
        vscroll = ttk.Scrollbar(frm, orient='vertical', command=canvas.yview)
        vscroll.pack(side='right', fill='y')
        canvas.pack(side='left', fill='both', expand=True)
        inner = ttk.Frame(canvas)
        canvas.create_window((0,0), window=inner, anchor='nw')
        canvas.configure(yscrollcommand=vscroll.set)
        def on_configure(event):
            canvas.configure(scrollregion=canvas.bbox('all'))
        inner.bind('<Configure>', on_configure)
        row = 0
        teacher_entries = []
        for slot in impacted:
            class_, section, p, subject = slot['class'], slot['section'], slot['period'], slot['subject']
            ttk.Label(inner, text=f"{class_} {section} Period {p+1}", background="#ffcccc").grid(row=row, column=0, sticky='w', padx=2, pady=2)
            ttk.Label(inner, text=subject).grid(row=row, column=1, sticky='w', padx=2)
            # Dropdown for available teachers
            available_teachers = [""] + [t for t in self.config['teachers'] if t != teacher and subject in teacher_subjects.get(t,[])]
            # Remove teachers already assigned at this period in any class/section
            busy_teachers = set()
            for c2 in classes:
                for s2 in sections:
                    tval = self.entries[(c2, s2, day, p)][1].get()
                    if tval:
                        busy_teachers.add(tval)
            available_teachers = [t for t in available_teachers if t not in busy_teachers]
            tvar = tk.StringVar(value=slot['teacher_var'].get())
            cb = ttk.Combobox(inner, textvariable=tvar, values=available_teachers, width=18, state='readonly')
            cb.grid(row=row, column=2, padx=2)
            teacher_entries.append((slot, tvar, cb))
            row += 1
        def save_changes():
            # Check for conflicts
            assigned = {}
            for slot, tvar, cb in teacher_entries:
                class_, section, p = slot['class'], slot['section'], slot['period']
                new_teacher = tvar.get()
                if new_teacher:
                    # Check if teacher is already assigned at this period in any class/section
                    for c2 in classes:
                        for s2 in sections:
                            if (c2, s2, day, p) == (class_, section, day, p):
                                continue
                            tval = self.entries[(c2, s2, day, p)][1].get()
                            if tval == new_teacher:
                                messagebox.showerror("Conflict", f"Teacher {new_teacher} is already assigned at {c2} {s2} Period {p+1}")
                                return
                    # Also check within this batch of changes
                    key = (new_teacher, p)
                    if key in assigned:
                        messagebox.showerror("Conflict", f"Teacher {new_teacher} assigned to multiple impacted slots at Period {p+1}")
                        return
                    assigned[key] = True
            # If all checks pass, update the main grid and color cells
            for slot, tvar, cb in teacher_entries:
                class_, section, p = slot['class'], slot['section'], slot['period']
                new_teacher = tvar.get()
                key = (class_, section, day, p)
                slot['teacher_var'].set(new_teacher)
                if new_teacher:
                    self.resolved_cells.add(key)
                    self.impacted_cells.discard(key)
                    if hasattr(self, 'cell_frames') and key in self.cell_frames:
                        self.cell_frames[key].configure(bg='#ccffcc')
                else:
                    self.impacted_cells.add(key)
                    self.resolved_cells.discard(key)
                    if hasattr(self, 'cell_frames') and key in self.cell_frames:
                        self.cell_frames[key].configure(bg='#ffcccc')
            self.load_timetable()  # Refresh grid with latest data from DB
            messagebox.showinfo("Saved", "Impacted slots updated.")
            win.destroy()
        btn_frame = ttk.Frame(win)
        btn_frame.pack(fill='x', pady=5)
        ttk.Button(btn_frame, text="Save Changes", command=save_changes).pack(side='left', padx=10)
        ttk.Button(btn_frame, text="Cancel", command=win.destroy).pack(side='right', padx=10)


if __name__ == "__main__":
    import tkinter as tk
    import traceback
    try:
        print("Launching Tkinter main window...")
        root = tk.Tk()
        root.geometry("1200x700+100+100")
        test_label = tk.Label(root, text="If you see this, Tkinter is working.", font=("Arial", 20), fg="red")
        test_label.pack(pady=50)
        root.update()
        import time
        time.sleep(2)
        test_label.destroy()
        app = TimetableApp(root)
        print("Entering mainloop...")
        root.mainloop()
        print("Exited mainloop.")
    except Exception as e:
        print("Exception occurred:", e)
        traceback.print_exc()
        try:
            from tkinter import messagebox
            messagebox.showerror("Error", f"Exception occurred:\n{e}\n\nSee terminal for details.")
        except Exception:
            pass
