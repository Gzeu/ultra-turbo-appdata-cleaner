"""
Application settings and configuration management
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional

class Settings:
    """Main settings manager for the application"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._get_default_config_path()
        self._settings = self._load_settings()
    
    def _get_default_config_path(self) -> str:
        """Get default configuration file path"""
        return os.path.join(os.path.expanduser("~"), ".ultra_turbo_cleaner", "config.json")
    
    def _load_settings(self) -> Dict[str, Any]:
        """Load settings from configuration file"""
        default_settings = {
            "scan_paths": [
                os.path.expandvars("%APPDATA%"),
                os.path.expandvars("%LOCALAPPDATA%"), 
                os.path.expandvars("%TEMP%"),
                "C:\\\\Windows\\\\Temp"
            ],
            "backup_enabled": True,
            "backup_path": os.path.join(os.path.expanduser("~"), ".ultra_turbo_cleaner", "backups"),
            "safe_mode": True,
            "max_file_age_days": 30,
            "min_file_size_mb": 1,
            "excluded_extensions": [".exe", ".dll", ".sys", ".ini"],
            "language": "ro_RO",
            "theme": "dark",
            "auto_backup": True,
            "confirmation_dialogs": True
        }
        
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                    default_settings.update(loaded_settings)
        except Exception as e:
            print(f"Error loading settings: {e}")
        
        return default_settings
    
    def save_settings(self):
        """Save current settings to file"""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self._settings, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving settings: {e}")
    
    def get(self, key: str, default=None):
        """Get setting value"""
        return self._settings.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set setting value"""
        self._settings[key] = value
    
    @property
    def scan_paths(self):
        return self.get("scan_paths", [])
    
    @property
    def backup_enabled(self):
        return self.get("backup_enabled", True)
    
    @property
    def safe_mode(self):
        return self.get("safe_mode", True)