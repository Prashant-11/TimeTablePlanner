@echo off
REM Git Setup Script for Class Flow Base Product (Windows)

echo 🚀 Setting up Class Flow Git Repository...

REM Check if Git is installed
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Git is not installed. Please install Git first:
    echo    Download from: https://git-scm.com/download/windows
    pause
    exit /b 1
)

REM Initialize repository
echo 📦 Initializing Git repository...
git init

REM Configure Git (update with your details)
echo 🔧 Configuring Git...
git config user.name "Class Flow Developer"
git config user.email "developer@classflow.com"

REM Add all files
echo 📁 Adding project files...
git add .

REM Initial commit
echo 💾 Creating initial commit...
git commit -m "🎯 Initial commit - Class Flow Base Product v1.0.0

Features included:
✅ Core timetable management system
✅ Auto-assign functionality  
✅ Teacher leave management with impact analysis
✅ Excel and PDF export capabilities
✅ Smart conflict detection
✅ Enhanced UI with scrolling
✅ Internet connectivity validation
✅ Current week display
✅ Editable teacher assignments

Ready for client customization:
🔮 License system (30-day trial)
🔮 Admin screen
🔮 Mobile contact management
🔮 Custom branding
🔮 Multi-language support"

REM Create main branch
echo 🌟 Setting up main branch...
git branch -M main

REM Create development branch
echo 🔧 Creating development branch...
git checkout -b development
git checkout main

echo ✅ Git repository setup complete!
echo.
echo 📋 Next Steps:
echo 1. Create remote repository on GitHub/GitLab
echo 2. Add remote: git remote add origin ^<repository-url^>
echo 3. Push to remote: git push -u origin main
echo.
echo 🎯 For client customization:
echo git checkout -b client-{name}
echo mkdir clients\{client-name}
echo # Customize and deploy

pause
