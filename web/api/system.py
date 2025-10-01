"""
System API endpoints for web interface
"""

import psutil
import os
from pathlib import Path
from typing import Dict, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class SystemAPI:
    """API for system information and monitoring"""
    
    def __init__(self):
        self.stats_cache = {}
        self.cache_timeout = 30  # seconds
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get comprehensive system information"""
        try:
            # Check cache
            now = datetime.now()
            if 'system_info' in self.stats_cache:
                cached_time, cached_data = self.stats_cache['system_info']
                if (now - cached_time).seconds < self.cache_timeout:
                    return cached_data
            
            # Gather system info
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('C:\\')
            cpu_percent = psutil.cpu_percent(interval=1)
            
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime = now - boot_time
            
            system_info = {
                'timestamp': now.isoformat(),
                'system': {
                    'platform': os.name,
                    'hostname': os.environ.get('COMPUTERNAME', 'Unknown'),
                    'username': os.environ.get('USERNAME', 'Unknown'),
                    'uptime_hours': round(uptime.total_seconds() / 3600, 1)
                },
                'memory': {
                    'total_gb': round(memory.total / (1024**3), 2),
                    'available_gb': round(memory.available / (1024**3), 2),
                    'used_gb': round(memory.used / (1024**3), 2),
                    'percentage': memory.percent
                },
                'disk': {
                    'total_gb': round(disk.total / (1024**3), 2),
                    'free_gb': round(disk.free / (1024**3), 2),
                    'used_gb': round(disk.used / (1024**3), 2),
                    'percentage': round((disk.used / disk.total) * 100, 1)
                },
                'cpu': {
                    'percentage': cpu_percent,
                    'count': psutil.cpu_count()
                },
                'appdata_paths': self._get_appdata_info()
            }
            
            # Cache the result
            self.stats_cache['system_info'] = (now, system_info)
            
            return system_info
            
        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            return {'error': str(e)}
    
    def _get_appdata_info(self) -> Dict[str, Dict]:
        """Get AppData directories information"""
        try:
            appdata_paths = {
                'local': os.path.expandvars('%LOCALAPPDATA%'),
                'roaming': os.path.expandvars('%APPDATA%'),
                'temp': os.path.expandvars('%TEMP%')
            }
            
            appdata_info = {}
            
            for name, path in appdata_paths.items():
                try:
                    path_obj = Path(path)
                    if path_obj.exists():
                        # Get directory size (sample first level only for speed)
                        size = self._get_directory_sample_size(path_obj)
                        file_count = len([f for f in path_obj.iterdir() if f.is_file()])
                        dir_count = len([f for f in path_obj.iterdir() if f.is_dir()])
                        
                        appdata_info[name] = {
                            'path': str(path_obj),
                            'exists': True,
                            'accessible': os.access(path_obj, os.R_OK | os.W_OK),
                            'size_mb': round(size / (1024**2), 2),
                            'file_count': file_count,
                            'dir_count': dir_count
                        }
                    else:
                        appdata_info[name] = {
                            'path': path,
                            'exists': False,
                            'accessible': False
                        }
                except Exception as e:
                    logger.debug(f"Error getting info for {name}: {e}")
                    appdata_info[name] = {
                        'path': path,
                        'exists': False,
                        'accessible': False,
                        'error': str(e)
                    }
            
            return appdata_info
            
        except Exception as e:
            logger.error(f"Error getting AppData info: {e}")
            return {}
    
    def _get_directory_sample_size(self, directory: Path, max_files: int = 100) -> int:
        """Get sample size of directory (for performance)"""
        try:
            total_size = 0
            file_count = 0
            
            for item in directory.iterdir():
                if file_count >= max_files:
                    break
                    
                try:
                    if item.is_file():
                        total_size += item.stat().st_size
                        file_count += 1
                except (PermissionError, OSError):
                    continue
            
            return total_size
            
        except Exception:
            return 0
    
    def get_cleanup_potential(self) -> Dict[str, Any]:
        """Estimate cleanup potential"""
        try:
            # Quick estimation based on common temp locations
            temp_paths = [
                os.path.expandvars('%TEMP%'),
                os.path.expandvars('%LOCALAPPDATA%\\Temp'),
                'C:\\Windows\\Temp'
            ]
            
            total_potential = 0
            file_count = 0
            accessible_paths = []
            
            for temp_path in temp_paths:
                try:
                    path_obj = Path(temp_path)
                    if path_obj.exists():
                        size = self._get_directory_sample_size(path_obj)
                        total_potential += size
                        accessible_paths.append(temp_path)
                        
                        # Count files
                        for item in path_obj.iterdir():
                            if item.is_file():
                                file_count += 1
                                if file_count >= 1000:  # Limit for performance
                                    break
                except Exception:
                    continue
            
            return {
                'estimated_cleanup_mb': round(total_potential / (1024**2), 2),
                'estimated_file_count': file_count,
                'accessible_temp_paths': len(accessible_paths),
                'paths_checked': accessible_paths
            }
            
        except Exception as e:
            logger.error(f"Error estimating cleanup potential: {e}")
            return {'error': str(e)}
    
    def get_running_processes(self) -> List[Dict]:
        """Get list of running processes"""
        try:
            processes = []
            
            for proc in psutil.process_iter(['pid', 'name', 'memory_percent', 'cpu_percent']):
                try:
                    if proc.info['memory_percent'] > 1.0:  # Only significant processes
                        processes.append({
                            'pid': proc.info['pid'],
                            'name': proc.info['name'],
                            'memory_percent': round(proc.info['memory_percent'], 2),
                            'cpu_percent': round(proc.info['cpu_percent'] or 0, 2)
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Sort by memory usage
            processes.sort(key=lambda x: x['memory_percent'], reverse=True)
            
            return processes[:20]  # Top 20 processes
            
        except Exception as e:
            logger.error(f"Error getting processes: {e}")
            return []
    
    def get_disk_usage_by_directory(self, base_path: str = None) -> Dict[str, Dict]:
        """Get disk usage breakdown by directory"""
        try:
            if base_path is None:
                base_path = os.path.expandvars('%USERPROFILE%')
            
            base_path_obj = Path(base_path)
            if not base_path_obj.exists():
                return {}
            
            directory_sizes = {}
            
            for item in base_path_obj.iterdir():
                if item.is_dir():
                    try:
                        size = self._get_directory_sample_size(item, max_files=50)
                        if size > 0:
                            directory_sizes[item.name] = {
                                'size_mb': round(size / (1024**2), 2),
                                'path': str(item)
                            }
                    except Exception:
                        continue
            
            # Sort by size
            sorted_dirs = dict(sorted(directory_sizes.items(), 
                                    key=lambda x: x[1]['size_mb'], reverse=True))
            
            return sorted_dirs
            
        except Exception as e:
            logger.error(f"Error getting disk usage: {e}")
            return {}