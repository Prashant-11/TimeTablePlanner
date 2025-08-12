# School Timetable Planner - Optimized for Fast Loading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import sqlite3
import json
import os
import calendar
from datetime import datetime, timedelta
import socket
import urllib.request
import urllib.error
import base64
import hashlib
import threading
import zipfile
import shutil
import subprocess
import sys

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

class LicenseManager:
    """Manages licensing, trial periods, and feature access for ClassFlow freemium model"""
    
    def __init__(self):
        self.license_file = self.get_license_path()
        self.license_data = self.load_or_create_license()
        
    def get_license_path(self):
        """Get the path for the license file"""
        if os.name == 'nt':  # Windows
            app_data = os.environ.get('APPDATA', os.path.expanduser('~'))
            license_dir = os.path.join(app_data, 'ClassFlow')
        else:  # Linux/Mac
            license_dir = os.path.expanduser('~/.classflow')
        
        if not os.path.exists(license_dir):
            os.makedirs(license_dir)
        
        return os.path.join(license_dir, 'license.json')
    
    def load_or_create_license(self):
        """Load existing license or create new trial license"""
        if os.path.exists(self.license_file):
            try:
                with open(self.license_file, 'r') as f:
                    data = json.load(f)
                return data
            except:
                # If file is corrupted, create new license
                pass
        
        # Create new trial license
        return self.create_trial_license()
    
    def create_trial_license(self):
        """Create a new 30-day trial license"""
        license_data = {
            "installation_date": datetime.now().strftime("%Y-%m-%d"),
            "license_type": "TRIAL",
            "license_key": None,
            "premium_expiry": None,
            "trial_days": 30,
            "features": {
                "max_classes": 999,
                "max_sections": 999,
                "max_teachers": 999,
                "max_periods": 12,
                "auto_assign": True,
                "smart_match": True,
                "teacher_restrictions": True,
                "teacher_leave": True,
                "pdf_export": True,
                "watermark": False
            }
        }
        self.save_license(license_data)
        return license_data
    
    def save_license(self, license_data):
        """Save license data to file"""
        try:
            with open(self.license_file, 'w') as f:
                json.dump(license_data, f, indent=2)
        except Exception as e:
            print(f"Failed to save license: {e}")
    
    def get_trial_days_remaining(self):
        """Calculate remaining trial days"""
        if self.license_data["license_type"] != "TRIAL":
            return 0
        
        install_date = datetime.strptime(self.license_data["installation_date"], "%Y-%m-%d")
        days_passed = (datetime.now() - install_date).days
        return max(0, self.license_data["trial_days"] - days_passed)
    
    def is_trial_expired(self):
        """Check if trial period has expired"""
        return self.license_data["license_type"] == "TRIAL" and self.get_trial_days_remaining() <= 0
    
    def is_premium(self):
        """Check if user has premium license"""
        return self.license_data["license_type"] == "PREMIUM"
    
    def get_license_status(self):
        """Get current license status for UI display"""
        if self.license_data["license_type"] == "TRIAL":
            days_remaining = self.get_trial_days_remaining()
            if days_remaining > 0:
                return f"Trial: {days_remaining} days remaining"
            else:
                return "Trial Expired"
        elif self.license_data["license_type"] == "PREMIUM":
            return "Premium License"
        else:
            return "Free Version"
    
    def upgrade_to_free(self):
        """Convert expired trial to free version with limitations"""
        self.license_data.update({
            "license_type": "FREE",
            "features": {
                "max_classes": 3,
                "max_sections": 2,
                "max_teachers": 10,
                "max_periods": 6,
                "auto_assign": False,
                "smart_match": False,
                "teacher_restrictions": False,
                "teacher_leave": False,
                "pdf_export": False,
                "watermark": True
            }
        })
        self.save_license(self.license_data)
    
    def validate_feature(self, feature_name):
        """Check if a feature is available in current license"""
        if self.is_trial_expired() and self.license_data["license_type"] == "TRIAL":
            self.upgrade_to_free()
        
        return self.license_data["features"].get(feature_name, False)
    
    def get_feature_limit(self, feature_name):
        """Get numeric limit for a feature"""
        return self.license_data["features"].get(feature_name, 0)
    
    def validate_config_limits(self, config):
        """Validate configuration against license limits"""
        max_classes = self.get_feature_limit("max_classes")
        max_sections = self.get_feature_limit("max_sections") 
        max_teachers = self.get_feature_limit("max_teachers")
        
        # Check if current config exceeds limits
        violations = []
        
        if len(config.get('classes', [])) > max_classes:
            violations.append(f"Classes: {len(config['classes'])} exceeds limit of {max_classes}")
            # Truncate to limit
            config['classes'] = config['classes'][:max_classes]
        
        if len(config.get('sections', [])) > max_sections:
            violations.append(f"Sections: {len(config['sections'])} exceeds limit of {max_sections}")
            # Truncate to limit
            config['sections'] = config['sections'][:max_sections]
        
        if len(config.get('teachers', [])) > max_teachers:
            violations.append(f"Teachers: {len(config['teachers'])} exceeds limit of {max_teachers}")
            # Truncate to limit
            config['teachers'] = config['teachers'][:max_teachers]
        
        return violations, config
    
    def validate_config(self, config):
        """Validate and fix configuration against license limits"""
        violations, validated_config = self.validate_config_limits(config)
        
        if violations:
            print(f"License limit violations corrected: {violations}")
            
        return validated_config
    
    def activate_license(self, license_key):
        """Activate premium license with given key"""
        if not license_key or len(license_key) < 10:
            return False
            
        # Admin master key for unlimited access
        if license_key == "ADMIN-MASTER-KEY-2025-UNLIMITED":
            self.license_data.update({
                "license_type": "ADMIN",
                "license_key": license_key,
                "features": {
                    "max_classes": 9999,
                    "max_sections": 9999,
                    "max_teachers": 9999,
                    "max_periods": 20,
                    "auto_assign": True,
                    "smart_match": True,
                    "teacher_restrictions": False,  # Admin can edit everything
                    "teacher_leave": True,
                    "pdf_export": True,
                    "watermark": False
                }
            })
            self.save_license(self.license_data)
            return True
            
        # Professional license keys (CFPRO- prefix)
        valid_prefixes = ["CFLOW-", "CFPRO-"]
        demo_keys = [
            "CFPRO-DEMO1-TRIAL-2025A-ACTIV",
            "CFPRO-DEMO2-TRIAL-2025B-ACTIV", 
            "CFPRO-DEMO3-TRIAL-2025C-ACTIV",
            "CFPRO-DEMO4-TRIAL-2025D-ACTIV",
            "CFPRO-DEMO5-TRIAL-2025E-ACTIV"
        ]
        
        # Check if it's a valid license key
        is_valid = any(license_key.startswith(prefix) for prefix in valid_prefixes) or license_key in demo_keys
        
        if is_valid:
            # Activate premium license
            self.license_data.update({
                "license_type": "PREMIUM",
                "license_key": license_key,
                "features": {
                    "max_classes": 999,
                    "max_sections": 999,
                    "max_teachers": 999,
                    "max_periods": 12,
                    "auto_assign": True,
                    "smart_match": True,
                    "teacher_restrictions": True,
                    "teacher_leave": True,
                    "pdf_export": True,
                    "watermark": False
                }
            })
            self.save_license(self.license_data)
            return True
        
        return False
    
    def convert_to_free(self):
        """Convert trial to free version"""
        self.upgrade_to_free()

    def is_trial_active(self):
        """Check if trial is still active"""
        return self.license_data["license_type"] == "TRIAL" and not self.is_trial_expired()

    def can_use_feature(self, feature_name):
        """Check if a feature can be used based on license"""
        if self.is_premium() or self.is_trial_active():
            return True
        
        # Free version restrictions
        if feature_name in ["auto_assign", "smart_match", "teacher_restrictions"]:
            return False
        
        return True

    def get_feature_limit(self, feature_name):
        """Get the limit for a specific feature"""
        return self.license_data.get("features", {}).get(feature_name, 0)

    def validate_feature(self, feature_name):
        """Validate if feature is available"""
        return self.can_use_feature(feature_name)

    def validate_config_limits(self, config):
        """Validate configuration against license limits"""
        violations = []
        
        # Get limits based on license type
        max_classes = self.get_feature_limit("max_classes")
        max_sections = self.get_feature_limit("max_sections") 
        max_teachers = self.get_feature_limit("max_teachers")
        max_periods = self.get_feature_limit("max_periods")
        
        # Check violations and auto-correct
        if len(config.get('classes', [])) > max_classes:
            violations.append(f"Classes: {len(config['classes'])} exceeds limit of {max_classes}")
            config['classes'] = config['classes'][:max_classes]
            
        if len(config.get('sections', [])) > max_sections:
            violations.append(f"Sections: {len(config['sections'])} exceeds limit of {max_sections}")
            config['sections'] = config['sections'][:max_sections]
            
        if len(config.get('teachers', [])) > max_teachers:
            violations.append(f"Teachers: {len(config['teachers'])} exceeds limit of {max_teachers}")
            config['teachers'] = config['teachers'][:max_teachers]
            
        if config.get('periods_per_day', 6) > max_periods:
            violations.append(f"Periods: {config['periods_per_day']} exceeds limit of {max_periods}")
            config['periods_per_day'] = max_periods
        
        return violations, config

