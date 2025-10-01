"""
Size calculation utilities
"""

from pathlib import Path
from typing import Union, Dict, List
import logging

logger = logging.getLogger(__name__)

class SizeCalculator:
    """Utility class for size calculations"""
    
    @staticmethod
    def get_file_size(file_path: Union[str, Path]) -> int:
        """Get file size in bytes"""
        try:
            file_path = Path(file_path)
            if file_path.exists() and file_path.is_file():
                return file_path.stat().st_size
            return 0
        except Exception as e:
            logger.error(f"Error getting file size for {file_path}: {e}")
            return 0
    
    @staticmethod
    def get_directory_size(dir_path: Union[str, Path], max_depth: int = None) -> Dict[str, int]:
        """Get directory size with breakdown"""
        try:
            dir_path = Path(dir_path)
            if not dir_path.exists() or not dir_path.is_dir():
                return {'total_size': 0, 'file_count': 0, 'error': 'Directory does not exist'}
            
            total_size = 0
            file_count = 0
            current_depth = 0
            
            def scan_directory(path: Path, depth: int) -> None:
                nonlocal total_size, file_count
                
                if max_depth and depth > max_depth:
                    return
                
                try:
                    for item in path.iterdir():
                        try:
                            if item.is_file():
                                total_size += item.stat().st_size
                                file_count += 1
                            elif item.is_dir():
                                scan_directory(item, depth + 1)
                        except (PermissionError, OSError):
                            continue
                except (PermissionError, OSError):
                    pass
            
            scan_directory(dir_path, 0)
            
            return {
                'total_size': total_size,
                'file_count': file_count,
                'directory_count': len([d for d in dir_path.rglob('*') if d.is_dir()]) if max_depth is None else -1
            }
            
        except Exception as e:
            logger.error(f"Error calculating directory size for {dir_path}: {e}")
            return {'total_size': 0, 'file_count': 0, 'error': str(e)}
    
    @staticmethod
    def format_size(size_bytes: int) -> str:
        """Format size in human-readable format"""
        if size_bytes == 0:
            return "0 B"
        
        units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
        unit_index = 0
        size = float(size_bytes)
        
        while size >= 1024.0 and unit_index < len(units) - 1:
            size /= 1024.0
            unit_index += 1
        
        return f"{size:.1f} {units[unit_index]}"
    
    @staticmethod
    def calculate_sizes_for_files(file_paths: List[Union[str, Path]]) -> Dict:
        """Calculate total size for a list of files"""
        total_size = 0
        valid_files = 0
        invalid_files = 0
        
        for file_path in file_paths:
            size = SizeCalculator.get_file_size(file_path)
            if size > 0:
                total_size += size
                valid_files += 1
            else:
                invalid_files += 1
        
        return {
            'total_size': total_size,
            'total_size_formatted': SizeCalculator.format_size(total_size),
            'valid_files': valid_files,
            'invalid_files': invalid_files,
            'total_files': len(file_paths)
        }
    
    @staticmethod
    def get_largest_files(dir_path: Union[str, Path], count: int = 10) -> List[Dict]:
        """Get largest files in directory"""
        try:
            dir_path = Path(dir_path)
            if not dir_path.exists():
                return []
            
            files_with_sizes = []
            
            for file_path in dir_path.rglob('*'):
                if file_path.is_file():
                    try:
                        size = file_path.stat().st_size
                        files_with_sizes.append({
                            'path': str(file_path),
                            'name': file_path.name,
                            'size': size,
                            'size_formatted': SizeCalculator.format_size(size)
                        })
                    except (PermissionError, OSError):
                        continue
            
            # Sort by size (descending) and return top N
            files_with_sizes.sort(key=lambda x: x['size'], reverse=True)
            return files_with_sizes[:count]
            
        except Exception as e:
            logger.error(f"Error finding largest files in {dir_path}: {e}")
            return []
    
    @staticmethod
    def estimate_compression_ratio(file_path: Union[str, Path]) -> float:
        """Estimate compression ratio for a file based on extension"""
        try:
            file_path = Path(file_path)
            extension = file_path.suffix.lower()
            
            # Compression ratios based on file type
            compression_ratios = {
                '.txt': 0.3,
                '.log': 0.2,
                '.json': 0.3,
                '.xml': 0.2,
                '.csv': 0.4,
                '.html': 0.3,
                '.css': 0.4,
                '.js': 0.4,
                '.sql': 0.3,
                '.cache': 0.6,
                '.tmp': 0.5,
                '.bak': 0.7,  # Already might be compressed
                '.jpg': 0.95,  # Already compressed
                '.jpeg': 0.95,
                '.png': 0.9,
                '.gif': 0.95,
                '.mp3': 0.98,
                '.mp4': 0.98,
                '.avi': 0.95,
                '.zip': 0.98,
                '.rar': 0.98,
                '.7z': 0.98,
                '.exe': 0.8,
                '.dll': 0.8
            }
            
            return compression_ratios.get(extension, 0.6)  # Default 60% compression
            
        except Exception:
            return 0.6