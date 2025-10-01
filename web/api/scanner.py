"""
Scanner API endpoints for web interface
"""

import asyncio
from pathlib import Path
from typing import List, Dict, Any
import logging
from datetime import datetime

from core.scanner import FileScanner
from core.analyzer import FileAnalyzer
from modules.appdata_cleaner import AppDataCleaner
from modules.temp_cleaner import TempCleaner
from modules.duplicate_finder import DuplicateFinder

logger = logging.getLogger(__name__)

class ScannerAPI:
    """API for scanning operations"""
    
    def __init__(self, progress_tracker):
        self.progress_tracker = progress_tracker
        self.scanner = None
        self.analyzer = None
    
    def _initialize_components(self, settings):
        """Initialize scanner components"""
        if not self.scanner:
            self.scanner = FileScanner(settings)
        if not self.analyzer:
            self.analyzer = FileAnalyzer(settings)
    
    def quick_scan(self, operation_id: str) -> Dict[str, Any]:
        """Perform quick scan of common locations"""
        try:
            from config.settings import Settings
            settings = Settings()
            self._initialize_components(settings)
            
            # Quick scan paths (most common cleanup locations)
            quick_paths = [
                os.path.expandvars('%TEMP%'),
                os.path.expandvars('%LOCALAPPDATA%\\Temp'),
                'C:\\Windows\\Temp'
            ]
            
            progress = self.progress_tracker.create_operation(
                operation_id, "Quick System Scan", len(quick_paths)
            )
            
            self.progress_tracker.start_operation(operation_id)
            
            all_files = []
            for i, path in enumerate(quick_paths):
                try:
                    path_obj = Path(path)
                    if path_obj.exists():
                        # Quick scan - limit depth and file count
                        files = self._quick_scan_path(path_obj, max_files=500)
                        all_files.extend(files)
                    
                    self.progress_tracker.update_progress(
                        operation_id, i + 1,
                        current_item=path,
                        status_message=f"Scanned {len(files)} files"
                    )
                    
                except Exception as e:
                    logger.error(f"Error scanning {path}: {e}")
                    continue
            
            # Quick analysis
            results = self._analyze_scan_results(all_files)
            
            self.progress_tracker.complete_operation(operation_id, True)
            
            return {
                'operation_id': operation_id,
                'scan_type': 'quick',
                'total_files': len(all_files),
                'cleanable_files': results['cleanable_count'],
                'potential_savings_mb': round(results['cleanable_size'] / (1024**2), 2),
                'categories': results['categories'],
                'scan_paths': quick_paths,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in quick scan: {e}")
            self.progress_tracker.complete_operation(operation_id, False)
            return {'error': str(e)}
    
    def full_scan(self, operation_id: str, scan_paths: List[str]) -> Dict[str, Any]:
        """Perform comprehensive system scan"""
        try:
            from config.settings import Settings
            settings = Settings()
            self._initialize_components(settings)
            
            progress = self.progress_tracker.create_operation(
                operation_id, "Full System Scan", len(scan_paths)
            )
            
            self.progress_tracker.start_operation(operation_id)
            
            all_files = []
            scan_stats = {'paths_scanned': 0, 'paths_failed': 0}
            
            for i, path in enumerate(scan_paths):
                try:
                    path_obj = Path(path)
                    if path_obj.exists():
                        # Full scan - no limits
                        files = asyncio.run(self.scanner.scan_path(path))
                        all_files.extend(files)
                        scan_stats['paths_scanned'] += 1
                    else:
                        scan_stats['paths_failed'] += 1
                    
                    self.progress_tracker.update_progress(
                        operation_id, i + 1,
                        current_item=path,
                        status_message=f"Found {len(files)} files"
                    )
                    
                except Exception as e:
                    logger.error(f"Error scanning {path}: {e}")
                    scan_stats['paths_failed'] += 1
                    continue
            
            # Full analysis
            analyzed_files = asyncio.run(self.analyzer.analyze_files(all_files))
            results = self._analyze_scan_results(analyzed_files)
            
            self.progress_tracker.complete_operation(operation_id, True)
            
            return {
                'operation_id': operation_id,
                'scan_type': 'full',
                'total_files': len(all_files),
                'analyzed_files': len(analyzed_files),
                'cleanable_files': results['cleanable_count'],
                'potential_savings_mb': round(results['cleanable_size'] / (1024**2), 2),
                'categories': results['categories'],
                'safety_breakdown': results['safety_levels'],
                'scan_paths': scan_paths,
                'scan_stats': scan_stats,
                'timestamp': datetime.now().isoformat(),
                'files': analyzed_files[:100]  # First 100 files for preview
            }
            
        except Exception as e:
            logger.error(f"Error in full scan: {e}")
            self.progress_tracker.complete_operation(operation_id, False)
            return {'error': str(e)}
    
    def _quick_scan_path(self, path: Path, max_files: int = 500) -> List[Dict]:
        """Quick scan of a path with limits"""
        files = []
        file_count = 0
        
        try:
            for item in path.rglob('*'):
                if file_count >= max_files:
                    break
                
                try:
                    if item.is_file():
                        stat_info = item.stat()
                        
                        files.append({
                            'path': str(item),
                            'name': item.name,
                            'size': stat_info.st_size,
                            'extension': item.suffix.lower(),
                            'modified_time': stat_info.st_mtime,
                            'age_days': (datetime.now().timestamp() - stat_info.st_mtime) / (24 * 3600)
                        })
                        
                        file_count += 1
                        
                except (PermissionError, OSError):
                    continue
                    
        except Exception as e:
            logger.error(f"Error in quick scan of {path}: {e}")
        
        return files
    
    def _analyze_scan_results(self, files: List[Dict]) -> Dict[str, Any]:
        """Analyze scan results for web display"""
        results = {
            'cleanable_count': 0,
            'cleanable_size': 0,
            'categories': {},
            'safety_levels': {},
            'extensions': {},
            'age_groups': {'0-7_days': 0, '7-30_days': 0, '30+_days': 0}
        }
        
        for file_info in files:
            # Count cleanable files
            if file_info.get('cleanable', False):
                results['cleanable_count'] += 1
                results['cleanable_size'] += file_info.get('size', 0)
            
            # Count by category
            category = file_info.get('category', 'unknown')
            results['categories'][category] = results['categories'].get(category, 0) + 1
            
            # Count by safety level
            safety = file_info.get('safety_level', 5)
            results['safety_levels'][str(safety)] = results['safety_levels'].get(str(safety), 0) + 1
            
            # Count by extension
            ext = file_info.get('extension', '')
            if ext:
                results['extensions'][ext] = results['extensions'].get(ext, 0) + 1
            
            # Age groups
            age = file_info.get('age_days', 0)
            if age <= 7:
                results['age_groups']['0-7_days'] += 1
            elif age <= 30:
                results['age_groups']['7-30_days'] += 1
            else:
                results['age_groups']['30+_days'] += 1
        
        # Sort extensions by count
        results['extensions'] = dict(
            sorted(results['extensions'].items(), key=lambda x: x[1], reverse=True)[:10]
        )
        
        return results
    
    def scan_appdata_only(self, operation_id: str) -> Dict[str, Any]:
        """Scan only AppData directories"""
        try:
            appdata_cleaner = AppDataCleaner(self.progress_tracker)
            
            self.progress_tracker.start_operation(operation_id)
            
            categorized_files = appdata_cleaner.scan_appdata()
            size_analysis = appdata_cleaner.get_size_analysis(categorized_files)
            
            self.progress_tracker.complete_operation(operation_id, True)
            
            return {
                'operation_id': operation_id,
                'scan_type': 'appdata',
                'categorized_files': {
                    category: len(files) for category, files in categorized_files.items()
                },
                'size_analysis': size_analysis,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in AppData scan: {e}")
            self.progress_tracker.complete_operation(operation_id, False)
            return {'error': str(e)}
    
    def scan_temp_files(self, operation_id: str, max_age_days: int = 7) -> Dict[str, Any]:
        """Scan only temporary files"""
        try:
            temp_cleaner = TempCleaner(self.progress_tracker)
            
            self.progress_tracker.start_operation(operation_id)
            
            categorized_files = temp_cleaner.scan_temp_files(max_age_days=max_age_days)
            analysis = temp_cleaner.get_temp_analysis(categorized_files)
            
            self.progress_tracker.complete_operation(operation_id, True)
            
            return {
                'operation_id': operation_id,
                'scan_type': 'temp_files',
                'max_age_days': max_age_days,
                'categorized_files': {
                    category: len(files) for category, files in categorized_files.items()
                },
                'analysis': analysis,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in temp files scan: {e}")
            self.progress_tracker.complete_operation(operation_id, False)
            return {'error': str(e)}
    
    def scan_duplicates(self, operation_id: str, scan_paths: List[str]) -> Dict[str, Any]:
        """Scan for duplicate files"""
        try:
            duplicate_finder = DuplicateFinder(self.progress_tracker)
            
            self.progress_tracker.start_operation(operation_id)
            
            path_objects = [Path(p) for p in scan_paths if Path(p).exists()]
            duplicates = duplicate_finder.find_duplicates(path_objects)
            analysis = duplicate_finder.get_duplicate_analysis(duplicates)
            
            self.progress_tracker.complete_operation(operation_id, True)
            
            return {
                'operation_id': operation_id,
                'scan_type': 'duplicates',
                'duplicate_groups': len(duplicates),
                'total_duplicates': analysis.get('total_duplicates', 0),
                'wasted_space_mb': round(analysis.get('total_wasted_space', 0) / (1024**2), 2),
                'analysis': analysis,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in duplicate scan: {e}")
            self.progress_tracker.complete_operation(operation_id, False)
            return {'error': str(e)}