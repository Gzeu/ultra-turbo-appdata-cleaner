"""
Cleaner API endpoints for web interface
"""

import asyncio
from pathlib import Path
from typing import List, Dict, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class CleanerAPI:
    """API for cleaning operations"""
    
    def __init__(self, cleaner_engine, progress_tracker):
        self.cleaner_engine = cleaner_engine
        self.progress_tracker = progress_tracker
    
    def clean_files(self, operation_id: str, file_paths: List[str], create_backup: bool = True) -> Dict[str, Any]:
        """Clean specified files"""
        try:
            progress = self.progress_tracker.create_operation(
                operation_id, "Cleaning Selected Files", len(file_paths)
            )
            
            self.progress_tracker.start_operation(operation_id)
            
            results = {
                'operation_id': operation_id,
                'files_processed': 0,
                'files_deleted': 0,
                'files_failed': 0,
                'bytes_freed': 0,
                'errors': [],
                'backup_created': False
            }
            
            # Create file info objects
            file_objects = []
            for file_path in file_paths:
                try:
                    path_obj = Path(file_path)
                    if path_obj.exists():
                        stat_info = path_obj.stat()
                        file_objects.append({
                            'path': file_path,
                            'size': stat_info.st_size,
                            'name': path_obj.name
                        })
                except Exception as e:
                    logger.warning(f"Could not process file {file_path}: {e}")
            
            # Create backup if requested
            if create_backup and file_objects:
                try:
                    from utils.backup_manager import BackupManager
                    backup_manager = BackupManager(self.cleaner_engine.settings)
                    backup_path = backup_manager.create_backup(
                        [f['path'] for f in file_objects], 
                        operation_id
                    )
                    results['backup_created'] = backup_path is not None
                    if backup_path:
                        results['backup_path'] = str(backup_path)
                except Exception as e:
                    logger.error(f"Backup creation failed: {e}")
                    results['errors'].append(f"Backup failed: {str(e)}")
            
            # Clean files
            for i, file_info in enumerate(file_objects):
                try:
                    file_path = Path(file_info['path'])
                    
                    if file_path.exists():
                        file_size = file_info['size']
                        file_path.unlink()
                        
                        results['files_deleted'] += 1
                        results['bytes_freed'] += file_size
                    
                    results['files_processed'] += 1
                    
                    self.progress_tracker.update_progress(
                        operation_id, i + 1,
                        current_item=file_info['name'],
                        status_message=f"Deleted {file_info['name']}"
                    )
                    
                except Exception as e:
                    logger.error(f"Failed to delete {file_info['path']}: {e}")
                    results['files_failed'] += 1
                    results['errors'].append(f"Failed to delete {file_info['name']}: {str(e)}")
            
            self.progress_tracker.complete_operation(operation_id, True)
            
            results['success'] = results['files_failed'] == 0
            results['timestamp'] = datetime.now().isoformat()
            
            return results
            
        except Exception as e:
            logger.error(f"Error in file cleaning: {e}")
            self.progress_tracker.complete_operation(operation_id, False)
            return {'error': str(e)}
    
    def clean_appdata(self, operation_id: str, categories: List[str] = None, 
                     include_potentially_safe: bool = False) -> Dict[str, Any]:
        """Clean AppData files"""
        try:
            from modules.appdata_cleaner import AppDataCleaner
            appdata_cleaner = AppDataCleaner(self.progress_tracker)
            
            self.progress_tracker.start_operation(operation_id)
            
            # Scan AppData
            categorized_files = appdata_cleaner.scan_appdata()
            
            # Clean files
            clean_results = appdata_cleaner.clean_safe_files(
                categorized_files, include_potentially_safe
            )
            
            self.progress_tracker.complete_operation(operation_id, True)
            
            return {
                'operation_id': operation_id,
                'operation_type': 'appdata_clean',
                'files_deleted': clean_results['files_deleted'],
                'bytes_freed': clean_results['bytes_freed'],
                'directories_removed': clean_results['directories_removed'],
                'failed_deletions': clean_results['failed_deletions'],
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in AppData cleaning: {e}")
            self.progress_tracker.complete_operation(operation_id, False)
            return {'error': str(e)}
    
    def clean_temp_files(self, operation_id: str, max_age_days: int = 7, 
                        categories: List[str] = None) -> Dict[str, Any]:
        """Clean temporary files"""
        try:
            from modules.temp_cleaner import TempCleaner
            temp_cleaner = TempCleaner(self.progress_tracker)
            
            self.progress_tracker.start_operation(operation_id)
            
            # Scan temp files
            categorized_files = temp_cleaner.scan_temp_files(max_age_days=max_age_days)
            
            # Clean files
            if categories is None:
                categories = ['old_temp_files', 'browser_cache']
            
            clean_results = temp_cleaner.clean_temp_files(categorized_files, categories)
            
            self.progress_tracker.complete_operation(operation_id, True)
            
            return {
                'operation_id': operation_id,
                'operation_type': 'temp_clean',
                'max_age_days': max_age_days,
                'categories_processed': clean_results['categories_processed'],
                'files_deleted': clean_results['files_deleted'],
                'bytes_freed': clean_results['bytes_freed'],
                'directories_removed': clean_results['directories_removed'],
                'failed_deletions': clean_results['failed_deletions'],
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in temp files cleaning: {e}")
            self.progress_tracker.complete_operation(operation_id, False)
            return {'error': str(e)}
    
    def remove_duplicates(self, operation_id: str, scan_paths: List[str], 
                         keep_strategy: str = 'newest') -> Dict[str, Any]:
        """Remove duplicate files"""
        try:
            from modules.duplicate_finder import DuplicateFinder
            duplicate_finder = DuplicateFinder(self.progress_tracker)
            
            self.progress_tracker.start_operation(operation_id)
            
            # Find duplicates
            path_objects = [Path(p) for p in scan_paths if Path(p).exists()]
            duplicates = duplicate_finder.find_duplicates(path_objects)
            
            # Remove duplicates
            remove_results = duplicate_finder.remove_duplicates(duplicates, keep_strategy)
            
            self.progress_tracker.complete_operation(operation_id, True)
            
            return {
                'operation_id': operation_id,
                'operation_type': 'duplicate_removal',
                'keep_strategy': keep_strategy,
                'duplicate_groups_processed': remove_results['duplicate_groups_processed'],
                'files_removed': remove_results['files_removed'],
                'bytes_freed': remove_results['bytes_freed'],
                'failed_removals': remove_results['failed_removals'],
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in duplicate removal: {e}")
            self.progress_tracker.complete_operation(operation_id, False)
            return {'error': str(e)}