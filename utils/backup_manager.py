"""
Backup and restore utilities
"""
import os
import shutil
import json
from pathlib import Path
from typing import List, Dict, Optional, Union
import logging
from datetime import datetime
import zipfile
import tempfile

logger = logging.getLogger(__name__)

class BackupManager:
    """Manage backup and restore operations"""
    
    def __init__(self, settings):
        self.settings = settings
        self.backup_root = Path(settings.get('backup_path', 
            os.path.join(os.path.expanduser('~'), '.ultra_turbo_cleaner', 'backups')))
        self.backup_root.mkdir(parents=True, exist_ok=True)
    
    def create_backup(self, files_to_backup: List[Union[str, Path]], 
                     operation_name: str, compress: bool = True) -> Optional[Path]:
        """Create backup of specified files"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"{operation_name}_{timestamp}"
            
            if compress:
                backup_path = self.backup_root / f"{backup_name}.zip"
                return self._create_zip_backup(files_to_backup, backup_path, operation_name)
            else:
                backup_path = self.backup_root / backup_name
                return self._create_directory_backup(files_to_backup, backup_path, operation_name)
            
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return None
    
    def _create_zip_backup(self, files_to_backup: List[Union[str, Path]], 
                          backup_path: Path, operation_name: str) -> Optional[Path]:
        """Create compressed ZIP backup"""
        try:
            backup_manifest = {
                'operation_name': operation_name,
                'created_at': datetime.now().isoformat(),
                'files': []
            }
            
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in files_to_backup:
                    file_path = Path(file_path)
                    
                    if not file_path.exists():
                        continue
                    
                    try:
                        if file_path.is_file():
                            # Use relative path as archive name to avoid path issues
                            archive_name = file_path.name
                            counter = 1
                            
                            # Handle duplicate filenames
                            while archive_name in [f['archive_name'] for f in backup_manifest['files']]:
                                name_parts = file_path.name.rsplit('.', 1)
                                if len(name_parts) == 2:
                                    archive_name = f"{name_parts[0]}_{counter}.{name_parts[1]}"
                                else:
                                    archive_name = f"{file_path.name}_{counter}"
                                counter += 1
                            
                            zipf.write(file_path, archive_name)
                            
                            backup_manifest['files'].append({
                                'original_path': str(file_path),
                                'archive_name': archive_name,
                                'size': file_path.stat().st_size,
                                'modified': file_path.stat().st_mtime
                            })
                            
                    except Exception as e:
                        logger.warning(f"Failed to backup file {file_path}: {e}")
                        continue
                
                # Add manifest to zip
                manifest_json = json.dumps(backup_manifest, indent=2)
                zipf.writestr('backup_manifest.json', manifest_json)
            
            logger.info(f"Created ZIP backup: {backup_path} with {len(backup_manifest['files'])} files")
            return backup_path
            
        except Exception as e:
            logger.error(f"Failed to create ZIP backup: {e}")
            return None
    
    def _create_directory_backup(self, files_to_backup: List[Union[str, Path]], 
                               backup_path: Path, operation_name: str) -> Optional[Path]:
        """Create directory-based backup"""
        try:
            backup_path.mkdir(parents=True, exist_ok=True)
            
            backup_manifest = {
                'operation_name': operation_name,
                'created_at': datetime.now().isoformat(),
                'files': []
            }
            
            for file_path in files_to_backup:
                file_path = Path(file_path)
                
                if not file_path.exists():
                    continue
                
                try:
                    if file_path.is_file():
                        # Copy file to backup directory
                        backup_file_path = backup_path / file_path.name
                        
                        # Handle duplicate filenames
                        counter = 1
                        while backup_file_path.exists():
                            name_parts = file_path.name.rsplit('.', 1)
                            if len(name_parts) == 2:
                                backup_file_path = backup_path / f"{name_parts[0]}_{counter}.{name_parts[1]}"
                            else:
                                backup_file_path = backup_path / f"{file_path.name}_{counter}"
                            counter += 1
                        
                        shutil.copy2(file_path, backup_file_path)
                        
                        backup_manifest['files'].append({
                            'original_path': str(file_path),
                            'backup_path': str(backup_file_path),
                            'size': file_path.stat().st_size,
                            'modified': file_path.stat().st_mtime
                        })
                        
                except Exception as e:
                    logger.warning(f"Failed to backup file {file_path}: {e}")
                    continue
            
            # Save manifest
            manifest_path = backup_path / 'backup_manifest.json'
            with open(manifest_path, 'w', encoding='utf-8') as f:
                json.dump(backup_manifest, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Created directory backup: {backup_path} with {len(backup_manifest['files'])} files")
            return backup_path
            
        except Exception as e:
            logger.error(f"Failed to create directory backup: {e}")
            return None
    
    def list_backups(self) -> List[Dict]:
        """List available backups"""
        backups = []
        
        try:
            for item in self.backup_root.iterdir():
                try:
                    backup_info = self._get_backup_info(item)
                    if backup_info:
                        backups.append(backup_info)
                except Exception as e:
                    logger.debug(f"Error reading backup info for {item}: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Failed to list backups: {e}")
        
        # Sort by creation time (newest first)
        backups.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return backups
    
    def _get_backup_info(self, backup_path: Path) -> Optional[Dict]:
        """Get information about a backup"""
        try:
            if backup_path.is_file() and backup_path.suffix == '.zip':
                # ZIP backup
                with zipfile.ZipFile(backup_path, 'r') as zipf:
                    manifest_data = zipf.read('backup_manifest.json').decode('utf-8')
                    manifest = json.loads(manifest_data)
                    
                    return {
                        'name': backup_path.stem,
                        'path': str(backup_path),
                        'type': 'zip',
                        'size': backup_path.stat().st_size,
                        'created_at': manifest.get('created_at'),
                        'operation_name': manifest.get('operation_name'),
                        'file_count': len(manifest.get('files', []))
                    }
            
            elif backup_path.is_dir():
                # Directory backup
                manifest_path = backup_path / 'backup_manifest.json'
                if manifest_path.exists():
                    with open(manifest_path, 'r', encoding='utf-8') as f:
                        manifest = json.load(f)
                    
                    return {
                        'name': backup_path.name,
                        'path': str(backup_path),
                        'type': 'directory',
                        'size': self._get_directory_size(backup_path),
                        'created_at': manifest.get('created_at'),
                        'operation_name': manifest.get('operation_name'),
                        'file_count': len(manifest.get('files', []))
                    }
            
            return None
            
        except Exception as e:
            logger.debug(f"Error getting backup info for {backup_path}: {e}")
            return None
    
    def restore_backup(self, backup_path: Union[str, Path], 
                      restore_to_original: bool = True) -> bool:
        """Restore files from backup"""
        try:
            backup_path = Path(backup_path)
            
            if not backup_path.exists():
                logger.error(f"Backup does not exist: {backup_path}")
                return False
            
            if backup_path.is_file() and backup_path.suffix == '.zip':
                return self._restore_zip_backup(backup_path, restore_to_original)
            elif backup_path.is_dir():
                return self._restore_directory_backup(backup_path, restore_to_original)
            else:
                logger.error(f"Unknown backup type: {backup_path}")
                return False
            
        except Exception as e:
            logger.error(f"Failed to restore backup {backup_path}: {e}")
            return False
    
    def _restore_zip_backup(self, backup_path: Path, restore_to_original: bool) -> bool:
        """Restore from ZIP backup"""
        try:
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                # Read manifest
                manifest_data = zipf.read('backup_manifest.json').decode('utf-8')
                manifest = json.loads(manifest_data)
                
                restore_count = 0
                
                for file_info in manifest.get('files', []):
                    try:
                        original_path = Path(file_info['original_path'])
                        archive_name = file_info['archive_name']
                        
                        if restore_to_original:
                            restore_path = original_path
                        else:
                            # Restore to temp location
                            temp_dir = Path(tempfile.gettempdir()) / 'utac_restore'
                            temp_dir.mkdir(exist_ok=True)
                            restore_path = temp_dir / archive_name
                        
                        # Create parent directory if needed
                        restore_path.parent.mkdir(parents=True, exist_ok=True)
                        
                        # Extract file
                        with zipf.open(archive_name) as source, open(restore_path, 'wb') as target:
                            shutil.copyfileobj(source, target)
                        
                        restore_count += 1
                        logger.debug(f"Restored: {archive_name} -> {restore_path}")
                        
                    except Exception as e:
                        logger.warning(f"Failed to restore file {file_info}: {e}")
                        continue
                
                logger.info(f"Restored {restore_count} files from ZIP backup")
                return restore_count > 0
            
        except Exception as e:
            logger.error(f"Failed to restore ZIP backup: {e}")
            return False
    
    def _restore_directory_backup(self, backup_path: Path, restore_to_original: bool) -> bool:
        """Restore from directory backup"""
        try:
            manifest_path = backup_path / 'backup_manifest.json'
            if not manifest_path.exists():
                logger.error(f"Backup manifest not found: {manifest_path}")
                return False
            
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
            
            restore_count = 0
            
            for file_info in manifest.get('files', []):
                try:
                    original_path = Path(file_info['original_path'])
                    backup_file_path = Path(file_info['backup_path'])
                    
                    if not backup_file_path.exists():
                        logger.warning(f"Backup file not found: {backup_file_path}")
                        continue
                    
                    if restore_to_original:
                        restore_path = original_path
                    else:
                        # Restore to temp location
                        temp_dir = Path(tempfile.gettempdir()) / 'utac_restore'
                        temp_dir.mkdir(exist_ok=True)
                        restore_path = temp_dir / backup_file_path.name
                    
                    # Create parent directory if needed
                    restore_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Copy file
                    shutil.copy2(backup_file_path, restore_path)
                    
                    restore_count += 1
                    logger.debug(f"Restored: {backup_file_path} -> {restore_path}")
                    
                except Exception as e:
                    logger.warning(f"Failed to restore file {file_info}: {e}")
                    continue
            
            logger.info(f"Restored {restore_count} files from directory backup")
            return restore_count > 0
            
        except Exception as e:
            logger.error(f"Failed to restore directory backup: {e}")
            return False
    
    def delete_backup(self, backup_path: Union[str, Path]) -> bool:
        """Delete a backup"""
        try:
            backup_path = Path(backup_path)
            
            if backup_path.is_file():
                backup_path.unlink()
            elif backup_path.is_dir():
                shutil.rmtree(backup_path)
            else:
                logger.warning(f"Backup not found: {backup_path}")
                return False
            
            logger.info(f"Deleted backup: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete backup {backup_path}: {e}")
            return False
    
    def cleanup_old_backups(self, max_age_days: int = 30, max_count: int = 10) -> int:
        """Cleanup old backups"""
        try:
            backups = self.list_backups()
            
            # Filter backups to delete
            cutoff_date = datetime.now() - timedelta(days=max_age_days)
            backups_to_delete = []
            
            for backup in backups[max_count:]:  # Keep most recent max_count
                try:
                    created_at = datetime.fromisoformat(backup['created_at'])
                    if created_at < cutoff_date:
                        backups_to_delete.append(backup)
                except Exception:
                    continue
            
            # Delete old backups
            deleted_count = 0
            for backup in backups_to_delete:
                if self.delete_backup(backup['path']):
                    deleted_count += 1
            
            logger.info(f"Cleaned up {deleted_count} old backups")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup old backups: {e}")
            return 0
    
    def _get_directory_size(self, dir_path: Path) -> int:
        """Get total size of directory"""
        total_size = 0
        try:
            for item in dir_path.rglob('*'):
                if item.is_file():
                    try:
                        total_size += item.stat().st_size
                    except Exception:
                        continue
        except Exception:
            pass
        return total_size