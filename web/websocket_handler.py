"""
WebSocket handler for real-time communication
"""

from flask_socketio import emit
import logging
from datetime import datetime
from core.progress import ProgressInfo

logger = logging.getLogger(__name__)

class WebSocketHandler:
    """Handle WebSocket communication for real-time updates"""
    
    def __init__(self, socketio, progress_tracker):
        self.socketio = socketio
        self.progress_tracker = progress_tracker
        self.connected_clients = set()
        
        # Register progress callback
        self.progress_tracker.add_callback(self._on_progress_update)
    
    def _on_progress_update(self, progress_info: ProgressInfo):
        """Handle progress updates and broadcast to clients"""
        try:
            progress_data = {
                'operation_id': progress_info.operation_id,
                'operation_name': progress_info.operation_name,
                'status': progress_info.status.value,
                'percentage': progress_info.percentage,
                'current': progress_info.current,
                'total': progress_info.total,
                'current_item': progress_info.current_item,
                'status_message': progress_info.status_message,
                'items_processed': progress_info.items_processed,
                'items_failed': progress_info.items_failed,
                'elapsed_seconds': progress_info.elapsed_time.total_seconds() if progress_info.elapsed_time else 0,
                'timestamp': datetime.now().isoformat()
            }
            
            # Broadcast to all connected clients
            self.socketio.emit('progress_update', progress_data)
            
            # Send specific events based on status
            if progress_info.status.value == 'completed':
                self.socketio.emit('operation_completed', {
                    'operation_id': progress_info.operation_id,
                    'operation_name': progress_info.operation_name,
                    'final_message': progress_info.status_message
                })
            elif progress_info.status.value == 'failed':
                self.socketio.emit('operation_failed', {
                    'operation_id': progress_info.operation_id,
                    'operation_name': progress_info.operation_name,
                    'error': progress_info.last_error
                })
            
        except Exception as e:
            logger.error(f"Error broadcasting progress update: {e}")
    
    def broadcast_system_stats(self, stats: dict):
        """Broadcast system statistics to all clients"""
        try:
            self.socketio.emit('system_stats_update', {
                'stats': stats,
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            logger.error(f"Error broadcasting system stats: {e}")
    
    def broadcast_scan_results(self, scan_results: dict):
        """Broadcast scan results to all clients"""
        try:
            self.socketio.emit('scan_results', {
                'results': scan_results,
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            logger.error(f"Error broadcasting scan results: {e}")
    
    def broadcast_cleaning_results(self, cleaning_results: dict):
        """Broadcast cleaning results to all clients"""
        try:
            self.socketio.emit('cleaning_results', {
                'results': cleaning_results,
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            logger.error(f"Error broadcasting cleaning results: {e}")
    
    def send_notification(self, message: str, notification_type: str = 'info'):
        """Send notification to all clients"""
        try:
            self.socketio.emit('notification', {
                'message': message,
                'type': notification_type,
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
    
    def send_error(self, error_message: str, operation_id: str = None):
        """Send error message to all clients"""
        try:
            self.socketio.emit('error', {
                'message': error_message,
                'operation_id': operation_id,
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            logger.error(f"Error sending error message: {e}")
    
    def handle_client_connect(self, client_id: str):
        """Handle new client connection"""
        self.connected_clients.add(client_id)
        logger.info(f"Client connected: {client_id}")
        
        # Send current system status to new client
        try:
            from web.api.system import SystemAPI
            system_api = SystemAPI()
            system_info = system_api.get_system_info()
            self.socketio.emit('initial_system_info', system_info)
        except Exception as e:
            logger.error(f"Error sending initial system info: {e}")
    
    def handle_client_disconnect(self, client_id: str):
        """Handle client disconnection"""
        self.connected_clients.discard(client_id)
        logger.info(f"Client disconnected: {client_id}")
    
    def get_connected_clients_count(self) -> int:
        """Get number of connected clients"""
        return len(self.connected_clients)