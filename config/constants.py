"""
Application constants and default values
"""

import os

# Application info
APP_NAME = "Ultra-Turbo AppData Cleaner"
APP_VERSION = "1.0.0"
APP_AUTHOR = "Pricop George"

# File patterns
SAFE_TO_DELETE_PATTERNS = [
    "*.tmp", "*.temp", "*.cache", "*.log", "*.old", "*.bak",
    "thumbs.db", "desktop.ini", "*.dmp", "*.chk"
]

DANGER_PATTERNS = [
    "*.exe", "*.dll", "*.sys", "*.ini", "*.cfg", "*.config",
    "*.key", "*.cert", "*.p12", "*.pfx"
]

BROWSER_CACHE_PATTERNS = [
    "*\\\\Cache\\\\*", "*\\\\GPUCache\\\\*", "*\\\\Code Cache\\\\*",
    "*\\\\Service Worker\\\\*", "*\\\\WebAssembly\\\\*"
]

# Size thresholds
MIN_FILE_SIZE_BYTES = 1024  # 1KB
MAX_FILE_SIZE_BYTES = 1024 * 1024 * 1024  # 1GB
DEFAULT_MAX_AGE_DAYS = 30

# System paths
APPDATA_PATHS = [
    os.path.expandvars("%APPDATA%"),
    os.path.expandvars("%LOCALAPPDATA%"),
    os.path.expandvars("%PROGRAMDATA%")
]

TEMP_PATHS = [
    os.path.expandvars("%TEMP%"),
    "C:\\\\Windows\\\\Temp",
    "C:\\\\Windows\\\\Prefetch"
]

# Browser paths
BROWSER_PATHS = {
    "chrome": os.path.expandvars("%LOCALAPPDATA%\\\\Google\\\\Chrome\\\\User Data"),
    "firefox": os.path.expandvars("%APPDATA%\\\\Mozilla\\\\Firefox\\\\Profiles"),
    "edge": os.path.expandvars("%LOCALAPPDATA%\\\\Microsoft\\\\Edge\\\\User Data"),
    "opera": os.path.expandvars("%APPDATA%\\\\Opera Software\\\\Opera Stable")
}

# Database settings
DB_NAME = "cleaner_db.sqlite"
DB_VERSION = 1

# Logging settings
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
MAX_LOG_SIZE_MB = 10
LOG_BACKUP_COUNT = 5