#!/bin/bash
# Git Setup Script for Class Flow Base Product

echo "🚀 Setting up Class Flow Git Repository..."

# Check if Git is installed
if ! command -v git &> /dev/null; then
    echo "❌ Git is not installed. Please install Git first:"
    echo "   Download from: https://git-scm.com/download/windows"
    exit 1
fi

# Initialize repository
echo "📦 Initializing Git repository..."
git init

# Add all files
echo "📁 Adding project files..."
git add .

# Initial commit
echo "💾 Creating initial commit..."
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

# Create main branch
echo "🌟 Setting up main branch..."
git branch -M main

# Create development branch
echo "🔧 Creating development branch..."
git checkout -b development
git checkout main

echo "✅ Git repository setup complete!"
echo ""
echo "📋 Next Steps:"
echo "1. Create remote repository on GitHub/GitLab"
echo "2. Add remote: git remote add origin <repository-url>"
echo "3. Push to remote: git push -u origin main"
echo ""
echo "🎯 For client customization:"
echo "git checkout -b client-{name}"
echo "mkdir clients/{client-name}"
echo "# Customize and deploy"
