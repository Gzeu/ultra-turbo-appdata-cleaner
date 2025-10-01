# 🚀 Ultra-Turbo AppData Cleaner

**Aplicație avansată Python pentru curățarea și optimizarea sistemului Windows**

O soluție completă pentru curățarea eficientă a fișierelor temporare, cache-ului browserelor, log-urilor vechi și a directorului AppData cu focus pe siguranța sistemului.

![Status](https://img.shields.io/badge/Status-Functional-brightgreen) ![Python](https://img.shields.io/badge/Python-3.8+-blue) ![Web](https://img.shields.io/badge/Web%20Interface-Ready-success) ![License](https://img.shields.io/badge/License-MIT-green)

## 🌟 Features Principale

### 🔍 **Scanare Inteligentă**
- **Scanare asincronă** pentru performanță optimă
- **Detecție automată** de fișiere temporare și cache
- **Analiză de siguranță** pe 5 niveluri (Very Safe → Dangerous)
- **Pattern matching** pentru aplicații specifice (Chrome, Firefox, Discord, VS Code)

### 🧹 **Curățare Avansată**
- **Module specializate** pentru fiecare tip de fișier
- **Backup automat** înainte de orice operațiune
- **Progress tracking** în timp real
- **Batch operations** pentru multiple locații

### 🛡️ **Siguranță Maximă**
- **Safety checks** pe multiple niveluri
- **Protected directories** detection
- **File-in-use** verification
- **System restore point** creation

### 🌐 **Interfață Web Modernă**
- **Dashboard interactiv** cu real-time updates
- **Control panel avansat** pentru operațiuni
- **Settings manager** complet
- **Live logs** cu filtering
- **Mobile responsive** design

## 📱 Instalare și Utilizare

### **Prerequisites**
```bash
# Python 3.8+ necesar
python --version

# Windows 10/11 (testat pe Windows 11)
```

### **Instalare Rapidă**
```bash
# 1. Clone repository
git clone https://github.com/Gzeu/ultra-turbo-appdata-cleaner.git
cd ultra-turbo-appdata-cleaner

# 2. Install core dependencies
pip install psutil pathlib

# 3. Pentru Web Interface (RECOMANDAT)
cd web
pip install -r requirements.txt

# 4. Run aplicația
python app.py       # Web interface
# SAU
cd ..
python main.py      # Console application
```

## 🌐 **Web Interface (Recomandat)**

### **Quick Start:**
```bash
cd web
python app.py
# Acces: http://localhost:5000
```

### **🎯 Dashboard Features:**
- **📊 System Overview** - Disk, Memory, CPU usage în timp real
- **📈 Interactive Charts** - Storage breakdown cu Chart.js
- **⚡ Quick Actions** - Scan și clean cu un click
- **📋 Activity Feed** - Monitor operațiuni în timp real
- **📱 Mobile Support** - Responsive pe toate dispozitivele

### **🎛️ Control Panel:**
- **🔍 Multiple Scan Types** - Quick, Full, AppData, Temp, Duplicates
- **📄 File Browser** cu checkbox selection
- **🎨 Safety Indicators** - Color coding pentru siguranță
- **🔧 Advanced Filters** - Categorie, siguranță, search
- **⚖️ Batch Operations** - Selecție și curățare multiplă

### **⚙️ Settings Manager:**
- **📂 Scan Paths** configuration
- **🛡️ Safety & Backup** settings
- **🎨 Theme Selection** - Dark/Light mode
- **🌍 Language Support** - Română/English

## 🔌 **API REST Endpoints**

```bash
# System Information
GET  /api/system/info           # Informații sistem

# Scan Operations
POST /api/scan/quick            # Scanare rapidă
POST /api/scan/full             # Scanare completă
POST /api/scan/appdata          # Scanare AppData
POST /api/scan/temp             # Scanare fișiere temp
POST /api/scan/duplicates       # Detectare duplicate

# Clean Operations
POST /api/clean/selected        # Curățare fișiere selectate
POST /api/clean/appdata         # Curățare AppData
POST /api/clean/temp            # Curățare temp files

# Progress & Settings
GET  /api/progress/{operation}  # Status operațiune
GET  /api/settings              # Obține setări
POST /api/settings              # Actualizează setări
```

## 🗂️ **Structura Proiectului**

```
ultra-turbo-appdata-cleaner/
├── main.py                    # Entry point principal
├── config/                   # 📁 Configurații aplicație
│   ├── __init__.py
│   ├── settings.py           # Management settings
│   ├── constants.py          # Constante aplicație
│   └── logging_config.py     # Configurare logging
├── core/                     # 🔧 Engine principal
│   ├── __init__.py
│   ├── cleaner.py            # Main cleaning engine
│   ├── scanner.py            # File system scanning
│   ├── analyzer.py           # File analysis & categorization
│   ├── safety.py             # Safety checks
│   └── progress.py           # Progress tracking
├── modules/                  # 🧩 Module specializate
│   ├── __init__.py
│   ├── appdata_cleaner.py    # Curățare AppData
│   ├── temp_cleaner.py       # Curățare temp files
│   ├── browser_cleaner.py    # Curățare cache browsere
│   ├── duplicate_finder.py   # Detecție duplicate
│   └── log_cleaner.py        # Curățare log-uri
├── utils/                    # 🛠️ Utilități
│   ├── __init__.py
│   ├── file_operations.py    # Operațiuni fișiere
│   ├── backup_manager.py     # Management backup
│   └── formatters.py         # Formatare date
└── web/                      # 🌐 **INTERFAȚA WEB COMPLETĂ**
    ├── app.py                # Flask application
    ├── config.py             # Web configuration
    ├── requirements.txt      # Web dependencies
    ├── websocket_handler.py  # Real-time communication
    ├── api/                  # 🔌 REST API
    │   ├── __init__.py
    │   ├── scanner.py        # Scan operations API
    │   ├── cleaner.py        # Clean operations API
    │   └── system.py         # System info API
    ├── templates/            # 📄 HTML Templates
    │   ├── base.html         # Layout principal
    │   ├── dashboard.html    # Dashboard interactiv
    │   ├── cleaner.html      # Control panel
    │   ├── settings.html     # Settings manager
    │   └── logs.html         # Log viewer
    ├── static/               # 📱 Frontend Assets
    │   ├── css/
    │   │   └── main.css      # Modern styling
    │   └── js/
    │       ├── main.js       # Core JavaScript
    │       ├── websocket.js  # WebSocket communication
    │       ├── dashboard.js  # Dashboard functions
    │       └── cleaner.js    # Cleaner functionality
    └── utils/                # 🔧 Web utilities
        ├── __init__.py
        ├── hash_calculator.py
        ├── size_calculator.py
        └── validators.py
```

## 🔥 **Module Specializate**

### **📁 AppData Cleaner**
- Curățare specializată pentru `%APPDATA%`, `%LOCALAPPDATA%`
- Pattern matching pentru Chrome, Firefox, Discord, VS Code
- Preserve configurări importante, șterge doar cache

### **⏰ Temp Cleaner**
- Detecție automată locații temporare
- Filtrare pe vârstă și dimensiune fișier
- Support pentru browser cache și system temp

### **🔍 Duplicate Finder**
- Algoritmi de hashing pentru detecție precisă
- Multiple strategii de păstrare (newest, oldest, shortest path)
- Analiză de spațiu irosit

### **🌍 Browser Cleaner**
- Support Chrome, Firefox, Edge, Opera
- Curățare cache, cookies, history
- Backup automat înainte de curățare

### **📜 Log Cleaner**
- Detecție inteligentă fișiere log
- Truncation pentru log-uri active
- Categorizare pe tip și importanță

## ⚙️ **Configurație**

### **Fișier Configurare:**
```json
{
  "scan_paths": [
    "%APPDATA%",
    "%LOCALAPPDATA%", 
    "%TEMP%",
    "C:\\Windows\\Temp"
  ],
  "backup_enabled": true,
  "safe_mode": true,
  "max_file_age_days": 30,
  "min_file_size_mb": 1,
  "excluded_extensions": [".exe", ".dll", ".sys"],
  "language": "ro_RO",
  "theme": "dark"
}
```

### **Localizare:**
- 🇷🇴 **Română** (default)
- 🇺🇸 **English** (disponibil)

## 📊 **Exemple de Utilizare**

### **Web Interface - Quick Start:**
```bash
# Start web server
cd web && python app.py

# Access dashboard
http://localhost:5000

# Quick scan via API
curl -X POST http://localhost:5000/api/scan/quick

# Clean temp files
curl -X POST http://localhost:5000/api/clean/temp \
  -H "Content-Type: application/json" \
  -d '{"max_age_days": 7, "create_backup": true}'
```

### **Console Application:**
```bash
# Rulare aplicație console
python main.py

# Sau cu parametri
python main.py --scan-type quick
python main.py --auto-clean
```

### **Python API Usage:**
```python
from config.settings import Settings
from core.cleaner import CleanerEngine
from modules.appdata_cleaner import AppDataCleaner

# Initialize
settings = Settings()
engine = CleanerEngine(settings)

# Quick AppData clean
appdata = AppDataCleaner(engine.progress_tracker)
files = appdata.scan_appdata()
results = appdata.clean_safe_files(files)

print(f"Cleaned {results['files_deleted']} files")
print(f"Freed {results['bytes_freed'] / (1024**2):.2f} MB")
```

## 📈 **Performance & Statistici**

### **Rezultate Tipice:**
- **AppData cleaning:** 200-500MB eliberat
- **Temp files:** 100-300MB eliberat 
- **Browser cache:** 50-200MB eliberat
- **Duplicates:** 10-100MB eliberat

### **Performanță:**
- **Scanare:** ~10,000 fișiere/secundă
- **Curățare:** ~1,000 fișiere/secundă
- **Memory usage:** <50MB RAM
- **Backup creation:** ~2-5MB/sec

## 🔒 **Siguranță și Backup**

### **Safety Levels:**
1. **🟢 Very Safe** - .tmp, .cache, thumbs.db
2. **🔵 Safe** - Browser cache, old logs
3. **🟡 Moderate** - User temp files
4. **🟠 Risky** - Application files
5. **🔴 Dangerous** - System files (BLOCKED)

### **Protected Locations:**
- `C:\Windows\System32\`
- `C:\Program Files\`
- `%USERPROFILE%\Documents\`
- Registry keys
- Active application files

### **Backup Strategy:**
- **Automatic backup** before every operation
- **ZIP compression** pentru spațiu optim
- **Manifest files** pentru tracking
- **Easy restoration** prin web interface

## 🌐 **Web Interface Screenshots**

### **📊 Dashboard:**
```
🏠 Ultra-Turbo AppData Cleaner Dashboard
├── 💾 System Overview
│   ├── Memory: 65% (8.2GB/16GB)
│   ├── Disk: 75% (750GB/1TB) 
│   └── Cleanup Potential: 2.4GB
├── 📊 Interactive Charts
│   ├── Storage breakdown (pie chart)
│   └── Cleanup categories (doughnut)
├── 🔔 Recent Activity Feed
└── ⚡ Quick Actions: [Scan] [Clean] [Settings]
```

### **🎛️ Cleaner Panel:**
```
🎯 Cleaning Control Panel
├── 🔍 Scan Options
│   ├── Type: [Quick|Full|AppData|Temp|Duplicates]
│   └── Max Age: 30 days, Min Size: 1MB
├── 📄 Results Table (sortable, filterable)
│   ├── Safety indicators cu color coding
│   ├── Checkbox selection pentru batch
│   └── File details cu preview
└── 🎯 Cleaning Controls
    ├── ☑️ Auto Backup (recommended)
    ├── ☑️ Safe Mode Only
    └── [Start Cleaning] cu confirmation
```

## 🛠️ **Development & Extensibilitate**

### **Arhitectură:**
- **Modular design** cu separația responsabilităților
- **Async processing** pentru performanță
- **Observer pattern** pentru progress updates
- **Strategy pattern** pentru cleaning algorithms

### **Extindere Module:**
```python
# Custom cleaning module
class CustomCleaner:
    def __init__(self, progress_tracker):
        self.progress_tracker = progress_tracker
    
    def scan_custom_files(self) -> Dict[str, List[Path]]:
        # Implementation
        pass
    
    def clean_custom_files(self) -> Dict:
        # Implementation 
        pass
```

### **API Extension:**
```python
# Add custom endpoint
@app.route('/api/custom/operation', methods=['POST'])
def custom_operation():
    # Custom logic
    return jsonify(results)
```

## 🔗 **Dependencies**

### **Core:**
- `psutil` - System monitoring
- `pathlib` - Path operations
- Standard Python libraries

### **Web Interface:**
- `Flask==2.3.3` - Web framework
- `Flask-SocketIO==5.3.6` - WebSocket support
- `psutil==5.9.5` - System monitoring
- `requests==2.31.0` - HTTP requests
- `Bootstrap 5` - UI framework (CDN)
- `Chart.js` - Interactive charts (CDN)

## 📝 **Changelog**

### **v1.0.0** (2025-10-01)
- ✨ Initial release cu toate modulele
- 🌐 Web interface complet cu API REST
- 🛡️ Safety system cu 5 niveluri
- 📊 Real-time progress tracking
- 💾 Backup system automat
- 🌍 Multi-browser support
- 🔍 Duplicate detection cu hashing
- ⚡ WebSocket pentru live updates
- 📱 Mobile responsive design
- 🎨 Dark/Light theme support

## 👤 **Author**

**Pricop George** - Blockchain Developer & AI Automation Specialist
- GitHub: [@Gzeu](https://github.com/Gzeu)
- Location: București, România
- Expertise: MultiversX blockchain, Python automation, Web development

## 📄 **License**

MIT License - see [LICENSE](LICENSE) file

## 🚀 **Getting Started**

1. **Web Interface** (recomandat pentru începători):
   ```bash
   git clone https://github.com/Gzeu/ultra-turbo-appdata-cleaner.git
   cd ultra-turbo-appdata-cleaner/web
   pip install -r requirements.txt
   python app.py
   # Access: http://localhost:5000
   ```

2. **Console Application**:
   ```bash
   cd ultra-turbo-appdata-cleaner
   python main.py
   ```

## 🎯 **Project Status**

- ✅ **Core Engine** - Fully implemented
- ✅ **Web Interface** - Complete with all features
- ✅ **API REST** - All endpoints functional
- ✅ **Safety System** - 5-level protection
- ✅ **Backup System** - Automatic ZIP backups
- ✅ **Real-time Updates** - WebSocket implementation
- ✅ **Mobile Support** - Responsive design
- ✅ **Documentation** - Complete README

---

**⚡ Ultra-Turbo AppData Cleaner** - Curățarea sistemului făcută simplu, sigur și eficient! 🎆

**🌟 Star the repo if you find it useful!**