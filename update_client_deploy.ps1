# ClassFlow Client Deployment Script
# This script copies the 3 essential files to clientdeploy folder
# Run this after any updates to exe, config, or database

Write-Host "🚀 ClassFlow Client Deployment Script" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Green

# Create clientdeploy folder if it doesn't exist
if (-not (Test-Path "clientdeploy")) {
    New-Item -ItemType Directory -Path "clientdeploy" | Out-Null
    Write-Host "✅ Created clientdeploy folder" -ForegroundColor Green
}

# Files to copy
$files = @(
    "ClassFlow_v1.3.exe",
    "config.json", 
    "timetable.db"
)

Write-Host "`n📋 Copying files to clientdeploy folder:" -ForegroundColor Yellow

foreach ($file in $files) {
    if (Test-Path $file) {
        Copy-Item $file "clientdeploy\" -Force
        $fileInfo = Get-Item $file
        $size = [math]::Round($fileInfo.Length / 1KB, 2)
        Write-Host "✅ $file ($size KB) - Modified: $($fileInfo.LastWriteTime)" -ForegroundColor Green
    } else {
        Write-Host "❌ $file - NOT FOUND!" -ForegroundColor Red
    }
}

# Show what's in the deployment folder
Write-Host "`n📦 Contents of clientdeploy folder:" -ForegroundColor Yellow
Get-ChildItem "clientdeploy" | Format-Table Name, Length, LastWriteTime -AutoSize

Write-Host "`n🎯 Client deployment ready!" -ForegroundColor Green
Write-Host "   Share the entire 'clientdeploy' folder with your client" -ForegroundColor Cyan
Write-Host "   or zip it and send: ClassFlow_v1.3.exe + config.json + timetable.db" -ForegroundColor Cyan

# Create a README for the client
$readmeContent = @"
# ClassFlow v1.3 - School Timetable Planner

## 📦 Installation Instructions:

1. **Extract all files** to a folder on your computer
2. **Double-click ClassFlow_v1.3.exe** to run the application
3. **Keep all 3 files together** in the same folder:
   - ClassFlow_v1.3.exe (Main application)
   - config.json (Configuration file)
   - timetable.db (Database file)

## ✨ New Features in v1.3:

- 🎯 **Teacher Restrictions**: Set which classes/sections each teacher can teach
- 💾 **Auto-Save**: Changes are automatically saved as you work
- 🔄 **Enhanced UI**: Modern interface with better visibility
- 📍 **Top-Right Save Button**: Clear save button in Teacher Restrictions dialog

## 🚀 How to Use Teacher Restrictions:

1. Click **"Teacher Management"** → **"Teacher Restrictions"**
2. Select teacher tabs to configure restrictions
3. Check boxes for allowed class-section combinations
4. Changes auto-save automatically
5. Click **"💾 SAVE & APPLY"** (top-right) for confirmation

## 📞 Support:

For any issues or questions, contact your ClassFlow administrator.

---
*Powered by Hypersync - An AI based education startup*
"@

Set-Content -Path "clientdeploy\README.txt" -Value $readmeContent
Write-Host "📝 Created README.txt for client instructions" -ForegroundColor Green
