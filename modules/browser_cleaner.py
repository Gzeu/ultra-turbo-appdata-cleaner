"""
Browser data cleaning module
"""
import os
import sqlite3
from pathlib import Path
from typing import List, Dict, Optional
import logging
from datetime import datetime
from core.progress import ProgressTracker

logger = logging.getLogger(__name__)

class BrowserCleaner:
    """Specialized cleaner for browser data"""
    
    def __init__(self, progress_tracker: ProgressTracker):
        self.progress_tracker = progress_tracker
        self.browser_paths = self._discover_browser_locations()
        self.stats = {
            'browsers_found': 0,
            'cache_cleaned': 0,
            'cookies_cleaned': 0,
            'history_cleaned': 0,
            'bytes_freed': 0
        }
    
    def _discover_browser_locations(self) -> Dict[str, Dict]:
        """Discover installed browsers and their data locations"""
        user_profile = Path(os.environ.get('USERPROFILE', ''))
        
        browsers = {
            'chrome': {
                'name': 'Google Chrome',
                'path': user_profile / 'AppData' / 'Local' / 'Google' / 'Chrome' / 'User Data',
                'cache_dirs': ['Default/Cache', 'Default/Code Cache', 'Default/GPUCache'],
                'data_files': {
                    'cookies': 'Default/Cookies',
                    'history': 'Default/History',
                    'web_data': 'Default/Web Data'
                }
            },
            'firefox': {
                'name': 'Mozilla Firefox',
                'path': user_profile / 'AppData' / 'Roaming' / 'Mozilla' / 'Firefox' / 'Profiles',
                'cache_dirs': ['cache2'],
                'data_files': {
                    'cookies': 'cookies.sqlite',
                    'history': 'places.sqlite',
                    'downloads': 'downloads.sqlite'
                }
            },
            'edge': {
                'name': 'Microsoft Edge',
                'path': user_profile / 'AppData' / 'Local' / 'Microsoft' / 'Edge' / 'User Data',
                'cache_dirs': ['Default/Cache', 'Default/Code Cache', 'Default/GPUCache'],
                'data_files': {
                    'cookies': 'Default/Cookies',
                    'history': 'Default/History',
                    'web_data': 'Default/Web Data'
                }
            }
        }
        
        # Check which browsers are installed
        available_browsers = {}
        for browser_id, config in browsers.items():
            if config['path'].exists():
                available_browsers[browser_id] = config
                self.stats['browsers_found'] += 1
                logger.info(f"Found {config['name']} at {config['path']}")
        
        return available_browsers
    
    def clean_browser_cache(self, browsers: List[str] = None) -> Dict:
        """Clean cache for specified browsers"""
        if browsers is None:
            browsers = list(self.browser_paths.keys())
        
        operation_id = f"browser_cache_clean_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        progress = self.progress_tracker.create_operation(
            operation_id, "Cleaning browser cache",
            len(browsers)
        )
        
        self.progress_tracker.start_operation(operation_id)
        
        results = {
            'browsers_processed': 0,
            'cache_dirs_cleaned': 0,
            'files_deleted': 0,
            'bytes_freed': 0,
            'errors': []
        }
        
        for i, browser_id in enumerate(browsers):
            if browser_id not in self.browser_paths:
                continue
            
            try:
                browser_config = self.browser_paths[browser_id]
                browser_path = browser_config['path']
                
                self.progress_tracker.update_progress(
                    operation_id, i + 1,
                    current_item=browser_config['name'],
                    status_message=f"Cleaning {browser_config['name']} cache"
                )
                
                # Clean cache directories
                for cache_dir in browser_config['cache_dirs']:
                    cache_path = browser_path / cache_dir
                    
                    if browser_id == 'firefox':
                        # Firefox has profiles, need to find them
                        for profile_dir in browser_path.iterdir():
                            if profile_dir.is_dir() and not profile_dir.name.startswith('.'):
                                profile_cache_path = profile_dir / cache_dir
                                if profile_cache_path.exists():
                                    cache_result = self._clean_directory(profile_cache_path)
                                    results['files_deleted'] += cache_result['files_deleted']
                                    results['bytes_freed'] += cache_result['bytes_freed']
                    else:
                        if cache_path.exists():
                            cache_result = self._clean_directory(cache_path)
                            results['files_deleted'] += cache_result['files_deleted']
                            results['bytes_freed'] += cache_result['bytes_freed']
                    
                    results['cache_dirs_cleaned'] += 1
                
                results['browsers_processed'] += 1
                
            except Exception as e:
                logger.error(f"Error cleaning {browser_id} cache: {e}")
                results['errors'].append(f"{browser_id}: {str(e)}")
        
        self.progress_tracker.complete_operation(operation_id, True)
        self.stats['cache_cleaned'] = results['cache_dirs_cleaned']
        self.stats['bytes_freed'] += results['bytes_freed']
        
        return results
    
    def clean_browser_history(self, browsers: List[str] = None, days_to_keep: int = 30) -> Dict:
        """Clean browser history older than specified days"""
        if browsers is None:
            browsers = list(self.browser_paths.keys())
        
        operation_id = f"browser_history_clean_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        progress = self.progress_tracker.create_operation(
            operation_id, "Cleaning browser history",
            len(browsers)
        )
        
        self.progress_tracker.start_operation(operation_id)
        
        results = {
            'browsers_processed': 0,
            'history_entries_deleted': 0,
            'errors': []
        }
        
        cutoff_timestamp = int((datetime.now().timestamp() - (days_to_keep * 24 * 3600)) * 1000000)
        
        for i, browser_id in enumerate(browsers):
            if browser_id not in self.browser_paths:
                continue
            
            try:
                browser_config = self.browser_paths[browser_id]
                
                self.progress_tracker.update_progress(
                    operation_id, i + 1,
                    current_item=browser_config['name'],
                    status_message=f"Cleaning {browser_config['name']} history"
                )
                
                if browser_id in ['chrome', 'edge']:
                    history_result = self._clean_chromium_history(
                        browser_config['path'] / browser_config['data_files']['history'],
                        cutoff_timestamp
                    )
                elif browser_id == 'firefox':
                    history_result = self._clean_firefox_history(
                        browser_config['path'], cutoff_timestamp
                    )
                else:
                    continue
                
                results['history_entries_deleted'] += history_result.get('entries_deleted', 0)
                results['browsers_processed'] += 1
                
            except Exception as e:
                logger.error(f"Error cleaning {browser_id} history: {e}")
                results['errors'].append(f"{browser_id}: {str(e)}")
        
        self.progress_tracker.complete_operation(operation_id, True)
        self.stats['history_cleaned'] = results['history_entries_deleted']
        
        return results
    
    def _clean_directory(self, directory_path: Path) -> Dict:
        """Clean all files in a directory"""
        result = {'files_deleted': 0, 'bytes_freed': 0}
        
        try:
            for item in directory_path.rglob('*'):
                if item.is_file():
                    try:
                        file_size = item.stat().st_size
                        item.unlink()
                        result['files_deleted'] += 1
                        result['bytes_freed'] += file_size
                    except Exception as e:
                        logger.debug(f"Could not delete {item}: {e}")
        except Exception as e:
            logger.error(f"Error cleaning directory {directory_path}: {e}")
        
        return result
    
    def _clean_chromium_history(self, history_file: Path, cutoff_timestamp: int) -> Dict:
        """Clean history from Chromium-based browsers"""
        result = {'entries_deleted': 0}
        
        if not history_file.exists():
            return result
        
        try:
            # Make a backup copy to work with
            backup_file = history_file.with_suffix('.bak')
            history_file.rename(backup_file)
            
            with sqlite3.connect(str(backup_file)) as source_conn:
                with sqlite3.connect(str(history_file)) as dest_conn:
                    # Copy schema
                    dest_conn.executescript(source_conn.iterdump())
                    
                    # Delete old history entries
                    cursor = dest_conn.execute(
                        "DELETE FROM urls WHERE last_visit_time < ?",
                        (cutoff_timestamp,)
                    )
                    result['entries_deleted'] = cursor.rowcount
                    
                    dest_conn.execute(
                        "DELETE FROM visits WHERE visit_time < ?",
                        (cutoff_timestamp,)
                    )
                    
                    dest_conn.commit()
            
            # Remove backup
            backup_file.unlink()
            
        except Exception as e:
            logger.error(f"Error cleaning Chromium history {history_file}: {e}")
            # Restore backup if something went wrong
            if backup_file.exists():
                backup_file.rename(history_file)
        
        return result
    
    def _clean_firefox_history(self, profiles_path: Path, cutoff_timestamp: int) -> Dict:
        """Clean history from Firefox profiles"""
        result = {'entries_deleted': 0}
        
        try:
            for profile_dir in profiles_path.iterdir():
                if not profile_dir.is_dir() or profile_dir.name.startswith('.'):
                    continue
                
                places_file = profile_dir / 'places.sqlite'
                if not places_file.exists():
                    continue
                
                with sqlite3.connect(str(places_file)) as conn:
                    # Firefox uses different timestamp format (microseconds since epoch)
                    firefox_cutoff = cutoff_timestamp
                    
                    cursor = conn.execute(
                        "DELETE FROM moz_historyvisits WHERE visit_date < ?",
                        (firefox_cutoff,)
                    )
                    result['entries_deleted'] += cursor.rowcount
                    
                    # Clean up orphaned places
                    conn.execute(
                        "DELETE FROM moz_places WHERE id NOT IN (SELECT place_id FROM moz_historyvisits)"
                    )
                    
                    conn.commit()
                    
        except Exception as e:
            logger.error(f"Error cleaning Firefox history: {e}")
        
        return result
    
    def get_browser_analysis(self) -> Dict:
        """Get analysis of browser data"""
        analysis = {
            'browsers_found': self.stats['browsers_found'],
            'browsers': {},
            'total_cache_size': 0
        }
        
        for browser_id, config in self.browser_paths.items():
            browser_analysis = {
                'name': config['name'],
                'path': str(config['path']),
                'cache_size': 0,
                'cache_dirs_found': 0
            }
            
            # Analyze cache size
            for cache_dir in config['cache_dirs']:
                cache_path = config['path'] / cache_dir
                
                if browser_id == 'firefox':
                    # Check all Firefox profiles
                    for profile_dir in config['path'].iterdir():
                        if profile_dir.is_dir() and not profile_dir.name.startswith('.'):
                            profile_cache_path = profile_dir / cache_dir
                            if profile_cache_path.exists():
                                cache_size = self._get_directory_size(profile_cache_path)
                                browser_analysis['cache_size'] += cache_size
                                browser_analysis['cache_dirs_found'] += 1
                else:
                    if cache_path.exists():
                        cache_size = self._get_directory_size(cache_path)
                        browser_analysis['cache_size'] += cache_size
                        browser_analysis['cache_dirs_found'] += 1
            
            browser_analysis['cache_size_formatted'] = self._format_bytes(browser_analysis['cache_size'])
            analysis['browsers'][browser_id] = browser_analysis
            analysis['total_cache_size'] += browser_analysis['cache_size']
        
        analysis['total_cache_size_formatted'] = self._format_bytes(analysis['total_cache_size'])
        
        return analysis
    
    def _get_directory_size(self, directory_path: Path) -> int:
        """Get total size of directory"""
        total_size = 0
        try:
            for item in directory_path.rglob('*'):
                if item.is_file():
                    try:
                        total_size += item.stat().st_size
                    except Exception:
                        continue
        except Exception:
            pass
        return total_size
    
    def _format_bytes(self, bytes_value: int) -> str:
        """Format bytes in human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.1f} PB"