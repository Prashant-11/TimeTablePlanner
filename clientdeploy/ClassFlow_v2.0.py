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
import base64
import hashlib

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
    
    def activate_premium_license(self, license_key):
        """Activate premium license with provided key"""
        # Simple validation - in production, this would verify with server
        if self.validate_license_key(license_key):
            self.license_data.update({
                "license_type": "PREMIUM",
                "license_key": license_key,
                "premium_expiry": (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d"),
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
    
    def validate_license_key(self, license_key):
        """Basic license key validation"""
        # Simple check - in production, this would be more sophisticated
        return (license_key.startswith("CFLOW-") and 
                len(license_key.replace("-", "")) >= 20 and
                license_key.count("-") >= 4)

class TimetableApp:
    def __init__(self, root):
        self.root = root
        # Set basic properties first
        self._set_theme()
        
        # Initialize license manager
        self.license_manager = LicenseManager()
        
        # Update title based on license status
        license_status = self.license_manager.get_license_status()
        self.root.title(f"ClassFlow v2.0 - {license_status}")
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

    # License checking methods
    def update_button_states(self):
        """Update button states based on license permissions"""
        # Auto-Assign button
        if self.license_manager.validate_feature("auto_assign"):
            self.auto_assign_btn.config(state='normal')
        else:
            self.auto_assign_btn.config(state='disabled')
        
        # Smart Match button
        if self.license_manager.validate_feature("smart_match"):
            self.smart_match_btn.config(state='normal')
        else:
            self.smart_match_btn.config(state='disabled')
        
        # Teacher Restrictions button
        if self.license_manager.validate_feature("teacher_restrictions"):
            self.teacher_restrictions_btn.config(state='normal')
        else:
            self.teacher_restrictions_btn.config(state='disabled')
        
        # Teacher Leave button
        if self.license_manager.validate_feature("teacher_leave"):
            self.teacher_leave_btn.config(state='normal')
        else:
            self.teacher_leave_btn.config(state='disabled')
        
        # Export PDF button
        if self.license_manager.validate_feature("pdf_export"):
            self.export_pdf_btn.config(state='normal')
        else:
            self.export_pdf_btn.config(state='disabled')
    
    def check_auto_assign(self):
        """Check license before executing auto-assign"""
        if self.license_manager.validate_feature("auto_assign"):
            self.auto_assign()
        else:
            self.show_upgrade_dialog("Auto-Assign")
    
    def check_smart_match(self):
        """Check license before executing smart match"""
        if self.license_manager.validate_feature("smart_match"):
            self.smart_match()
        else:
            self.show_upgrade_dialog("Smart Match")
    
    def check_teacher_restrictions(self):
        """Check license before showing teacher restrictions"""
        if self.license_manager.validate_feature("teacher_restrictions"):
            self.show_teacher_restrictions()
        else:
            self.show_upgrade_dialog("Teacher Restrictions")
    
    def check_teacher_leave(self):
        """Check license before showing teacher leave"""
        if self.license_manager.validate_feature("teacher_leave"):
            self.mark_leave()
        else:
            self.show_upgrade_dialog("Teacher Leave Management")
    
    def check_export_pdf(self):
        """Check license before PDF export"""
        if self.license_manager.validate_feature("pdf_export"):
            self.export_pdf()
        else:
            self.show_upgrade_dialog("PDF Export")
    
    def show_upgrade_dialog(self, feature_name="Premium Features"):
        """Show upgrade dialog for premium features with improved UI and seamless upgrade"""
        upgrade_win = tk.Toplevel(self.root)
        upgrade_win.title("Upgrade to Premium - ClassFlow")
        upgrade_win.geometry("700x600")
        upgrade_win.resizable(False, False)
        upgrade_win.configure(bg="#f8f9fa")
        
        # Make window modal and center it
        upgrade_win.transient(self.root)
        upgrade_win.grab_set()
        
        # Center the window
        upgrade_win.update_idletasks()
        x = (upgrade_win.winfo_screenwidth() // 2) - (700 // 2)
        y = (upgrade_win.winfo_screenheight() // 2) - (600 // 2)
        upgrade_win.geometry(f"700x600+{x}+{y}")
        
        # Main container with scrollable frame
        main_container = tk.Frame(upgrade_win, bg="#f8f9fa")
        main_container.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Header
        header_frame = tk.Frame(main_container, bg="#2d6cdf", height=90, relief="raised", borderwidth=2)
        header_frame.pack(fill='x', pady=(0, 15))
        header_frame.pack_propagate(False)
        
        header_label = tk.Label(header_frame, 
            text="🚀 Upgrade to ClassFlow Premium", 
            font=("Segoe UI", 18, "bold"),
            foreground="white",
            bg="#2d6cdf")
        header_label.pack(expand=True, pady=15)
        
        # Feature info with better styling
        feature_frame = tk.Frame(main_container, bg="#fff3cd", relief="solid", borderwidth=2)
        feature_frame.pack(fill='x', pady=(0, 15))
        
        feature_label = tk.Label(feature_frame,
            text=f"🔒 {feature_name} requires a Premium License",
            font=("Segoe UI", 13, "bold"),
            bg="#fff3cd",
            fg="#856404",
            padx=15,
            pady=12,
            wraplength=650,
            justify='center')
        feature_label.pack()
        
        # Benefits section with better layout
        benefits_title = tk.Label(main_container, 
            text="✨ Premium Benefits:",
            font=("Segoe UI", 15, "bold"),
            bg="#f8f9fa",
            fg="#2d6cdf")
        benefits_title.pack(anchor='w', pady=(5, 8))
        
        # Create scrollable benefits frame
        benefits_frame = tk.Frame(main_container, bg="#f8f9fa")
        benefits_frame.pack(fill='x', pady=(0, 15))
        
        benefits = [
            "🤖 Auto-Assign & Smart Match algorithms for optimal scheduling",
            "👥 Advanced Teacher Restrictions management with flexible rules", 
            "📅 Teacher Leave management system with automatic replacements",
            "📄 Professional PDF exports without watermarks",
            "� Unlimited classes, sections, teachers, and periods",
            "🎯 Priority customer support and feature updates",
            "☁️ Future: Cloud synchronization and mobile app access",
            "📊 Advanced analytics and reporting features"
        ]
        
        for i, benefit in enumerate(benefits):
            benefit_frame = tk.Frame(benefits_frame, bg="#f8f9fa")
            benefit_frame.pack(fill='x', pady=2)
            
            benefit_label = tk.Label(benefit_frame,
                text=benefit,
                font=("Segoe UI", 11),
                bg="#f8f9fa",
                fg="#495057",
                anchor='w',
                wraplength=650,
                justify='left')
            benefit_label.pack(side='left', fill='x', expand=True)
        
        # Pricing section with better styling
        pricing_frame = tk.Frame(main_container, bg="#d4edda", relief="solid", borderwidth=2)
        pricing_frame.pack(fill='x', pady=(10, 15))
        
        pricing_title = tk.Label(pricing_frame,
            text="💰 Affordable Pricing Plans",
            font=("Segoe UI", 13, "bold"),
            bg="#d4edda",
            fg="#155724")
        pricing_title.pack(pady=(10, 5))
        
        pricing_details = tk.Label(pricing_frame,
            text="🏫 School Plan: ₹499/month | 🏛️ Institution Plan: ₹999/month\n" +
                 "💳 Easy payment options | 🔄 Cancel anytime | 💯 30-day money-back guarantee",
            font=("Segoe UI", 10),
            bg="#d4edda",
            fg="#155724",
            wraplength=650,
            justify='center')
        pricing_details.pack(pady=(0, 10))
        
        # Action buttons with improved layout
        button_frame = tk.Frame(main_container, bg="#f8f9fa")
        button_frame.pack(fill='x', pady=(15, 10))
        
        # Primary upgrade button (orange/prominent)
        upgrade_btn = tk.Button(button_frame, 
                               text="🚀 UPGRADE TO PREMIUM NOW",
                               command=lambda: self.initiate_upgrade_process(upgrade_win),
                               bg="#ff6b35",
                               fg="white",
                               font=("Segoe UI", 14, "bold"),
                               relief="flat",
                               padx=30,
                               pady=12,
                               cursor="hand2",
                               bd=0)
        upgrade_btn.pack(pady=(0, 10))
        
        # Secondary action frame
        secondary_frame = tk.Frame(button_frame, bg="#f8f9fa")
        secondary_frame.pack(fill='x')
        
        # Activate License button
        activate_btn = tk.Button(secondary_frame, 
                                text="🔑 I Have a License Key",
                                command=lambda: self.show_activation_dialog(upgrade_win),
                                bg="#28a745",
                                fg="white",
                                font=("Segoe UI", 11, "bold"),
                                relief="flat",
                                padx=15,
                                pady=8,
                                cursor="hand2")
        activate_btn.pack(side='left', padx=(0, 10))
        
        # Contact Sales button
        contact_btn = tk.Button(secondary_frame, 
                               text="📞 Contact Sales",
                               command=self.contact_sales,
                               bg="#007bff",
                               fg="white",
                               font=("Segoe UI", 11, "bold"),
                               relief="flat",
                               padx=15,
                               pady=8,
                               cursor="hand2")
        contact_btn.pack(side='left', padx=(0, 10))
        
        # Close button
        close_btn = tk.Button(secondary_frame, 
                             text="❌ Close",
                             command=upgrade_win.destroy,
                             bg="#6c757d",
                             fg="white",
                             font=("Segoe UI", 11),
                             relief="flat",
                             padx=15,
                             pady=8,
                             cursor="hand2")
        close_btn.pack(side='right')
        
        # Focus and bring to front
        upgrade_win.focus_set()
        upgrade_win.lift()
        
    def initiate_upgrade_process(self, parent_win):
        """Initiate seamless upgrade process"""
        # Close upgrade dialog
        parent_win.destroy()
        
        # Show upgrade options
        self.show_upgrade_options()
    
    def show_upgrade_options(self):
        """Show upgrade options with seamless payment integration"""
        options_win = tk.Toplevel(self.root)
        options_win.title("Choose Your Plan - ClassFlow Premium")
        options_win.geometry("600x400")
        options_win.resizable(False, False)
        options_win.configure(bg="#f8f9fa")
        
        # Make modal and center
        options_win.transient(self.root)
        options_win.grab_set()
        
        # Center window
        options_win.update_idletasks()
        x = (options_win.winfo_screenwidth() // 2) - (600 // 2)
        y = (options_win.winfo_screenheight() // 2) - (400 // 2)
        options_win.geometry(f"600x400+{x}+{y}")
        
        # Main container
        main_container = tk.Frame(options_win, bg="#f8f9fa")
        main_container.pack(fill='both', expand=True, padx=30, pady=30)
        
        # Header
        header_label = tk.Label(main_container,
            text="Choose Your Premium Plan",
            font=("Segoe UI", 18, "bold"),
            bg="#f8f9fa",
            fg="#2d6cdf")
        header_label.pack(pady=(0, 20))
        
        # Plan options
        plans_frame = tk.Frame(main_container, bg="#f8f9fa")
        plans_frame.pack(fill='x', expand=True)
        
        # School Plan
        school_frame = tk.Frame(plans_frame, bg="#e3f2fd", relief="solid", borderwidth=2)
        school_frame.pack(side='left', fill='both', expand=True, padx=(0, 10))
        
        tk.Label(school_frame, text="🏫 School Plan", font=("Segoe UI", 14, "bold"), 
                bg="#e3f2fd", fg="#1976d2").pack(pady=10)
        tk.Label(school_frame, text="₹499/month", font=("Segoe UI", 16, "bold"), 
                bg="#e3f2fd", fg="#1976d2").pack()
        tk.Label(school_frame, text="Perfect for single schools\n• Up to 50 teachers\n• Unlimited classes\n• All premium features", 
                font=("Segoe UI", 10), bg="#e3f2fd", wraplength=200, justify='center').pack(pady=10)
        
        school_btn = tk.Button(school_frame, text="Select School Plan", 
                              command=lambda: self.process_payment("school", options_win),
                              bg="#1976d2", fg="white", font=("Segoe UI", 11, "bold"),
                              padx=20, pady=8, cursor="hand2")
        school_btn.pack(pady=10)
        
        # Institution Plan
        institution_frame = tk.Frame(plans_frame, bg="#e8f5e8", relief="solid", borderwidth=2)
        institution_frame.pack(side='right', fill='both', expand=True, padx=(10, 0))
        
        tk.Label(institution_frame, text="🏛️ Institution Plan", font=("Segoe UI", 14, "bold"), 
                bg="#e8f5e8", fg="#2e7d32").pack(pady=10)
        tk.Label(institution_frame, text="₹999/month", font=("Segoe UI", 16, "bold"), 
                bg="#e8f5e8", fg="#2e7d32").pack()
        tk.Label(institution_frame, text="For multiple schools\n• Unlimited teachers\n• Multi-school management\n• Priority support", 
                font=("Segoe UI", 10), bg="#e8f5e8", wraplength=200, justify='center').pack(pady=10)
        
        institution_btn = tk.Button(institution_frame, text="Select Institution Plan", 
                                   command=lambda: self.process_payment("institution", options_win),
                                   bg="#2e7d32", fg="white", font=("Segoe UI", 11, "bold"),
                                   padx=20, pady=8, cursor="hand2")
        institution_btn.pack(pady=10)
        
        # Close button
        close_btn = tk.Button(main_container, text="❌ Cancel", command=options_win.destroy,
                             bg="#6c757d", fg="white", font=("Segoe UI", 11),
                             padx=20, pady=8, cursor="hand2")
        close_btn.pack(pady=(20, 0))
    
    def process_payment(self, plan_type, parent_win):
        """Process payment and upgrade seamlessly"""
        # Close options window
        parent_win.destroy()
        
        # Show payment processing
        payment_win = tk.Toplevel(self.root)
        payment_win.title("Payment - ClassFlow Premium")
        payment_win.geometry("500x300")
        payment_win.resizable(False, False)
        payment_win.configure(bg="#f8f9fa")
        
        # Make modal and center
        payment_win.transient(self.root)
        payment_win.grab_set()
        
        # Center window
        payment_win.update_idletasks()
        x = (payment_win.winfo_screenwidth() // 2) - (500 // 2)
        y = (payment_win.winfo_screenheight() // 2) - (300 // 2)
        payment_win.geometry(f"500x300+{x}+{y}")
        
        main_container = tk.Frame(payment_win, bg="#f8f9fa")
        main_container.pack(fill='both', expand=True, padx=40, pady=40)
        
        # Payment info
        plan_name = "School Plan (₹499/month)" if plan_type == "school" else "Institution Plan (₹999/month)"
        
        tk.Label(main_container, text="💳 Payment Information", 
                font=("Segoe UI", 16, "bold"), bg="#f8f9fa", fg="#2d6cdf").pack(pady=(0, 15))
        
        tk.Label(main_container, text=f"Selected: {plan_name}", 
                font=("Segoe UI", 12, "bold"), bg="#f8f9fa").pack(pady=5)
        
        # Payment options
        tk.Label(main_container, text="Choose Payment Method:", 
                font=("Segoe UI", 11), bg="#f8f9fa").pack(pady=(10, 5))
        
        payment_frame = tk.Frame(main_container, bg="#f8f9fa")
        payment_frame.pack(pady=10)
        
        # Payment buttons
        razorpay_btn = tk.Button(payment_frame, text="💳 Pay with Razorpay", 
                                command=lambda: self.open_payment_link(plan_type, "razorpay", payment_win),
                                bg="#528ff0", fg="white", font=("Segoe UI", 11, "bold"),
                                padx=15, pady=8, cursor="hand2")
        razorpay_btn.pack(pady=5)
        
        paytm_btn = tk.Button(payment_frame, text="📱 Pay with PayTM", 
                             command=lambda: self.open_payment_link(plan_type, "paytm", payment_win),
                             bg="#00baf2", fg="white", font=("Segoe UI", 11, "bold"),
                             padx=15, pady=8, cursor="hand2")
        paytm_btn.pack(pady=5)
        
        # Manual activation option
        tk.Label(main_container, text="Or contact sales for bank transfer/other options", 
                font=("Segoe UI", 9), bg="#f8f9fa", fg="#6c757d").pack(pady=(15, 5))
        
        contact_btn = tk.Button(main_container, text="📞 Contact Sales", 
                               command=self.contact_sales,
                               bg="#6c757d", fg="white", font=("Segoe UI", 10),
                               padx=15, pady=6, cursor="hand2")
        contact_btn.pack(pady=5)
        
        # Close button
        close_btn = tk.Button(main_container, text="❌ Cancel", command=payment_win.destroy,
                             bg="#dc3545", fg="white", font=("Segoe UI", 10),
                             padx=15, pady=6, cursor="hand2")
        close_btn.pack(pady=(10, 0))
    
    def open_payment_link(self, plan_type, payment_method, parent_win):
        """Open payment link and handle post-payment"""
        import webbrowser
        
        # Close payment window
        parent_win.destroy()
        
        # Payment URLs (replace with actual payment gateway URLs)
        payment_urls = {
            "school": {
                "razorpay": "https://razorpay.me/@classflow499",
                "paytm": "https://paytm.me/classflow-school"
            },
            "institution": {
                "razorpay": "https://razorpay.me/@classflow999", 
                "paytm": "https://paytm.me/classflow-institution"
            }
        }
        
        # Open payment URL
        url = payment_urls.get(plan_type, {}).get(payment_method, "")
        if url:
            webbrowser.open(url)
        
        # Show post-payment instructions
        self.show_post_payment_instructions(plan_type)
    
    def show_post_payment_instructions(self, plan_type):
        """Show instructions after payment"""
        instructions_win = tk.Toplevel(self.root)
        instructions_win.title("Payment Submitted - ClassFlow Premium")
        instructions_win.geometry("550x350")
        instructions_win.resizable(False, False)
        instructions_win.configure(bg="#f8f9fa")
        
        # Make modal and center
        instructions_win.transient(self.root)
        instructions_win.grab_set()
        
        # Center window
        instructions_win.update_idletasks()
        x = (instructions_win.winfo_screenwidth() // 2) - (550 // 2)
        y = (instructions_win.winfo_screenheight() // 2) - (350 // 2)
        instructions_win.geometry(f"550x350+{x}+{y}")
        
        main_container = tk.Frame(instructions_win, bg="#f8f9fa")
        main_container.pack(fill='both', expand=True, padx=30, pady=30)
        
        # Success header
        tk.Label(main_container, text="✅ Payment Submitted Successfully!", 
                font=("Segoe UI", 16, "bold"), bg="#f8f9fa", fg="#28a745").pack(pady=(0, 15))
        
        # Instructions
        instructions = [
            "🔄 Your payment is being processed",
            "📧 You will receive a license key via email within 24 hours",
            "🔑 Use the license key to activate Premium features",
            "📞 Contact support if you don't receive the key",
            "💡 Save this information for your records"
        ]
        
        for instruction in instructions:
            tk.Label(main_container, text=instruction, font=("Segoe UI", 11), 
                    bg="#f8f9fa", anchor='w', wraplength=490, justify='left').pack(fill='x', pady=3)
        
        # Contact info
        contact_frame = tk.Frame(main_container, bg="#e3f2fd", relief="solid", borderwidth=1)
        contact_frame.pack(fill='x', pady=(15, 10))
        
        tk.Label(contact_frame, text="📞 Support Contact", font=("Segoe UI", 12, "bold"), 
                bg="#e3f2fd", fg="#1976d2").pack(pady=(8, 5))
        tk.Label(contact_frame, text="Email: support@classflow.in\nPhone: +91-XXXX-XXXXXX", 
                font=("Segoe UI", 10), bg="#e3f2fd", justify='center').pack(pady=(0, 8))
        
        # Close button
        close_btn = tk.Button(main_container, text="✅ Got It", command=instructions_win.destroy,
                             bg="#28a745", fg="white", font=("Segoe UI", 12, "bold"),
                             padx=20, pady=8, cursor="hand2")
        close_btn.pack(pady=(15, 0))
    
    def show_activation_dialog(self, parent_win=None):
        """Show license activation dialog"""
        if parent_win:
            parent_win.destroy()
        
        activation_win = tk.Toplevel(self.root)
        activation_win.title("Activate Premium License")
        activation_win.geometry("500x300")
        activation_win.resizable(False, False)
        activation_win.configure(bg="#f8f9fa")
        
        # Make window modal and center it
        activation_win.transient(self.root)
        activation_win.grab_set()
        
        # Center the window
        activation_win.update_idletasks()
        x = (activation_win.winfo_screenwidth() // 2) - (500 // 2)
        y = (activation_win.winfo_screenheight() // 2) - (300 // 2)
        activation_win.geometry(f"500x300+{x}+{y}")
        
        # Main container
        main_container = tk.Frame(activation_win, bg="#f8f9fa")
        main_container.pack(fill='both', expand=True, padx=30, pady=30)
        
        # Title
        title_label = tk.Label(main_container, 
            text="🔑 Enter License Key",
            font=("Segoe UI", 16, "bold"),
            bg="#f8f9fa",
            fg="#2d6cdf")
        title_label.pack(pady=(0, 20))
        
        # Instructions
        instructions = tk.Label(main_container,
            text="Enter your ClassFlow Premium license key below:",
            font=("Segoe UI", 11),
            bg="#f8f9fa",
            fg="#6c757d")
        instructions.pack(pady=(0, 20))
        
        # License key entry
        key_frame = tk.Frame(main_container, bg="#f8f9fa")
        key_frame.pack(fill='x', pady=(0, 20))
        
        tk.Label(key_frame, text="License Key:", font=("Segoe UI", 12), bg="#f8f9fa").pack(anchor='w')
        
        license_key_var = tk.StringVar()
        key_entry = tk.Entry(key_frame, 
                            textvariable=license_key_var,
                            font=("Segoe UI", 11),
                            width=50)
        key_entry.pack(fill='x', pady=(5, 0))
        key_entry.focus()
        
        # Example format
        example_label = tk.Label(key_frame,
            text="Format: CFLOW-SCHOOL-XXXX-XXXX-XXXX-XXXX",
            font=("Segoe UI", 9),
            bg="#f8f9fa",
            fg="#6c757d")
        example_label.pack(anchor='w', pady=(5, 0))
        
        # Buttons
        button_frame = tk.Frame(main_container, bg="#f8f9fa")
        button_frame.pack(fill='x', pady=20)
        
        def activate_license():
            license_key = license_key_var.get().strip()
            if not license_key:
                messagebox.showerror("Error", "Please enter a license key.")
                return
            
            if self.license_manager.activate_premium_license(license_key):
                messagebox.showinfo("Success", 
                    "🎉 Premium license activated successfully!\n\n"
                    "All premium features are now available.")
                
                # Update UI
                self.update_button_states()
                license_status = self.license_manager.get_license_status()
                self.root.title(f"ClassFlow v2.0 - {license_status}")
                
                activation_win.destroy()
            else:
                messagebox.showerror("Invalid License", 
                    "The license key is invalid. Please check and try again.\n\n"
                    "Contact sales if you need assistance.")
        
        # Activate button
        activate_btn = tk.Button(button_frame, 
                                text="✅ Activate License",
                                command=activate_license,
                                bg="#28a745",
                                fg="white",
                                font=("Segoe UI", 12, "bold"),
                                relief="flat",
                                padx=20,
                                pady=8,
                                cursor="hand2")
        activate_btn.pack(side='left')
        
        # Cancel button
        cancel_btn = tk.Button(button_frame, 
                              text="❌ Cancel",
                              command=activation_win.destroy,
                              bg="#6c757d",
                              fg="white",
                              font=("Segoe UI", 12),
                              relief="flat",
                              padx=20,
                              pady=8,
                              cursor="hand2")
        cancel_btn.pack(side='right')
        
        # Bind Enter key
        activation_win.bind('<Return>', lambda e: activate_license())
        activation_win.bind('<Escape>', lambda e: activation_win.destroy())
    
    def contact_sales(self):
        """Show contact information for sales"""
        messagebox.showinfo("Contact Sales",
            "📞 Contact ClassFlow Sales\n\n"
            "Email: sales@hypersync.ai\n"
            "Phone: +91-XXXX-XXXX-XX\n"
            "Website: www.classflow.ai\n\n"
            "Our team will help you choose the right plan\n"
            "and provide immediate license activation!")

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

        # PROMINENT FIXED SAVE PANEL - Always visible at top
        save_panel = tk.Frame(self.root, bg="#2d6cdf", relief="raised", borderwidth=4, height=70)
        save_panel.pack(fill='x', padx=5, pady=5)
        save_panel.pack_propagate(False)
        
        # Save panel content with large save button
        save_content = tk.Frame(save_panel, bg="#2d6cdf")
        save_content.pack(expand=True, fill='both', padx=15, pady=10)
        
        # Huge prominent save button - impossible to miss
        self.main_save_btn = tk.Button(save_content, 
                                      text="💾 SAVE TIMETABLE NOW", 
                                      command=self.save_timetable,
                                      font=("Segoe UI", 16, "bold"),
                                      bg="#28a745", 
                                      fg="white",
                                      relief="raised",
                                      borderwidth=4,
                                      padx=30,
                                      pady=10,
                                      cursor="hand2",
                                      activebackground="#218838",
                                      activeforeground="white")
        self.main_save_btn.pack(side='left')
        
        # Auto-save status indicator
        self.auto_save_indicator = tk.Label(save_content,
                                           text="🔄 AUTO-SAVE: ENABLED",
                                           font=("Segoe UI", 12, "bold"),
                                           bg="#2d6cdf",
                                           fg="#90EE90")
        self.auto_save_indicator.pack(side='left', padx=30)
        
        # Save status display
        self.save_status_display = tk.Label(save_content,
                                           text="📊 Ready to save your timetable",
                                           font=("Segoe UI", 11),
                                           bg="#2d6cdf",
                                           fg="white")
        self.save_status_display.pack(side='left', padx=20)
        
        # Current time in save panel
        self.save_panel_time = tk.Label(save_content,
                                       text=f"📅 {self.current_date_str}",
                                       font=("Segoe UI", 10),
                                       bg="#2d6cdf",
                                       fg="white")
        self.save_panel_time.pack(side='right')

        # Top controls - now below save panel
        controls = ttk.Frame(self.root)
        controls.pack(fill='x', padx=10, pady=5)

        ttk.Label(controls, text="Year:").pack(side='left')
        ttk.Entry(controls, textvariable=self.selected_year, width=6).pack(side='left', padx=5)
        
        ttk.Label(controls, text="Week:").pack(side='left')
        ttk.Entry(controls, textvariable=self.selected_week, width=4).pack(side='left', padx=5)
        
        # Load button (save is now in prominent panel above)
        ttk.Button(controls, text="📂 Load Timetable", command=self.load_timetable).pack(side='left', padx=10)
        
        # Quick status indicator for controls row
        self.quick_status = ttk.Label(controls, text="� Large SAVE button available above ⬆️", foreground="blue")
        self.quick_status.pack(side='left', padx=20)
        
        # License status display
        license_frame = ttk.Frame(self.root)
        license_frame.pack(fill='x', padx=10, pady=2)
        
        # License status label
        license_status = self.license_manager.get_license_status()
        trial_days = self.license_manager.get_trial_days_remaining()
        
        if self.license_manager.license_data["license_type"] == "TRIAL" and trial_days > 0:
            status_color = "#ff6b35" if trial_days <= 7 else "#28a745"
            status_text = f"🚀 {license_status} - Upgrade to Premium for unlimited access!"
        elif self.license_manager.license_data["license_type"] == "FREE":
            status_color = "#6c757d"
            status_text = "📝 Free Version - Limited features | Upgrade to Premium for full access"
        elif self.license_manager.license_data["license_type"] == "PREMIUM":
            status_color = "#28a745"
            status_text = "✨ Premium License Active - All features unlocked!"
        else:
            status_color = "#dc3545"
            status_text = "⚠️ Trial Expired - Upgrade to continue using advanced features"
        
        self.license_status_label = ttk.Label(license_frame, 
                                             text=status_text,
                                             foreground=status_color,
                                             font=("Segoe UI", 9, "bold"))
        self.license_status_label.pack(side='left')
        
        # Show remaining features for free users
        if not self.license_manager.is_premium() and self.license_manager.license_data["license_type"] != "TRIAL":
            limits_text = f"Limits: {self.license_manager.get_feature_limit('max_classes')} classes, {self.license_manager.get_feature_limit('max_sections')} sections, {self.license_manager.get_feature_limit('max_teachers')} teachers"
            limits_label = ttk.Label(license_frame,
                                    text=limits_text,
                                    foreground="#856404",
                                    font=("Segoe UI", 8))
            limits_label.pack(side='left', padx=(20, 0))
        
        # Move edit buttons to separate row to make space
        edit_frame = ttk.Frame(self.root)
        edit_frame.pack(fill='x', padx=10, pady=2)
        
        ttk.Label(edit_frame, text="Configuration:").pack(side='left', padx=5)
        ttk.Button(edit_frame, text="Edit Classes", command=self.edit_classes).pack(side='left', padx=5)
        ttk.Button(edit_frame, text="Edit Sections", command=self.edit_sections).pack(side='left', padx=5)
        ttk.Button(edit_frame, text="Edit Teachers", command=self.edit_teachers).pack(side='left', padx=5)
        
        # Action buttons
        actions = ttk.Frame(self.root)
        actions.pack(fill='x', padx=10, pady=5)
        
        # Actions and tools section
        self.auto_assign_btn = ttk.Button(actions, text="Auto-Assign", command=self.check_auto_assign)
        self.auto_assign_btn.pack(side='left', padx=5)
        
        self.smart_match_btn = ttk.Button(actions, text="Smart Match", command=self.check_smart_match, style='Green.TButton')
        self.smart_match_btn.pack(side='left', padx=5)
        
        # Configuration section
        ttk.Button(actions, text="Teacher Mapping", command=self.show_teacher_subject_mapping).pack(side='left', padx=5)
        
        self.teacher_restrictions_btn = ttk.Button(actions, text="Teacher Restrictions", command=self.check_teacher_restrictions)
        self.teacher_restrictions_btn.pack(side='left', padx=5)
        
        ttk.Button(actions, text="Setup", command=self.show_setup).pack(side='left', padx=5)
        
        # Operations section  
        self.teacher_leave_btn = ttk.Button(actions, text="Teacher Leave", command=self.check_teacher_leave)
        self.teacher_leave_btn.pack(side='left', padx=5)
        
        ttk.Button(actions, text="Export Excel", command=self.export_excel).pack(side='left', padx=5)
        
        self.export_pdf_btn = ttk.Button(actions, text="Export PDF", command=self.check_export_pdf)
        self.export_pdf_btn.pack(side='left', padx=5)
        
        ttk.Button(actions, text="Refresh", command=self.refresh_grid).pack(side='left', padx=5)
        
        # Add upgrade button if not premium
        if not self.license_manager.is_premium() and self.license_manager.get_trial_days_remaining() <= 7:
            upgrade_btn = ttk.Button(actions, text="🚀 Upgrade to Premium", command=self.show_upgrade_dialog)
            upgrade_btn.pack(side='right', padx=10)
        
        # Update button states based on license
        self.update_button_states()

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
        
        # Status bar at bottom for save feedback
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill='x', side='bottom', padx=10, pady=2)
        
        # Save status indicator
        self.bottom_save_status = ttk.Label(status_frame, text="💾 Save Status: Auto-save enabled | Manual Save button available above", foreground="green", font=("Segoe UI", 9))
        self.bottom_save_status.pack(side='left')
        
        # Current academic info
        academic_info = ttk.Label(status_frame, text=f"📚 Academic Week {self.current_week} | {self.current_date_str}", font=("Segoe UI", 9))
        academic_info.pack(side='right')

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
                        subj_cb = ttk.Combobox(frame, textvariable=subj_var, values=subject_values, width=8, name=f"subj_{cell_key}")
                        subj_cb.pack(side='top', fill='x', padx=1, pady=1)
                        
                        # Teacher dropdown - initially with all teachers, will be filtered by subject
                        # Filter initial teacher values by class-section restrictions
                        allowed_teachers = self.filter_teachers_by_restrictions(self.config['teachers'], class_, section)
                        teacher_values = [""] + allowed_teachers  # Add blank option
                        teacher_cb = ttk.Combobox(frame, textvariable=teacher_var, values=teacher_values, width=12, name=f"teacher_{cell_key}")
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
                            
                            # Auto-save when subject is changed
                            self.auto_save_changes()
                        
                        def on_teacher_change(event=None, key=cell_key):
                            self.resolved_cells.add(key)
                            self.impacted_cells.discard(key)
                            if key in self.cell_frames:
                                self.cell_frames[key].configure(style='GreenCell.TFrame')
                            
                            # Auto-save when teacher is changed  
                            self.auto_save_changes()
                        
                        # Bind events
                        subj_cb.bind('<<ComboboxSelected>>', on_subject_change)
                        subj_cb.bind('<KeyRelease>', on_subject_change)  # For manual typing
                        teacher_cb.bind('<FocusOut>', on_teacher_change)
                        teacher_cb.bind('<Return>', on_teacher_change)
                        teacher_cb.bind('<<ComboboxSelected>>', on_teacher_change)
                        col += 1
                row += 1

    def refresh_grid(self):
        """Refresh the timetable grid - rebuilds if periods changed"""
        # Check if periods per day has changed
        config_periods = self.config.get('periods_per_day', 7)
        if hasattr(self, 'periods') and self.periods != config_periods:
            # Periods changed - need to rebuild the entire grid
            self.periods = config_periods
            self.rebuild_grid()
        else:
            # Just refresh display
            self.update_display()
    
    def update_display(self):
        """Update the display and scrollbars without rebuilding"""
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
    
    def rebuild_grid(self):
        """Completely rebuild the timetable grid with new structure"""
        try:
            # Rebuild the grid with new periods count
            self.draw_grid()
            
            # Load existing data
            self.load_data()
            
            # Update display
            self.update_display()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to rebuild grid: {str(e)}")

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

    def auto_save_restriction(self, teacher, class_name, section, var):
        """Auto-save individual teacher restriction changes"""
        try:
            # Remove existing restriction for this combination
            self.c.execute("DELETE FROM teacher_restrictions WHERE teacher=? AND class=? AND section=?", 
                          (teacher, class_name, section))
            
            # Add restriction if checkbox is checked
            if var.get():
                self.c.execute("INSERT INTO teacher_restrictions (teacher, class, section) VALUES (?, ?, ?)",
                              (teacher, class_name, section))
            
            self.conn.commit()
            
            # Update UI feedback
            restriction_count = self.c.execute("SELECT COUNT(*) FROM teacher_restrictions WHERE teacher=?", (teacher,)).fetchone()[0]
            total_restrictions = self.c.execute("SELECT COUNT(*) FROM teacher_restrictions").fetchone()[0]
            
            # Show subtle feedback (could add status label if needed)
            print(f"Auto-saved: {teacher} restriction for {class_name}-{section} ({'added' if var.get() else 'removed'})")
            print(f"Teacher {teacher} now has {restriction_count} restrictions, total: {total_restrictions}")
            
            # Refresh teacher dropdowns to reflect changes
            self.refresh_teacher_dropdowns()
            
        except Exception as e:
            print(f"Auto-save restriction error: {e}")
    
    def auto_save_changes(self):
        """Auto-save changes with a small delay to avoid excessive saves"""
        if hasattr(self, '_save_timer'):
            self.root.after_cancel(self._save_timer)
        
        # Save after 2 seconds of inactivity
        self._save_timer = self.root.after(2000, self._perform_auto_save)
    
    def _perform_auto_save(self):
        """Perform the actual auto-save"""
        try:
            year = self.selected_year.get()
            week = self.selected_week.get()
            
            # Clear old data for this week
            self.c.execute("DELETE FROM timetable WHERE year=? AND week=?", (year, week))
            
            # Save current grid - only cells with both subject and teacher
            saved_count = 0
            for (class_, section, day, period), (subj_var, teacher_var) in self.entries.items():
                subject = subj_var.get().strip()
                teacher = teacher_var.get().strip()
                if subject and teacher:  # Only save filled cells
                    self.c.execute('''
                        INSERT INTO timetable (year, week, class, section, day, period, subject, teacher)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (year, week, class_, section, day, period, subject, teacher))
                    saved_count += 1
                    
            self.conn.commit()
            
            # Update prominent save panel indicators
            current_time = datetime.now().strftime("%I:%M %p")
            
            if hasattr(self, 'auto_save_indicator'):
                self.auto_save_indicator.config(text=f"✅ AUTO-SAVED: {saved_count} entries", fg="#90EE90")
                # Reset after 4 seconds
                self.root.after(4000, lambda: self.auto_save_indicator.config(text="🔄 AUTO-SAVE: ENABLED", fg="#90EE90"))
            
            if hasattr(self, 'save_status_display'):
                self.save_status_display.config(text=f"📊 Last auto-save: {saved_count} entries at {current_time}")
            
            if hasattr(self, 'save_count_label'):
                self.save_count_label.config(text=f"📊 Entries: {saved_count} saved")
            
            if hasattr(self, 'last_save_label'):
                self.last_save_label.config(text=f"⏰ Auto-saved: {current_time}")
            
            # Update status label if exists (old one)
            if hasattr(self, 'save_status_label'):
                self.save_status_label.config(text=f"✅ Auto-Saved: {saved_count} entries", foreground="green")
                # Reset status after 3 seconds
                self.root.after(3000, lambda: self.save_status_label.config(text="🔄 Auto-Save: ON", foreground="green"))
            
            self.root.title(f"ClassFlow v1.3 - Auto-saved {saved_count} entries ✓")
            
            # Reset title after 3 seconds
            self.root.after(3000, lambda: self.root.title("ClassFlow v1.3"))
            
        except Exception as e:
            print(f"Auto-save error: {e}")
    
    def save_timetable(self):
        """Manual save with confirmation"""
        year = self.selected_year.get()
        week = self.selected_week.get()
        
        # Clear old data
        self.c.execute("DELETE FROM timetable WHERE year=? AND week=?", (year, week))
        
        # Save current grid
        saved_count = 0
        for (class_, section, day, period), (subj_var, teacher_var) in self.entries.items():
            subject = subj_var.get().strip()
            teacher = teacher_var.get().strip()
            if subject and teacher:  # Only save filled cells
                self.c.execute('''
                    INSERT INTO timetable (year, week, class, section, day, period, subject, teacher)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (year, week, class_, section, day, period, subject, teacher))
                saved_count += 1
                
        self.conn.commit()
        
        # Update prominent save panel indicators
        current_time = datetime.now().strftime("%I:%M %p")
        
        if hasattr(self, 'auto_save_indicator'):
            self.auto_save_indicator.config(text=f"💾 MANUAL SAVE: {saved_count} entries", fg="#FFD700")
            # Reset after 6 seconds
            self.root.after(6000, lambda: self.auto_save_indicator.config(text="🔄 AUTO-SAVE: ENABLED", fg="#90EE90"))
        
        if hasattr(self, 'save_status_display'):
            self.save_status_display.config(text=f"📊 Manual save: {saved_count} entries at {current_time}")
        
        if hasattr(self, 'last_save_label'):
            self.last_save_label.config(text=f"⏰ Manual save: {current_time}")
        
        # Update status label if exists (old one)
        if hasattr(self, 'save_status_label'):
            self.save_status_label.config(text=f"💾 Manual Save: {saved_count} entries", foreground="blue")
            # Reset status after 5 seconds
            self.root.after(5000, lambda: self.save_status_label.config(text="🔄 Auto-Save: ON", foreground="green"))
        
        messagebox.showinfo("Manual Save", f"Timetable manually saved!\n\n✅ {saved_count} entries saved for Year {year}, Week {week}\n\n💡 Note: Changes are also auto-saved as you work")

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
                        
                        # Further filter by class-section restrictions
                        available_teachers = self.filter_teachers_by_restrictions(
                            available_teachers, class_, section
                        )
                        
                        teacher_cb['values'] = [""] + available_teachers
                    
                    rows_loaded += 1
            
            if rows_loaded > 0:
                messagebox.showinfo("Success", f"Loaded timetable for Year {year}, Week {week}\n{rows_loaded} entries loaded.")
            else:
                messagebox.showinfo("No Data", f"No saved timetable found for Year {year}, Week {week}")
                
        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load timetable:\n{str(e)}")
            print(f"Load error: {e}")

    def refresh_teacher_dropdowns(self):
        """Refresh all teacher dropdowns to respect current restrictions"""
        if not hasattr(self, 'entries') or not self.entries:
            return
            
        teacher_subjects = self.config.get('teacher_subjects', {})
        
        for cell_key in self.entries:
            class_, section, day, period = cell_key
            if cell_key in self.teacher_cbs:
                teacher_cb = self.teacher_cbs[cell_key]
                subj_var, teacher_var = self.entries[cell_key]
                current_subject = subj_var.get()
                
                if current_subject and current_subject != "":
                    # Filter by subject first
                    if teacher_subjects:
                        available_teachers = [teacher for teacher, subjects in teacher_subjects.items() 
                                            if current_subject in subjects]
                    else:
                        available_teachers = self.config['teachers']
                else:
                    # No subject selected, show all teachers for this class-section
                    available_teachers = self.config['teachers']
                
                # Filter by class-section restrictions
                available_teachers = self.filter_teachers_by_restrictions(
                    available_teachers, class_, section
                )
                
                # Update dropdown
                teacher_cb['values'] = [""] + available_teachers
    
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
        
        # Check if teacher restrictions are active
        self.c.execute("SELECT COUNT(*) FROM teacher_restrictions")
        restriction_count = self.c.fetchone()[0]
        
        if restriction_count > 0:
            messagebox.showinfo("Success", 
                f"Auto-assign completed with Teacher Restrictions applied!\n\n"
                f"✅ Filled {filled_count} out of {total_cells} timetable slots\n"
                f"🔒 {restriction_count} teacher class-section restrictions respected\n"
                f"📝 Only allowed teachers assigned to each class-section")
        else:
            messagebox.showinfo("Success", 
                f"Auto-assign completed!\n\n"
                f"✅ Filled {filled_count} out of {total_cells} timetable slots\n"
                f"ℹ️ No teacher restrictions configured - all teachers available")

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
        
        # Check for watermark requirement
        should_watermark = self.license_manager.validate_feature("watermark")
        
        file = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
        )
        if not file:
            return
        
        try:
            # Create Excel writer object
            with pd.ExcelWriter(file, engine='openpyxl') as writer:
                # Add watermark sheet if required
                if should_watermark:
                    watermark_data = pd.DataFrame({
                        'ClassFlow Free Version': [
                            'Generated by ClassFlow Free Version',
                            'Upgrade to Premium for advanced features:',
                            '• Auto-Assign & Smart Match',
                            '• Teacher Restrictions & Leave Management', 
                            '• Clean exports without watermarks',
                            '• Unlimited classes, sections, teachers',
                            '',
                            'Contact: sales@hypersync.ai',
                            'Website: www.classflow.ai'
                        ]
                    })
                    watermark_data.to_excel(writer, sheet_name='Upgrade to Premium', index=False)
                
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

    def show_setup(self):
        """Show comprehensive setup dialog for classes, sections, teachers, and periods"""
        setup_win = tk.Toplevel(self.root)
        setup_win.title("ClassFlow - Application Setup")
        setup_win.geometry("800x700")
        setup_win.resizable(True, True)
        setup_win.configure(bg="#f8f9fa")
        
        # Make window modal and center it
        setup_win.transient(self.root)
        setup_win.grab_set()
        
        # Center the window
        setup_win.update_idletasks()
        x = (setup_win.winfo_screenwidth() // 2) - (800 // 2)
        y = (setup_win.winfo_screenheight() // 2) - (700 // 2)
        setup_win.geometry(f"800x700+{x}+{y}")
        
        # Main container
        main_container = tk.Frame(setup_win, bg="#f8f9fa")
        main_container.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Header
        header_frame = tk.Frame(main_container, bg="#2d6cdf", height=80)
        header_frame.pack(fill='x', pady=(0, 20))
        header_frame.pack_propagate(False)
        
        header_label = tk.Label(header_frame, 
            text="⚙️ ClassFlow Application Setup", 
            font=("Segoe UI", 18, "bold"),
            foreground="white",
            bg="#2d6cdf")
        header_label.pack(expand=True, pady=20)
        
        # Create notebook for different setup categories
        notebook = ttk.Notebook(main_container)
        notebook.pack(fill='both', expand=True, pady=(0, 20))
        
        # Tab 1: Periods Configuration
        periods_frame = tk.Frame(notebook, bg="#ffffff")
        notebook.add(periods_frame, text="📅 Periods")
        
        periods_container = tk.Frame(periods_frame, bg="#ffffff")
        periods_container.pack(fill='both', expand=True, padx=30, pady=30)
        
        # Periods setup
        periods_title = tk.Label(periods_container, 
            text="📅 Daily Periods Configuration",
            font=("Segoe UI", 16, "bold"),
            bg="#ffffff",
            fg="#2d6cdf")
        periods_title.pack(anchor='w', pady=(0, 20))
        
        periods_desc = tk.Label(periods_container,
            text="Configure how many periods per day your school has:",
            font=("Segoe UI", 11),
            bg="#ffffff",
            fg="#6c757d")
        periods_desc.pack(anchor='w', pady=(0, 20))
        
        periods_input_frame = tk.Frame(periods_container, bg="#ffffff")
        periods_input_frame.pack(fill='x', pady=(0, 20))
        
        tk.Label(periods_input_frame, 
            text="Periods per Day:", 
            font=("Segoe UI", 12, "bold"),
            bg="#ffffff").pack(side='left', padx=(0, 10))
        
        periods_var = tk.IntVar(value=self.config.get('periods_per_day', 7))
        periods_spinbox = tk.Spinbox(periods_input_frame, 
            from_=4, to=12, 
            textvariable=periods_var,
            font=("Segoe UI", 12),
            width=5)
        periods_spinbox.pack(side='left')
        
        tk.Label(periods_input_frame, 
            text="(Range: 4-12 periods)",
            font=("Segoe UI", 10),
            bg="#ffffff",
            fg="#6c757d").pack(side='left', padx=(10, 0))
        
        # Warning about grid rebuild
        warning_frame = tk.Frame(periods_container, bg="#fff3cd", relief="solid", borderwidth=1)
        warning_frame.pack(fill='x', pady=20)
        
        warning_label = tk.Label(warning_frame,
            text="⚠️ Changing periods will rebuild the timetable grid. Existing data will be preserved.",
            font=("Segoe UI", 10, "bold"),
            bg="#fff3cd",
            fg="#856404",
            padx=15,
            pady=10)
        warning_label.pack()
        
        # Tab 2: Classes & Sections
        classes_frame = tk.Frame(notebook, bg="#ffffff")
        notebook.add(classes_frame, text="🏫 Classes & Sections")
        
        classes_container = tk.Frame(classes_frame, bg="#ffffff")
        classes_container.pack(fill='both', expand=True, padx=30, pady=30)
        
        # Classes section
        classes_title = tk.Label(classes_container, 
            text="🏫 Classes Configuration",
            font=("Segoe UI", 16, "bold"),
            bg="#ffffff",
            fg="#2d6cdf")
        classes_title.pack(anchor='w', pady=(0, 10))
        
        classes_desc = tk.Label(classes_container,
            text="Current Classes: " + ", ".join(self.config['classes']),
            font=("Segoe UI", 11),
            bg="#ffffff",
            fg="#495057",
            wraplength=700)
        classes_desc.pack(anchor='w', pady=(0, 20))
        
        # Sections section
        sections_title = tk.Label(classes_container, 
            text="📋 Sections Configuration",
            font=("Segoe UI", 16, "bold"),
            bg="#ffffff",
            fg="#2d6cdf")
        sections_title.pack(anchor='w', pady=(20, 10))
        
        sections_desc = tk.Label(classes_container,
            text="Current Sections: " + ", ".join(self.config['sections']),
            font=("Segoe UI", 11),
            bg="#ffffff",
            fg="#495057")
        sections_desc.pack(anchor='w', pady=(0, 20))
        
        # Note about editing
        note_frame = tk.Frame(classes_container, bg="#d1ecf1", relief="solid", borderwidth=1)
        note_frame.pack(fill='x', pady=20)
        
        note_label = tk.Label(note_frame,
            text="ℹ️ To modify classes and sections, please edit the config.json file directly and restart the application.",
            font=("Segoe UI", 10),
            bg="#d1ecf1",
            fg="#0c5460",
            padx=15,
            pady=10,
            wraplength=650)
        note_label.pack()
        
        # Tab 3: Teachers
        teachers_frame = tk.Frame(notebook, bg="#ffffff")
        notebook.add(teachers_frame, text="👨‍🏫 Teachers")
        
        teachers_container = tk.Frame(teachers_frame, bg="#ffffff")
        teachers_container.pack(fill='both', expand=True, padx=30, pady=30)
        
        teachers_title = tk.Label(teachers_container, 
            text="👨‍🏫 Teachers Overview",
            font=("Segoe UI", 16, "bold"),
            bg="#ffffff",
            fg="#2d6cdf")
        teachers_title.pack(anchor='w', pady=(0, 20))
        
        # Teachers count
        teacher_count = tk.Label(teachers_container,
            text=f"Total Teachers: {len(self.config['teachers'])}",
            font=("Segoe UI", 12, "bold"),
            bg="#ffffff",
            fg="#28a745")
        teacher_count.pack(anchor='w', pady=(0, 10))
        
        # Create scrollable teacher list
        teachers_scroll_frame = tk.Frame(teachers_container, bg="#ffffff")
        teachers_scroll_frame.pack(fill='both', expand=True, pady=(0, 20))
        
        teachers_canvas = tk.Canvas(teachers_scroll_frame, bg="#f8f9fa", height=200)
        teachers_scrollbar = ttk.Scrollbar(teachers_scroll_frame, orient="vertical", command=teachers_canvas.yview)
        teachers_scrollable_frame = tk.Frame(teachers_canvas, bg="#f8f9fa")
        
        teachers_scrollable_frame.bind(
            "<Configure>",
            lambda e: teachers_canvas.configure(scrollregion=teachers_canvas.bbox("all"))
        )
        
        teachers_canvas.create_window((0, 0), window=teachers_scrollable_frame, anchor="nw")
        teachers_canvas.configure(yscrollcommand=teachers_scrollbar.set)
        
        # Display teachers in a grid
        teacher_display = tk.Label(teachers_scrollable_frame,
            text=", ".join(self.config['teachers']),
            font=("Segoe UI", 10),
            bg="#f8f9fa",
            fg="#495057",
            wraplength=650,
            justify="left",
            padx=15,
            pady=15)
        teacher_display.pack(fill='x')
        
        teachers_canvas.pack(side="left", fill="both", expand=True)
        teachers_scrollbar.pack(side="right", fill="y")
        
        # Note about teacher editing
        teacher_note_frame = tk.Frame(teachers_container, bg="#d1ecf1", relief="solid", borderwidth=1)
        teacher_note_frame.pack(fill='x', pady=20)
        
        teacher_note_label = tk.Label(teacher_note_frame,
            text="ℹ️ To modify the teacher list, please edit the config.json file directly and restart the application.",
            font=("Segoe UI", 10),
            bg="#d1ecf1",
            fg="#0c5460",
            padx=15,
            pady=10)
        teacher_note_label.pack()
        
        # Save and Close buttons
        button_frame = tk.Frame(main_container, bg="#f8f9fa")
        button_frame.pack(fill='x', pady=(10, 0))
        
        def save_setup():
            """Save the setup changes"""
            try:
                new_periods = periods_var.get()
                current_periods = self.config.get('periods_per_day', 7)
                
                if new_periods != current_periods:
                    # Update config
                    self.config['periods_per_day'] = new_periods
                    
                    # Save to file
                    with open('config.json', 'w') as f:
                        json.dump(self.config, f, indent=2)
                    
                    # Rebuild grid
                    self.refresh_grid()
                    
                    messagebox.showinfo("Setup Saved", 
                        f"✅ Setup configuration saved!\n\n"
                        f"📅 Periods per day updated to: {new_periods}\n"
                        f"🔄 Timetable grid has been rebuilt")
                else:
                    messagebox.showinfo("Setup", "No changes to save.")
                
                setup_win.destroy()
                
            except Exception as e:
                messagebox.showerror("Error", f"Error saving setup: {str(e)}")
        
        def cancel_setup():
            setup_win.destroy()
        
        # Save button
        save_btn = tk.Button(button_frame, 
                            text="💾 Save Changes",
                            command=save_setup,
                            bg="#28a745",
                            fg="white",
                            font=("Segoe UI", 12, "bold"),
                            relief="flat",
                            padx=20,
                            pady=10,
                            cursor="hand2")
        save_btn.pack(side='right', padx=(10, 0))
        
        # Cancel button
        cancel_btn = tk.Button(button_frame, 
                              text="❌ Cancel",
                              command=cancel_setup,
                              bg="#6c757d",
                              fg="white",
                              font=("Segoe UI", 12, "bold"),
                              relief="flat",
                              padx=20,
                              pady=10,
                              cursor="hand2")
        cancel_btn.pack(side='right', padx=(10, 0))
        
        # Bind keyboard shortcuts
        setup_win.bind('<Return>', lambda e: save_setup())
        setup_win.bind('<Escape>', lambda e: cancel_setup())
        setup_win.bind('<Control-s>', lambda e: save_setup())
        
        # Focus
        setup_win.focus_set()
        setup_win.lift()
        
        # Protocol for window close
        setup_win.protocol("WM_DELETE_WINDOW", cancel_setup)

    def show_teacher_restrictions(self):
        """Show a dialog to manage teacher class-section restrictions"""
        win = tk.Toplevel(self.root)
        win.title("ClassFlow - Teacher Class-Section Restrictions")
        win.geometry("1000x750")
        win.resizable(True, True)
        win.configure(bg="#f8f9fa")
        
        # Make window modal and center it
        win.transient(self.root)
        win.grab_set()
        
        # Center the window
        win.update_idletasks()
        x = (win.winfo_screenwidth() // 2) - (1000 // 2)
        y = (win.winfo_screenheight() // 2) - (750 // 2)
        win.geometry(f"1000x750+{x}+{y}")
        
        # Main frame with better styling
        main_frame = tk.Frame(win, bg="#f8f9fa")
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Title header with save button at top right
        title_frame = tk.Frame(main_frame, bg="#2d6cdf", height=80)
        title_frame.pack(fill='x', pady=(0, 20))
        title_frame.pack_propagate(False)
        
        # Title on the left
        title_label = tk.Label(title_frame, 
            text="🎯 Teacher Class-Section Restrictions", 
            font=("Segoe UI", 18, "bold"),
            foreground="white",
            bg="#2d6cdf")
        title_label.pack(side='left', expand=True, pady=20, padx=20)
        
        # Save functions
        def save_restrictions():
            """Manual save function - mainly for user confidence and final confirmation"""
            try:
                # Count current restrictions to show in confirmation
                self.c.execute("SELECT COUNT(*) FROM teacher_restrictions")
                total_restrictions = self.c.fetchone()[0]
                
                # Since auto-save is working, this is mainly for user feedback
                # Refresh teacher dropdowns to ensure consistency
                self.refresh_teacher_dropdowns()
                
                win.destroy()
                messagebox.showinfo("Teacher Restrictions Saved", 
                    f"✅ Teacher Restrictions Confirmed!\n\n"
                    f"📊 Total Restrictions: {total_restrictions} class-section combinations\n"
                    f"🔄 Auto-save was active: All changes already saved automatically\n"
                    f"🎯 Teacher dropdowns updated: Only allowed teachers shown in each cell\n\n"
                    f"💡 Your restrictions are now active in the main timetable!")
                
            except Exception as e:
                messagebox.showerror("Error", f"Error confirming restrictions: {str(e)}")
        
        def cancel():
            """Cancel and close dialog"""
            result = messagebox.askyesno("Close Teacher Restrictions", 
                "Close Teacher Restrictions dialog?\n\n"
                "✅ All changes have been auto-saved automatically\n"
                "📝 No data will be lost")
            if result:
                win.destroy()
        
        # PROMINENT SAVE BUTTON - TOP RIGHT POSITION
        save_btn = tk.Button(title_frame, 
                            text="💾 SAVE & APPLY", 
                            command=save_restrictions,
                            font=("Segoe UI", 12, "bold"),
                            bg="#28a745",
                            fg="white",
                            relief="raised",
                            borderwidth=3,
                            padx=25,
                            pady=10,
                            cursor="hand2",
                            activebackground="#218838",
                            activeforeground="white")
        save_btn.pack(side='right', padx=(10, 20), pady=15)
        
        # Add hover effects for save button
        def on_save_enter(event):
            save_btn.config(bg="#218838", relief="raised", borderwidth=4)
        def on_save_leave(event):
            save_btn.config(bg="#28a745", relief="raised", borderwidth=3)
        save_btn.bind("<Enter>", on_save_enter)
        save_btn.bind("<Leave>", on_save_leave)
        
        # Close button next to save
        close_btn = tk.Button(title_frame,
                              text="❌ CLOSE",
                              command=cancel,
                              font=("Segoe UI", 10),
                              bg="#dc3545",
                              fg="white", 
                              relief="raised",
                              borderwidth=2,
                              padx=15,
                              pady=10,
                              cursor="hand2",
                              activebackground="#c82333",
                              activeforeground="white")
        close_btn.pack(side='right', padx=(0, 10), pady=15)
        
        # Add hover effects for close button
        def on_close_enter(event):
            close_btn.config(bg="#c82333")
        def on_close_leave(event):
            close_btn.config(bg="#dc3545")
        close_btn.bind("<Enter>", on_close_enter)
        close_btn.bind("<Leave>", on_close_leave)
        
        # Instructions with better styling and auto-save notice
        instructions_frame = tk.Frame(main_frame, bg="#e9ecef", relief="solid", borderwidth=1)
        instructions_frame.pack(fill='x', pady=(0, 20))
        
        instruction_label = tk.Label(instructions_frame, 
            text="📋 Configure which classes and sections each teacher can teach by clicking on teacher tabs below:\n✅ Changes are AUTOMATICALLY SAVED as you check/uncheck boxes - No manual saving needed!\n💾 Use the GREEN SAVE BUTTON at top-right for final confirmation and feedback", 
            font=("Segoe UI", 11),
            foreground="#495057",
            bg="#e9ecef",
            wraplength=900,
            justify="left",
            padx=20,
            pady=15)
        instruction_label.pack(anchor='w')
        
        # Create notebook for teachers with better styling - now takes full remaining space
        notebook_frame = tk.Frame(main_frame, bg="#f8f9fa")
        notebook_frame.pack(fill='both', expand=True, pady=(0, 10))
        
        style = ttk.Style()
        
        # Configure tab styling for better visibility
        style.configure('Teacher.TNotebook', 
                       tabposition='n',
                       background="#f8f9fa")
        style.configure('Teacher.TNotebook.Tab', 
                       padding=[20, 12], 
                       font=('Segoe UI', 10, 'bold'),
                       focuscolor="none")
        
        # Map styles for different states
        style.map('Teacher.TNotebook.Tab',
                 background=[('selected', '#2d6cdf'),
                            ('active', '#5a9cff'),
                            ('!active', '#dee2e6')],
                 foreground=[('selected', 'white'),
                            ('active', 'white'),
                            ('!active', '#495057')],
                 expand=[('selected', [2, 2, 2, 0])])
        
        notebook = ttk.Notebook(notebook_frame, style='Teacher.TNotebook')
        notebook.pack(fill='both', expand=True)
        
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
            existing_for_teacher = existing_restrictions.get(teacher, [])
            has_restrictions = len(existing_for_teacher) > 0
            
            # Create more descriptive tab text with better icons
            if has_restrictions:
                tab_text = f"�‍🏫 {teacher} ({len(existing_for_teacher)})"
                tab_tooltip = f"{teacher} has {len(existing_for_teacher)} class-section restrictions"
            else:
                tab_text = f"👤 {teacher} (All)"
                tab_tooltip = f"{teacher} can teach any class-section (no restrictions)"
            
            # Teacher frame with better styling
            teacher_frame = tk.Frame(notebook, bg="#ffffff")
            notebook.add(teacher_frame, text=tab_text)
            
            # Create a modern container with padding
            container = ttk.Frame(teacher_frame)
            container.pack(fill='both', expand=True, padx=20, pady=20)
            
            # Teacher name header - make it more prominent with better styling
            header_frame = ttk.Frame(container)
            header_frame.pack(fill='x', pady=(0, 20))
            
            teacher_icon = "👩‍🏫" if "female" in teacher.lower() or any(name in teacher.lower() for name in ["priya", "sita", "maya", "rita"]) else "👨‍🏫"
            
            teacher_header = tk.Label(header_frame, 
                text=f"{teacher_icon} {teacher}",
                font=("Segoe UI", 18, "bold"),
                foreground="#2d6cdf",
                bg="#f8f9fa",
                relief="solid",
                borderwidth=1,
                padx=20,
                pady=10)
            teacher_header.pack(anchor='w')
            
            # Status indicator with better styling
            existing_for_teacher = existing_restrictions.get(teacher, [])
            if existing_for_teacher:
                status_text = f"✅ Restrictions Active: {len(existing_for_teacher)} class-section combinations allowed"
                status_color = "#28a745"
                status_bg = "#d4edda"
            else:
                status_text = "ℹ️ No Restrictions: Can teach any class-section combination"
                status_color = "#6c757d"
                status_bg = "#e2e3e5"
            
            status_frame = tk.Frame(header_frame, bg=status_bg, relief="solid", borderwidth=1)
            status_frame.pack(fill='x', pady=(10, 0))
            
            status_label = tk.Label(status_frame,
                text=status_text,
                font=("Segoe UI", 10, "bold"),
                foreground=status_color,
                bg=status_bg,
                padx=15,
                pady=8)
            status_label.pack(anchor='w')
            
            # Instructions for this teacher with better styling
            instructions_frame = ttk.Frame(container)
            instructions_frame.pack(fill='x', pady=(0, 20))
            
            teacher_instruction = tk.Label(instructions_frame, 
                text=f"📚 Configure class-section restrictions for {teacher}:",
                font=("Segoe UI", 12, "bold"),
                foreground="#495057")
            teacher_instruction.pack(anchor='w', pady=(0, 5))
            
            helper_text = tk.Label(instructions_frame,
                text="✓ Check the boxes for classes and sections this teacher can teach\n✗ Uncheck to restrict access to those combinations",
                font=("Segoe UI", 9),
                foreground="#6c757d")
            helper_text.pack(anchor='w')
            
            # Create scrollable frame for class-section options with proper configuration
            scroll_container = ttk.Frame(container)
            scroll_container.pack(fill='both', expand=True)
            
            # Create canvas with proper dimensions
            canvas = tk.Canvas(scroll_container, 
                              highlightthickness=0, 
                              bg="#ffffff",
                              height=400,  # Set specific height
                              relief="sunken",
                              borderwidth=1)
            
            # Create scrollbar with proper binding
            scrollbar = ttk.Scrollbar(scroll_container, orient="vertical", command=canvas.yview)
            scrollable_frame = ttk.Frame(canvas)
            
            # Bind frame configuration to update canvas scroll region
            def configure_scroll_region(event=None):
                canvas.configure(scrollregion=canvas.bbox("all"))
            
            scrollable_frame.bind("<Configure>", configure_scroll_region)
            
            # Create window in canvas
            canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            
            # Bind canvas width to frame width
            def configure_canvas_width(event):
                canvas_width = event.width
                canvas.itemconfig(canvas_window, width=canvas_width)
            
            canvas.bind('<Configure>', configure_canvas_width)
            canvas.configure(yscrollcommand=scrollbar.set)
            
            # Pack canvas and scrollbar properly
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
            # Create checkboxes for each class-section combination
            teacher_restrictions[teacher] = {}
            existing_for_teacher = existing_restrictions.get(teacher, [])
            
            # Add padding to scrollable content
            content_frame = ttk.Frame(scrollable_frame)
            content_frame.pack(fill='both', expand=True, padx=10, pady=10)
            
            for class_name in self.config['classes']:
                # Class frame with modern card styling
                class_frame = tk.Frame(content_frame, 
                    bg="#ffffff",
                    relief="solid", 
                    borderwidth=2,
                    highlightbackground="#dee2e6",
                    highlightthickness=1)
                class_frame.pack(fill='x', pady=8, padx=5)
                
                # Class header with icon and styling
                class_header_frame = tk.Frame(class_frame, bg="#f8f9fa", height=40)
                class_header_frame.pack(fill='x', padx=2, pady=2)
                class_header_frame.pack_propagate(False)
                
                class_title = tk.Label(class_header_frame, 
                    text=f"📚 {class_name}", 
                    font=("Segoe UI", 12, "bold"),
                    bg="#f8f9fa",
                    fg="#495057")
                class_title.pack(side='left', padx=15, pady=8)
                
                # Count of selected sections for this class
                selected_count = sum(1 for cls, sec in existing_for_teacher if cls == class_name)
                if selected_count > 0:
                    count_label = tk.Label(class_header_frame,
                        text=f"✓ {selected_count} sections",
                        font=("Segoe UI", 9, "bold"),
                        bg="#d4edda",
                        fg="#155724",
                        padx=8,
                        pady=2)
                    count_label.pack(side='right', padx=15, pady=8)
                
                # Section checkboxes with better layout
                section_content_frame = tk.Frame(class_frame, bg="#ffffff")
                section_content_frame.pack(fill='x', padx=15, pady=10)
                
                # Add a subtle label for sections
                section_label = tk.Label(section_content_frame, 
                    text="Available Sections:", 
                    font=("Segoe UI", 10, "bold"),
                    bg="#ffffff",
                    fg="#6c757d")
                section_label.pack(anchor='w', pady=(0, 8))
                
                # Create a grid layout for sections with better spacing and proper functionality
                checkbox_container = tk.Frame(section_content_frame, bg="#ffffff")
                checkbox_container.pack(fill='x', pady=5)
                
                # Use grid layout for better control
                sections_per_row = 3  # Display 3 sections per row
                row = 0
                col = 0
                
                for section in self.config['sections']:
                    var = tk.BooleanVar()
                    # Check if this combination exists in restrictions
                    if (class_name, section) in existing_for_teacher:
                        var.set(True)
                    
                    # Create a frame for each checkbox with proper padding
                    cb_frame = tk.Frame(checkbox_container, 
                                       bg="#ffffff",
                                       relief="flat",
                                       borderwidth=0,
                                       padx=5,
                                       pady=3)
                    cb_frame.grid(row=row, column=col, sticky='ew', padx=8, pady=4)
                    
                    # Configure grid weight for proper expansion
                    checkbox_container.grid_columnconfigure(col, weight=1)
                    
                    # Create checkbutton with improved styling and functionality
                    cb = tk.Checkbutton(cb_frame, 
                        text=f"Section {section}", 
                        variable=var,
                        font=("Segoe UI", 10),
                        bg="#ffffff",
                        fg="#495057",
                        activebackground="#e9ecef",
                        activeforeground="#495057",
                        selectcolor="#ffffff",
                        borderwidth=2,
                        highlightthickness=0,
                        relief="solid",
                        indicatoron=True,
                        cursor="hand2",
                        anchor="w",
                        padx=8,
                        pady=5,
                        command=lambda t=teacher, c=class_name, s=section, v=var: self.auto_save_restriction(t, c, s, v))
                    cb.pack(fill='x', anchor='w')
                    
                    # Move to next position
                    col += 1
                    if col >= sections_per_row:
                        col = 0
                        row += 1
                    
                    # Store the variable
                    if class_name not in teacher_restrictions[teacher]:
                        teacher_restrictions[teacher][class_name] = {}
                    teacher_restrictions[teacher][class_name][section] = var
            
            # Enable mouse wheel scrolling with proper event binding
            def bind_mousewheel(event):
                def _on_mousewheel(e):
                    canvas.yview_scroll(int(-1*(e.delta/120)), "units")
                canvas.bind_all("<MouseWheel>", _on_mousewheel)
            
            def unbind_mousewheel(event):
                canvas.unbind_all("<MouseWheel>")
            
            # Bind events when mouse enters/leaves the canvas
            canvas.bind('<Enter>', bind_mousewheel)
            canvas.bind('<Leave>', unbind_mousewheel)
            
            # Also bind to scrollable_frame for better coverage
            scrollable_frame.bind('<Enter>', bind_mousewheel)
            scrollable_frame.bind('<Leave>', unbind_mousewheel)
            
            # Set initial focus to enable scrolling
            canvas.focus_set()
        
        # Add Hypersync footer with better styling
        footer_frame = tk.Frame(win, bg="#343a40", height=40)
        footer_frame.pack(fill='x', side='bottom')
        footer_frame.pack_propagate(False)
        
        footer_label = tk.Label(footer_frame, 
                                text="Hypersync - An AI based education startup", 
                                font=("Segoe UI", 10, "bold"),
                                foreground="#ffffff",
                                bg="#343a40")
        footer_label.pack(expand=True, pady=10)
        
        # Focus and keyboard bindings
        win.focus_set()
        win.lift()  # Bring window to front
        
        # Bind keyboard shortcuts
        win.bind('<Return>', lambda e: save_restrictions())
        win.bind('<Escape>', lambda e: cancel())
        win.bind('<Control-s>', lambda e: save_restrictions())
        
        # Set focus to first tab
        notebook.focus_set()
        
        # Protocol for window close button
        win.protocol("WM_DELETE_WINDOW", cancel)

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
