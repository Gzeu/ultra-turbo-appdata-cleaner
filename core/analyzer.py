"""
File analysis and categorization module
"""
import os
import hashlib
import mimetypes
from pathlib import Path
from typing import Dict, List, Tuple, Set
from enum import Enum
import json
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class FileCategory(Enum):
    SAFE_TO_DELETE = "safe"
    POTENTIALLY_DANGEROUS = "dangerous" 
    CRITICAL_SYSTEM = "critical"
    USER_DATA = "user_data"
    CACHE = "cache"
    TEMP = "temp"
    LOG = "log"
    BACKUP = "backup"

class FileSafetyLevel(Enum):
    VERY_SAFE = 1
    SAFE = 2
    MODERATE = 3
    RISKY = 4
    DANGEROUS = 5

class FileAnalyzer:
    def __init__(self, settings):
        self.settings = settings
        self.patterns = self._load_patterns()
        
    def _load_patterns(self) -> Dict:
        """Load file categorization patterns"""
        return {
            "safe_extensions": [
                ".tmp", ".temp", ".log", ".cache", ".bak", ".old",
                ".~", ".swp", ".swo", ".pid", ".lock"
            ],
            "dangerous_extensions": [
                ".exe", ".dll", ".sys", ".ini", ".reg", ".bat",
                ".cmd", ".ps1", ".vbs", ".scr"
            ],
            "safe_directories": [
                "temp", "tmp", "cache", "logs", "backup", "old",
                "thumbnails", "cookies", "history"
            ]
        }
    
    def analyze_file(self, file_path: Path) -> Tuple[FileCategory, FileSafetyLevel]:
        """Analyze file and determine category and safety level"""
        try:
            extension = file_path.suffix.lower()
            
            if self._is_critical_system_file(file_path):
                return FileCategory.CRITICAL_SYSTEM, FileSafetyLevel.DANGEROUS
            
            if self._is_safe_temp_file(file_path):
                return FileCategory.TEMP, FileSafetyLevel.VERY_SAFE
                
            if self._is_cache_file(file_path):
                return FileCategory.CACHE, FileSafetyLevel.SAFE
                
            if self._is_log_file(file_path):
                return FileCategory.LOG, FileSafetyLevel.SAFE
            
            if extension in self.patterns["dangerous_extensions"]:
                return FileCategory.POTENTIALLY_DANGEROUS, FileSafetyLevel.RISKY
            
            return FileCategory.USER_DATA, FileSafetyLevel.MODERATE
            
        except Exception as e:
            logger.error(f"Error analyzing file {file_path}: {e}")
            return FileCategory.USER_DATA, FileSafetyLevel.RISKY
    
    def _is_critical_system_file(self, file_path: Path) -> bool:
        """Check if file is critical for system"""
        critical_paths = [
            "windows/system32",
            "windows/syswow64", 
            "program files"
        ]
        path_str = str(file_path).lower()
        return any(critical in path_str for critical in critical_paths)
    
    def _is_safe_temp_file(self, file_path: Path) -> bool:
        """Check if file is temporary and safe"""
        temp_indicators = [
            file_path.suffix.lower() in [".tmp", ".temp", ".~"],
            "temp" in file_path.name.lower(),
            file_path.name.startswith("~")
        ]
        return any(temp_indicators)
    
    def _is_cache_file(self, file_path: Path) -> bool:
        """Check if file is cache"""
        cache_indicators = [
            "cache" in str(file_path).lower(),
            "thumbnails" in str(file_path).lower(),
            file_path.name.lower() in ["thumbs.db", "desktop.ini"]
        ]
        return any(cache_indicators)
    
    def _is_log_file(self, file_path: Path) -> bool:
        """Check if file is log"""
        return (file_path.suffix.lower() == ".log" or 
                "log" in file_path.name.lower())
    
    async def analyze_files(self, file_paths: List[Dict]) -> List[Dict]:
        """Analyze multiple files"""
        results = []
        for file_info in file_paths:
            try:
                file_path = Path(file_info["path"])
                category, safety = self.analyze_file(file_path)
                
                file_info["category"] = category.value
                file_info["safety_level"] = safety.value
                file_info["cleanable"] = safety.value <= 2  # VERY_SAFE or SAFE
                
                results.append(file_info)
            except Exception as e:
                logger.error(f"Error analyzing {file_info}: {e}")
                file_info["category"] = "unknown"
                file_info["safety_level"] = 5
                file_info["cleanable"] = False
                results.append(file_info)
        
        return results