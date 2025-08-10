# School Timetable Planner
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
    def __init__(self, root):
        self.root = root
        self.root.title("School Weekly Timetable Planner")
        self.root.geometry("1200x700")
        self.config = CONFIG
        self.selected_week = tk.IntVar(value=datetime.now().isocalendar()[1])
        self.selected_year = tk.IntVar(value=datetime.now().year)
        self.impacted_cells = set()
        self.resolved_cells = set()
        self.entries = {}
        self.teacher_cbs = {}
        self.cell_frames = {}
        self.style = ttk.Style()
        self._set_theme()
        self.setup_ui()
        self.load_timetable()
        
    def _set_theme(self):
        self.root.configure(bg="#f0f4f8")
        self.style.theme_use('clam')
        self.style.configure('TFrame', background="#f0f4f8")
        self.style.configure('TLabel', background="#f0f4f8", font=("Segoe UI", 10))
        self.style.configure('Header.TLabel', background="#2d6cdf", foreground="#fff", 
                           font=("Segoe UI", 11, "bold"), anchor="center")
        self.style.configure('TButton', font=("Segoe UI", 10, "bold"), background="#2d6cdf", 
                           foreground="#fff")
        self.style.map('TButton', background=[('active', '#1b4e91')], foreground=[('active', '#fff')])
        self.style.configure('TCombobox', font=("Segoe UI", 10))
        
    def setup_ui(self):
        # Header
        header = ttk.Label(self.root, text="School Timetable Planner", font=('Segoe UI', 16, 'bold'))
        header.pack(pady=10)

        # Controls frame
        controls = ttk.Frame(self.root)
        controls.pack(fill='x', padx=10, pady=5)

        # Year and week
        ttk.Label(controls, text="Year:").pack(side='left')
        ttk.Entry(controls, textvariable=self.selected_year, width=6).pack(side='left', padx=5)
        ttk.Label(controls, text="Week:").pack(side='left')
        ttk.Entry(controls, textvariable=self.selected_week, width=4).pack(side='left', padx=5)
        ttk.Button(controls, text="Load", command=self.load_timetable).pack(side='left', padx=5)
        ttk.Button(controls, text="Save", command=self.save_timetable).pack(side='left', padx=5)

        # Edit buttons
        ttk.Button(controls, text="Edit Classes", command=self.edit_classes).pack(side='right', padx=5)
        ttk.Button(controls, text="Edit Sections", command=self.edit_sections).pack(side='right', padx=5)
        ttk.Button(controls, text="Edit Teachers", command=self.edit_teachers).pack(side='right', padx=5)
        ttk.Button(controls, text="Edit Subjects", command=self.edit_subjects).pack(side='right', padx=5)

        # Action buttons
        actions = ttk.Frame(self.root)
        actions.pack(fill='x', padx=10, pady=5)
        ttk.Button(actions, text="Auto-Assign", command=self.auto_assign_week).pack(side='left', padx=5)
        ttk.Button(actions, text="Mark Leave", command=self.mark_teacher_on_leave).pack(side='left', padx=5)
        ttk.Button(actions, text="Export Excel", command=self.export_excel).pack(side='left', padx=5)
        ttk.Button(actions, text="Teacher-Subject Mapping", command=self.show_teacher_subject_mapping).pack(side='left', padx=5)
        ttk.Button(actions, text="Refresh", command=self.draw_grid).pack(side='left', padx=5)

        # Grid container
        container = ttk.Frame(self.root)
        container.pack(fill='both', expand=True, padx=10, pady=10)
        # Scrollable canvas for grid
        canvas = tk.Canvas(container, bg="#f0f4f8", highlightthickness=0)
        xscroll = ttk.Scrollbar(container, orient='horizontal', command=canvas.xview)
        yscroll = ttk.Scrollbar(container, orient='vertical', command=canvas.yview)
        self.grid_frame = ttk.Frame(canvas)
        self.grid_frame.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.create_window((0, 0), window=self.grid_frame, anchor='nw')
        canvas.configure(xscrollcommand=xscroll.set, yscrollcommand=yscroll.set)
        canvas.pack(side='left', fill='both', expand=True)
        yscroll.pack(side='right', fill='y')
        xscroll.pack(side='bottom', fill='x')
        self.draw_grid()

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
        
    def draw_grid(self):
        self.config = load_config()
        for widget in self.grid_frame.winfo_children():
            widget.destroy()
            
        days = [calendar.day_name[i] for i in range(5)]
        periods = self.config['periods_per_day']
        
        # Headers
        ttk.Label(self.grid_frame, text="Class", style='Header.TLabel').grid(row=0, column=0)
        ttk.Label(self.grid_frame, text="Section", style='Header.TLabel').grid(row=0, column=1)
        
        col = 2
        for d in days:
            for p in range(periods):
                ttk.Label(self.grid_frame, text=f"{d}\nP{p+1}", 
                         style='Header.TLabel').grid(row=0, column=col)
                col += 1
                
        # Cells
        row = 1
        for class_ in self.config['classes']:
            for section in self.config['sections']:
                ttk.Label(self.grid_frame, text=class_).grid(row=row, column=0)
                ttk.Label(self.grid_frame, text=section).grid(row=row, column=1)
                
                col = 2
                for d in days:
                    for p in range(periods):
                        cell_key = (class_, section, d, p)
                        
                        # Thicker border for impacted cells
                        if cell_key in self.impacted_cells:
                            frame = tk.Frame(self.grid_frame, bd=4, relief="solid", bg='#ff0000', highlightbackground='#ff0000', highlightcolor='#ff0000', highlightthickness=4)
                        else:
                            frame = tk.Frame(self.grid_frame, bd=2, relief="solid")
                        frame.grid(row=row, column=col, sticky='nsew')
                        # Set initial color
                        if cell_key in self.impacted_cells:
                            frame.configure(bg='#ffcccc', highlightbackground='#ff0000', highlightcolor='#ff0000', highlightthickness=4)  # strong red
                        elif cell_key in self.resolved_cells:
                            frame.configure(bg='#ccffcc', highlightbackground='#eaf0fa', highlightcolor='#eaf0fa', highlightthickness=2)  # green
                        else:
                            frame.configure(bg='#eaf0fa', highlightbackground='#eaf0fa', highlightcolor='#eaf0fa', highlightthickness=2)  # default
                            
                        subj_var = tk.StringVar()
                        teacher_var = tk.StringVar()
                        
                        subj_cb = ttk.Combobox(frame, textvariable=subj_var,
                                             values=self.config['subjects'], width=10)
                        subj_cb.pack(fill='x', padx=1, pady=1)
                        
                        teacher_entry = ttk.Entry(frame, textvariable=teacher_var, width=10)
                        teacher_entry.pack(fill='x', padx=1, pady=1)
                        
                        self.entries[cell_key] = (subj_var, teacher_var)
                        self.cell_frames[cell_key] = frame
                        
                        def on_teacher_change(event=None, key=cell_key, frame=frame):
                            if teacher_var.get():
                                self.resolved_cells.add(key)
                                self.impacted_cells.discard(key)
                                frame.configure(bg='#ccffcc', highlightbackground='#eaf0fa', highlightcolor='#eaf0fa', highlightthickness=2)  # green
                            elif key in self.impacted_cells:
                                frame.configure(bg='#ffcccc', highlightbackground='#ff0000', highlightcolor='#ff0000', highlightthickness=4)  # strong red
                            else:
                                frame.configure(bg='#eaf0fa', highlightbackground='#eaf0fa', highlightcolor='#eaf0fa', highlightthickness=2)  # default
                                
                        teacher_entry.bind('<FocusOut>', on_teacher_change)
                        teacher_entry.bind('<Return>', on_teacher_change)
                        teacher_var.trace('w', lambda *args, key=cell_key, frame=frame: 
                                        on_teacher_change(key=key, frame=frame))
                        
                        col += 1
                row += 1
                
    def load_timetable(self):
        year = self.selected_year.get()
        week = self.selected_week.get()
        
        # Clear current entries
        for key, (subj_var, teacher_var) in self.entries.items():
            subj_var.set("")
            teacher_var.set("")
            
        # Load from database
        with sqlite3.connect(DB_FILE) as conn:
            c = conn.cursor()
            c.execute("""
                SELECT class, section, day, period, subject, teacher 
                FROM timetable 
                WHERE day LIKE ?
            """, (f"{year}-W{week:02d}-%",))
            
            for row in c.fetchall():
                class_, section, day, period, subject, teacher = row
                d = day.split('-')[-1]  # Extract day name
                if (class_, section, d, period) in self.entries:
                    self.entries[(class_, section, d, period)][0].set(subject)
                    self.entries[(class_, section, d, period)][1].set(teacher)
                    
    def save_timetable(self):
        year = self.selected_year.get()
        week = self.selected_week.get()
        
        with sqlite3.connect(DB_FILE) as conn:
            c = conn.cursor()
            
            # Clear old entries
            c.execute("DELETE FROM timetable WHERE day LIKE ?", 
                     (f"{year}-W{week:02d}-%",))
            
            # Save current entries
            for (class_, section, d, p), (subj_var, teacher_var) in self.entries.items():
                subject = subj_var.get()
                teacher = teacher_var.get()
                
                if subject and teacher:
                    day_str = f"{year}-W{week:02d}-{d}"
                    
                    # Check for conflicts
                    c.execute("""
                        SELECT * FROM timetable 
                        WHERE day=? AND period=? AND teacher=? 
                        AND NOT (class=? AND section=?)
                    """, (day_str, p, teacher, class_, section))
                    
                    if c.fetchone():
                        messagebox.showerror(
                            "Conflict", 
                            f"Teacher {teacher} already assigned at {d} Period {p+1}"
                        )
                        return
                        
                    c.execute("""
                        INSERT INTO timetable 
                        (class, section, day, period, subject, teacher) 
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (class_, section, day_str, p, subject, teacher))
                    
            conn.commit()
        messagebox.showinfo("Success", "Timetable saved successfully")
        
    def export_excel(self):
        file = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")]
        )
        
        if not file:
            return
            
        data = []
        days = [calendar.day_name[i] for i in range(5)]
        
        for (class_, section, d, p), (subj_var, teacher_var) in self.entries.items():
            if subj_var.get() or teacher_var.get():
                data.append({
                    'Class': class_,
                    'Section': section,
                    'Day': d,
                    'Period': p + 1,
                    'Subject': subj_var.get(),
                    'Teacher': teacher_var.get()
                })
                
        if not data:
            messagebox.showwarning("Warning", "No data to export")
            return
            
        df = pd.DataFrame(data)
        
        with pd.ExcelWriter(file) as writer:
            for class_ in self.config['classes']:
                for section in self.config['sections']:
                    df_section = df[
                        (df['Class'] == class_) & 
                        (df['Section'] == section)
                    ]
                    
                    if not df_section.empty:
                        pivot = df_section.pivot(
                            index='Day',
                            columns='Period',
                            values=['Subject', 'Teacher']
                        )
                        pivot.columns = [f"P{col[1]} {col[0]}" 
                                       for col in pivot.columns]
                        pivot.to_excel(
                            writer,
                            sheet_name=f"{class_}-{section}",
                            index=True
                        )
                        
        messagebox.showinfo("Success", f"Exported to {file}")
        
    def auto_assign_week(self):
        days = [calendar.day_name[i] for i in range(5)]
        periods = self.config['periods_per_day']
        subjects = self.config['subjects']
        teachers = self.config['teachers']
        teacher_subjects = self.config.get('teacher_subjects', {})
        for d in days:
            for p in range(periods):
                used_teachers = set()
                for class_ in self.config['classes']:
                    for section in self.config['sections']:
                        subject = subjects[p % len(subjects)]
                        # Find teachers who can teach this subject and are not used in this period
                        available_teachers = [t for t in teachers if subject in teacher_subjects.get(t, []) and t not in used_teachers]
                        assigned_teacher = available_teachers[0] if available_teachers else ""
                        self.entries[(class_, section, d, p)][0].set(subject)
                        self.entries[(class_, section, d, p)][1].set(assigned_teacher)
                        if assigned_teacher:
                            used_teachers.add(assigned_teacher)
        messagebox.showinfo("Success", "Teachers auto-assigned for the week (subject mapping enforced)")
        
    def show_teacher_subject_mapping(self):
        mapping = self.config.get('teacher_subjects', {})
        win = tk.Toplevel(self.root)
        win.title("Teacher-Subject Mapping")
        win.geometry("500x500")
        
        outer_frame = ttk.Frame(win, padding="10")
        outer_frame.pack(fill='both', expand=True)
        
        # Scrollable canvas
        canvas = tk.Canvas(outer_frame)
        scrollbar = ttk.Scrollbar(outer_frame, orient='vertical', command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        inner = ttk.Frame(canvas)
        canvas.create_window((0, 0), window=inner, anchor='nw')
        inner.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        
        teacher_vars = {}
        subject_vars = {}
        row = 0
        for teacher in self.config['teachers']:
            ttk.Label(inner, text=teacher).grid(row=row, column=0, sticky='w', pady=2)
            var = tk.StringVar(value=", ".join(mapping.get(teacher, [])))
            entry = ttk.Entry(inner, textvariable=var, width=40)
            entry.grid(row=row, column=1, sticky='ew', padx=5)
            teacher_vars[teacher] = var
            row += 1
        # Add new teacher row
        ttk.Label(inner, text="Add Teacher:").grid(row=row, column=0, sticky='w', pady=10)
        new_teacher_var = tk.StringVar()
        new_teacher_entry = ttk.Entry(inner, textvariable=new_teacher_var, width=18)
        new_teacher_entry.grid(row=row, column=1, sticky='w', padx=5)
        new_subjects_var = tk.StringVar()
        new_subjects_entry = ttk.Entry(inner, textvariable=new_subjects_var, width=40)
        new_subjects_entry.grid(row=row, column=2, sticky='w', padx=5)
        row += 1
        
        def save_mapping():
            new_mapping = {}
            for teacher, var in teacher_vars.items():
                subjects = [s.strip() for s in var.get().split(',') if s.strip() in self.config['subjects']]
                new_mapping[teacher] = subjects
            # Add new teacher if provided
            new_teacher = new_teacher_var.get().strip()
            new_subjects = [s.strip() for s in new_subjects_var.get().split(',') if s.strip() in self.config['subjects']]
            if new_teacher and new_teacher not in new_mapping:
                new_mapping[new_teacher] = new_subjects
                # Also add to config teachers list
                if new_teacher not in self.config['teachers']:
                    self.config['teachers'].append(new_teacher)
            self.config['teacher_subjects'] = new_mapping
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=2)
            win.destroy()
            self.draw_grid()
        
        btn_frame = ttk.Frame(outer_frame)
        btn_frame.pack(fill='x', pady=10)
        ttk.Button(btn_frame, text="Save", command=save_mapping).pack(side='left', padx=10)
        ttk.Button(btn_frame, text="Close", command=win.destroy).pack(side='right', padx=10)
        
    def mark_teacher_on_leave(self):
        win = tk.Toplevel(self.root)
        win.title("Mark Teacher Leave")
        
        frame = ttk.Frame(win, padding="10")
        frame.pack()
        
        ttk.Label(frame, text="Teacher:").grid(row=0, column=0, sticky='w')
        teacher_var = tk.StringVar()
        ttk.Combobox(frame, textvariable=teacher_var,
                    values=self.config['teachers']).grid(row=0, column=1, padx=5)
        
        ttk.Label(frame, text="Day:").grid(row=1, column=0, sticky='w')
        day_var = tk.StringVar()
        ttk.Combobox(frame, textvariable=day_var,
                    values=[calendar.day_name[i] for i in range(5)]).grid(row=1, column=1, padx=5)
        
        def process():
            teacher = teacher_var.get()
            day = day_var.get()
            
            if not teacher or not day:
                messagebox.showerror("Error", "Please select teacher and day")
                return
                
            # Mark impacted cells red
            for cell_key, (_, teacher_v) in self.entries.items():
                if teacher_v.get() == teacher and cell_key[2] == day:
                    self.impacted_cells.add(cell_key)
                    self.resolved_cells.discard(cell_key)
                    if cell_key in self.cell_frames:
                        self.cell_frames[cell_key].configure(bg='#ffcccc')
                        
            win.destroy()
            self.show_reassignment_dialog(teacher, day)
            
        ttk.Button(frame, text="Process", command=process).grid(row=2, column=0, columnspan=2, pady=10)
        
    def show_reassignment_dialog(self, teacher, day):
        win = tk.Toplevel(self.root)
        win.title(f"Reassign {teacher} on {day}")
        win.geometry("500x400")
        frame = ttk.Frame(win, padding="10")
        frame.pack(fill='both', expand=True)
        impacted = []
        for cell_key, (subj_var, teacher_var) in self.entries.items():
            if teacher_var.get() == teacher and cell_key[2] == day:
                impacted.append((cell_key, subj_var.get()))
        if not impacted:
            messagebox.showinfo("No Impact", "No classes found for this teacher on this day")
            win.destroy()
            return
        row = 0
        entries = {}
        for (class_, section, _, period), subject in impacted:
            ttk.Label(frame, text=f"{class_} {section} P{period+1}", background='#ffcccc').grid(row=row, column=0, sticky='w')
            ttk.Label(frame, text=subject).grid(row=row, column=1, padx=5)
            # Only show available teachers for this class/section/period
            available_teachers = []
            for t in self.config['teachers']:
                if t == teacher:
                    continue
                busy = False
                for c2 in self.config['classes']:
                    for s2 in self.config['sections']:
                        if (c2, s2, day, period) == (class_, section, day, period):
                            continue
                        tval = self.entries[(c2, s2, day, period)][1].get()
                        if tval == t:
                            busy = True
                            break
                    if busy:
                        break
                if not busy:
                    available_teachers.append(t)
            var = tk.StringVar()
            cb = ttk.Combobox(frame, textvariable=var, values=available_teachers)
            cb.grid(row=row, column=2, padx=5)
            entries[(class_, section, period)] = var
            row += 1
        def save():
            for (class_, section, period), var in entries.items():
                new_teacher = var.get()
                if new_teacher:
                    cell_key = (class_, section, day, period)
                    self.entries[cell_key][1].set(new_teacher)
                    self.resolved_cells.add(cell_key)
                    self.impacted_cells.discard(cell_key)
                    if cell_key in self.cell_frames:
                        self.cell_frames[cell_key].configure(bg='#ccffcc', highlightbackground='#eaf0fa', highlightcolor='#eaf0fa', highlightthickness=2)
            win.destroy()
        ttk.Button(frame, text="Save", command=save).grid(row=row, column=0, columnspan=3, pady=10)
        
if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = TimetableApp(root)
        root.mainloop()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
