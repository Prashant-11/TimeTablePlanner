# Class Flow - School Timetable Planner

## 🎯 Base Product - Version 1.0

**Class Flow** is a comprehensive school timetable management system built with Python Tkinter. This is the base product that will be customized for different clients.

### 🌟 Key Features

- **Dynamic Timetable Grid**: Scrollable interface supporting multiple classes and sections
- **Auto-Assign Intelligence**: Smart teacher and subject assignment
- **Teacher Leave Management**: Complete workflow with impact analysis and substitute assignment
- **Export Capabilities**: Excel (multi-worksheet) and PDF export
- **Smart Conflict Detection**: Validates teacher assignments and scheduling conflicts
- **Teacher Mapping**: Flexible subject-teacher assignment system
- **Data Persistence**: SQLite database with year/week organization

### 🔧 Technical Stack

- **Python 3.11.4**: Core development language
- **Tkinter**: GUI framework with enhanced scrolling
- **SQLite**: Database for persistent storage
- **pandas + openpyxl**: Excel export functionality
- **reportlab**: PDF generation
- **PyInstaller**: Executable packaging

### 📁 Project Structure

```
Class Flow Base/
├── school_timetable_planner_new.py    # Main application file
├── config.json                        # Dynamic configuration
├── timetable.db                        # SQLite database
├── generate_help_pdf.py               # Help documentation generator
├── TimetablePlanner_Help.pdf          # User manual
├── TimetablePlanner_Help.txt          # Text documentation
├── TimetablePlannerApp/                # Distribution folder
│   ├── dist/ClassFlow.exe             # Standalone executable
│   └── build/                         # Build artifacts
└── Documents/                         # Additional documentation

# Future Structure (Client-specific):
clients/
├── client-a/                          # Custom version for Client A
├── client-b/                          # Custom version for Client B
└── README.md                         # Client setup instructions
```

### 🚀 Quick Start

1. **Standalone Executable**: Run `TimetablePlannerApp/dist/ClassFlow.exe`
2. **Python Development**: Run `python school_timetable_planner_new.py`

### 📋 Current Features

#### Core Functionality
- ✅ Internet connectivity validation
- ✅ Current week display in header
- ✅ Dynamic class/section/teacher management
- ✅ Editable teacher assignments (combobox dropdowns)
- ✅ Enhanced scrolling (horizontal + vertical)

#### Teacher Leave Management
- ✅ Professional dialog with step-by-step workflow
- ✅ Real-time impact analysis
- ✅ Substitute teacher selection
- ✅ Visual feedback (red cells for impacted periods)
- ✅ Detailed confirmation messages

#### Export & Reports
- ✅ Excel export with separate worksheets per class
- ✅ PDF export with professional formatting
- ✅ Help documentation generation

#### Data Management
- ✅ Save/Load timetables by year and week
- ✅ Teacher-subject mapping configuration
- ✅ Smart conflict detection and resolution

### 🔮 Future Roadmap

#### Planned Features for Client Versions
- 🔐 **Licensing System**: 30-day trial with activation
- 👨‍💼 **Admin Screen**: User management and system settings
- 📱 **Contact Management**: Mobile number updates and communication
- 🎨 **Custom Branding**: Client-specific logos and themes
- 🌐 **Multi-language Support**: Localization for different regions
- ☁️ **Cloud Sync**: Optional cloud backup and synchronization
- 📊 **Advanced Reports**: Attendance, workload analysis, etc.

### 🏗️ Development Setup

#### Requirements
- Python 3.11.4+
- pip packages: `tkinter pandas openpyxl reportlab pyinstaller`

#### Building Executable
```bash
cd TimetablePlannerApp
pyinstaller --onefile --windowed --name="ClassFlow" school_timetable_planner_new.py
```

### 📝 Configuration

The `config.json` file contains:
- Classes and sections
- Teachers and subjects
- Teacher-subject mappings
- System settings

### 💾 Database Schema

SQLite database (`timetable.db`) with tables:
- `timetable`: Main timetable data (year, week, class, section, day, period, subject, teacher)

### 🎯 Client Customization Strategy

Each client will have:
1. **Separate branch**: `client-{name}` in Git
2. **Custom config**: Client-specific settings and branding
3. **License integration**: Trial and activation system
4. **Feature toggles**: Enable/disable features per client
5. **Custom executable**: Branded with client name

### 🔧 Support & Maintenance

- **Base Product Updates**: Merged into client branches
- **Client-Specific Features**: Developed in separate branches
- **Bug Fixes**: Applied to base and propagated to clients
- **Version Management**: Semantic versioning (v1.x.x)

### 📞 Contact

For development and customization inquiries, contact the development team.

---

**Built with ❤️ for educational institutions**
