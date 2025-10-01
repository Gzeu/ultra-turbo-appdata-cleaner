"""
Flask web application for Ultra-Turbo AppData Cleaner
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_socketio import SocketIO, emit
import os
import sys
from pathlib import Path
import threading
import json
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import Settings
from config.logging_config import setup_logging
from core.cleaner import CleanerEngine
from core.progress import ProgressTracker
from modules.appdata_cleaner import AppDataCleaner
from modules.temp_cleaner import TempCleaner
from modules.browser_cleaner import BrowserCleaner
from web.api.system import SystemAPI
from web.api.scanner import ScannerAPI
from web.api.cleaner import CleanerAPI
from web.websocket_handler import WebSocketHandler

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'ultra-turbo-cleaner-secret-key-2025'
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize components
settings = Settings()
setup_logging()
progress_tracker = ProgressTracker()
cleaner_engine = CleanerEngine(settings)

# Initialize API handlers
system_api = SystemAPI()
scanner_api = ScannerAPI(progress_tracker)
cleaner_api = CleanerAPI(cleaner_engine, progress_tracker)
websocket_handler = WebSocketHandler(socketio, progress_tracker)

# Global state
app_state = {
    'last_scan_results': None,
    'current_operation': None,
    'system_stats': None
}

@app.route('/')
def dashboard():
    """Main dashboard page"""
    try:
        # Get system information
        system_info = system_api.get_system_info()
        app_state['system_stats'] = system_info
        
        return render_template('dashboard.html', 
                             system_info=system_info,
                             app_state=app_state)
    except Exception as e:
        return render_template('error.html', error=str(e))

@app.route('/cleaner')
def cleaner():
    """Cleaner control panel page"""
    return render_template('cleaner.html', 
                         scan_results=app_state.get('last_scan_results'),
                         app_state=app_state)

@app.route('/settings')
def settings_page():
    """Settings management page"""
    current_settings = {
        'scan_paths': settings.scan_paths,
        'backup_enabled': settings.backup_enabled,
        'safe_mode': settings.safe_mode,
        'max_file_age_days': settings.get('max_file_age_days', 30),
        'min_file_size_mb': settings.get('min_file_size_mb', 1)
    }
    return render_template('settings.html', settings=current_settings)

@app.route('/logs')
def logs():
    """Logs viewer page"""
    return render_template('logs.html')

# API Routes
@app.route('/api/system/info')
def api_system_info():
    """Get system information"""
    try:
        info = system_api.get_system_info()
        return jsonify(info)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/scan/quick', methods=['POST'])
def api_quick_scan():
    """Quick system scan"""
    try:
        operation_id = f"quick_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Start scan in background thread
        def scan_thread():
            try:
                results = scanner_api.quick_scan(operation_id)
                app_state['last_scan_results'] = results
                socketio.emit('scan_complete', results)
            except Exception as e:
                socketio.emit('scan_error', {'error': str(e)})
        
        thread = threading.Thread(target=scan_thread)
        thread.start()
        
        return jsonify({'operation_id': operation_id, 'status': 'started'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/scan/full', methods=['POST'])
def api_full_scan():
    """Full system scan"""
    try:
        data = request.get_json() or {}
        paths = data.get('paths', settings.scan_paths)
        operation_id = f"full_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        def scan_thread():
            try:
                results = scanner_api.full_scan(operation_id, paths)
                app_state['last_scan_results'] = results
                socketio.emit('scan_complete', results)
            except Exception as e:
                socketio.emit('scan_error', {'error': str(e)})
        
        thread = threading.Thread(target=scan_thread)
        thread.start()
        
        return jsonify({'operation_id': operation_id, 'status': 'started'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/clean/selected', methods=['POST'])
def api_clean_selected():
    """Clean selected files"""
    try:
        data = request.get_json()
        files = data.get('files', [])
        create_backup = data.get('backup', True)
        
        operation_id = f"clean_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        def clean_thread():
            try:
                results = cleaner_api.clean_files(operation_id, files, create_backup)
                socketio.emit('clean_complete', results)
            except Exception as e:
                socketio.emit('clean_error', {'error': str(e)})
        
        thread = threading.Thread(target=clean_thread)
        thread.start()
        
        return jsonify({'operation_id': operation_id, 'status': 'started'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/progress/<operation_id>')
def api_get_progress(operation_id):
    """Get operation progress"""
    try:
        progress = progress_tracker.get_progress(operation_id)
        if progress:
            return jsonify({
                'operation_id': progress.operation_id,
                'status': progress.status.value,
                'percentage': progress.percentage,
                'current_item': progress.current_item,
                'status_message': progress.status_message,
                'items_processed': progress.items_processed
            })
        else:
            return jsonify({'error': 'Operation not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/settings', methods=['GET', 'POST'])
def api_settings():
    """Get or update settings"""
    if request.method == 'GET':
        current_settings = {
            'scan_paths': settings.scan_paths,
            'backup_enabled': settings.backup_enabled,
            'safe_mode': settings.safe_mode,
            'max_file_age_days': settings.get('max_file_age_days', 30),
            'min_file_size_mb': settings.get('min_file_size_mb', 1)
        }
        return jsonify(current_settings)
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            
            # Update settings
            if 'scan_paths' in data:
                settings.set('scan_paths', data['scan_paths'])
            if 'backup_enabled' in data:
                settings.set('backup_enabled', data['backup_enabled'])
            if 'safe_mode' in data:
                settings.set('safe_mode', data['safe_mode'])
            if 'max_file_age_days' in data:
                settings.set('max_file_age_days', data['max_file_age_days'])
            if 'min_file_size_mb' in data:
                settings.set('min_file_size_mb', data['min_file_size_mb'])
            
            # Save settings
            settings.save_settings()
            
            return jsonify({'status': 'success', 'message': 'Settings updated'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

# WebSocket events
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    emit('connected', {'status': 'Connected to Ultra-Turbo AppData Cleaner'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print('Client disconnected')

@socketio.on('request_system_stats')
def handle_system_stats_request():
    """Handle request for system statistics"""
    try:
        stats = system_api.get_system_info()
        emit('system_stats', stats)
    except Exception as e:
        emit('error', {'message': str(e)})

if __name__ == '__main__':
    print("🌐 Starting Ultra-Turbo AppData Cleaner Web Interface...")
    print("📱 Access at: http://localhost:5000")
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)