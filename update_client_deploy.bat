@echo off
echo.
echo ===============================================
echo   ClassFlow Client Deployment Update Script
echo ===============================================
echo.

REM Create clientdeploy folder if it doesn't exist
if not exist "clientdeploy" mkdir clientdeploy

echo Copying files to clientdeploy folder...
echo.

REM Copy the latest executable (check multiple possible names)
if exist "dist\ClassFlow_v1.4_TopSave.exe" (
    copy /Y "dist\ClassFlow_v1.4_TopSave.exe" "clientdeploy\ClassFlow_Latest.exe" >nul
    echo ✓ ClassFlow_Latest.exe copied (from v1.4_TopSave)
) else if exist "ClassFlow_v1.4.exe" (
    copy /Y "ClassFlow_v1.4.exe" "clientdeploy\ClassFlow_Latest.exe" >nul
    echo ✓ ClassFlow_Latest.exe copied (from v1.4)
) else if exist "ClassFlow_v1.3.exe" (
    copy /Y "ClassFlow_v1.3.exe" "clientdeploy\ClassFlow_Latest.exe" >nul
    echo ✓ ClassFlow_Latest.exe copied (from v1.3)
) else (
    echo ❌ No ClassFlow executable found!
)

REM Copy config and database
copy /Y "config.json" "clientdeploy\" >nul  
if exist "config.json" echo ✓ config.json copied

copy /Y "timetable.db" "clientdeploy\" >nul
if exist "timetable.db" echo ✓ timetable.db copied

REM Copy database auxiliary files if they exist
if exist "timetable.db-shm" copy /Y "timetable.db-shm" "clientdeploy\" >nul
if exist "timetable.db-wal" copy /Y "timetable.db-wal" "clientdeploy\" >nul

echo.
echo Contents of clientdeploy folder:
echo ================================
dir clientdeploy /B

echo.
echo ✅ Client deployment ready!
echo 📦 Share the 'clientdeploy' folder with your client
echo 🚀 Client can run ClassFlow_Latest.exe directly
echo.
pause
