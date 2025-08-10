#!/usr/bin/env python3
"""
ClassFlow Executable Builder
Builds the standalone executable for ClassFlow Timetable Planner
"""

import subprocess
import sys
import os
import shutil
from pathlib import Path

def build_executable():
    """Build the ClassFlow executable using PyInstaller"""
    
    print("🚀 Building ClassFlow Executable...")
    print("=" * 50)
    
    # Ensure we're in the right directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Clean previous build
    build_dirs = ['build', 'dist', '__pycache__']
    for dir_name in build_dirs:
        if os.path.exists(dir_name):
            print(f"🧹 Cleaning {dir_name}/")
            shutil.rmtree(dir_name)
    
    # Remove old spec file
    spec_files = ['*.spec']
    for spec_file in spec_files:
        if os.path.exists(spec_file):
            os.remove(spec_file)
    
    # PyInstaller command
    cmd = [
        'pyinstaller',
        '--onefile',
        '--windowed',
        '--name=ClassFlow',
        '--icon=icon.ico',  # Add if you have an icon
        'school_timetable_planner_new.py'
    ]
    
    try:
        print("🔨 Running PyInstaller...")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ Build successful!")
        
        # Copy essential files to dist
        essential_files = ['config.json', 'timetable.db']
        dist_dir = Path('dist')
        
        for file_name in essential_files:
            if os.path.exists(file_name):
                shutil.copy2(file_name, dist_dir)
                print(f"📄 Copied {file_name} to dist/")
        
        print("\n🎉 ClassFlow.exe built successfully!")
        print(f"📁 Location: {dist_dir.absolute() / 'ClassFlow.exe'}")
        print(f"📦 Size: {(dist_dir / 'ClassFlow.exe').stat().st_size / (1024*1024):.1f} MB")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print("❌ Build failed!")
        print(f"Error: {e}")
        print(f"Output: {e.stdout}")
        print(f"Error: {e.stderr}")
        return False
    except FileNotFoundError:
        print("❌ PyInstaller not found!")
        print("Install with: pip install pyinstaller")
        return False

if __name__ == "__main__":
    build_executable()
