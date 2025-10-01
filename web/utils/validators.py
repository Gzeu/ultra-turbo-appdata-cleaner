"""
Validation utilities for web interface
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Union, Optional
import logging

logger = logging.getLogger(__name__)

class Validators:
    """Utility class for various validations"""
    
    @staticmethod
    def is_valid_path(path: Union[str, Path]) -> bool:
        """Validate if path is valid and safe"""
        try:
            path = str(path).strip()
            if not path:
                return False
            
            # Check for invalid characters
            invalid_chars = ['<', '>', '"', '|', '?', '*']
            if any(char in path for char in invalid_chars):
                return False
            
            # Check for reserved names (Windows)
            reserved_names = [
                'CON', 'PRN', 'AUX', 'NUL',
                'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
                'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
            ]
            
            path_parts = Path(path).parts
            for part in path_parts:
                if part.upper() in reserved_names:
                    return False
            
            return True
            
        except Exception as e:
            logger.debug(f"Path validation error: {e}")
            return False
    
    @staticmethod
    def is_safe_to_delete(file_path: Union[str, Path]) -> Dict[str, Union[bool, str]]:
        """Check if file is safe to delete"""
        try:
            file_path = Path(file_path)
            
            # Check if file exists
            if not file_path.exists():
                return {'safe': False, 'reason': 'File does not exist'}
            
            path_str = str(file_path).lower()
            
            # Critical system directories - NEVER delete
            critical_paths = [
                'c:\\windows\\system32',
                'c:\\windows\\syswow64', 
                'c:\\program files',
                'c:\\program files (x86)',
                '\\windows\\',
                '\\system32\\',
                '\\syswow64\\'
            ]
            
            for critical_path in critical_paths:
                if critical_path in path_str:
                    return {'safe': False, 'reason': 'Critical system directory'}
            
            # Protected file types
            dangerous_extensions = ['.exe', '.dll', '.sys', '.ini', '.cfg', '.reg']
            if file_path.suffix.lower() in dangerous_extensions:
                # Allow deletion in temp directories
                temp_indicators = ['temp', 'tmp', 'cache']
                if not any(temp in path_str for temp in temp_indicators):
                    return {'safe': False, 'reason': 'System file type'}
            
            # User important directories
            user_important = [
                '\\documents\\',
                '\\desktop\\',
                '\\downloads\\',
                '\\pictures\\',
                '\\music\\',
                '\\videos\\'
            ]
            
            for important_path in user_important:
                if important_path in path_str:
                    return {'safe': False, 'reason': 'Important user directory'}
            
            # Check if file is in use
            if Validators.is_file_in_use(file_path):
                return {'safe': False, 'reason': 'File is currently in use'}
            
            return {'safe': True, 'reason': 'File appears safe to delete'}
            
        except Exception as e:
            logger.error(f"Safety check error for {file_path}: {e}")
            return {'safe': False, 'reason': f'Error during safety check: {str(e)}'}
    
    @staticmethod
    def is_file_in_use(file_path: Union[str, Path]) -> bool:
        """Check if file is currently in use"""
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                return False
            
            # Try to open file in exclusive mode
            with open(file_path, 'r+b'):
                pass
            return False
            
        except (PermissionError, OSError):
            return True
        except Exception:
            return True
    
    @staticmethod
    def validate_scan_paths(paths: List[str]) -> Dict[str, List[str]]:
        """Validate list of scan paths"""
        valid_paths = []
        invalid_paths = []
        warning_paths = []
        
        for path_str in paths:
            path_str = path_str.strip()
            if not path_str:
                continue
            
            # Expand environment variables
            expanded_path = os.path.expandvars(path_str)
            
            # Basic path validation
            if not Validators.is_valid_path(expanded_path):
                invalid_paths.append(path_str)
                continue
            
            path = Path(expanded_path)
            
            # Check if path exists
            if not path.exists():
                invalid_paths.append(path_str)
                continue
            
            # Check if path is accessible
            try:
                list(path.iterdir())
            except (PermissionError, OSError):
                warning_paths.append(path_str)
                continue
            
            # Check for potentially dangerous paths
            path_lower = str(path).lower()
            dangerous_indicators = ['system32', 'program files']
            
            if any(indicator in path_lower for indicator in dangerous_indicators):
                warning_paths.append(path_str)
            else:
                valid_paths.append(path_str)
        
        return {
            'valid': valid_paths,
            'invalid': invalid_paths,
            'warnings': warning_paths
        }
    
    @staticmethod
    def validate_settings(settings: Dict) -> Dict[str, List[str]]:
        """Validate application settings"""
        errors = []
        warnings = []
        
        # Validate scan paths
        if 'scan_paths' in settings:
            path_validation = Validators.validate_scan_paths(settings['scan_paths'])
            if path_validation['invalid']:
                errors.extend([f"Invalid path: {path}" for path in path_validation['invalid']])
            if path_validation['warnings']:
                warnings.extend([f"Potentially risky path: {path}" for path in path_validation['warnings']])
        
        # Validate age settings
        if 'max_file_age_days' in settings:
            age = settings['max_file_age_days']
            if not isinstance(age, (int, float)) or age <= 0 or age > 3650:  # 10 years max
                errors.append("Max file age must be between 1 and 3650 days")
        
        # Validate size settings
        if 'min_file_size_mb' in settings:
            size = settings['min_file_size_mb']
            if not isinstance(size, (int, float)) or size < 0 or size > 1000:  # 1GB max
                errors.append("Min file size must be between 0 and 1000 MB")
        
        # Validate backup path
        if 'backup_path' in settings and settings['backup_path']:
            backup_path = settings['backup_path']
            if not Validators.is_valid_path(backup_path):
                errors.append("Invalid backup path")
            else:
                backup_dir = Path(backup_path)
                if backup_dir.exists() and not os.access(backup_dir, os.W_OK):
                    errors.append("Backup path is not writable")
        
        return {
            'errors': errors,
            'warnings': warnings
        }
    
    @staticmethod
    def is_valid_email(email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def is_valid_file_pattern(pattern: str) -> bool:
        """Validate file pattern (glob-style)"""
        try:
            # Basic validation for glob patterns
            if not pattern:
                return False
            
            # Check for invalid characters that could be dangerous
            invalid_chars = ['<', '>', '"', '|']
            if any(char in pattern for char in invalid_chars):
                return False
            
            # Test if it's a valid glob pattern by trying to use it
            test_path = Path('.')
            list(test_path.glob(pattern))  # This will raise an error if pattern is invalid
            
            return True
            
        except Exception:
            return False
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename for safe usage"""
        # Remove or replace invalid characters
        filename = re.sub(r'[<>:"/\|?*]', '_', filename)
        
        # Remove control characters
        filename = re.sub(r'[\x00-\x1f\x7f]', '', filename)
        
        # Limit length
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            filename = name[:255-len(ext)] + ext
        
        # Remove leading/trailing spaces and dots
        filename = filename.strip(' .')
        
        # Ensure it's not empty
        if not filename:
            filename = 'unnamed_file'
        
        return filename