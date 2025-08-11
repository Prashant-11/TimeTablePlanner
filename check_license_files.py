import os
import json

# Check for license file in AppData
license_path = os.path.join(os.environ.get('APPDATA', ''), 'ClassFlow', 'license.json')
print(f"License file path: {license_path}")

if os.path.exists(license_path):
    print("✅ License file found!")
    try:
        with open(license_path, 'r') as f:
            license_data = json.load(f)
        print("License data contents:")
        for key, value in license_data.items():
            print(f"  {key}: {value}")
    except Exception as e:
        print(f"Error reading license file: {e}")
else:
    print("❌ No license file found")
    
    # Check if directory exists
    license_dir = os.path.dirname(license_path)
    if os.path.exists(license_dir):
        print(f"License directory exists: {license_dir}")
        files = os.listdir(license_dir)
        print(f"Files in directory: {files}")
    else:
        print("License directory doesn't exist")

# Also check current directory for any license files
print("\nChecking current directory for license files...")
current_files = [f for f in os.listdir('.') if 'license' in f.lower()]
if current_files:
    print("License-related files found:")
    for f in current_files:
        print(f"  - {f}")
else:
    print("No license files in current directory")

# Check clientdeploy for license files
clientdeploy_path = 'clientdeploy'
if os.path.exists(clientdeploy_path):
    print(f"\nChecking {clientdeploy_path} for license files...")
    client_files = [f for f in os.listdir(clientdeploy_path) if 'license' in f.lower()]
    if client_files:
        print("License-related files found:")
        for f in client_files:
            print(f"  - {f}")
    else:
        print("No license files in clientdeploy")
