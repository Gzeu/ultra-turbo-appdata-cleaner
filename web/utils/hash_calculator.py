"""
Hash calculation utilities for file operations
"""

import hashlib
from pathlib import Path
from typing import Optional, Union
import logging

logger = logging.getLogger(__name__)

class HashCalculator:
    """Utility class for file hash calculations"""
    
    @staticmethod
    def calculate_md5(file_path: Union[str, Path], chunk_size: int = 8192) -> Optional[str]:
        """Calculate MD5 hash of a file"""
        try:
            file_path = Path(file_path)
            if not file_path.exists() or not file_path.is_file():
                return None
            
            hash_md5 = hashlib.md5()
            with open(file_path, 'rb') as f:
                while chunk := f.read(chunk_size):
                    hash_md5.update(chunk)
            
            return hash_md5.hexdigest()
            
        except Exception as e:
            logger.error(f"Error calculating MD5 for {file_path}: {e}")
            return None
    
    @staticmethod
    def calculate_sha256(file_path: Union[str, Path], chunk_size: int = 8192) -> Optional[str]:
        """Calculate SHA256 hash of a file"""
        try:
            file_path = Path(file_path)
            if not file_path.exists() or not file_path.is_file():
                return None
            
            hash_sha256 = hashlib.sha256()
            with open(file_path, 'rb') as f:
                while chunk := f.read(chunk_size):
                    hash_sha256.update(chunk)
            
            return hash_sha256.hexdigest()
            
        except Exception as e:
            logger.error(f"Error calculating SHA256 for {file_path}: {e}")
            return None
    
    @staticmethod
    def quick_hash(file_path: Union[str, Path], sample_size: int = 1024) -> Optional[str]:
        """Calculate quick hash using first and last bytes + file size"""
        try:
            file_path = Path(file_path)
            if not file_path.exists() or not file_path.is_file():
                return None
            
            file_size = file_path.stat().st_size
            
            # For small files, use full content
            if file_size <= sample_size * 2:
                return HashCalculator.calculate_md5(file_path)
            
            hash_md5 = hashlib.md5()
            
            with open(file_path, 'rb') as f:
                # Read first sample_size bytes
                first_chunk = f.read(sample_size)
                hash_md5.update(first_chunk)
                
                # Add file size to hash
                hash_md5.update(str(file_size).encode())
                
                # Read last sample_size bytes
                f.seek(-sample_size, 2)
                last_chunk = f.read(sample_size)
                hash_md5.update(last_chunk)
            
            return hash_md5.hexdigest()
            
        except Exception as e:
            logger.error(f"Error calculating quick hash for {file_path}: {e}")
            return None