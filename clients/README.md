# Client-Specific Versions

This folder will contain customized versions of Class Flow for different clients.

## 📁 Structure

Each client will have their own folder with:

```
clients/
├── client-name/
│   ├── config.json              # Client-specific configuration
│   ├── school_timetable_planner_new.py  # Customized main file
│   ├── branding/                # Client logos, themes, colors
│   ├── license/                 # License management files
│   └── dist/                    # Client-specific executable
```

## 🎯 Planned Client Features

### License Management
- 30-day trial period
- Activation key system
- Usage tracking
- Expiration notifications

### Admin Screen
- User management
- System settings
- License status
- Usage analytics

### Contact Management
- Teacher contact details
- Mobile number updates
- Communication features
- Emergency contacts

### Custom Branding
- Client logo integration
- Custom color schemes
- Personalized app name
- Client-specific help documentation

## 🔧 Setup Process for New Client

1. Create new branch: `git checkout -b client-{name}`
2. Create client folder: `mkdir clients/{client-name}`
3. Copy base files and customize
4. Implement client-specific features
5. Test and build executable
6. Deploy to client

## 🚀 Maintenance Strategy

- Base product updates merged into client branches
- Client-specific features developed separately
- Regular maintenance and support cycles
- Version control for each client deployment

---

Ready for client customization and deployment! 🎯
