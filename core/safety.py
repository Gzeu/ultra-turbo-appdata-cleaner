"""
Safety checks and validation module
"""
import os
import shutil
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional
import logging
from enum import Enum
import psutil

logger = logging.getLogger(__name__)

class SafetyLevel(Enum):
    NONE = 0
    BASIC = 1
    STANDARD = 2
    PARANOID = 3

class SafetyChecker:
    def __init__(self, settings):
        self.settings = settings
        self.safety_level = SafetyLevel.STANDARD
        self.critical_processes = self._load_critical_processes()
        self.protected_directories = self._load_protected_directories()
        
    def _load_critical_processes(self) -> Set[str]:
        """Load critical processes that shouldn't be affected"""
        return {
            "explorer.exe", "winlogon.exe", "csrss.exe", "smss.exe",
            "wininit.exe", "services.exe", "lsass.exe", "dwm.exe"
        }
    
    def _load_protected_directories(self) -> Set[Path]:
        """Load protected directories that shouldn't be modified"""
        system_root = Path(os.environ.get("SYSTEMROOT", "C:\\Windows"))
        program_files = Path(os.environ.get("PROGRAMFILES", "C:\\Program Files"))
        
        return {
            system_root,
            system_root / "System32",
            system_root / "SysWOW64",
            program_files
        }
    
    def is_safe_to_delete(self, file_info: Dict) -> bool:
        """Check if file is safe to delete"""
        try:
            file_path = Path(file_info["path"])
            
            # Check if in protected directory
            for protected in self.protected_directories:
                try:
                    if file_path.is_relative_to(protected):
                        return False
                except (ValueError, OSError):
                    continue
            
            # Check if file is in use
            if self._is_file_in_use(file_path):
                return False
            
            # Check safety level from analyzer
            safety_level = file_info.get("safety_level", 5)
            return safety_level <= 2  # VERY_SAFE or SAFE only
            
        except Exception as e:
            logger.error(f"Error checking safety for {file_info}: {e}")
            return False
    
    def _is_file_in_use(self, file_path: Path) -> bool:
        """Check if file is currently in use"""
        try:
            with open(file_path, 'r+b'):
                pass
            return False
        except (PermissionError, OSError):
            return True
        except Exception:
            return True
    
    def pre_operation_checks(self, target_paths: List[Path]) -> Tuple[bool, List[str]]:
        """Perform checks before any operation"""
        warnings = []
        can_proceed = True
        
        # Check running processes
        if not self._check_running_processes():
            warnings.append("Critical processes check failed")
            can_proceed = False
        
        # Check permissions
        inaccessible = self._check_permissions(target_paths)
        if inaccessible:
            warnings.append(f"Cannot access {len(inaccessible)} files")
        
        return can_proceed, warnings
    
    def _check_running_processes(self) -> bool:
        """Check that critical processes are running normally"""
        try:
            running_processes = {proc.name().lower() for proc in psutil.process_iter(['name'])}
            critical_running = self.critical_processes.intersection(running_processes)
            return len(critical_running) >= len(self.critical_processes) * 0.8
        except Exception:
            return False
    
    def _check_permissions(self, target_paths: List[Path]) -> List[Path]:
        """Check permissions for target files"""
        inaccessible = []
        for path in target_paths:
            try:
                if path.exists():
                    path.stat()
            except (PermissionError, OSError):
                inaccessible.append(path)
        return inaccessible