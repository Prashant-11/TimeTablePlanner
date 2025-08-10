# Class Flow - Testing Checklist for Demo

## 1. Launch & UI
- [ ] App launches without errors (from .exe and Python script)
- [ ] Header shows "Class Flow" and "beta release"
- [ ] All main buttons visible: Auto-Assign, Smart Match, Teacher Mapping, Teacher Leave, Edit Classes, Edit Sections, Edit Teachers, Export Excel, Export PDF, Refresh

## 2. Data Editing
- [ ] Edit Classes: Add/remove classes, verify grid updates
- [ ] Edit Sections: Add/remove sections, verify grid updates
- [ ] Edit Teachers: Add/remove teachers, verify grid and mapping updates
- [ ] Teacher Mapping: Edit subject mapping for teachers, save and verify

## 3. Timetable Grid
- [ ] Grid displays all classes, sections, days, periods
- [ ] Can manually assign subjects and teachers in cells
- [ ] Changes persist after Save/Load

## 4. Auto-Assign
- [ ] Auto-Assign fills all cells with valid subject/teacher (no blanks)
- [ ] No teacher is double-booked in the same period (Smart Match shows no conflicts)

## 5. Smart Match
- [ ] Smart Match detects conflicts if a teacher is assigned to multiple classes/sections in the same period (case-insensitive)
- [ ] No false positives/negatives

## 6. Teacher Leave
- [ ] Mark a teacher on leave for a day, impacted cells are highlighted
- [ ] Can reassign impacted periods and save

## 7. Export
- [ ] Export Excel creates a valid file with all timetable data
- [ ] Export PDF creates a valid file with all timetable data

## 8. General
- [ ] No crashes or freezes during normal use
- [ ] All changes persist after closing and reopening the app

---

**Testers:**
- Mark each item as complete or note any issues found.
- Report any unexpected behavior, missing features, or UI glitches.

---

**Prepared by:** GitHub Copilot
**Date:** August 10, 2025
