"""
Progress tracking and reporting module
"""
import time
import threading
from typing import Dict, Callable, Optional, Any
from enum import Enum
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class OperationStatus(Enum):
    PENDING = "pending"
    RUNNING = "running" 
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ProgressType(Enum):
    DETERMINATE = "determinate"
    INDETERMINATE = "indeterminate"

@dataclass
class ProgressInfo:
    """Information about operation progress"""
    operation_id: str
    operation_name: str
    status: OperationStatus = OperationStatus.PENDING
    progress_type: ProgressType = ProgressType.DETERMINATE
    
    current: int = 0
    total: int = 0
    percentage: float = 0.0
    
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    elapsed_time: timedelta = field(default_factory=lambda: timedelta(0))
    
    current_item: str = ""
    items_processed: int = 0
    items_failed: int = 0
    
    status_message: str = ""
    last_error: Optional[str] = None

class ProgressTracker:
    def __init__(self):
        self.operations: Dict[str, ProgressInfo] = {}
        self.callbacks: Dict[str, list] = {}
        self.lock = threading.Lock()
        
    def create_operation(self, operation_id: str, operation_name: str, 
                        total_items: int = 0) -> ProgressInfo:
        """Create new operation for tracking"""
        with self.lock:
            progress_info = ProgressInfo(
                operation_id=operation_id,
                operation_name=operation_name,
                total=total_items
            )
            self.operations[operation_id] = progress_info
            return progress_info
    
    def start_operation(self, operation_id: str, total_items: int = 0) -> bool:
        """Start an operation"""
        with self.lock:
            if operation_id not in self.operations:
                # Create operation if it doesn't exist
                self.create_operation(operation_id, operation_id, total_items)
            
            progress = self.operations[operation_id]
            progress.status = OperationStatus.RUNNING
            progress.start_time = datetime.now()
            return True
    
    def update_progress(self, operation_id: str, current: Optional[int] = None,
                       current_item: str = "", status_message: str = "") -> bool:
        """Update operation progress"""
        with self.lock:
            if operation_id not in self.operations:
                return False
            
            progress = self.operations[operation_id]
            
            if current is not None:
                progress.current = current
                if progress.total > 0:
                    progress.percentage = (current / progress.total) * 100.0
            
            if current_item:
                progress.current_item = current_item
                progress.items_processed += 1
            
            if status_message:
                progress.status_message = status_message
            
            return True
    
    def complete_operation(self, operation_id: str = None, success: bool = True) -> bool:
        """Mark operation as completed"""
        with self.lock:
            if operation_id and operation_id not in self.operations:
                return False
            
            # If no operation_id provided, complete the most recent one
            if not operation_id and self.operations:
                operation_id = list(self.operations.keys())[-1]
            
            if not operation_id:
                return False
                
            progress = self.operations[operation_id]
            progress.status = OperationStatus.COMPLETED if success else OperationStatus.FAILED
            progress.end_time = datetime.now()
            
            if progress.start_time:
                progress.elapsed_time = progress.end_time - progress.start_time
            
            return True
    
    def get_progress(self, operation_id: str) -> Optional[ProgressInfo]:
        """Get progress information for operation"""
        with self.lock:
            return self.operations.get(operation_id)