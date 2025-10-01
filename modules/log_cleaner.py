"""
Log files cleaning module
"""
import os
from pathlib import Path
from typing import List, Dict, Optional
import logging
from datetime import datetime, timedelta
from core.progress import ProgressTracker

logger = logging.getLogger(__name__)

class LogCleaner:
    """Specialized cleaner for log files"""
    
    def __init__(self, progress_tracker: ProgressTracker):
        self.progress_tracker = progress_tracker
        self.log_locations = self._discover_log_locations()
        self.stats = {
            'locations_scanned': 0,
            'log_files_found': 0,
            'log_files_cleaned': 0,
            'bytes_freed': 0
        }
    
    def _discover_log_locations(self) -> Dict[str, Path]:
        """Discover common log file locations"""
        locations = {}
        
        # Common Windows log locations
        log_paths = [
            ('windows_logs', Path('C:/Windows/Logs')),
            ('windows_temp_logs', Path('C:/Windows/Temp')),
            ('system_logs', Path('C:/Windows/System32/LogFiles')),
            ('iis_logs', Path('C:/inetpub/logs/LogFiles')),
        ]
        
        # User-specific log locations
        try:
            user_profile = Path(os.environ.get('USERPROFILE', ''))
            user_log_paths = [
                ('user_temp_logs', user_profile / 'AppData' / 'Local' / 'Temp'),
                ('application_logs', user_profile / 'AppData' / 'Local'),
                ('roaming_logs', user_profile / 'AppData' / 'Roaming'),
            ]
            log_paths.extend(user_log_paths)
        except Exception as e:
            logger.warning(f"Could not add user log locations: {e}")
        
        # Check accessibility
        for name, path in log_paths:
            try:
                if path.exists() and os.access(path, os.R_OK):
                    locations[name] = path
                    logger.info(f"Log location accessible: {name} = {path}")
            except Exception as e:
                logger.debug(f"Error checking log location {name}: {e}")
        
        return locations
    
    def scan_log_files(self, max_age_days: int = 30, min_size_mb: float = 0.1) -> Dict[str, List[Path]]:
        """Scan for log files based on criteria"""
        operation_id = f"log_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        min_size_bytes = int(min_size_mb * 1024 * 1024)
        
        progress = self.progress_tracker.create_operation(
            operation_id, "Scanning log files",
            len(self.log_locations)
        )
        
        self.progress_tracker.start_operation(operation_id)
        
        categorized_logs = {
            'old_logs': [],
            'large_logs': [],
            'application_logs': [],
            'system_logs': [],
            'error_logs': []
        }
        
        for i, (location_name, location_path) in enumerate(self.log_locations.items()):
            try:
                self.progress_tracker.update_progress(
                    operation_id, i + 1,
                    current_item=location_name,
                    status_message=f"Scanning {location_name}"
                )
                
                logs_in_location = self._scan_location_for_logs(
                    location_path, cutoff_date, min_size_bytes
                )
                
                # Categorize logs
                for log_file in logs_in_location:
                    category = self._categorize_log_file(log_file, location_name, cutoff_date, min_size_bytes)
                    categorized_logs[category].append(log_file)
                
                self.stats['locations_scanned'] += 1
                self.stats['log_files_found'] += len(logs_in_location)
                
            except Exception as e:
                logger.error(f"Error scanning log location {location_name}: {e}")
        
        self.progress_tracker.complete_operation(operation_id, True)
        
        return categorized_logs
    
    def _scan_location_for_logs(self, location_path: Path, cutoff_date: datetime, min_size_bytes: int) -> List[Path]:
        """Scan a location for log files"""
        log_files = []
        log_extensions = {'.log', '.txt', '.out', '.err', '.trace'}
        log_patterns = ['log', 'trace', 'debug', 'error', 'warn']
        
        try:
            for item in location_path.rglob('*'):
                try:
                    if not item.is_file():
                        continue
                    
                    file_name = item.name.lower()
                    file_extension = item.suffix.lower()
                    
                    # Check if it's a log file
                    is_log = (
                        file_extension in log_extensions or
                        any(pattern in file_name for pattern in log_patterns) or
                        'log' in str(item.parent).lower()
                    )
                    
                    if is_log:
                        stat_info = item.stat()
                        modified_time = datetime.fromtimestamp(stat_info.st_mtime)
                        file_size = stat_info.st_size
                        
                        # Include if old enough or large enough
                        if modified_time < cutoff_date or file_size >= min_size_bytes:
                            log_files.append(item)
                        
                except (PermissionError, OSError):
                    continue
                except Exception:
                    continue
        
        except Exception as e:
            logger.error(f"Error scanning location {location_path}: {e}")
        
        return log_files
    
    def _categorize_log_file(self, log_file: Path, location_name: str, 
                            cutoff_date: datetime, min_size_bytes: int) -> str:
        """Categorize a log file"""
        try:
            file_name = log_file.name.lower()
            
            # Check for error logs
            error_indicators = ['error', 'err', 'exception', 'crash', 'dump']
            if any(indicator in file_name for indicator in error_indicators):
                return 'error_logs'
            
            # Check for system logs
            if 'system' in location_name.lower() or 'windows' in location_name.lower():
                return 'system_logs'
            
            # Check file characteristics
            stat_info = log_file.stat()
            modified_time = datetime.fromtimestamp(stat_info.st_mtime)
            file_size = stat_info.st_size
            
            # Categorize by age and size
            if file_size >= min_size_bytes and modified_time < cutoff_date:
                return 'large_logs'
            elif modified_time < cutoff_date:
                return 'old_logs'
            else:
                return 'application_logs'
                
        except Exception:
            return 'application_logs'
    
    def clean_log_files(self, categorized_logs: Dict[str, List[Path]], 
                       categories_to_clean: List[str] = None) -> Dict:
        """Clean log files from specified categories"""
        if categories_to_clean is None:
            categories_to_clean = ['old_logs', 'large_logs']
        
        operation_id = f"log_clean_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        files_to_clean = []
        for category in categories_to_clean:
            if category in categorized_logs:
                files_to_clean.extend(categorized_logs[category])
        
        progress = self.progress_tracker.create_operation(
            operation_id, "Cleaning log files",
            len(files_to_clean)
        )
        
        self.progress_tracker.start_operation(operation_id)
        
        results = {
            'files_deleted': 0,
            'bytes_freed': 0,
            'failed_deletions': [],
            'categories_processed': categories_to_clean
        }
        
        for i, log_file in enumerate(files_to_clean):
            try:
                if not log_file.exists():
                    continue
                
                file_size = log_file.stat().st_size
                
                # Try to truncate first (safer for active logs)
                if self._is_likely_active_log(log_file):
                    try:
                        with open(log_file, 'w') as f:
                            f.truncate(0)
                        logger.info(f"Truncated active log: {log_file}")
                    except Exception:
                        # If truncation fails, try deletion
                        log_file.unlink()
                else:
                    # Delete inactive logs
                    log_file.unlink()
                
                results['files_deleted'] += 1
                results['bytes_freed'] += file_size
                self.stats['log_files_cleaned'] += 1
                self.stats['bytes_freed'] += file_size
                
                self.progress_tracker.update_progress(
                    operation_id, i + 1,
                    current_item=log_file.name,
                    status_message=f"Cleaned from {log_file.parent.name}"
                )
                
            except Exception as e:
                logger.error(f"Failed to clean log file {log_file}: {e}")
                results['failed_deletions'].append(str(log_file))
        
        self.progress_tracker.complete_operation(operation_id, True)
        
        return results
    
    def _is_likely_active_log(self, log_file: Path) -> bool:
        """Check if log file is likely still being written to"""
        try:
            stat_info = log_file.stat()
            
            # Check if modified recently (within last hour)
            modified_time = datetime.fromtimestamp(stat_info.st_mtime)
            if datetime.now() - modified_time < timedelta(hours=1):
                return True
            
            # Check for common active log indicators
            file_name = log_file.name.lower()
            active_indicators = ['current', 'today', 'latest', 'active']
            if any(indicator in file_name for indicator in active_indicators):
                return True
            
            return False
            
        except Exception:
            return False
    
    def get_log_analysis(self, categorized_logs: Dict[str, List[Path]]) -> Dict:
        """Analyze found log files"""
        analysis = {
            'total_log_files': 0,
            'total_size_bytes': 0,
            'categories': {},
            'largest_logs': []
        }
        
        all_logs_with_info = []
        
        for category, logs in categorized_logs.items():
            category_size = 0
            category_count = len(logs)
            
            for log_file in logs:
                try:
                    if log_file.exists() and log_file.is_file():
                        file_stat = log_file.stat()
                        file_size = file_stat.st_size
                        
                        category_size += file_size
                        all_logs_with_info.append({
                            'path': log_file,
                            'size': file_size,
                            'category': category
                        })
                except Exception:
                    continue
            
            analysis['categories'][category] = {
                'file_count': category_count,
                'total_size_bytes': category_size,
                'total_size_formatted': self._format_bytes(category_size)
            }
            
            analysis['total_log_files'] += category_count
            analysis['total_size_bytes'] += category_size
        
        # Top 10 largest log files
        largest_logs = sorted(all_logs_with_info, key=lambda x: x['size'], reverse=True)[:10]
        analysis['largest_logs'] = [
            {
                'path': str(log['path']),
                'size_formatted': self._format_bytes(log['size']),
                'category': log['category']
            }
            for log in largest_logs
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