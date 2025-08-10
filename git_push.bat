@echo off
echo.
echo =====================================
echo   ClassFlow Git Push Script
echo =====================================
echo.

set GIT_PATH="C:\Program Files\Git\bin\git.exe"

echo Adding all changes to git...
%GIT_PATH% add .

echo.
echo Committing changes...
%GIT_PATH% commit -m "ClassFlow v1.4: Top-right save button fix, cleanup unwanted files, updated client deployment"

echo.
echo Pushing to remote repository...
%GIT_PATH% push origin main

echo.
echo ✅ Changes pushed to git successfully!
echo.
pause
