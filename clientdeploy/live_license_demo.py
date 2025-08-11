#!/usr/bin/env python3
"""
ClassFlow License Demo - Shows exactly what happens in each scenario
"""

import os
import json
from datetime import datetime, timedelta

def create_license_file(license_data, scenario_name):
    """Create a license file and show its contents"""
    
    # Find the license file location
    if os.name == 'nt':  # Windows
        app_data = os.environ.get('APPDATA', os.path.expanduser('~'))
        license_dir = os.path.join(app_data, 'ClassFlow')
    else:  # Linux/Mac
        license_dir = os.path.expanduser('~/.classflow')
    
    # Ensure directory exists
    if not os.path.exists(license_dir):
        os.makedirs(license_dir)
    
    license_file = os.path.join(license_dir, 'license.json')
    
    # Write the license file
    with open(license_file, 'w') as f:
        json.dump(license_data, f, indent=2)
    
    print(f"\n📄 {scenario_name}")
    print("=" * 60)
    print(f"License file created at: {license_file}")
    print("\nLicense Contents:")
    print(json.dumps(license_data, indent=2))
    
    # Calculate trial days for TRIAL licenses
    if license_data.get('license_type') == 'TRIAL':
        install_date = datetime.strptime(license_data['installation_date'], "%Y-%m-%d")
        days_passed = (datetime.now() - install_date).days
        days_remaining = max(0, license_data.get('trial_days', 30) - days_passed)
        print(f"\n⏰ Trial Days Remaining: {days_remaining}")
        
        if days_remaining <= 0:
            print("⚠️  TRIAL EXPIRED - Will auto-convert to FREE when ClassFlow opens!")
        elif days_remaining <= 7:
            print("🟡 TRIAL EXPIRING SOON - Warning messages will appear!")
        else:
            print("✅ TRIAL ACTIVE - All features available!")
    
    return license_file

def demo_1_fresh_trial():
    """Demo 1: Fresh 30-day trial"""
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
    
    license_file = create_license_file(license_data, "DEMO 1: Fresh 30-Day Trial")
    
    print("\n🎬 What You'll See in ClassFlow:")
    print("   📋 Window Title: 'ClassFlow v2.0 - Trial: 30 days remaining'")
    print("   📊 Status Bar: '🚀 Trial: 30 days remaining - Upgrade to Premium for unlimited access!'")
    print("   ✅ All buttons ENABLED:")
    print("      • Auto-Assign (blue button)")
    print("      • Smart Match (blue button)")
    print("      • Teacher Restrictions (blue button)")
    print("      • Teacher Leave (blue button)")
    print("      • Export PDF (blue button)")
    print("   📏 Scale: Unlimited classes, sections, teachers")
    print("   📄 Exports: Clean (no watermark)")
    
    return license_file

def demo_2_trial_expiring():
    """Demo 2: Trial with 7 days remaining"""
    install_date = datetime.now() - timedelta(days=23)  # 23 days ago = 7 days remaining
    
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
    
    license_file = create_license_file(license_data, "DEMO 2: Trial Expiring Soon (7 Days)")
    
    print("\n🎬 What You'll See in ClassFlow:")
    print("   📋 Window Title: 'ClassFlow v2.0 - Trial: 7 days remaining'")
    print("   📊 Status Bar: '🟡 Trial: 7 days remaining - Upgrade soon to keep advanced features!'")
    print("   ✅ All buttons still ENABLED but with orange warning messages")
    print("   🚀 'Upgrade to Premium' button becomes more prominent")
    print("   ⚠️  Warning dialogs may appear on startup")
    
    return license_file

def demo_3_trial_expired():
    """Demo 3: Expired trial"""
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
    
    license_file = create_license_file(license_data, "DEMO 3: Expired Trial (Will Auto-Convert)")
    
    print("\n🎬 What Happens When ClassFlow Opens:")
    print("   🔄 Detects expired trial automatically")
    print("   🔄 Converts license from TRIAL to FREE")
    print("   📋 Window Title changes to: 'ClassFlow v2.0 - Free Version'")
    print("   📊 Status Bar changes to: '📝 Free Version - Limited features | Upgrade to Premium'")
    print("   ❌ Premium buttons become DISABLED and grayed out")
    print("   📏 Scale limits enforced immediately")
    
    return license_file

