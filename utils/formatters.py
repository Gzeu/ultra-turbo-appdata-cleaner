"""
Data formatting utilities
"""
from typing import Union, Dict, Any
from datetime import datetime, timedelta
import json

class Formatters:
    """Utilities for formatting data for display"""
    
    @staticmethod
    def format_bytes(bytes_value: Union[int, float]) -> str:
        """Format bytes in human readable format"""
        if bytes_value == 0:
            return "0 B"
        
        units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
        unit_index = 0
        
        while bytes_value >= 1024.0 and unit_index < len(units) - 1:
            bytes_value /= 1024.0
            unit_index += 1
        
        return f"{bytes_value:.1f} {units[unit_index]}"
    
    @staticmethod
    def format_duration(seconds: Union[int, float]) -> str:
        """Format duration in human readable format"""
        if seconds < 60:
            return f"{seconds:.1f} seconds"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f} minutes"
        elif seconds < 86400:
            hours = seconds / 3600
            return f"{hours:.1f} hours"
        else:
            days = seconds / 86400
            return f"{days:.1f} days"
    
    @staticmethod
    def format_timestamp(timestamp: Union[datetime, float, str]) -> str:
        """Format timestamp in readable format"""
        try:
            if isinstance(timestamp, str):
                dt = datetime.fromisoformat(timestamp)
            elif isinstance(timestamp, float):
                dt = datetime.fromtimestamp(timestamp)
            else:
                dt = timestamp
            
            return dt.strftime("%Y-%m-%d %H:%M:%S")
            
        except Exception:
            return str(timestamp)
    
    @staticmethod
    def format_percentage(value: Union[int, float], total: Union[int, float]) -> str:
        """Format percentage with proper handling of zero division"""
        if total == 0:
            return "0.0%"
        
        percentage = (value / total) * 100
        return f"{percentage:.1f}%"
    
    @staticmethod
    def format_file_count(count: int) -> str:
        """Format file count with proper pluralization"""
        if count == 1:
            return "1 file"
        else:
            return f"{count:,} files"
    
    @staticmethod
    def format_speed(bytes_per_second: Union[int, float]) -> str:
        """Format speed in human readable format"""
        return f"{Formatters.format_bytes(bytes_per_second)}/s"
    
    @staticmethod
    def format_progress_bar(current: int, total: int, width: int = 50) -> str:
        """Create ASCII progress bar"""
        if total == 0:
            percentage = 0
        else:
            percentage = min(current / total, 1.0)
        
        filled_width = int(width * percentage)
        bar = '█' * filled_width + '░' * (width - filled_width)
        
        return f"[{bar}] {percentage * 100:.1f}%"
    
    @staticmethod
    def format_table_row(columns: list, widths: list) -> str:
        """Format table row with proper column alignment"""
        formatted_columns = []
        
        for i, (column, width) in enumerate(zip(columns, widths)):
            column_str = str(column)
            if len(column_str) > width:
                column_str = column_str[:width-3] + '...'
            
            # Right-align numbers, left-align text
            if isinstance(column, (int, float)):
                formatted_columns.append(column_str.rjust(width))
            else:
                formatted_columns.append(column_str.ljust(width))
        
        return ' | '.join(formatted_columns)
    
    @staticmethod
    def format_json_pretty(data: Dict[str, Any]) -> str:
        """Format JSON data for pretty printing"""
        try:
            return json.dumps(data, indent=2, ensure_ascii=False, default=str)
        except Exception:
            return str(data)
    
    @staticmethod
    def format_file_age(modified_time: Union[datetime, float]) -> str:
        """Format file age in human readable format"""
        try:
            if isinstance(modified_time, float):
                modified_dt = datetime.fromtimestamp(modified_time)
            else:
                modified_dt = modified_time
            
            age = datetime.now() - modified_dt
            
            if age.days > 365:
                years = age.days // 365
                return f"{years} year{'s' if years > 1 else ''} ago"
            elif age.days > 30:
                months = age.days // 30
                return f"{months} month{'s' if months > 1 else ''} ago"
            elif age.days > 0:
                return f"{age.days} day{'s' if age.days > 1 else ''} ago"
            elif age.seconds > 3600:
                hours = age.seconds // 3600
                return f"{hours} hour{'s' if hours > 1 else ''} ago"
            elif age.seconds > 60:
                minutes = age.seconds // 60
                return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
            else:
                return "Just now"
                
        except Exception:
            return "Unknown"
    
    @staticmethod
    def truncate_path(path: str, max_length: int = 50) -> str:
        """Truncate long file paths for display"""
        if len(path) <= max_length:
            return path
        
        # Try to keep the filename and some parent directories
        parts = path.replace('\\', '/').split('/')
        
        if len(parts) <= 2:
            # Path too simple to truncate meaningfully
            return path[:max_length-3] + '...'
        
        # Keep filename and work backwards
        result = parts[-1]
        remaining_length = max_length - len(result) - 3  # Reserve space for '...'
        
        for i in range(len(parts) - 2, -1, -1):
            part_with_sep = '/' + parts[i] if i > 0 else parts[i]
            if len(result) + len(part_with_sep) <= remaining_length:
                result = part_with_sep + '/' + result
            else:
                result = '...' + result
                break
        
        return result