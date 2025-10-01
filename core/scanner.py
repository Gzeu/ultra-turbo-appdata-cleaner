"""
File and directory scanning functionality
"""

import logging
import asyncio
import os
from pathlib import Path
from typing import List, Dict, Any, AsyncGenerator
import stat
import time

logger = logging.getLogger(__name__)

class FileScanner:
    """File system scanner for detecting files to clean"""
    
    def __init__(self, settings):
        self.settings = settings
        self.excluded_extensions = set(settings.get("excluded_extensions", []))
        self.min_file_size = settings.get("min_file_size_mb", 1) * 1024 * 1024
        self.max_file_age_days = settings.get("max_file_age_days", 30)
        
    async def scan_path(self, path: str) -> List[Dict[str, Any]]:
        """Scan a single path for files"""
        logger.info(f"Scanning path: {path}")
        
        try:
            path_obj = Path(path)
            if not path_obj.exists():
                logger.warning(f"Path does not exist: {path}")
                return []
            
            files = []
            async for file_info in self._scan_directory_async(path_obj):
                files.append(file_info)
                
                # Yield control periodically for better responsiveness
                if len(files) % 1000 == 0:
                    await asyncio.sleep(0.01)
            
            logger.info(f"Found {len(files)} files in {path}")
            return files
            
        except PermissionError:
            logger.warning(f"Permission denied accessing: {path}")
            return []
        except Exception as e:
            logger.error(f"Error scanning {path}: {e}")
            return []
    
    async def _scan_directory_async(self, directory: Path) -> AsyncGenerator[Dict[str, Any], None]:
        """Asynchronously scan directory and yield file information"""
        try:
            for item in directory.iterdir():
                try:
                    if item.is_file():
                        file_info = await self._get_file_info(item)
                        if file_info and self._should_include_file(file_info):
                            yield file_info
                    
                    elif item.is_dir() and not item.is_symlink():
                        # Recursively scan subdirectories
                        if self._should_scan_directory(item):
                            async for subfile in self._scan_directory_async(item):
                                yield subfile
                
                except (PermissionError, OSError) as e:
                    logger.debug(f"Cannot access {item}: {e}")
                    continue
                
                # Yield control
                await asyncio.sleep(0)
                
        except (PermissionError, OSError) as e:
            logger.debug(f"Cannot scan directory {directory}: {e}")
    
    async def _get_file_info(self, file_path: Path) -> Dict[str, Any]:
        """Get detailed information about a file"""
        try:
            stat_info = file_path.stat()
            
            return {
                "path": str(file_path),
                "name": file_path.name,
                "extension": file_path.suffix.lower(),
                "size": stat_info.st_size,
                "created_time": stat_info.st_ctime,
                "modified_time": stat_info.st_mtime,
                "accessed_time": stat_info.st_atime,
                "is_hidden": bool(stat_info.st_file_attributes & stat.FILE_ATTRIBUTE_HIDDEN) 
                             if hasattr(stat, 'FILE_ATTRIBUTE_HIDDEN') else False,
                "parent_dir": str(file_path.parent),
                "age_days": (time.time() - stat_info.st_mtime) / (24 * 3600)
            }
            
        except Exception as e:
            logger.debug(f"Error getting file info for {file_path}: {e}")
            return None
    
    def _should_include_file(self, file_info: Dict[str, Any]) -> bool:
        """Determine if file should be included in scan results"""
        # Check file extension
        if file_info["extension"] in self.excluded_extensions:
            return False
        
        # Check file size
        if file_info["size"] < self.min_file_size:
            return False
        
        # Check file age
        if file_info["age_days"] < 1:  # Don't touch very recent files
            return False
        
        return True
    
    def _should_scan_directory(self, directory: Path) -> bool:
        """Determine if directory should be scanned"""
        dir_name = directory.name.lower()
        
        # Skip system directories
        system_dirs = {
            "windows", "program files", "program files (x86)", 
            "system32", "syswow64", "$recycle.bin", "system volume information"
        }
        
        if dir_name in system_dirs:
            return False
        
        # Skip hidden directories that are likely system-critical
        try:
            if hasattr(stat, 'FILE_ATTRIBUTE_HIDDEN'):
                if directory.stat().st_file_attributes & stat.FILE_ATTRIBUTE_HIDDEN:
                    # Allow some known cache directories
                    allowed_hidden = {"appdata", "cache", "temp", "temporary internet files"}
                    if not any(allowed in dir_name for allowed in allowed_hidden):
                        return False
        except (AttributeError, OSError):
            pass
        
        return True
    
    def get_scan_statistics(self, files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get statistics about scanned files"""
        if not files:
            return {}
        
        total_size = sum(f["size"] for f in files)
        extensions = {}
        age_groups = {"0-7_days": 0, "7-30_days": 0, "30+_days": 0}
        
        for file_info in files:
            # Count extensions
            ext = file_info["extension"]
            extensions[ext] = extensions.get(ext, 0) + 1
            
            # Group by age
            age = file_info["age_days"]
            if age <= 7:
                age_groups["0-7_days"] += 1
            elif age <= 30:
                age_groups["7-30_days"] += 1
            else:
                age_groups["30+_days"] += 1
        
        return {
            "total_files": len(files),
            "total_size_mb": total_size / (1024 * 1024),
            "extensions": dict(sorted(extensions.items(), key=lambda x: x[1], reverse=True)[:10]),
            "age_distribution": age_groups,
            "average_file_size_mb": total_size / len(files) / (1024 * 1024),
            "largest_files": sorted(files, key=lambda x: x["size"], reverse=True)[:10]
        }