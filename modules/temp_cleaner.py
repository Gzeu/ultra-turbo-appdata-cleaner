"""
Temporary files cleaning module
"""
import os
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Set, Optional
import logging
from datetime import datetime, timedelta
from core.progress import ProgressTracker, ProgressType

logger = logging.getLogger(__name__)

class TempCleaner:
    """Specialized cleaner for temporary files"""
    
    def __init__(self, progress_tracker: ProgressTracker):
        self.progress_tracker = progress_tracker
        self.temp_locations = self._discover_temp_locations()
        self.stats = {
            'locations_scanned': 0,
            'files_found': 0,
            'files_cleaned': 0,
            'bytes_freed': 0,
            'errors': 0
        }
    
    def _discover_temp_locations(self) -> Dict[str, Path]:
        """Discover all locations for temporary files"""
        locations = {}
        
        # Standard Windows locations
        temp_dirs = [
            ('system_temp', Path(tempfile.gettempdir())),
            ('user_temp', Path(os.environ.get('TEMP', ''))),
            ('windows_temp', Path('C:\\Windows\\Temp')),
        ]
        
        # Add browser temp locations
        try:
            user_profile = Path(os.environ.get('USERPROFILE', ''))
            additional_temps = [
                ('ie_temp', user_profile / 'AppData' / 'Local' / 'Microsoft' / 'Windows' / 'INetCache'),
                ('edge_temp', user_profile / 'AppData' / 'Local' / 'Microsoft' / 'Edge' / 'User Data' / 'Default' / 'Cache'),
                ('chrome_temp', user_profile / 'AppData' / 'Local' / 'Google' / 'Chrome' / 'User Data' / 'Default' / 'Cache'),
            ]
            temp_dirs.extend(additional_temps)
        except Exception as e:
            logger.warning(f"Could not add browser temp locations: {e}")
        
        # Check accessibility
        for name, path in temp_dirs:
            try:
                if path.exists() and os.access(path, os.R_OK):
                    locations[name] = path
                    logger.info(f"Temp location accessible: {name} = {path}")
            except Exception as e:
                logger.warning(f"Error checking temp location {name}: {e}")
        
        return locations
    
    def scan_temp_files(self, max_age_days: int = 7, min_size_mb: float = 0.1) -> Dict[str, List[Path]]:
        """Scan temporary files based on specified criteria"""
        operation_id = f"temp_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        min_size_bytes = int(min_size_mb * 1024 * 1024)
        
        progress = self.progress_tracker.create_operation(
            operation_id, "Scanning temporary files",
            len(self.temp_locations)
        )
        
        self.progress_tracker.start_operation(operation_id)
        
        categorized_files = {
            'old_temp_files': [],
            'large_temp_files': [],
            'browser_cache': [],
            'system_temp': [],
            'locked_files': []
        }
        
        for i, (location_name, location_path) in enumerate(self.temp_locations.items()):
            try:
                self.progress_tracker.update_progress(
                    operation_id, i + 1,
                    current_item=location_name,
                    status_message=f"Scanning {location_name}"
                )
                
                files_in_location = self._scan_location(
                    location_path, cutoff_date, min_size_bytes
                )
                
                # Categorize files based on location and characteristics
                for file_path in files_in_location:
                    category = self._categorize_temp_file(file_path, location_name, cutoff_date, min_size_bytes)
                    categorized_files[category].append(file_path)
                
                self.stats['locations_scanned'] += 1
                self.stats['files_found'] += len(files_in_location)
                
            except Exception as e:
                logger.error(f"Error scanning location {location_name}: {e}")
                self.stats['errors'] += 1
        
        # Check for locked files
        self._check_locked_files(categorized_files)
        
        self.progress_tracker.complete_operation(operation_id, True)
        
        return categorized_files
    
    def _scan_location(self, location_path: Path, cutoff_date: datetime, min_size_bytes: int) -> List[Path]:
        """Scan a specific location for temporary files"""
        temp_files = []
        
        try:
            for item in location_path.rglob('*'):
                try:
                    if not item.is_file():
                        continue
                    
                    modified_time = datetime.fromtimestamp(item.stat().st_mtime)
                    file_size = item.stat().st_size
                    
                    # Criteria for inclusion
                    is_old = modified_time < cutoff_date
                    is_large = file_size >= min_size_bytes
                    is_temp_extension = self._has_temp_extension(item)
                    
                    if is_old or is_large or is_temp_extension:
                        temp_files.append(item)
                        
                except (PermissionError, OSError):
                    continue
                except Exception:
                    continue
        
        except Exception as e:
            logger.error(f"Error scanning location {location_path}: {e}")
        
        return temp_files
    
    def _categorize_temp_file(self, file_path: Path, location_name: str, 
                             cutoff_date: datetime, min_size_bytes: int) -> str:
        """Categorize a temporary file"""
        try:
            # Check if browser cache
            browser_indicators = ['cache', 'firefox', 'chrome', 'edge', 'inetcache']
            if any(indicator in location_name.lower() for indicator in browser_indicators):
                return 'browser_cache'
            
            # Check if system temp
            if 'system' in location_name.lower() or 'windows' in location_name.lower():
                return 'system_temp'
            
            # Check based on age and size
            file_stat = file_path.stat()
            modified_time = datetime.fromtimestamp(file_stat.st_mtime)
            file_size = file_stat.st_size
            
            if file_size >= min_size_bytes and modified_time < cutoff_date:
                return 'large_temp_files'
            elif modified_time < cutoff_date:
                return 'old_temp_files'
            else:
                return 'old_temp_files'  # Default
                
        except Exception:
            return 'old_temp_files'
    
    def _has_temp_extension(self, file_path: Path) -> bool:
        """Check if file has temporary extension"""
        temp_extensions = {
            '.tmp', '.temp', '.~', '.bak', '.old', '.cache',
            '.log', '.pid', '.lock', '.swp', '.swo'
        }
        return file_path.suffix.lower() in temp_extensions
    
    def _check_locked_files(self, categorized_files: Dict[str, List[Path]]) -> None:
        """Check which files are locked and move to separate category"""
        for category in list(categorized_files.keys()):
            if category == 'locked_files':
                continue
                
            files_to_move = []
            remaining_files = []
            
            for file_path in categorized_files[category]:
                if self._is_file_locked(file_path):
                    files_to_move.append(file_path)
                else:
                    remaining_files.append(file_path)
            
            categorized_files[category] = remaining_files
            categorized_files['locked_files'].extend(files_to_move)
    
    def _is_file_locked(self, file_path: Path) -> bool:
        """Check if file is locked/in use"""
        try:
            with open(file_path, 'r+b'):
                pass
            return False
        except (PermissionError, OSError):
            return True
        except Exception:
            return True
    
    def clean_temp_files(self, categorized_files: Dict[str, List[Path]], 
                        categories_to_clean: List[str] = None) -> Dict:
        """Clean temporary files from specified categories"""
        if categories_to_clean is None:
            categories_to_clean = ['old_temp_files', 'browser_cache']
        
        operation_id = f"temp_clean_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        files_to_clean = []
        for category in categories_to_clean:
            if category in categorized_files:
                files_to_clean.extend(categorized_files[category])
        
        progress = self.progress_tracker.create_operation(
            operation_id, "Cleaning temporary files",
            len(files_to_clean)
        )
        
        self.progress_tracker.start_operation(operation_id)
        
        results = {
            'files_deleted': 0,
            'bytes_freed': 0,
            'failed_deletions': [],
            'directories_removed': 0,
            'categories_processed': categories_to_clean
        }
        
        for i, file_path in enumerate(files_to_clean):
            try:
                if not file_path.exists():
                    continue
                
                file_size = file_path.stat().st_size
                
                # Delete file
                file_path.unlink()
                
                results['files_deleted'] += 1
                results['bytes_freed'] += file_size
                self.stats['files_cleaned'] += 1
                self.stats['bytes_freed'] += file_size
                
                self.progress_tracker.update_progress(
                    operation_id, i + 1,
                    current_item=file_path.name,
                    status_message=f"Cleaned from {file_path.parent.name}"
                )
                
            except Exception as e:
                logger.error(f"Failed to delete {file_path}: {e}")
                results['failed_deletions'].append(str(file_path))
                self.stats['errors'] += 1
        
        self.progress_tracker.complete_operation(operation_id, True)
        
        return results
    
    def get_temp_analysis(self, categorized_files: Dict[str, List[Path]]) -> Dict:
        """Analyze found temporary files"""
        analysis = {
            'total_files': 0,
            'total_size_bytes': 0,
            'categories': {},
            'largest_files': [],
            'oldest_files': []
        }
        
        all_files_with_info = []
        
        for category, files in categorized_files.items():
            category_size = 0
            category_count = len(files)
            
            for file_path in files:
                try:
                    if file_path.exists() and file_path.is_file():
                        file_stat = file_path.stat()
                        file_size = file_stat.st_size
                        file_modified = datetime.fromtimestamp(file_stat.st_mtime)
                        
                        category_size += file_size
                        all_files_with_info.append({
                            'path': file_path,
                            'size': file_size,
                            'modified': file_modified,
                            'category': category
                        })
                except Exception:
                    continue
            
            analysis['categories'][category] = {
                'file_count': category_count,
                'total_size_bytes': category_size,
                'total_size_formatted': self._format_bytes(category_size)
            }
            
            analysis['total_files'] += category_count
            analysis['total_size_bytes'] += category_size
        
        # Top 10 largest files
        largest_files = sorted(all_files_with_info, key=lambda x: x['size'], reverse=True)[:10]
        analysis['largest_files'] = [
            {
                'path': str(f['path']),
                'size_formatted': self._format_bytes(f['size']),
                'category': f['category']
            }
            for f in largest_files
        ]
        
        analysis['total_size_formatted'] = self._format_bytes(analysis['total_size_bytes'])
        
        return analysis
    
    def _format_bytes(self, bytes_value: int) -> str:
        """Format bytes in human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.1f} PB"