def demo_4_free_license():
    """Demo 4: Free license (after conversion)"""
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
    
    license_file = create_license_file(license_data, "DEMO 4: Free License (Post-Trial)")
    
    print("\n🎬 What You'll See in ClassFlow:")
    print("   📋 Window Title: 'ClassFlow v2.0 - Free Version'")
    print("   📊 Status Bar: '📝 Free Version - Limited features | Upgrade to Premium for full access'")
    print("\n   ❌ DISABLED Premium Features:")
    print("      • Auto-Assign button (grayed out)")
    print("      • Smart Match button (grayed out)")
    print("      • Teacher Restrictions button (grayed out)")
    print("      • Teacher Leave button (grayed out)")
    print("      • Export PDF button (grayed out)")
    print("\n   ✅ AVAILABLE Free Features:")
    print("      • Manual timetable creation")
    print("      • Basic editing (classes, subjects, teachers)")
    print("      • Save/Load timetables")
    print("      • Excel export (with watermark)")
    print("\n   📏 Scale Limitations:")
    print("      • Maximum 3 classes")
    print("      • Maximum 2 sections")
    print("      • Maximum 10 teachers")
    print("      • Maximum 6 periods per day")
    print("\n   🚀 New Button Appears: 'Upgrade to Premium' (orange)")
    
    return license_file

def demo_5_premium_license():
    """Demo 5: Premium license"""
    license_data = {
        "installation_date": datetime.now().strftime("%Y-%m-%d"),
        "license_type": "PREMIUM",
        "license_key": "CFLOW-SCHOOL-DEMO-1234-5678-9012",
        "premium_expiry": None,
        "trial_days": 0,
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
    
    license_file = create_license_file(license_data, "DEMO 5: Premium License")
    
    print("\n🎬 What You'll See in ClassFlow:")
    print("   📋 Window Title: 'ClassFlow v2.0 - Premium License'")
    print("   📊 Status Bar: '✨ Premium License Active - All features unlocked!'")
    print("   ✅ ALL features ENABLED and unlimited!")
    print("   🎉 No upgrade prompts or restrictions")
    
    return license_file

def main():
    print("🎬 ClassFlow v2.0 License System Live Demonstration")
    print("=" * 60)
    print("This demo creates actual license files and shows you exactly")
    print("what will happen in each scenario when you run ClassFlow.")
    print()
    
    demos = [
        ("1", "Fresh 30-Day Trial", demo_1_fresh_trial),
        ("2", "Trial Expiring (7 Days)", demo_2_trial_expiring),
        ("3", "Expired Trial", demo_3_trial_expired),
        ("4", "Free License", demo_4_free_license),
        ("5", "Premium License", demo_5_premium_license)
    ]
    
    for num, name, demo_func in demos:
        print(f"\n{'='*60}")
        print(f"🎯 SCENARIO {num}: {name}")
        print(f"{'='*60}")
        
        license_file = demo_func()
        
        print(f"\n🚀 To Test This Scenario:")
        print(f"   1. Run: python school_timetable_planner_new.py")
        print(f"   2. Observe the window title and status bar")
        print(f"   3. Try clicking various buttons")
        print(f"   4. Test export functionality")
        
        if num != "5":  # Don't pause after the last demo
            response = input(f"\nPress Enter to continue to next scenario, or 'q' to quit: ")
            if response.lower() == 'q':
                break
    
    print(f"\n✅ Demo Complete!")
    print(f"\n📁 License file location: {license_file}")
    print(f"\n🔧 To test different scenarios:")
    print(f"   • Run this demo again to switch scenarios")
    print(f"   • Or manually edit the license.json file")
    print(f"   • Or use the interactive testing tool: python test_license_system.py")
    
    print(f"\n🎮 Try These Tests:")
    print(f"   1. Launch ClassFlow and check window title")
    print(f"   2. Click disabled premium features in FREE mode")
    print(f"   3. Test the upgrade dialog and license activation")
    print(f"   4. Export Excel files to see watermarking")
    print(f"   5. Try exceeding scale limits in FREE mode")

if __name__ == "__main__":
    main()
