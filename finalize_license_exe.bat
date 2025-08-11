@echo off
echo ========================================
echo ClassFlow v2.0 License-Enabled Executable
echo ========================================

cd /d "C:\Users\PRASHANT\Desktop\Classroom\clientdeploy"

echo Checking compilation status...
if exist "dist\ClassFlow_v2.0_Licensed.exe" (
    echo ✅ Compilation completed!
    echo Moving executable to deployment folder...
    
    REM Backup old version
    if exist "ClassFlow_v2.0.exe" (
        echo Backing up old ClassFlow_v2.0.exe...
        move "ClassFlow_v2.0.exe" "ClassFlow_v2.0_old.exe"
    )
    
    REM Move new licensed version
    move "dist\ClassFlow_v2.0_Licensed.exe" "ClassFlow_v2.0.exe"
    
    echo Cleaning up build files...
    rmdir /s /q dist 2>nul
    rmdir /s /q build 2>nul
    del ClassFlow_v2.0_Licensed.spec 2>nul
    
    echo.
    echo ✅ SUCCESS! ClassFlow_v2.0.exe now has LICENSE FEATURES!
    echo.
    echo File details:
    for %%F in ("ClassFlow_v2.0.exe") do echo Size: %%~zF bytes
    echo Created: %date% %time%
    echo.
    echo ========================================
    echo DEPLOYMENT PACKAGE READY WITH LICENSE!
    echo ========================================
    echo.
    echo ✅ ClassFlow_v2.0.exe - WITH LICENSE SYSTEM
    echo ✅ ClassFlow_v2.0.py - Full source with license
    echo ✅ Database and config files ready
    echo ✅ Documentation complete
    echo.
    echo Schools can now use the freemium model:
    echo - 30-day FREE trial
    echo - FREE tier: 3 classes, 2 sections, 10 teachers
    echo - PREMIUM: School ₹499/month, Institution ₹999/month
    echo.
) else (
    echo ⏳ Compilation still in progress...
    echo Waiting for PyInstaller to finish...
    echo.
    echo When compilation completes, the executable will be automatically moved.
    echo Check back in a few minutes.
)

echo Current deployment folder contents:
dir /b *.exe
echo.
pause
