"""
Duplicate files detection and removal module
"""
import hashlib
from pathlib import Path
from typing import List, Dict, Set, Tuple
import logging
from datetime import datetime
from core.progress import ProgressTracker
from collections import defaultdict

logger = logging.getLogger(__name__)

class DuplicateFinder:
    """Find and remove duplicate files"""
    
    def __init__(self, progress_tracker: ProgressTracker):
        self.progress_tracker = progress_tracker
        self.hash_cache = {}
        self.stats = {
            'files_scanned': 0,
            'duplicates_found': 0,
            'duplicates_removed': 0,
            'bytes_freed': 0
        }
    
    def find_duplicates(self, scan_paths: List[Path], min_file_size: int = 1024) -> Dict[str, List[Path]]:
        """Find duplicate files in specified paths"""
        operation_id = f"duplicate_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # First pass: collect all files
        all_files = []
        for path in scan_paths:
            if path.exists():
                for file_path in path.rglob('*'):
                    if file_path.is_file() and file_path.stat().st_size >= min_file_size:
                        all_files.append(file_path)
        
        progress = self.progress_tracker.create_operation(
            operation_id, "Finding duplicate files",
            len(all_files)
        )
        
        self.progress_tracker.start_operation(operation_id)
        
        # Group files by size first (quick duplicate detection)
        size_groups = defaultdict(list)
        for file_path in all_files:
            try:
                file_size = file_path.stat().st_size
                size_groups[file_size].append(file_path)
            except Exception as e:
                logger.debug(f"Error getting size for {file_path}: {e}")
        
        # Only check files that have same-size candidates
        potential_duplicates = []
        for size, files in size_groups.items():
            if len(files) > 1:
                potential_duplicates.extend(files)
        
        # Second pass: hash potential duplicates
        hash_groups = defaultdict(list)
        
        for i, file_path in enumerate(potential_duplicates):
            try:
                self.progress_tracker.update_progress(
                    operation_id, i + 1,
                    current_item=file_path.name,
                    status_message="Calculating file hashes"
                )
                
                file_hash = self._calculate_file_hash(file_path)
                if file_hash:
                    hash_groups[file_hash].append(file_path)
                    self.stats['files_scanned'] += 1
                
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
        
        # Filter to actual duplicates (hash groups with multiple files)
        duplicates = {}
        for file_hash, files in hash_groups.items():
            if len(files) > 1:
                duplicates[file_hash] = files
                self.stats['duplicates_found'] += len(files) - 1  # Don't count the original
        
        self.progress_tracker.complete_operation(operation_id, True)
        
        return duplicates
    
    def _calculate_file_hash(self, file_path: Path, chunk_size: int = 8192) -> str:
        """Calculate MD5 hash of file"""
        if str(file_path) in self.hash_cache:
            return self.hash_cache[str(file_path)]
        
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, 'rb') as f:
                while chunk := f.read(chunk_size):
                    hash_md5.update(chunk)
            
            file_hash = hash_md5.hexdigest()
            self.hash_cache[str(file_path)] = file_hash
            return file_hash
            
        except Exception as e:
            logger.error(f"Error calculating hash for {file_path}: {e}")
            return None
    
    def remove_duplicates(self, duplicates: Dict[str, List[Path]], 
                         keep_strategy: str = 'newest') -> Dict:
        """Remove duplicate files based on strategy"""
        operation_id = f"duplicate_remove_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        files_to_remove = []
        for file_hash, files in duplicates.items():
            files_to_keep, files_to_delete = self._select_files_to_remove(files, keep_strategy)
            files_to_remove.extend(files_to_delete)
        
        progress = self.progress_tracker.create_operation(
            operation_id, "Removing duplicate files",
            len(files_to_remove)
        )
        
        self.progress_tracker.start_operation(operation_id)
        
        results = {
            'files_removed': 0,
            'bytes_freed': 0,
            'failed_removals': [],
            'duplicate_groups_processed': len(duplicates)
        }
        
        for i, file_path in enumerate(files_to_remove):
            try:
                if file_path.exists():
                    file_size = file_path.stat().st_size
                    file_path.unlink()
                    
                    results['files_removed'] += 1
                    results['bytes_freed'] += file_size
                    self.stats['duplicates_removed'] += 1
                    self.stats['bytes_freed'] += file_size
                
                self.progress_tracker.update_progress(
                    operation_id, i + 1,
                    current_item=file_path.name,
                    status_message="Removing duplicates"
                )
                
            except Exception as e:
                logger.error(f"Failed to remove {file_path}: {e}")
                results['failed_removals'].append(str(file_path))
        
        self.progress_tracker.complete_operation(operation_id, True)
        
        return results
    
    def _select_files_to_remove(self, files: List[Path], strategy: str) -> Tuple[List[Path], List[Path]]:
        """Select which files to keep and which to remove"""
        if len(files) <= 1:
            return files, []
        
        files_with_info = []
        for file_path in files:
            try:
                stat_info = file_path.stat()
                files_with_info.append({
                    'path': file_path,
                    'size': stat_info.st_size,
                    'modified_time': stat_info.st_mtime,
                    'created_time': stat_info.st_ctime
                })
            except Exception as e:
                logger.debug(f"Error getting info for {file_path}: {e}")
        
        if not files_with_info:
            return [], files
        
        # Sort based on strategy
        if strategy == 'newest':
            # Keep the newest file (highest modified time)
            files_with_info.sort(key=lambda x: x['modified_time'], reverse=True)
        elif strategy == 'oldest':
            # Keep the oldest file (lowest modified time)
            files_with_info.sort(key=lambda x: x['modified_time'])
        elif strategy == 'shortest_path':
            # Keep file with shortest path (likely in a more important location)
            files_with_info.sort(key=lambda x: len(str(x['path'])))
        elif strategy == 'longest_path':
            # Keep file with longest path
            files_with_info.sort(key=lambda x: len(str(x['path'])), reverse=True)
        else:
            # Default to newest
            files_with_info.sort(key=lambda x: x['modified_time'], reverse=True)
        
        # Keep the first file, remove the rest
        files_to_keep = [files_with_info[0]['path']]
        files_to_remove = [info['path'] for info in files_with_info[1:]]
        
        return files_to_keep, files_to_remove
    
    def get_duplicate_analysis(self, duplicates: Dict[str, List[Path]]) -> Dict:
        """Analyze duplicate files"""
        analysis = {
            'duplicate_groups': len(duplicates),
            'total_duplicates': 0,
            'total_wasted_space': 0,
            'largest_duplicate_groups': [],
            'most_wasted_space_groups': []
        }
        
        group_analysis = []
        
        for file_hash, files in duplicates.items():
            if len(files) <= 1:
                continue
            
            try:
                # Get file size (all files in group have same size)
                file_size = files[0].stat().st_size
                duplicates_count = len(files) - 1  # Don't count the original
                wasted_space = file_size * duplicates_count
                
                group_info = {
                    'hash': file_hash,
                    'file_count': len(files),
                    'duplicates_count': duplicates_count,
                    'file_size': file_size,
                    'wasted_space': wasted_space,
                    'files': [str(f) for f in files]
                }
                
                group_analysis.append(group_info)
                analysis['total_duplicates'] += duplicates_count
                analysis['total_wasted_space'] += wasted_space
                
            except Exception as e:
                logger.debug(f"Error analyzing duplicate group: {e}")
        
        # Sort by file count for largest groups
        analysis['largest_duplicate_groups'] = sorted(
            group_analysis, key=lambda x: x['file_count'], reverse=True
        )[:10]
        
        # Sort by wasted space
        analysis['most_wasted_space_groups'] = sorted(
            group_analysis, key=lambda x: x['wasted_space'], reverse=True
        )[:10]
        
        analysis['total_wasted_space_formatted'] = self._format_bytes(analysis['total_wasted_space'])
        
        return analysis
    
    def _format_bytes(self, bytes_value: int) -> str:
        """Format bytes in human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.1f} PB"