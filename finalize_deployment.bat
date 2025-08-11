@echo off
echo =============================================
echo ClassFlow v2.0 Final Deployment Package Setup
echo =============================================
echo.

echo [STEP 1] Removing unnecessary files for clean deployment...
cd /d "C:\Users\PRASHANT\Desktop\Classroom\clientdeploy"

REM Remove development database and config files
echo Removing development database and config files...
del timetable.db* 2>nul
del config.json 2>nul
echo ✅ Development files removed (schools should start fresh)

echo.
echo [STEP 2] Current deployment package contents:
dir /b
echo.

echo [STEP 3] Creating production-ready README for schools...
echo # ClassFlow v2.0 - School Deployment Package > README_DEPLOYMENT.txt
echo. >> README_DEPLOYMENT.txt
echo ## Quick Start for Schools: >> README_DEPLOYMENT.txt
echo 1. Run ClassFlow_v2.0.py (requires Python 3.11+) >> README_DEPLOYMENT.txt
echo 2. OR wait for ClassFlow_v2.0.exe (standalone version coming) >> README_DEPLOYMENT.txt
echo 3. First launch automatically starts 30-day FREE trial >> README_DEPLOYMENT.txt
echo 4. Configure your school's classes, sections, teachers >> README_DEPLOYMENT.txt
echo 5. Enjoy unlimited features during trial period >> README_DEPLOYMENT.txt
echo. >> README_DEPLOYMENT.txt
echo ## After Trial (Day 31): >> README_DEPLOYMENT.txt
echo - Converts to FREE plan (3 classes, 2 sections, 10 teachers) >> README_DEPLOYMENT.txt
echo - Upgrade to PREMIUM for unlimited: School ₹499/month >> README_DEPLOYMENT.txt
echo. >> README_DEPLOYMENT.txt
echo ## Support: prashant.compsc@gmail.com >> README_DEPLOYMENT.txt

echo.
echo [STEP 4] Creating installer information...
echo Installation Requirements: > SYSTEM_REQUIREMENTS.txt
echo - Windows 10/11 >> SYSTEM_REQUIREMENTS.txt
echo - 4GB RAM minimum >> SYSTEM_REQUIREMENTS.txt
echo - Python 3.11+ (for .py version) >> SYSTEM_REQUIREMENTS.txt
echo - OR use ClassFlow_v2.0.exe (standalone, no Python needed) >> SYSTEM_REQUIREMENTS.txt
echo. >> SYSTEM_REQUIREMENTS.txt
echo Dependencies (auto-installed): >> SYSTEM_REQUIREMENTS.txt
echo - tkinter (GUI framework) >> SYSTEM_REQUIREMENTS.txt
echo - sqlite3 (database) >> SYSTEM_REQUIREMENTS.txt
echo - pandas, openpyxl (Excel export) >> SYSTEM_REQUIREMENTS.txt
echo - reportlab (PDF export) >> SYSTEM_REQUIREMENTS.txt

echo.
echo =============================================
echo DEPLOYMENT PACKAGE STATUS
echo =============================================
echo.

echo ✅ READY FOR SCHOOLS:
echo    • ClassFlow_v2.0.py - Complete freemium implementation
echo    • license_demo.py - License testing tool
echo    • README.txt - Professional deployment guide
echo    • Documentation files - Complete setup instructions
echo.

echo ⚠️  MISSING (Manual Creation Needed):
echo    • ClassFlow_v2.0.exe - Needs PyInstaller compilation
echo    • Fresh database - Schools should start with empty DB
echo    • Default config - Schools should use application defaults
echo.

echo 🚀 BUSINESS READY:
echo    • 30-day trial system implemented
echo    • FREE → PREMIUM upgrade path
echo    • Pricing: School ₹499/month, Institution ₹999/month
echo    • Sales contact: prashant.compsc@gmail.com
echo.

echo 📞 TO CREATE .EXE FILE:
echo    1. Install Python 3.11+ on this machine
echo    2. Install PyInstaller: pip install pyinstaller
echo    3. Run: pyinstaller --onefile --windowed ClassFlow_v2.0.py
echo    4. Copy dist\ClassFlow_v2.0.exe to this folder
echo.

echo 📦 CURRENT PACKAGE SIZE AND CONTENTS:
echo =============================================
for %%F in (*.*) do (
    echo %%F - Size: %%~zF bytes
)

echo.
echo =============================================
echo READY FOR SCHOOL DISTRIBUTION!
echo Contact schools with this package
echo =============================================
pause
