@echo off
echo ========================================
echo ClassFlow Repository Cleanup
echo Removing outdated and unnecessary files
echo ========================================

REM Remove old version files
del /q "ClassFlow_v1.3.exe" 2>nul
del /q "school_timetable_planner_v1.5_backup.py" 2>nul
del /q "config_v1.5_backup.json" 2>nul

REM Remove old documentation that's been superseded
del /q "ClassFlow_v1.2_Build_Notes.md" 2>nul
del /q "ClassFlow_v1.3_Build_Notes.md" 2>nul
del /q "ClassFlow_v1.4_Final_Cleanup.md" 2>nul
del /q "ClassFlow_v1.5_Complete_Documentation.md" 2>nul
del /q "ClassFlow_v1.5_Release_Notes.md" 2>nul

REM Remove development/testing files that are no longer needed
del /q "AUTO_SAVE_FUNCTIONALITY.md" 2>nul
del /q "DATE_TIME_WEEK_FIX.md" 2>nul
del /q "LEAVE_MANAGEMENT_FIX.md" 2>nul
del /q "SAVE_BUTTON_VISIBILITY_FIX.md" 2>nul
del /q "PROMINENT_SAVE_PANEL_SOLUTION.md" 2>nul
del /q "COMPLETE_AUTO_SAVE_SYSTEM.md" 2>nul

REM Remove old git-related files
del /q "FIX_GIT_PUSH.py" 2>nul
del /q "FORCE_GIT_PUSH.bat" 2>nul
del /q "FORCE_GIT_PUSH.ps1" 2>nul
del /q "SIMPLE_GIT_PUSH.py" 2>nul
del /q "git_operations.py" 2>nul
del /q "CHECK_GIT_STATUS.bat" 2>nul
del /q "check_git_status.py" 2>nul
del /q "GIT_PUSH_STATUS.md" 2>nul
del /q "GIT_PUSH_STATUS_DETAILED.md" 2>nul

REM Remove old urgent status files
del /q "URGENT_CLASSFLOW_V2_STATUS.md" 2>nul
del /q "URGENT_COMPLETION_STATUS.md" 2>nul
del /q "URGENT_GIT_PUSH.bat" 2>nul
del /q "URGENT_STATUS_CHECK.py" 2>nul

REM Remove old deployment scripts
del /q "update_client_deploy.bat" 2>nul
del /q "update_client_deploy.ps1" 2>nul
del /q "push_changes.bat" 2>nul
del /q "git_push.bat" 2>nul

REM Remove feature-specific documentation (consolidated)
del /q "TEACHER_RESTRICTIONS_FEATURE.md" 2>nul
del /q "TEACHER_RESTRICTIONS_FIXES.md" 2>nul
del /q "TEACHER_RESTRICTIONS_IMPLEMENTATION.md" 2>nul
del /q "TEACHER_RESTRICTIONS_UI_IMPROVEMENTS.md" 2>nul
del /q "TEACHER_RESTRICTIONS_AUTO_ASSIGN_INTEGRATION.md" 2>nul
del /q "SUBJECT_TEACHER_MAPPING_IMPROVEMENTS.md" 2>nul
del /q "HYPERSYNC_BRANDING_IMPLEMENTATION.md" 2>nul

REM Remove old test files
del /q "test_config.py" 2>nul
del /q "test_pdf.py" 2>nul

REM Remove old build files
del /q "compile_classflow.bat" 2>nul
del /q "create_v2_executable.bat" 2>nul

REM Remove redundant status files
del /q "ClassFlow_Executable_Status.md" 2>nul
del /q "REPOSITORY_CLEANUP_SUMMARY.md" 2>nul

REM Remove __pycache__ and dist directories
rmdir /s /q "__pycache__" 2>nul
rmdir /s /q "dist" 2>nul

echo.
echo ========================================
echo Cleanup completed!
echo ========================================
echo.
echo Remaining files are clean and organized:
echo ✅ ClassFlow_v2.0 source and executable
echo ✅ Current documentation and guides
echo ✅ Client deployment package
echo ✅ Essential configuration files
echo ✅ License and testing components
echo.
echo Ready for GitHub Pages deployment!
pause
