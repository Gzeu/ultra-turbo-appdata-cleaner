"""
Specialized AppData cleaning module
"""
import os
import shutil
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional
import logging
import json
from datetime import datetime, timedelta
from core.analyzer import FileAnalyzer, FileCategory, FileSafetyLevel
from core.progress import ProgressTracker, ProgressType

logger = logging.getLogger(__name__)

class AppDataCleaner:
    """Specialized cleaner for AppData directories"""
    
    def __init__(self, progress_tracker: ProgressTracker):
        self.progress_tracker = progress_tracker
        self.analyzer = FileAnalyzer({})
        self.appdata_roots = self._get_appdata_locations()
        self.safe_patterns = self._load_safe_cleaning_patterns()
        self.stats = {
            'files_analyzed': 0,
            'files_cleaned': 0,
            'bytes_freed': 0,
            'errors': 0
        }
    
    def _get_appdata_locations(self) -> Dict[str, Path]:
        """Get AppData locations for current user"""
        user_profile = Path(os.environ.get('USERPROFILE', ''))
        
        locations = {
            'local': user_profile / 'AppData' / 'Local',
            'roaming': user_profile / 'AppData' / 'Roaming', 
            'local_low': user_profile / 'AppData' / 'LocalLow'
        }
        
        # Check accessibility
        accessible_locations = {}
        for name, path in locations.items():
            if path.exists() and os.access(path, os.R_OK | os.W_OK):
                accessible_locations[name] = path
                logger.info(f"AppData {name} location accessible: {path}")
            else:
                logger.warning(f"AppData {name} location not accessible: {path}")
        
        return accessible_locations
    
    def _load_safe_cleaning_patterns(self) -> Dict:
        """Load safe cleaning patterns for AppData"""
        return {
            "safe_directories": [
                "temp", "tmp", "cache", "cookies", "thumbnails",
                "logs", "crashreports", "dumps", "backup"
            ],
            "safe_file_patterns": [
                "*.tmp", "*.temp", "*.log", "*.cache", "*.bak",
                "thumbs.db", "desktop.ini", "*.old", "*.~"
            ],
            "application_specific": {
                "chrome": {
                    "safe_clean": ["Cache", "Code Cache", "GPUCache", "ShaderCache"],
                    "preserve": ["Bookmarks", "History", "Login Data", "Preferences"]
                },
                "firefox": {
                    "safe_clean": ["cache2", "thumbnails", "crashes"],
                    "preserve": ["bookmarks.html", "places.sqlite", "key4.db"]
                },
                "discord": {
                    "safe_clean": ["Cache", "blob_storage", "GPUCache"],
                    "preserve": ["Local State", "Preferences"]
                },
                "vscode": {
                    "safe_clean": ["logs", "CachedExtensions", "clp"],
                    "preserve": ["User/settings.json", "User/keybindings.json"]
                }
            },
            "never_clean": [
                "Microsoft/Windows", "Microsoft/Credentials",
                "Adobe/Common", "NVIDIA Corporation"
            ]
        }
    
    def scan_appdata(self, location_types: List[str] = None) -> Dict[str, List[Path]]:
        """Scan AppData directories and categorize files"""
        if location_types is None:
            location_types = list(self.appdata_roots.keys())
        
        operation_id = f"appdata_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        all_files = []
        for location_type in location_types:
            if location_type in self.appdata_roots:
                root_path = self.appdata_roots[location_type]
                files_in_location = list(root_path.rglob('*'))
                all_files.extend(files_in_location)
        
        progress = self.progress_tracker.create_operation(
            operation_id, "Scanning AppData directories", 
            len(all_files)
        )
        
        self.progress_tracker.start_operation(operation_id)
        
        categorized_files = {
            'safe_to_clean': [],
            'potentially_safe': [],
            'preserve': [],
            'unknown': []
        }
        
        for i, file_path in enumerate(all_files):
            try:
                if not file_path.is_file():
                    continue
                
                category = self._categorize_appdata_file(file_path)
                categorized_files[category].append(file_path)
                
                self.progress_tracker.update_progress(
                    operation_id, i + 1,
                    current_item=file_path.name,
                    status_message=f"Analyzing {file_path.parent.name}"
                )
                
                self.stats['files_analyzed'] += 1
                
            except Exception as e:
                logger.error(f"Error analyzing {file_path}: {e}")
                categorized_files['unknown'].append(file_path)
        
        self.progress_tracker.complete_operation(operation_id, True)
        
        return categorized_files
    
    def _categorize_appdata_file(self, file_path: Path) -> str:
        """Categorize an AppData file for cleaning"""
        try:
            path_parts = file_path.parts
            appdata_index = -1
            
            for i, part in enumerate(path_parts):
                if part.lower() == 'appdata':
                    appdata_index = i
                    break
            
            if appdata_index == -1:
                return 'unknown'
            
            # Extract application and subpaths
            if len(path_parts) > appdata_index + 3:
                app_name = path_parts[appdata_index + 3].lower()
                subpath = '/'.join(path_parts[appdata_index + 4:]).lower()
            else:
                return 'preserve'  # Files in AppData root
            
            # Check never_clean patterns
            for never_pattern in self.safe_patterns['never_clean']:
                if never_pattern.lower() in str(file_path).lower():
                    return 'preserve'
            
            # Check obviously safe files
            file_name = file_path.name.lower()
            file_extension = file_path.suffix.lower()
            
            # Obviously safe files
            safe_extensions = ['.tmp', '.temp', '.log', '.cache', '.bak', '.old']
            if file_extension in safe_extensions:
                return 'safe_to_clean'
            
            safe_names = ['thumbs.db', 'desktop.ini']
            if file_name in safe_names:
                return 'safe_to_clean'
            
            # Safe directories
            parent_name = file_path.parent.name.lower()
            for safe_dir in self.safe_patterns['safe_directories']:
                if safe_dir in parent_name:
                    return 'safe_to_clean'
            
            # Application-specific checks
            if app_name in self.safe_patterns['application_specific']:
                app_config = self.safe_patterns['application_specific'][app_name]
                
                # Check safe_clean directories
                for safe_clean_dir in app_config.get('safe_clean', []):
                    if safe_clean_dir.lower() in subpath:
                        return 'safe_to_clean'
                
                # Check preserve files
                for preserve_pattern in app_config.get('preserve', []):
                    if preserve_pattern.lower() in subpath:
                        return 'preserve'
            
            # Use general analyzer for other cases
            category, safety = self.analyzer.analyze_file(file_path)
            
            if safety in [FileSafetyLevel.VERY_SAFE, FileSafetyLevel.SAFE]:
                return 'safe_to_clean'
            elif safety == FileSafetyLevel.MODERATE:
                return 'potentially_safe'
            else:
                return 'preserve'
                
        except Exception as e:
            logger.error(f"Error categorizing file {file_path}: {e}")
            return 'unknown'
    
    def clean_safe_files(self, categorized_files: Dict[str, List[Path]], 
                        include_potentially_safe: bool = False) -> Dict:
        """Clean files marked as safe"""
        operation_id = f"appdata_clean_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        files_to_clean = categorized_files['safe_to_clean'].copy()
        if include_potentially_safe:
            files_to_clean.extend(categorized_files['potentially_safe'])
        
        progress = self.progress_tracker.create_operation(
            operation_id, "Cleaning AppData files",
            len(files_to_clean)
        )
        
        self.progress_tracker.start_operation(operation_id)
        
        results = {
            'files_deleted': 0,
            'bytes_freed': 0,
            'failed_deletions': [],
            'directories_removed': 0
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
    
    def get_size_analysis(self, categorized_files: Dict[str, List[Path]]) -> Dict:
        """Analyze sizes for each category"""
        analysis = {}
        
        for category, files in categorized_files.items():
            total_size = 0
            file_count = len(files)
            
            for file_path in files:
                try:
                    if file_path.exists() and file_path.is_file():
                        total_size += file_path.stat().st_size
                except Exception:
                    continue
            
            analysis[category] = {
                'file_count': file_count,
                'total_size_bytes': total_size,
                'total_size_formatted': self._format_bytes(total_size)
            }
        
        return analysis
    
    def _format_bytes(self, bytes_value: int) -> str:
        """Format bytes in human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.1f} PB"
    
    def get_cleaning_report(self) -> Dict:
        """Generate report for AppData cleaning"""
        return {
            'timestamp': datetime.now().isoformat(),
            'statistics': self.stats.copy(),
            'appdata_locations': {name: str(path) for name, path in self.appdata_roots.items()},
            'cleaning_patterns_loaded': len(self.safe_patterns.get('application_specific', {}))
        }