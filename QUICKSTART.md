# 🚀 Ultra-Turbo AppData Cleaner - Quick Start Guide

**Get up and running in 3 minutes!** 🕒

## 📱 Option 1: Web Interface (Recommended)

### **Instalare rapidă:**
```bash
# 1. Clone repository
git clone https://github.com/Gzeu/ultra-turbo-appdata-cleaner.git
cd ultra-turbo-appdata-cleaner

# 2. Install dependencies
pip install flask flask-socketio psutil

# 3. Start web interface
python main.py
# SAU direct:
python web/app.py
```

### **Access:**
- **URL:** http://localhost:5000
- **DRY_RUN:** 🔒 Enabled by default (no files deleted)

---

## 💻 Option 2: Command Line Interface

```bash
# CLI mode
python main.py --cli

# Interactive menu cu opțiuni
```

---

## 🖼️ Option 3: GUI Desktop

```bash
# GUI mode (requires tkinter)
python main.py --gui
```

---

## 🔧 Advanced Setup (Optional)

### **Install as Package:**
```bash
# Editable installation
pip install -e .

# With web dependencies
pip install -e ".[web]"

# With all development tools
pip install -e ".[dev,test]"
```

### **Run as Package:**
```bash
# After installation
utac                    # Web interface
utac --cli              # CLI mode
utac --gui              # GUI mode
```

---

## 🔒 Safety Features

### **DRY_RUN Mode (Default):**
- **No files are actually deleted**
- Safe for testing and exploration
- Shows what WOULD be cleaned

### **Disable DRY_RUN (DANGER):**
```bash
# Windows CMD
set DRY_RUN=0
python main.py

# PowerShell
$env:DRY_RUN="0"
python main.py

# Direct argument
python main.py --no-dry-run
```

---

## 🎥 Quick Demo

1. **Start Web Interface:**
   ```bash
   python main.py
   ```

2. **Open Browser:** http://localhost:5000

3. **Try Features:**
   - 📊 **Dashboard** - View system stats
   - 🔍 **Quick Scan** - Scan for cleanable files
   - ⚙️ **Settings** - Configure options
   - 📜 **Logs** - View operation logs

4. **Toggle Theme:** Click 🌙 button in navbar

---

## ❌ Troubleshooting

### **Import Errors:**
```bash
# If you get ModuleNotFoundError
set PYTHONPATH=%CD%
python main.py

# Or use module syntax
python -m web.app
```

### **Missing Dependencies:**
```bash
# Install web requirements
pip install flask flask-socketio psutil requests

# Or from file
cd web
pip install -r requirements.txt
```

### **Port Already in Use:**
```bash
# Kill existing Python processes
taskkill /F /IM python.exe /T

# Or change port in code (web/app.py line ~290)
# socketio.run(app, debug=True, host='0.0.0.0', port=5001)
```

---

## 📊 Features Overview

### **Web Interface:**
- 📊 **Dashboard** with real-time system stats
- 🔍 **Multiple scan types** (Quick, Full, AppData, Temp)
- 📄 **File browser** with safety indicators
- ⚙️ **Settings management** with validation
- 📜 **Live logs** with filtering
- 🌐 **API endpoints** for automation
- 📱 **Mobile responsive** design

### **CLI Interface:**
- Interactive menu system
- Quick scan and clean operations
- Settings management
- Progress indicators

### **Safety Features:**
- 5-level safety system
- Automatic backups
- Protected directory detection
- File-in-use verification
- DRY_RUN mode by default

---

## 🚀 Next Steps

1. **Explore Web Interface** - Most features available
2. **Run Safe Scans** - DRY_RUN shows what would be cleaned
3. **Configure Settings** - Customize scan paths and safety
4. **Check Documentation** - Full README.md for advanced usage
5. **Test APIs** - Use /api/health, /api/system/info endpoints

---

**🎆 Ready to clean your system safely and efficiently!**

For issues or questions: [GitHub Issues](https://github.com/Gzeu/ultra-turbo-appdata-cleaner/issues)