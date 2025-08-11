#!/usr/bin/env python3
"""
ClassFlow License Demo Script
Demonstrates trial system behavior automatically
"""

import os
import json
from datetime import datetime, timedelta
import subprocess
import sys
import time

class LicenseDemo:
    def __init__(self):
        # Find the license file location
        if os.name == 'nt':  # Windows
            app_data = os.environ.get('APPDATA', os.path.expanduser('~'))
            self.license_dir = os.path.join(app_data, 'ClassFlow')
        else:  # Linux/Mac
            self.license_dir = os.path.expanduser('~/.classflow')
        
        self.license_file = os.path.join(self.license_dir, 'license.json')
        
        # Ensure directory exists
        if not os.path.exists(self.license_dir):
            os.makedirs(self.license_dir)
    
    def show_license_info(self):
        """Display current license information"""
        if not os.path.exists(self.license_file):
            print("❌ No license file found")
            return
        
        try:
            with open(self.license_file, 'r') as f:
                license_data = json.load(f)
            
            print("\n📄 Current License Information:")
            print(f"   License Type: {license_data.get('license_type', 'Unknown')}")
            print(f"   Installation Date: {license_data.get('installation_date', 'Unknown')}")
            
            if license_data.get('license_type') == 'TRIAL':
                install_date = datetime.strptime(license_data['installation_date'], "%Y-%m-%d")
                days_passed = (datetime.now() - install_date).days
                days_remaining = max(0, license_data.get('trial_days', 30) - days_passed)
                print(f"   Trial Days Remaining: {days_remaining}")
                
                if days_remaining <= 0:
                    print("   ⚠️  Trial has EXPIRED!")
                elif days_remaining <= 7:
                    print("   🟡 Trial expiring soon!")
                else:
                    print("   ✅ Trial active")
            
            print(f"   License Key: {license_data.get('license_key', 'None')}")
            
            print("\n🔧 Feature Permissions:")
            features = license_data.get('features', {})
            for feature, enabled in features.items():
                status = "✅" if enabled else "❌"
                print(f"   {status} {feature}: {enabled}")
            
        except Exception as e:
            print(f"❌ Error reading license: {e}")
    
    def create_trial_license(self, days_remaining=30):
        """Create a trial license with specified days remaining"""
        install_date = datetime.now() - timedelta(days=(30 - days_remaining))
        
        license_data = {
            "installation_date": install_date.strftime("%Y-%m-%d"),
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
        
        with open(self.license_file, 'w') as f:
            json.dump(license_data, f, indent=2)
        
        print(f"✅ Created trial license with {days_remaining} days remaining")
        return license_data
    
    def create_expired_trial(self):
        """Create an expired trial license"""
        install_date = datetime.now() - timedelta(days=35)  # 35 days ago = expired
        
        license_data = {
            "installation_date": install_date.strftime("%Y-%m-%d"),
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
        
        with open(self.license_file, 'w') as f:
            json.dump(license_data, f, indent=2)
        
        print(f"✅ Created EXPIRED trial license (35 days old)")
        return license_data
    
    def create_free_license(self):
        """Create a free license with restrictions"""
        license_data = {
            "installation_date": datetime.now().strftime("%Y-%m-%d"),
            "license_type": "FREE",
            "license_key": None,
            "premium_expiry": None,
            "trial_days": 0,
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
        }
        
        with open(self.license_file, 'w') as f:
            json.dump(license_data, f, indent=2)
        
        print(f"✅ Created FREE license with restrictions")
        return license_data

def main():
    demo = LicenseDemo()
    
    print("🎬 ClassFlow License System Live Demo")
    print("=" * 50)
    print(f"License location: {demo.license_file}")
    print()
    
    # Demo 1: Fresh 30-day trial
    print("🎯 DEMO 1: Fresh 30-Day Trial")
    print("-" * 30)
    demo.create_trial_license(30)
    demo.show_license_info()
    print("\n▶️ Window Title would show: 'ClassFlow v2.0 - Trial: 30 days remaining'")
    print("▶️ Status Bar would show: '🚀 Trial: 30 days remaining - Upgrade to Premium for unlimited access!'")
    print("▶️ All premium features would be ENABLED")
    
    input("\nPress Enter to continue to next demo...")
    
    # Demo 2: Trial with 7 days remaining
    print("\n🎯 DEMO 2: Trial Expiring Soon (7 Days Left)")
    print("-" * 45)
    demo.create_trial_license(7)
    demo.show_license_info()
    print("\n▶️ Window Title would show: 'ClassFlow v2.0 - Trial: 7 days remaining'")
    print("▶️ Status Bar would show: '🟡 Trial: 7 days remaining - Upgrade soon to keep advanced features!'")
    print("▶️ All premium features still ENABLED but with orange warning")
    
    input("\nPress Enter to continue to next demo...")
    
    # Demo 3: Trial with 1 day remaining
    print("\n🎯 DEMO 3: Trial Almost Expired (1 Day Left)")
    print("-" * 42)
    demo.create_trial_license(1)
    demo.show_license_info()
    print("\n▶️ Window Title would show: 'ClassFlow v2.0 - Trial: 1 day remaining'")
    print("▶️ Status Bar would show: '⚠️ Trial: 1 day remaining - Upgrade now to keep advanced features!'")
    print("▶️ All premium features still ENABLED but with urgent warning")
    
    input("\nPress Enter to continue to next demo...")
    
    # Demo 4: Expired trial
    print("\n🎯 DEMO 4: Expired Trial (Auto-Converts to FREE)")
    print("-" * 46)
    demo.create_expired_trial()
    demo.show_license_info()
    print("\n▶️ When ClassFlow launches, it will detect the expired trial")
    print("▶️ It will automatically convert from TRIAL to FREE license")
    print("▶️ Window Title would show: 'ClassFlow v2.0 - Free Version'")
    print("▶️ Premium features would be DISABLED immediately")
    
    input("\nPress Enter to continue to next demo...")
    
    # Demo 5: Free license (what it becomes after trial expires)
    print("\n🎯 DEMO 5: Free License (After Trial Expiry)")
    print("-" * 43)
    demo.create_free_license()
    demo.show_license_info()
    print("\n▶️ Window Title: 'ClassFlow v2.0 - Free Version'")
    print("▶️ Status Bar: '📝 Free Version - Limited features | Upgrade to Premium for full access'")
    print("▶️ Premium features are DISABLED:")
    print("   ❌ Auto-Assign button grayed out")
    print("   ❌ Smart Match button grayed out")
    print("   ❌ Teacher Restrictions button grayed out")
    print("   ❌ Teacher Leave button grayed out")
    print("   ❌ PDF Export button grayed out")
    print("   🚀 'Upgrade to Premium' button appears")
    print("\n▶️ Scale limitations enforced:")
    print("   📏 Maximum 3 classes")
    print("   📏 Maximum 2 sections")
    print("   📏 Maximum 10 teachers")
    print("   📏 Maximum 6 periods per day")
    print("\n▶️ Excel export includes watermark: 'ClassFlow Free Version'")
    
    input("\nPress Enter to see what happens when users click disabled features...")
    
    print("\n🎯 DEMO 6: User Clicks Disabled Feature")
    print("-" * 39)
    print("▶️ User clicks 'Auto-Assign' button (disabled)")
    print("▶️ Upgrade dialog appears with:")
    print("   💎 Orange header: 'Upgrade to ClassFlow Premium'")
    print("   📋 List of 7 premium benefits")
    print("   💰 Pricing: School Plan ₹499/month, Institution ₹999/month")
    print("   🔑 'I Have a License Key' button")
    print("   📞 'Contact Sales' button")
    print("   ❌ 'Close' button")
    
    print("\n✅ Demo Complete!")
    print("🚀 To test live behavior:")
    print("   1. Run: python school_timetable_planner_new.py")
    print("   2. Try clicking the disabled features")
    print("   3. Test the upgrade dialog and license activation")
    
    print(f"\n📁 License file saved at: {demo.license_file}")
    print("You can manually edit this file to test different scenarios")

if __name__ == "__main__":
    main()
