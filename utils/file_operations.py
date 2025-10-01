"""
Low-level file system operations utilities
"""
import os
import shutil
from pathlib import Path
from typing import List, Dict, Optional, Union
import logging
from datetime import datetime
import tempfile

logger = logging.getLogger(__name__)

class FileOperations:
    """Low-level file operations with safety checks"""
    
    @staticmethod
    def safe_delete_file(file_path: Union[str, Path]) -> bool:
        """Safely delete a single file"""
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                return True
            
            if not file_path.is_file():
                logger.warning(f"Path is not a file: {file_path}")
                return False
            
            # Check if file is in use
            if FileOperations._is_file_locked(file_path):
                logger.warning(f"File is locked/in use: {file_path}")
                return False
            
            file_path.unlink()
            logger.debug(f"Deleted file: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete file {file_path}: {e}")
            return False
    
    @staticmethod
    def safe_delete_directory(dir_path: Union[str, Path], recursive: bool = False) -> bool:
        """Safely delete a directory"""
        try:
            dir_path = Path(dir_path)
            if not dir_path.exists():
                return True
            
            if not dir_path.is_dir():
                logger.warning(f"Path is not a directory: {dir_path}")
                return False
            
            if recursive:
                shutil.rmtree(dir_path)
                logger.debug(f"Deleted directory recursively: {dir_path}")
            else:
                dir_path.rmdir()  # Only works if empty
                logger.debug(f"Deleted empty directory: {dir_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete directory {dir_path}: {e}")
            return False
    
    @staticmethod
    def safe_copy_file(source: Union[str, Path], destination: Union[str, Path], 
                      overwrite: bool = False) -> bool:
        """Safely copy a file"""
        try:
            source = Path(source)
            destination = Path(destination)
            
            if not source.exists() or not source.is_file():
                logger.error(f"Source file does not exist: {source}")
                return False
            
            if destination.exists() and not overwrite:
                logger.warning(f"Destination exists and overwrite=False: {destination}")
                return False
            
            # Create destination directory if needed
            destination.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.copy2(source, destination)
            logger.debug(f"Copied file: {source} -> {destination}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to copy file {source} -> {destination}: {e}")
            return False
    
    @staticmethod
    def safe_move_file(source: Union[str, Path], destination: Union[str, Path]) -> bool:
        """Safely move/rename a file"""
        try:
            source = Path(source)
            destination = Path(destination)
            
            if not source.exists():
                logger.error(f"Source file does not exist: {source}")
                return False
            
            # Create destination directory if needed
            destination.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.move(str(source), str(destination))
            logger.debug(f"Moved file: {source} -> {destination}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to move file {source} -> {destination}: {e}")
            return False
    
    @staticmethod
    def get_file_info(file_path: Union[str, Path]) -> Optional[Dict]:
        """Get detailed file information"""
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                return None
            
            stat_info = file_path.stat()
            
            return {
                'path': str(file_path),
                'name': file_path.name,
                'size': stat_info.st_size,
                'created': datetime.fromtimestamp(stat_info.st_ctime),
                'modified': datetime.fromtimestamp(stat_info.st_mtime),
                'accessed': datetime.fromtimestamp(stat_info.st_atime),
                'is_file': file_path.is_file(),
                'is_directory': file_path.is_dir(),
                'extension': file_path.suffix.lower(),
                'parent': str(file_path.parent)
            }
            
        except Exception as e:
            logger.error(f"Failed to get file info for {file_path}: {e}")
            return None
    
    @staticmethod
    def create_temp_file(suffix: str = '.tmp', prefix: str = 'utac_') -> Optional[Path]:
        """Create a temporary file"""
        try:
            fd, temp_path = tempfile.mkstemp(suffix=suffix, prefix=prefix)
            os.close(fd)  # Close the file descriptor
            return Path(temp_path)
        except Exception as e:
            logger.error(f"Failed to create temp file: {e}")
            return None
    
    @staticmethod
    def create_temp_directory(suffix: str = '', prefix: str = 'utac_') -> Optional[Path]:
        """Create a temporary directory"""
        try:
            temp_dir = tempfile.mkdtemp(suffix=suffix, prefix=prefix)
            return Path(temp_dir)
        except Exception as e:
            logger.error(f"Failed to create temp directory: {e}")
            return None
    
    @staticmethod
    def _is_file_locked(file_path: Path) -> bool:
        """Check if file is locked/in use"""
        try:
            with open(file_path, 'r+b'):
                pass
            return False
        except (PermissionError, OSError):
            return True
        except Exception:
            return True
    
    @staticmethod
    def ensure_directory_exists(dir_path: Union[str, Path]) -> bool:
        """Ensure directory exists, create if necessary"""
        try:
            dir_path = Path(dir_path)
            dir_path.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            logger.error(f"Failed to create directory {dir_path}: {e}")
            return False
    
    @staticmethod
    def get_directory_size(dir_path: Union[str, Path]) -> int:
        """Get total size of directory in bytes"""
        try:
            dir_path = Path(dir_path)
            total_size = 0
            
            for item in dir_path.rglob('*'):
                if item.is_file():
                    try:
                        total_size += item.stat().st_size
                    except (OSError, PermissionError):
                        continue
            
            return total_size
            
        except Exception as e:
            logger.error(f"Failed to calculate directory size for {dir_path}: {e}")
            return 0
    
    @staticmethod
    def count_files_in_directory(dir_path: Union[str, Path]) -> Dict[str, int]:
        """Count files and directories in path"""
        try:
            dir_path = Path(dir_path)
            counts = {'files': 0, 'directories': 0, 'total': 0}
            
            for item in dir_path.rglob('*'):
                try:
                    if item.is_file():
                        counts['files'] += 1
                    elif item.is_dir():
                        counts['directories'] += 1
                    counts['total'] += 1
                except (OSError, PermissionError):
                    continue
            
            return counts
            
        except Exception as e:
            logger.error(f"Failed to count files in {dir_path}: {e}")
            return {'files': 0, 'directories': 0, 'total': 0}