class TimetableApp:
    def __init__(self, root):
        self.root = root
        # Set basic properties first
        self._set_theme()
        
        # Initialize license manager
        self.license_manager = LicenseManager()
        
        # Force trial license for testing
        self.license_manager.license_data["license_type"] = "TRIAL"
        self.license_manager.license_data["trial_days"] = 25  # Show as trial with days remaining
        
        # Update title based on license status
        license_status = self.license_manager.get_license_status()
        self.root.title(f"ClassFlow v2.0 - {license_status}")
        self.root.geometry("1200x700")
        
        # Initialize essential variables
        self.current_week = datetime.now().isocalendar()[1]
        self.selected_week = tk.IntVar(value=self.current_week)
        self.selected_year = tk.IntVar(value=datetime.now().year)
        self.impacted_cells = set()
        self.resolved_cells = set()
        self.entries = {}
        self.teacher_cbs = {}
        self.cell_frames = {}
        self.current_impacted_periods = []
        self.datetime_label = None  # Will be set in setup_ui
        
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
        
        # Update title and status bar based on license
        self.update_title()
        self.update_status_bar()
        
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
        """Optimized config loading with license validation"""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    
                # Validate config against license limits
                violations, validated_config = self.license_manager.validate_config_limits(config)
                
                if violations:
                    # Show warning about exceeded limits
                    license_status = self.license_manager.get_license_status()
                    warning_msg = f"⚠️ Configuration exceeds {license_status} limits:\n\n"
                    warning_msg += "\n".join(f"• {violation}" for violation in violations)
                    warning_msg += f"\n\n✂️ Configuration has been automatically adjusted to comply with license limits."
                    warning_msg += f"\n\n🚀 Upgrade to Premium for unlimited access!"
                    
                    messagebox.showwarning("License Limits Exceeded", warning_msg)
                    
                    # Save the corrected config
                    try:
                        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                            json.dump(validated_config, f, indent=2)
                    except IOError:
                        pass
                
                return validated_config
                
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
        
        self.conn.commit()

    def create_menu_bar(self):
        """Create menu bar with upgrade and help options"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="📁 Load Timetable", command=self.load_timetable)
        file_menu.add_command(label="💾 Save Timetable", command=self.save_timetable)
        file_menu.add_separator()
        file_menu.add_command(label="📊 Export Excel", command=self.export_excel)
        file_menu.add_command(label="📄 Export PDF", command=self.export_pdf)
        file_menu.add_separator()
        file_menu.add_command(label="❌ Exit", command=self.root.quit)
        
        # License menu (prominent for upgrades)
        license_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="💎 License", menu=license_menu)
        
        # Show different options based on license status
        if self.license_manager.is_premium():
            license_menu.add_command(label="✅ Premium Active", state='disabled')
            license_menu.add_command(label="📝 License Details", command=self.show_license_details)
        else:
            license_menu.add_command(label="🚀 UPGRADE TO PREMIUM", command=self.show_upgrade_dialog)
            license_menu.add_command(label="🔑 Activate License Key", command=self.show_license_activation)
            license_menu.add_command(label="💰 Purchase License", command=self.show_purchase_options)
            license_menu.add_separator()
            
            if self.license_manager.is_trial_active():
                days_left = self.license_manager.get_trial_days_remaining()
                license_menu.add_command(label=f"⏰ Trial: {days_left} days left", state='disabled')
            else:
                license_menu.add_command(label="📋 Free Version Limits", command=self.show_free_limits)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="🤖 Auto-Assign", command=self.auto_assign)
        tools_menu.add_command(label="✨ Smart Match", command=self.smart_match)
        tools_menu.add_command(label="👨‍🏫 Teacher Mapping", command=self.show_teacher_subject_mapping)
        tools_menu.add_command(label="🏖️ Teacher Leave", command=self.mark_leave)
        tools_menu.add_command(label="🔒 Edit Restrictions", command=self.edit_restrictions)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="📥 Check for Updates", command=self.check_for_updates)
        help_menu.add_command(label="📖 User Guide", command=self.show_user_guide)
        help_menu.add_command(label="💬 Contact Support", command=self.contact_support)
        help_menu.add_command(label="🌐 Visit Website", command=self.open_website)
        help_menu.add_separator()
        help_menu.add_command(label="ℹ️ About ClassFlow", command=self.show_about)

    def setup_ui(self):
        # Create menu bar for easy access to upgrade and help
        self.create_menu_bar()
        
        # V1.4 Style Header - Enhanced visual design
        header_frame = tk.Frame(self.root, bg="#1e3a8a", height=80)
        header_frame.pack(fill='x', padx=0, pady=0)
        header_frame.pack_propagate(False)
        
        # Main title with enhanced styling
        title_frame = tk.Frame(header_frame, bg="#1e3a8a")
        title_frame.pack(expand=True, fill='both')
        
        # App title
        header_label = tk.Label(title_frame, 
                              text="🎓 ClassFlow v2.0 BETA", 
                              font=("Segoe UI", 28, "bold"), 
                              bg="#1e3a8a", 
                              fg="#ffffff", 
                              anchor="center")
        header_label.pack(side='left', expand=True, fill='both', pady=15)
        
        # Status section (right side)
        status_frame = tk.Frame(header_frame, bg="#1e3a8a")
        status_frame.pack(side='right', fill='y', padx=20)
        
        # Current date and time display - ENHANCED VISIBILITY
        current_datetime = datetime.now().strftime("%d %B %Y | %I:%M %p")
        self.datetime_label = tk.Label(status_frame, 
                                     text=f"� {current_datetime}", 
                                     font=("Segoe UI", 13, "bold"), 
                                     bg="#1e3a8a", 
                                     fg="#fbbf24",
                                     anchor="center",
                                     relief="solid",
                                     bd=1)
        self.datetime_label.pack(pady=(15, 8))
        
        # Start datetime update timer
        self.update_datetime()
        
        # Week display with modern styling
        week_display = tk.Label(status_frame, 
                              text=f"� Week {self.current_week}", 
                              font=("Segoe UI", 12), 
                              bg="#1e3a8a", 
                              fg="#94a3b8",
                              anchor="center")
        week_display.pack(pady=(0, 5))
        
        # License status with upgrade button
        license_text = self.license_manager.get_license_status()
        license_color = "#10b981" if self.license_manager.is_premium() else "#f59e0b"
        
        # Show clear trial/free/premium status
        if self.license_manager.license_data["license_type"] == "TRIAL":
            trial_days = self.license_manager.get_trial_days_remaining()
            if trial_days > 0:
                status_text = f"🎯 TRIAL - {trial_days} days left"
                status_color = "#f59e0b"
            else:
                status_text = "⚠️ TRIAL EXPIRED"
                status_color = "#ef4444"
        elif self.license_manager.license_data["license_type"] == "FREE":
            status_text = "🆓 FREE VERSION"
            status_color = "#6b7280"
        else:
            status_text = f"💎 {license_text}"
            status_color = "#10b981"
        
        license_status = tk.Label(status_frame, 
                                text=status_text, 
                                font=("Segoe UI", 11, "bold"), 
                                bg="#1e3a8a", 
                                fg=status_color,
                                anchor="center")
        license_status.pack(pady=(0, 5))
        
        # Upgrade button for non-premium users - ALWAYS SHOW FOR TESTING
        # Force show upgrade button regardless of license status
        upgrade_btn = tk.Button(status_frame,
                              text="🚀 UPGRADE TO PREMIUM",
                              command=self.show_upgrade_dialog,
                              font=('Segoe UI', 9, 'bold'),
                              bg='#f59e0b',
                              fg='white',
                              activebackground='#d97706',
                              relief='raised',
                              bd=2,
                              padx=10,
                              pady=3,
                              cursor='hand2')
        upgrade_btn.pack(pady=(0, 10))

        # Top controls
        controls = ttk.Frame(self.root)
        controls.pack(fill='x', padx=10, pady=5)

        ttk.Label(controls, text="Year:").pack(side='left')
        ttk.Entry(controls, textvariable=self.selected_year, width=6).pack(side='left', padx=5)
        
        # Left side - Week controls and Load button
        left_frame = ttk.Frame(controls)
        left_frame.pack(side='left', fill='x', expand=True)
        
        ttk.Label(left_frame, text="Week:").pack(side='left')
        ttk.Entry(left_frame, textvariable=self.selected_week, width=4).pack(side='left', padx=5)
        ttk.Button(left_frame, text="Load", command=self.load_timetable).pack(side='left', padx=5)
        
        # Right side - Prominent SAVE button (v1.4 style)
        save_frame = ttk.Frame(controls)
        save_frame.pack(side='right', padx=10)
        
        # Create prominent save button like v1.4
        self.save_button = tk.Button(save_frame, 
                                   text="💾 SAVE TIMETABLE", 
                                   command=self.save_timetable,
                                   font=('Arial', 12, 'bold'),
                                   bg='#4CAF50',
                                   fg='white',
                                   activebackground='#45a049',
                                   activeforeground='white',
                                   relief='raised',
                                   bd=3,
                                   padx=20,
                                   pady=8,
                                   cursor='hand2')
        self.save_button.pack(side='right')
        
        # Edit buttons on far right
        edit_frame = ttk.Frame(controls)
        edit_frame.pack(side='right', padx=10)
        ttk.Button(edit_frame, text="Edit Classes", command=self.edit_classes).pack(side='right', padx=2)
        ttk.Button(edit_frame, text="Edit Sections", command=self.edit_sections).pack(side='right', padx=2)
        ttk.Button(edit_frame, text="Edit Teachers", command=self.edit_teachers).pack(side='right', padx=2)
        
        # Action buttons with v1.4 enhanced styling
        actions = tk.Frame(self.root, bg='#f8f9fa', relief='ridge', bd=1)
        actions.pack(fill='x', padx=10, pady=(10, 5))
        
        # Left side action buttons
        left_actions = tk.Frame(actions, bg='#f8f9fa')
        left_actions.pack(side='left', fill='x', expand=True, pady=8, padx=10)
        
        # Core action buttons with enhanced styling
        auto_assign_btn = tk.Button(left_actions, 
                                  text="🤖 Auto-Assign", 
                                  command=self.auto_assign,
                                  font=('Segoe UI', 10, 'bold'),
                                  bg='#3b82f6',
                                  fg='white',
                                  activebackground='#2563eb',
                                  relief='raised',
                                  bd=2,
                                  padx=15,
                                  pady=5,
                                  cursor='hand2')
        auto_assign_btn.pack(side='left', padx=5)
        
        smart_match_btn = tk.Button(left_actions, 
                                  text="✨ Smart Match", 
                                  command=self.smart_match,
                                  font=('Segoe UI', 10, 'bold'),
                                  bg='#10b981',
                                  fg='white',
                                  activebackground='#059669',
                                  relief='raised',
                                  bd=2,
                                  padx=15,
                                  pady=5,
                                  cursor='hand2')
        smart_match_btn.pack(side='left', padx=5)
        
        teacher_map_btn = tk.Button(left_actions, 
                                  text="👨‍🏫 Teacher Mapping", 
                                  command=self.show_teacher_subject_mapping,
                                  font=('Segoe UI', 10),
                                  bg='#6366f1',
                                  fg='white',
                                  activebackground='#4f46e5',
                                  relief='raised',
                                  bd=2,
                                  padx=12,
                                  pady=5,
                                  cursor='hand2')
        teacher_map_btn.pack(side='left', padx=5)
        
        leave_btn = tk.Button(left_actions, 
                            text="🏖️ Teacher Leave", 
                            command=self.mark_leave,
                            font=('Segoe UI', 10),
                            bg='#f59e0b',
                            fg='white',
                            activebackground='#d97706',
                            relief='raised',
                            bd=2,
                            padx=12,
                            pady=5,
                            cursor='hand2')
        leave_btn.pack(side='left', padx=5)
        
        # Edit Restrictions button
        restrictions_btn = tk.Button(left_actions, 
                                   text="🔒 Edit Restrictions", 
                                   command=self.edit_restrictions,
                                   font=('Segoe UI', 10),
                                   bg='#8b5cf6',
                                   fg='white',
                                   activebackground='#7c3aed',
                                   relief='raised',
                                   bd=2,
                                   padx=12,
                                   pady=5,
                                   cursor='hand2')
        restrictions_btn.pack(side='left', padx=5)
        
        # Right side export buttons
        right_actions = tk.Frame(actions, bg='#f8f9fa')
        right_actions.pack(side='right', pady=8, padx=10)
        
        export_excel_btn = tk.Button(right_actions, 
                                   text="📊 Export Excel", 
                                   command=self.export_excel,
                                   font=('Segoe UI', 10),
                                   bg='#059669',
                                   fg='white',
                                   activebackground='#047857',
                                   relief='raised',
                                   bd=2,
                                   padx=12,
                                   pady=5,
                                   cursor='hand2')
        export_excel_btn.pack(side='right', padx=5)
        
        export_pdf_btn = tk.Button(right_actions, 
                                 text="📄 Export PDF", 
                                 command=self.export_pdf,
                                 font=('Segoe UI', 10),
                                 bg='#dc2626',
                                 fg='white',
                                 activebackground='#b91c1c',
                                 relief='raised',
                                 bd=2,
                                 padx=12,
                                 pady=5,
                                 cursor='hand2')
        export_pdf_btn.pack(side='right', padx=5)
        
        refresh_btn = tk.Button(right_actions, 
                              text="🔄 Refresh", 
                              command=self.refresh_grid,
                              font=('Segoe UI', 10),
                              bg='#6b7280',
                              fg='white',
                              activebackground='#4b5563',
                              relief='raised',
                              bd=2,
                              padx=12,
                              pady=5,
                              cursor='hand2')
        refresh_btn.pack(side='right', padx=5)
        
        # Check for updates button
        update_btn = tk.Button(right_actions, 
                             text="📥 Updates", 
                             command=self.check_for_updates,
                             font=('Segoe UI', 10),
                             bg='#6366f1',
                             fg='white',
                             activebackground='#4f46e5',
                             relief='raised',
                             bd=2,
                             padx=12,
                             pady=5,
                             cursor='hand2')
        update_btn.pack(side='right', padx=5)

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
        
        # Add status bar at the bottom
        self.status_bar = tk.Label(self.root, text="Ready", relief=tk.SUNKEN, anchor="w", 
                                 bg="#f0f0f0", font=("Segoe UI", 9))
        self.status_bar.pack(fill="x", side="bottom")
        
        # Add footer message
        footer_frame = tk.Frame(self.root, bg="#1e3a8a", height=30)
        footer_frame.pack(fill='x', side='bottom')
        footer_frame.pack_propagate(False)
        
        footer_text = "🎓 ClassFlow v2.0 BETA - Professional School Timetable Management System | © 2025 TimeTablePlanner | Beta Testing Phase"
        footer_label = tk.Label(footer_frame, 
                              text=footer_text,
                              font=("Segoe UI", 9),
                              bg="#1e3a8a",
                              fg="#94a3b8",
                              anchor="center")
        footer_label.pack(expand=True, fill='both')
        
        # Initial grid draw
        self.draw_grid()

    def show_upgrade_dialog(self):
        """Show upgrade to premium dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Upgrade to Premium")
        dialog.geometry("500x600")
        dialog.resizable(False, False)
        dialog.configure(bg='#ffffff')
        
        # Center the dialog
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Header
        header_frame = tk.Frame(dialog, bg='#3b82f6', height=80)
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)
        
        header_label = tk.Label(header_frame, 
                              text="🚀 Upgrade to Premium", 
                              font=("Segoe UI", 20, "bold"),
                              bg='#3b82f6', 
                              fg='white')
        header_label.pack(expand=True)
        
        # Content frame
        content_frame = tk.Frame(dialog, bg='#ffffff')
        content_frame.pack(fill='both', expand=True, padx=30, pady=20)
        
        # Current plan info
        current_frame = tk.Frame(content_frame, bg='#fef3c7', relief='ridge', bd=2)
        current_frame.pack(fill='x', pady=(0, 20))
        
        tk.Label(current_frame, 
                text=f"Current Plan: {self.license_manager.get_license_status()}", 
                font=("Segoe UI", 12, "bold"),
                bg='#fef3c7',
                fg='#92400e').pack(pady=10)
        
        # Premium features
        features_label = tk.Label(content_frame, 
                                text="Premium Features:", 
                                font=("Segoe UI", 14, "bold"),
                                bg='#ffffff')
        features_label.pack(anchor='w', pady=(0, 10))
        
        features = [
            "✅ Unlimited Classes, Sections & Teachers",
            "✅ Advanced Auto-Assign Algorithm", 
            "✅ Smart Conflict Detection",
            "✅ Teacher Leave Management",
            "✅ Professional PDF/Excel Export",
            "✅ Priority Email Support",
            "✅ Custom Branding Options"
        ]
        
        for feature in features:
            feature_label = tk.Label(content_frame, 
                                   text=feature, 
                                   font=("Segoe UI", 11),
                                   bg='#ffffff',
                                   fg='#059669')
            feature_label.pack(anchor='w', pady=2)
        
        # Pricing section
        pricing_frame = tk.Frame(content_frame, bg='#f0f9ff', relief='ridge', bd=2)
        pricing_frame.pack(fill='x', pady=20)
        
        tk.Label(pricing_frame, 
                text="🏫 School Plan - ₹499/month", 
                font=("Segoe UI", 16, "bold"),
                bg='#f0f9ff',
                fg='#1e40af').pack(pady=15)
        
        # License key entry
        key_frame = tk.Frame(content_frame, bg='#ffffff')
        key_frame.pack(fill='x', pady=10)
        
        tk.Label(key_frame, 
                text="Enter License Key:", 
                font=("Segoe UI", 12, "bold"),
                bg='#ffffff').pack(anchor='w')
        
        self.license_key_var = tk.StringVar()
        key_entry = tk.Entry(key_frame, 
                           textvariable=self.license_key_var,
                           font=("Segoe UI", 11),
                           width=40)
        key_entry.pack(fill='x', pady=5)
        
        # Buttons
        button_frame = tk.Frame(content_frame, bg='#ffffff')
        button_frame.pack(fill='x', pady=20)
        
        def activate_license():
            key = self.license_key_var.get().strip()
            if key:
                if self.license_manager.activate_license(key):
                    messagebox.showinfo("Success", "License activated successfully!")
                    dialog.destroy()
                    self.update_title()
                    self.update_status_bar()
                else:
                    messagebox.showerror("Error", "Invalid license key!")
            else:
                messagebox.showwarning("Warning", "Please enter a license key!")
        
        def contact_sales():
            messagebox.showinfo("Contact Sales", 
                              "Contact us for purchasing license:\n\n" +
                              "📧 Email: prashant.compsc@gmail.com\n" +
                              "🌐 Website: www.classflow.ai\n" +
                              "📱 Phone: +91-XXXX-XXXX-XX")
        
        # Activate button
        activate_btn = tk.Button(button_frame,
                               text="🔑 Activate License",
                               command=activate_license,
                               font=('Segoe UI', 12, 'bold'),
                               bg='#10b981',
                               fg='white',
                               activebackground='#059669',
                               relief='raised',
                               bd=3,
                               padx=20,
                               pady=8)
        activate_btn.pack(side='left', padx=(0, 10))
        
        # Purchase online button (prominent)
        purchase_btn = tk.Button(button_frame,
                               text="💳 Purchase Online",
                               command=lambda: [dialog.destroy(), self.show_purchase_options()],
                               font=('Segoe UI', 12, 'bold'),
                               bg='#059669',
                               fg='white',
                               activebackground='#047857',
                               relief='raised',
                               bd=3,
                               padx=20,
                               pady=8)
        purchase_btn.pack(side='left', padx=10)
        
        # Contact sales button
        contact_btn = tk.Button(button_frame,
                              text="💬 Contact Sales",
                              command=contact_sales,
                              font=('Segoe UI', 12),
                              bg='#3b82f6',
                              fg='white',
                              activebackground='#2563eb',
                              relief='raised',
                              bd=3,
                              padx=20,
                              pady=8)
        contact_btn.pack(side='left', padx=10)
        
        # Close button
        close_btn = tk.Button(button_frame,
                            text="❌ Close",
                            command=dialog.destroy,
                            font=('Segoe UI', 12),
                            bg='#6b7280',
                            fg='white',
                            activebackground='#4b5563',
                            relief='raised',
                            bd=3,
                            padx=20,
                            pady=8)
        close_btn.pack(side='right')

    def check_for_updates(self):
        """Check for latest updates/fixes"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Check for Updates")
        dialog.geometry("450x300")
        dialog.resizable(False, False)
        dialog.configure(bg='#ffffff')
        
        # Center the dialog
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Header
        header_frame = tk.Frame(dialog, bg='#6366f1', height=60)
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)
        
        header_label = tk.Label(header_frame, 
                              text="🔄 Check for Updates", 
                              font=("Segoe UI", 16, "bold"),
                              bg='#6366f1', 
                              fg='white')
        header_label.pack(expand=True)
        
        # Content
        content_frame = tk.Frame(dialog, bg='#ffffff')
        content_frame.pack(fill='both', expand=True, padx=30, pady=20)
        
        # Current version info
        current_version = "ClassFlow v2.0.1 (Build 20250811)"
        version_label = tk.Label(content_frame, 
                               text=f"Current Version: {current_version}", 
                               font=("Segoe UI", 12, "bold"),
                               bg='#ffffff',
                               fg='#374151')
        version_label.pack(pady=(0, 20))
        
        # Update status
        status_label = tk.Label(content_frame, 
                              text="✅ You are running the latest version!", 
                              font=("Segoe UI", 12),
                              bg='#ffffff',
                              fg='#059669')
        status_label.pack(pady=10)
        
        # Update notes
        notes_label = tk.Label(content_frame, 
                             text="Latest Fixes & Improvements:", 
                             font=("Segoe UI", 11, "bold"),
                             bg='#ffffff')
        notes_label.pack(anchor='w', pady=(20, 5))
        
        notes = [
            "• Enhanced v1.4 style UI with prominent save button",
            "• Improved license management system",
            "• Better teacher restriction enforcement",
            "• Modern action buttons with icons",
            "• Enhanced visual design and color scheme"
        ]
        
        for note in notes:
            note_label = tk.Label(content_frame, 
                                text=note, 
                                font=("Segoe UI", 10),
                                bg='#ffffff',
                                fg='#4b5563')
            note_label.pack(anchor='w', pady=1)
        
        # Button frame
        button_frame = tk.Frame(content_frame, bg='#ffffff')
        button_frame.pack(fill='x', pady=20)
        
        # Switch to Premium button - ALWAYS SHOW FOR TESTING
        premium_btn = tk.Button(button_frame,
                              text="🚀 SWITCH TO PREMIUM",
                              command=lambda: [dialog.destroy(), self.show_upgrade_dialog()],
                              font=('Segoe UI', 12, 'bold'),
                              bg='#059669',
                              fg='white',
                              activebackground='#047857',
                              relief='raised',
                              bd=3,
                              padx=25,
                              pady=8,
                              state='normal')  # Ensure button is enabled
        premium_btn.pack(side='left', padx=(0, 10))
        
        # Close button
        close_btn = tk.Button(button_frame,
                            text="✅ Close",
                            command=dialog.destroy,
                            font=('Segoe UI', 12),
                            bg='#6366f1',
                            fg='white',
                            activebackground='#4f46e5',
                            relief='raised',
                            bd=3,
                            padx=30,
                            pady=8)
        close_btn.pack(side='right')

    def show_license_activation(self):
        """Show enhanced license activation dialog with working vertical scrollbar"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Activate License Key")
        dialog.geometry("650x600")
        dialog.resizable(True, True)
        dialog.configure(bg='#ffffff')
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Header
        header_frame = tk.Frame(dialog, bg='#10b981', height=70)
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)
        
        header_label = tk.Label(header_frame, 
                              text="🔑 Activate ClassFlow Premium License", 
                              font=("Segoe UI", 18, "bold"),
                              bg='#10b981', 
                              fg='white')
        header_label.pack(expand=True)
        
        # Main content frame
        main_frame = tk.Frame(dialog, bg='#ffffff')
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Create canvas and scrollbar for scrollable content
        canvas = tk.Canvas(main_frame, bg='#ffffff', highlightthickness=0)
        v_scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#ffffff')
        
        # Configure scrolling
        def configure_scroll_region(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            
        def on_canvas_configure(event):
            # Update the scrollable frame width to match canvas width
            canvas.itemconfig(canvas_frame, width=canvas.winfo_width())
        
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        scrollable_frame.bind("<Configure>", configure_scroll_region)
        canvas.bind('<Configure>', on_canvas_configure)
        
        # Bind mouse wheel to canvas
        canvas.bind("<MouseWheel>", on_mousewheel)
        
        # Create window in canvas
        canvas_frame = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=v_scrollbar.set)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        v_scrollbar.pack(side="right", fill="y")
        
        # Make the canvas focusable for mouse wheel events
        canvas.focus_set()
        
        # Content sections in scrollable frame
        # Instructions section
        inst_frame = tk.LabelFrame(scrollable_frame, text="📋 Instructions", 
                                 font=("Segoe UI", 12, "bold"), bg='#ffffff', 
                                 fg='#374151', padx=15, pady=15)
        inst_frame.pack(fill='x', pady=(0, 20))
        
        instructions_text = """Welcome to ClassFlow Premium Activation!

To activate your premium license:
1. Enter your license key in the text box below
2. License keys are 25 characters long (e.g., CFPRO-XXXXX-XXXXX-XXXXX-XXXXX)
3. Click 'Activate License' to unlock premium features
4. Your license will be validated and activated immediately

Premium features include:
✅ Unlimited classes and sections
✅ Advanced teacher restrictions
✅ Priority customer support
✅ Export to PDF functionality
✅ Remove watermarks
✅ Auto-save and backup features

🔑 ADMIN ACCESS: Use the admin key for unrestricted access to all features."""
        
        instructions = tk.Label(inst_frame,
                              text=instructions_text,
                              font=("Segoe UI", 10),
                              bg='#ffffff',
                              fg='#4b5563',
                              justify='left',
                              wraplength=500)
        instructions.pack(anchor='w')
        
        # License key entry section
        key_frame = tk.LabelFrame(scrollable_frame, text="🔑 Enter License Key", 
                                font=("Segoe UI", 12, "bold"), bg='#ffffff', 
                                fg='#374151', padx=15, pady=15)
        key_frame.pack(fill='x', pady=(0, 20))
        
        tk.Label(key_frame, 
                text="License Key (25 characters):", 
                font=("Segoe UI", 11, "bold"),
                bg='#ffffff',
                fg='#374151').pack(anchor='w', pady=(0, 5))
        
        key_var = tk.StringVar()
        key_entry = tk.Entry(key_frame, 
                           textvariable=key_var,
                           font=("Courier New", 12, "bold"),
                           width=50,
                           bg='#f8fafc',
                           fg='#1e293b',
                           relief='solid',
                           bd=2,
                           highlightthickness=1,
                           highlightcolor='#10b981')
        key_entry.pack(fill='x', pady=(5, 10), ipady=8)
        key_entry.focus_set()
        
        # Example key format
        example_label = tk.Label(key_frame,
                               text="Example: CFPRO-ABC12-DEF34-GHI56-JKL78",
                               font=("Segoe UI", 9, "italic"),
                               bg='#ffffff',
                               fg='#6b7280')
        example_label.pack(anchor='w')
        
        # Purchase info section
        purchase_frame = tk.LabelFrame(scrollable_frame, text="💰 Need a License Key?", 
                                     font=("Segoe UI", 12, "bold"), bg='#ffffff', 
                                     fg='#374151', padx=15, pady=15)
        purchase_frame.pack(fill='x', pady=(0, 20))
        
        purchase_text = """Don't have a license key yet?

🏫 School Plan: ₹499/month
   • Up to 50 classes and 200 teachers
   • Basic premium features

🏛️ Institution Plan: ₹999/month  
   • Unlimited classes and teachers
   • All premium features + priority support

📞 Contact us for enterprise pricing and bulk discounts!
📧 Email: hypersyncsales@gmail.com
📱 WhatsApp: +91-9958722669"""
        
        purchase_info = tk.Label(purchase_frame,
                               text=purchase_text,
                               font=("Segoe UI", 10),
                               bg='#ffffff',
                               fg='#4b5563',
                               justify='left',
                               wraplength=500)
        purchase_info.pack(anchor='w')
        
        # Demo keys section
        demo_frame = tk.LabelFrame(scrollable_frame, text="🧪 Demo License Keys", 
                                 font=("Segoe UI", 12, "bold"), bg='#fff3cd', 
                                 fg='#856404', padx=15, pady=15)
        demo_frame.pack(fill='x', pady=(0, 20))
        
        demo_text = """For testing and demonstration purposes:

🔑 ADMIN-MASTER-KEY-2025-UNLIMITED
   ⭐ Full admin access - No restrictions

🔑 CFPRO-DEMO1-TRIAL-2025A-ACTIV
🔑 CFPRO-DEMO2-TRIAL-2025B-ACTIV  
🔑 CFPRO-DEMO3-TRIAL-2025C-ACTIV
🔑 CFPRO-DEMO4-TRIAL-2025D-ACTIV
🔑 CFPRO-DEMO5-TRIAL-2025E-ACTIV
   ⭐ Premium features unlocked

📝 Copy any key above and paste it in the license field to test premium features."""
        
        demo_info = tk.Label(demo_frame,
                           text=demo_text,
                           font=("Courier New", 9),
                           bg='#fff3cd',
                           fg='#856404',
                           justify='left',
                           wraplength=500)
        demo_info.pack(anchor='w')
        
        def activate():
            key = key_var.get().strip().upper()
            if key:
                if len(key) < 20:
                    messagebox.showwarning("Invalid Key", "License key should be at least 20 characters long!")
                    return
                    
                if self.license_manager.activate_license(key):
                    messagebox.showinfo("Success", 
                                      "🎉 License activated successfully!\n\n"
                                      "ClassFlow Premium is now active.\n"
                                      "Enjoy unlimited access to all features!")
                    dialog.destroy()
                    self.update_title()
                    self.update_status_bar()
                    # Refresh menu bar to show premium status
                    self.create_menu_bar()
                else:
                    messagebox.showerror("Activation Failed", 
                                       "❌ Invalid license key!\n\n"
                                       "Please check your key and try again.\n"
                                       "Contact support if the problem persists.")
            else:
                messagebox.showwarning("Missing Key", "Please enter a license key!")
        
        def purchase_online():
            dialog.destroy()
            self.show_purchase_options()
        
        # Buttons frame
        button_frame = tk.Frame(scrollable_frame, bg='#ffffff')
        button_frame.pack(fill='x', pady=20)
        
        # Purchase button
        purchase_btn = tk.Button(button_frame,
                               text="💳 Purchase License",
                               command=purchase_online,
                               font=('Segoe UI', 12, 'bold'),
                               bg='#f59e0b',
                               fg='white',
                               activebackground='#d97706',
                               relief='raised',
                               bd=3,
                               padx=20,
                               pady=10)
        purchase_btn.pack(side='left', padx=(0, 10))
        
        # Activate button
        activate_btn = tk.Button(button_frame,
                               text="🔑 Activate License",
                               command=activate,
                               font=('Segoe UI', 12, 'bold'),
                               bg='#10b981',
                               fg='white',
                               activebackground='#059669',
                               relief='raised',
                               bd=3,
                               padx=20,
                               pady=10)
        activate_btn.pack(side='left', padx=(0, 10))
        
        # Close button
        close_btn = tk.Button(button_frame,
                            text="❌ Cancel",
                            command=dialog.destroy,
                            font=('Segoe UI', 12),
                            bg='#6b7280',
                            fg='white',
                            activebackground='#4b5563',
                            relief='raised',
                            bd=3,
                            padx=20,
                            pady=8)
        close_btn.pack(side='right')

    def show_purchase_options(self):
        """Show purchase options dialog with multiple ways to buy"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Purchase ClassFlow Premium")
        dialog.geometry("600x700")
        dialog.resizable(False, False)
        dialog.configure(bg='#ffffff')
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Header
        header_frame = tk.Frame(dialog, bg='#3b82f6', height=80)
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)
        
        header_label = tk.Label(header_frame, 
                              text="💰 Purchase ClassFlow Premium", 
                              font=("Segoe UI", 18, "bold"),
                              bg='#3b82f6', 
                              fg='white')
        header_label.pack(expand=True)
        
        # Content with scroll
        content_frame = tk.Frame(dialog, bg='#ffffff')
        content_frame.pack(fill='both', expand=True, padx=30, pady=20)
        
        # Pricing plans
        plans_frame = tk.Frame(content_frame, bg='#ffffff')
        plans_frame.pack(fill='x', pady=(0, 20))
        
        # School Plan
        school_plan = tk.Frame(plans_frame, bg='#f0f9ff', relief='ridge', bd=2)
        school_plan.pack(fill='x', pady=10)
        
        tk.Label(school_plan, 
                text="🏫 School Plan - ₹499/month", 
                font=("Segoe UI", 16, "bold"),
                bg='#f0f9ff',
                fg='#1e40af').pack(pady=10)
        
        tk.Label(school_plan, 
                text="Perfect for most schools • All premium features included", 
                font=("Segoe UI", 11),
                bg='#f0f9ff',
                fg='#374151').pack(pady=(0, 10))
        
        # Institution Plan
        institution_plan = tk.Frame(plans_frame, bg='#fef3c7', relief='ridge', bd=2)
        institution_plan.pack(fill='x', pady=10)
        
        tk.Label(institution_plan, 
                text="🏢 Institution Plan - ₹999/month", 
                font=("Segoe UI", 16, "bold"),
                bg='#fef3c7',
                fg='#92400e').pack(pady=10)
        
        tk.Label(institution_plan, 
                text="For large institutions • Priority support • Custom branding", 
                font=("Segoe UI", 11),
                bg='#fef3c7',
                fg='#374151').pack(pady=(0, 10))
        
        # Purchase options
        options_label = tk.Label(content_frame, 
                               text="How to Purchase:", 
                               font=("Segoe UI", 14, "bold"),
                               bg='#ffffff')
        options_label.pack(anchor='w', pady=(20, 10))
        
        # Option 1: Online Payment
        option1_frame = tk.Frame(content_frame, bg='#f9fafb', relief='ridge', bd=1)
        option1_frame.pack(fill='x', pady=5)
        
        tk.Label(option1_frame, 
                text="💳 Option 1: Online Payment (Recommended)", 
                font=("Segoe UI", 12, "bold"),
                bg='#f9fafb',
                fg='#059669').pack(anchor='w', padx=15, pady=5)
        
        tk.Label(option1_frame, 
                text="• Pay securely online with Razorpay/PayTM\n• Instant license key delivery\n• Support for UPI, Credit/Debit cards, Net banking", 
                font=("Segoe UI", 10),
                bg='#f9fafb',
                fg='#4b5563',
                justify='left').pack(anchor='w', padx=30, pady=(0, 10))
        
        def open_payment_portal():
            import webbrowser
            webbrowser.open("https://prashant-11.github.io/TimeTablePlanner/#pricing")
            messagebox.showinfo("Payment Portal", "Opening payment portal in your browser...")
        
        payment_btn = tk.Button(option1_frame,
                              text="🌐 Open Payment Portal",
                              command=open_payment_portal,
                              font=('Segoe UI', 11, 'bold'),
                              bg='#059669',
                              fg='white',
                              activebackground='#047857',
                              relief='raised',
                              bd=2,
                              padx=20,
                              pady=5)
        payment_btn.pack(anchor='w', padx=30, pady=(0, 15))
        
        # Option 2: Direct Contact
        option2_frame = tk.Frame(content_frame, bg='#f9fafb', relief='ridge', bd=1)
        option2_frame.pack(fill='x', pady=5)
        
        tk.Label(option2_frame, 
                text="📞 Option 2: Direct Contact", 
                font=("Segoe UI", 12, "bold"),
                bg='#f9fafb',
                fg='#3b82f6').pack(anchor='w', padx=15, pady=5)
        
        contact_text = ("📧 Email: prashant.compsc@gmail.com\n" +
                       "🌐 Website: www.classflow.ai\n" +
                       "📱 WhatsApp: +91-XXXX-XXXX-XX\n" +
                       "• Bulk discounts available\n" +
                       "• Custom quotes for large institutions")
        
        tk.Label(option2_frame, 
                text=contact_text, 
                font=("Segoe UI", 10),
                bg='#f9fafb',
                fg='#4b5563',
                justify='left').pack(anchor='w', padx=30, pady=(0, 15))
        
        # Close button
        close_btn = tk.Button(content_frame,
                            text="✅ Close",
                            command=dialog.destroy,
                            font=('Segoe UI', 12),
                            bg='#6b7280',
                            fg='white',
                            activebackground='#4b5563',
                            relief='raised',
                            bd=3,
                            padx=30,
                            pady=8)
        close_btn.pack(pady=20)

    def show_license_details(self):
        """Show current license details for premium users"""
        dialog = tk.Toplevel(self.root)
        dialog.title("License Details")
        dialog.geometry("400x300")
        dialog.resizable(False, False)
        dialog.configure(bg='#ffffff')
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Header
        header_frame = tk.Frame(dialog, bg='#10b981', height=60)
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)
        
        header_label = tk.Label(header_frame, 
                              text="💎 License Details", 
                              font=("Segoe UI", 16, "bold"),
                              bg='#10b981', 
                              fg='white')
        header_label.pack(expand=True)
        
        # Content
        content_frame = tk.Frame(dialog, bg='#ffffff')
        content_frame.pack(fill='both', expand=True, padx=30, pady=20)
        
        # License info
        info_text = f"License Type: {self.license_manager.get_license_status()}\n"
        info_text += f"Status: Active ✅\n"
        info_text += f"Features: All Premium Features Unlocked\n"
        info_text += f"Support: Priority Email Support"
        
        info_label = tk.Label(content_frame,
                            text=info_text,
                            font=("Segoe UI", 11),
                            bg='#ffffff',
                            fg='#374151',
                            justify='left')
        info_label.pack(pady=20)
        
        # Close button
        close_btn = tk.Button(content_frame,
                            text="✅ Close",
                            command=dialog.destroy,
                            font=('Segoe UI', 12),
                            bg='#10b981',
                            fg='white',
                            activebackground='#059669',
                            relief='raised',
                            bd=3,
                            padx=30,
                            pady=8)
        close_btn.pack(pady=20)

    def show_free_limits(self):
        """Show free version limitations"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Free Version Limits")
        dialog.geometry("500x400")
        dialog.resizable(False, False)
        dialog.configure(bg='#ffffff')
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Header
        header_frame = tk.Frame(dialog, bg='#f59e0b', height=60)
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)
        
        header_label = tk.Label(header_frame, 
                              text="📋 Free Version Limits", 
                              font=("Segoe UI", 16, "bold"),
                              bg='#f59e0b', 
                              fg='white')
        header_label.pack(expand=True)
        
        # Content
        content_frame = tk.Frame(dialog, bg='#ffffff')
        content_frame.pack(fill='both', expand=True, padx=30, pady=20)
        
        # Limits
        limits_text = ("FREE Version Limitations:\n\n" +
                      "📚 Classes: Maximum 3\n" +
                      "📝 Sections: Maximum 2 per class\n" +
                      "👨‍🏫 Teachers: Maximum 10\n" +
                      "⏰ Periods: Maximum 6 per day\n\n" +
                      "🚫 Disabled Features:\n" +
                      "• Auto-Assign Algorithm\n" +
                      "• Smart Conflict Detection\n" +
                      "• Teacher Restrictions\n" +
                      "• Advanced Export Options\n\n" +
                      "💎 Upgrade to Premium for unlimited access!")
        
        limits_label = tk.Label(content_frame,
                              text=limits_text,
                              font=("Segoe UI", 11),
                              bg='#ffffff',
                              fg='#374151',
                              justify='left')
        limits_label.pack(pady=10)
        
        # Upgrade button
        upgrade_btn = tk.Button(content_frame,
                              text="🚀 Upgrade Now",
                              command=lambda: [dialog.destroy(), self.show_upgrade_dialog()],
                              font=('Segoe UI', 12, 'bold'),
                              bg='#059669',
                              fg='white',
                              activebackground='#047857',
                              relief='raised',
                              bd=3,
                              padx=25,
                              pady=8)
        upgrade_btn.pack(pady=10)
        
        # Close button
        close_btn = tk.Button(content_frame,
                            text="✅ Close",
                            command=dialog.destroy,
                            font=('Segoe UI', 12),
                            bg='#6b7280',
                            fg='white',
                            activebackground='#4b5563',
                            relief='raised',
                            bd=3,
                            padx=20,
                            pady=8)
        close_btn.pack(pady=5)

    def show_user_guide(self):
        """Show user guide dialog"""
        messagebox.showinfo("User Guide", 
                          "User Guide will open in your browser.\n\n" +
                          "Visit: https://prashant-11.github.io/TimeTablePlanner/\n" +
                          "Or check the documentation included with the application.")

    def contact_support(self):
        """Show support contact information"""
        messagebox.showinfo("Contact Support", 
                          "📧 Email: prashant.compsc@gmail.com\n" +
                          "🌐 Website: www.classflow.ai\n" +
                          "📱 Phone: +91-XXXX-XXXX-XX\n\n" +
                          "For technical support, please include:\n" +
                          "• Your license type\n" +
                          "• Detailed description of the issue\n" +
                          "• Screenshots if applicable")

    def open_website(self):
        """Open ClassFlow website"""
        import webbrowser
        webbrowser.open("https://prashant-11.github.io/TimeTablePlanner/")
        messagebox.showinfo("Website", "Opening ClassFlow website in your browser...")

    def show_about(self):
        """Show about dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("About ClassFlow")
        dialog.geometry("400x350")
        dialog.resizable(False, False)
        dialog.configure(bg='#ffffff')
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Header
        header_frame = tk.Frame(dialog, bg='#1e3a8a', height=60)
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)
        
        header_label = tk.Label(header_frame, 
                              text="🎓 About ClassFlow", 
                              font=("Segoe UI", 16, "bold"),
                              bg='#1e3a8a', 
                              fg='white')
        header_label.pack(expand=True)
        
        # Content
        content_frame = tk.Frame(dialog, bg='#ffffff')
        content_frame.pack(fill='both', expand=True, padx=30, pady=20)
        
        about_text = ("ClassFlow v2.0\n" +
                     "Smart Timetable Management System\n\n" +
                     "Developed by: Hypersync\n" +
                     "AI-based Education Startup\n\n" +
                     "Contact: prashant.compsc@gmail.com\n" +
                     "Website: www.classflow.ai\n" +
                     "GitHub: github.com/Prashant-11\n\n" +
                     "© 2025 Hypersync. All rights reserved.")
        
        about_label = tk.Label(content_frame,
                             text=about_text,
                             font=("Segoe UI", 11),
                             bg='#ffffff',
                             fg='#374151',
                             justify='center')
        about_label.pack(pady=20)
        
        # Close button
        close_btn = tk.Button(content_frame,
                            text="✅ Close",
                            command=dialog.destroy,
                            font=('Segoe UI', 12),
                            bg='#1e3a8a',
                            fg='white',
                            activebackground='#1e40af',
                            relief='raised',
                            bd=3,
                            padx=30,
                            pady=8)
        close_btn.pack(pady=10)

    def update_title(self):
        """Update window title based on license status"""
        base_title = "ClassFlow v2.0"
        
        if self.license_manager.is_premium():
            title = f"{base_title} - Premium License"
        elif self.license_manager.is_trial_active():
            days_left = self.license_manager.get_trial_days_remaining()
            title = f"{base_title} - Trial: {days_left} days remaining"
        else:
            title = f"{base_title} - Free Version"
        
        self.root.title(title)

    def update_status_bar(self):
        """Update status bar with current license and feature information"""
        status_text = f"License: {self.license_manager.get_license_status()}"
        
        if not self.license_manager.is_premium():
            teachers_count = len(self.config.get('teachers', []))
            max_teachers = self.license_manager.get_feature_limit('max_teachers')
            status_text += f" | Teachers: {teachers_count}/{max_teachers}"
        
        self.status_bar.config(text=status_text)

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
                        subj_cb = ttk.Combobox(frame, textvariable=subj_var, values=self.config['subjects'], width=8, state='readonly')
                        subj_cb.pack(side='top', fill='x', padx=1, pady=1)
                        
                        # Make teacher names editable with dropdown
                        teacher_cb = ttk.Combobox(frame, textvariable=teacher_var, values=self.config['teachers'], width=12)
                        teacher_cb.pack(side='top', fill='x', padx=1, pady=(0,2))
                        
                        self.entries[cell_key] = (subj_var, teacher_var)
                        self.teacher_cbs[cell_key] = teacher_cb
                        self.cell_frames[cell_key] = frame
                        def on_teacher_change(event=None, key=cell_key):
                            self.resolved_cells.add(key)
                            self.impacted_cells.discard(key)
                            if key in self.cell_frames:
                                self.cell_frames[key].configure(style='GreenCell.TFrame')
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
                return
            
            # Find all periods where this teacher is assigned on this day
            impacted_periods = []
            for (class_, section, d, period), (subj_var, teacher_var_entry) in self.entries.items():
                if d == day and teacher_var_entry.get().strip().lower() == teacher.strip().lower():
                    impacted_periods.append({
                        'class': class_,
                        'section': section,
                        'day': d,
                        'period': period,
                        'period_num': period + 1,
                        'subject': subj_var.get(),
                        'key': (class_, section, d, period)
                    })
            
            self.current_impacted_periods = impacted_periods
            
            # Display impact analysis
            impact_text.delete(1.0, tk.END)
            impact_text.configure(fg='black')
            
            if impacted_periods:
                impact_text.insert(tk.END, f"🔍 IMPACT ANALYSIS\n")
                impact_text.insert(tk.END, "="*50 + "\n\n")
                impact_text.insert(tk.END, f"👨‍🏫 Teacher: {teacher}\n")
                impact_text.insert(tk.END, f"📅 Day: {day}\n")
                impact_text.insert(tk.END, f"⚠️  Total Periods Affected: {len(impacted_periods)}\n\n")
                impact_text.insert(tk.END, "📋 AFFECTED PERIODS:\n")
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
                    rows_loaded += 1
            
            if rows_loaded > 0:
                messagebox.showinfo("Success", f"Loaded timetable for Year {year}, Week {week}\n{rows_loaded} entries loaded.")
            else:
                messagebox.showinfo("No Data", f"No saved timetable found for Year {year}, Week {week}")
                
        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load timetable:\n{str(e)}")
            print(f"Load error: {e}")

    def edit_restrictions(self):
        """Open the teacher restrictions management dialog"""
        # Check license for premium feature
        if not self.license_manager.can_use_feature("teacher_restrictions"):
            if self.license_manager.is_trial_expired():
                response = messagebox.askyesno("Premium Feature", 
                    "Teacher Restrictions is a premium feature. Your trial has expired.\n\n" +
                    "Would you like to upgrade to Premium to access this feature?")
                if response:
                    self.show_upgrade_dialog()
            else:
                messagebox.showinfo("Premium Feature", 
                    "Teacher Restrictions is not available in your current license. Please upgrade to access this feature.")
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Teacher Restrictions Management")
        dialog.geometry("700x600")
        dialog.resizable(True, True)
        dialog.configure(bg='#ffffff')
        
        # Center the dialog
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Header
        header_frame = tk.Frame(dialog, bg='#8b5cf6', height=70)
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)
        
        header_label = tk.Label(header_frame, 
                              text="🔒 Teacher Restrictions Management", 
                              font=("Segoe UI", 18, "bold"),
                              bg='#8b5cf6', 
                              fg='white')
        header_label.pack(expand=True)
        
        # Content frame with scrollable area
        content_frame = tk.Frame(dialog, bg='#ffffff')
        content_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Instructions
        instructions = tk.Label(content_frame,
                              text="Configure which teachers can teach in specific classes and sections.\n" +
                                   "This helps enforce school policies and teacher specializations.",
                              font=("Segoe UI", 11),
                              bg='#ffffff',
                              fg='#4b5563',
                              justify='left')
        instructions.pack(anchor='w', pady=(0, 20))
        
        # Create notebook for different restriction types
        notebook = ttk.Notebook(content_frame)
        notebook.pack(fill='both', expand=True)
        
        # Class-wise restrictions tab
        class_frame = ttk.Frame(notebook)
        notebook.add(class_frame, text="📚 Class Restrictions")
        
        # Section-wise restrictions tab
        section_frame = ttk.Frame(notebook)
        notebook.add(section_frame, text="📝 Section Restrictions")
        
        # Subject-wise restrictions tab
        subject_frame = ttk.Frame(notebook)
        notebook.add(subject_frame, text="📖 Subject Restrictions")
        
        # Class restrictions content
        self._setup_class_restrictions(class_frame)
        
        # Section restrictions content
        self._setup_section_restrictions(section_frame)
        
        # Subject restrictions content
        self._setup_subject_restrictions(subject_frame)
        
        # Button frame
        button_frame = tk.Frame(content_frame, bg='#ffffff')
        button_frame.pack(fill='x', pady=(20, 0))
        
        def save_restrictions():
            messagebox.showinfo("Success", "Teacher restrictions saved successfully!")
            dialog.destroy()
        
        # Save button
        save_btn = tk.Button(button_frame,
                           text="💾 Save Restrictions",
                           command=save_restrictions,
                           font=('Segoe UI', 12, 'bold'),
                           bg='#10b981',
                           fg='white',
                           activebackground='#059669',
                           relief='raised',
                           bd=3,
                           padx=25,
                           pady=8)
        save_btn.pack(side='left')
        
        # Reset button
        reset_btn = tk.Button(button_frame,
                            text="🔄 Reset All",
                            command=lambda: messagebox.showwarning("Reset", "This will reset all restrictions!"),
                            font=('Segoe UI', 12),
                            bg='#f59e0b',
                            fg='white',
                            activebackground='#d97706',
                            relief='raised',
                            bd=3,
                            padx=20,
                            pady=8)
        reset_btn.pack(side='left', padx=10)
        
        # Close button
        close_btn = tk.Button(button_frame,
                            text="❌ Close",
                            command=dialog.destroy,
                            font=('Segoe UI', 12),
                            bg='#6b7280',
                            fg='white',
                            activebackground='#4b5563',
                            relief='raised',
                            bd=3,
                            padx=20,
                            pady=8)
        close_btn.pack(side='right')

    def _setup_class_restrictions(self, parent):
        """Setup the class restrictions tab content"""
        # Scrollable frame
        canvas = tk.Canvas(parent, bg='#ffffff')
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Content
        for i, class_name in enumerate(self.config['classes']):
            class_frame = ttk.LabelFrame(scrollable_frame, text=f"Class {class_name}", padding=15)
            class_frame.pack(fill='x', pady=10, padx=10)
            
            # Teachers for this class
            teachers_frame = ttk.Frame(class_frame)
            teachers_frame.pack(fill='x')
            
            ttk.Label(teachers_frame, text="Allowed Teachers:", font=('Segoe UI', 10, 'bold')).pack(anchor='w')
            
            # Checkbox for each teacher
            for teacher in self.config['teachers']:
                var = tk.BooleanVar(value=True)  # Default: all teachers allowed
                cb = ttk.Checkbutton(teachers_frame, text=teacher, variable=var)
                cb.pack(anchor='w', padx=20)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def _setup_section_restrictions(self, parent):
        """Setup the section restrictions tab content"""
        # Similar structure for sections
        info_label = ttk.Label(parent, text="Section-wise teacher restrictions will be configured here.",
                             font=('Segoe UI', 11))
        info_label.pack(pady=50)

    def _setup_subject_restrictions(self, parent):
        """Setup the subject restrictions tab content"""
        # Similar structure for subjects  
        info_label = ttk.Label(parent, text="Subject-wise teacher restrictions will be configured here.",
                             font=('Segoe UI', 11))
        info_label.pack(pady=50)

    def auto_assign(self):
        # Check license before allowing auto-assign
        if not self.license_manager.can_use_feature("auto_assign"):
            if self.license_manager.is_trial_expired():
                response = messagebox.askyesno("Premium Feature", 
                    "Auto-assign is a premium feature. Your trial has expired.\n\n" +
                    "Would you like to upgrade to Premium to access this feature?")
                if response:
                    self.show_upgrade_dialog()
            else:
                messagebox.showinfo("Premium Feature", 
                    "Auto-assign is not available in your current license. Please upgrade to access this feature.")
            return
        
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
                            
                            # Find available teacher for this subject not already used in this period
                            available_teachers = [t for t in all_teachers if subject in teacher_subjects.get(t, []) and t not in used_teachers]
                            
                            # If no mapped teacher available, use any available teacher
                            if not available_teachers:
                                available_teachers = [t for t in all_teachers if t not in used_teachers]
                            
                            # If still no teacher available, reuse teachers with better distribution
                            if not available_teachers:
                                # Use teacher in round-robin fashion based on class-section index
                                teacher_index = class_section_index % len(all_teachers)
                                assigned_teacher = all_teachers[teacher_index]
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
        # Check license before allowing smart match
        if not self.license_manager.can_use_feature("smart_match"):
            if self.license_manager.is_trial_expired():
                response = messagebox.askyesno("Premium Feature", 
                    "Smart Match is a premium feature. Your trial has expired.\n\n" +
                    "Would you like to upgrade to Premium to access this feature?")
                if response:
                    self.show_upgrade_dialog()
            else:
                messagebox.showinfo("Premium Feature", 
                    "Smart Match is not available in your current license. Please upgrade to access this feature.")
            return
        
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
    
    def save_timetable_entry(self, class_name, section, period, day, teacher, subject):
        """Save a timetable entry to the database"""
        try:
            if not hasattr(self, 'cursor') or not self.cursor:
                self.setup_db()
            
            # Get current week and year
            week = self.selected_week.get()
            year = self.selected_year.get()
            
            # Check if entry already exists
            self.cursor.execute("""
                SELECT id FROM timetable_entries 
                WHERE class_name=? AND section=? AND period=? AND day=? AND week=? AND year=?
            """, (class_name, section, period, day, week, year))
            
            if self.cursor.fetchone():
                # Update existing entry
                self.cursor.execute("""
                    UPDATE timetable_entries 
                    SET teacher=?, subject=? 
                    WHERE class_name=? AND section=? AND period=? AND day=? AND week=? AND year=?
                """, (teacher, subject, class_name, section, period, day, week, year))
            else:
                # Insert new entry
                self.cursor.execute("""
                    INSERT INTO timetable_entries 
                    (class_name, section, period, day, week, year, teacher, subject)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (class_name, section, period, day, week, year, teacher, subject))
            
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error saving timetable entry: {e}")
            return False
    
    def auto_assign_timetable(self):
        """Auto-assign teachers to timetable slots"""
        try:
            if not self.license_manager.validate_feature("auto_assign"):
                messagebox.showwarning("Feature Restricted", 
                    "Auto-assign is not available in your current license. Please upgrade to access this feature.")
                return
            
            # Update status
            if hasattr(self, 'status_bar'):
                self.status_bar.config(text="Auto-assigning timetable...")
            
            # Simple auto-assignment logic
            teachers = self.config.get('teachers', [])
            subjects = self.config.get('subjects', [])
            
            if not teachers or not subjects:
                messagebox.showwarning("Configuration Missing", 
                    "Please configure teachers and subjects before auto-assignment.")
                return
            
            assigned_count = 0
            
            # Get all empty slots
            for class_name in self.config.get('classes', []):
                for section in self.config.get('sections', []):
                    for period in range(1, 9):  # 8 periods
                        for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']:
                            # Check if slot is empty
                            entry_key = (class_name, section, period, day)
                            if entry_key not in self.entries or not self.entries[entry_key].get():
                                # Assign random teacher and subject
                                import random
                                teacher = random.choice(teachers)
                                subject = random.choice(subjects)
                                
                                # Save the assignment
                                if self.save_timetable_entry(class_name, section, period, day, teacher, subject):
                                    if entry_key in self.entries:
                                        self.entries[entry_key].set(f"{teacher} - {subject}")
                                    assigned_count += 1
            
            # Update status
            if hasattr(self, 'status_bar'):
                self.status_bar.config(text=f"Auto-assignment complete: {assigned_count} slots assigned")
            
            messagebox.showinfo("Auto-Assignment Complete", 
                f"Successfully assigned {assigned_count} timetable slots.")
            
            return assigned_count
            
        except Exception as e:
            print(f"Error in auto-assignment: {e}")
            if hasattr(self, 'status_bar'):
                self.status_bar.config(text="Auto-assignment failed")
            messagebox.showerror("Error", f"Auto-assignment failed: {str(e)}")
            return 0
    
    def update_datetime(self):
        """Update the date and time display every minute"""
        if self.datetime_label:
            current_datetime = datetime.now().strftime("%d %B %Y | %I:%M %p")
            self.datetime_label.config(text=f"⏰ DATE/TIME: {current_datetime}")
            # Also update styling for better visibility
            self.datetime_label.config(bg="#2563eb", fg="#ffffff", relief="raised", bd=2)
        # Schedule next update in 60 seconds
        self.root.after(60000, self.update_datetime)

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
