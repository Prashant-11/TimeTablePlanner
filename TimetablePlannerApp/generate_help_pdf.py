from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

help_txt = """
# School Timetable Planner - Help Guide

## Overview
This application is a comprehensive school timetable planner built with Python and Tkinter. It allows you to manage classes, sections, teachers, subjects, and generate weekly timetables with advanced features like auto-assignment, teacher leave management, and export to PDF/Excel.

## Features
- Login System (if enabled)
- Timetable Grid: View and edit the weekly timetable for all classes and sections.
- Auto Assign: Automatically assign teachers to periods based on subject mapping and availability.
- Smart Match: Advanced assignment logic for optimal teacher allocation.
- Teacher On Leave: Mark a teacher as on leave for a day and reassign their periods.
- Edit Mapping: Edit which teachers can teach which subjects.
- Export: Save the timetable as PDF or Excel.
- Configurable: All data (classes, sections, teachers, subjects, mapping) is stored in config.json.
- Refresh: Reload the timetable from the database.

## How to Use
1. Start the App: Double-click the executable or run python school_timetable_planner.py.
2. Select Year & Week: Use the top bar to choose the academic year and week number.
3. Edit Timetable: Click cells to assign subjects and teachers. Use dropdowns for quick selection.
4. Auto Assign/Smart Match: Use these buttons for automatic teacher allocation.
5. Teacher On Leave: Mark a teacher as absent and reassign their classes for the day.
6. Edit Mapping: Update which teachers can teach which subjects.
7. Export: Save the timetable as PDF or Excel for sharing/printing.
8. Refresh: Reload the timetable if you made changes elsewhere.

## File Descriptions
- school_timetable_planner.py: Main application file.
- config.json: Stores all classes, sections, teachers, subjects, and mappings.
- timetable.db: SQLite database for timetable data.
- TimetablePlanner_Help.txt: This help file.

## Creating an Executable
1. Install PyInstaller:
   pip install pyinstaller
2. Build the Executable:
   pyinstaller --onefile --noconsole --add-data "config.json;." --add-data "timetable.db;." school_timetable_planner.py
   - The executable will be in the dist folder.
   - Copy config.json and timetable.db to the same folder as the .exe if not bundled.

## Cleaning Up Unwanted Files
- Keep only:
  - school_timetable_planner.py
  - config.json
  - timetable.db
  - TimetablePlanner_Help.txt
- You can delete: .bak files, old versions, test scripts, images, HTML, JS, CSS, and any folders not needed for your use.

## Troubleshooting
- PDF Export Fails: Make sure reportlab is installed (pip install reportlab).
- Excel Export Fails: Make sure pandas and openpyxl are installed.
- UI Issues: Ensure you are using Python 3.7+ and have all dependencies installed.

## Contact
For further help, contact your developer or IT support.
"""

c = canvas.Canvas("TimetablePlanner_Help.pdf", pagesize=A4)
width, height = A4
lines = help_txt.split('\n')
y = height - 40
for line in lines:
    if y < 40:
        c.showPage()
        y = height - 40
    c.setFont("Helvetica", 10)
    c.drawString(40, y, line)
    y -= 15
c.save()
print("PDF help file created: TimetablePlanner_Help.pdf")
