"""
Flask web application for Ultra-Turbo AppData Cleaner
"""

# Fix import path issues
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_socketio import SocketIO, emit
import os
from datetime import datetime
import threading
import json
import logging

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'ultra-turbo-cleaner-secret-key-2025'
socketio = SocketIO(app, cors_allowed_origins="*")

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global state
app_state = {
    'last_scan_results': None,
    'current_operation': None,
    'system_stats': None,
    'dry_run_mode': os.environ.get('DRY_RUN', '0') == '1'
}

# Try to import core modules (with fallbacks)
try:
    from config.settings import Settings
    from core.cleaner import CleanerEngine
    from core.progress import ProgressTracker
    from web.api.system import SystemAPI
    from web.api.scanner import ScannerAPI
    from web.api.cleaner import CleanerAPI
    from web.websocket_handler import WebSocketHandler
    
    # Initialize components
    settings = Settings()
    progress_tracker = ProgressTracker()
    cleaner_engine = CleanerEngine(settings)
    
    # Initialize API handlers
    system_api = SystemAPI()
    scanner_api = ScannerAPI(progress_tracker)
    cleaner_api = CleanerAPI(cleaner_engine, progress_tracker)
    websocket_handler = WebSocketHandler(socketio, progress_tracker)
    
    logger.info("All modules loaded successfully")
    app_state['modules_loaded'] = True
    
except ImportError as e:
    logger.warning(f"Some modules not available: {e}")
    app_state['modules_loaded'] = False
    
    # Mock objects for development
    class MockAPI:
        def get_system_info(self):
            return {
                'timestamp': datetime.now().isoformat(),
                'system': {'platform': 'Windows', 'hostname': 'Test', 'username': 'User', 'uptime_hours': 24},
                'memory': {'total_gb': 16, 'available_gb': 8, 'used_gb': 8, 'percentage': 50},
                'disk': {'total_gb': 1000, 'free_gb': 500, 'used_gb': 500, 'percentage': 50},
                'cpu': {'percentage': 25, 'count': 8},
                'appdata_paths': {
                    'local': {'path': 'C:\\Users\\User\\AppData\\Local', 'exists': True, 'accessible': True, 'size_mb': 1000, 'file_count': 500, 'dir_count': 50},
                    'roaming': {'path': 'C:\\Users\\User\\AppData\\Roaming', 'exists': True, 'accessible': True, 'size_mb': 500, 'file_count': 200, 'dir_count': 30}
                }
            }
        
        def quick_scan(self, operation_id):
            return {
                'operation_id': operation_id,
                'scan_type': 'quick',
                'total_files': 150,
                'cleanable_files': 75,
                'potential_savings_mb': 250,
                'categories': {'temp': 50, 'cache': 25},
                'timestamp': datetime.now().isoformat()
            }
    
    system_api = MockAPI()
    scanner_api = MockAPI()
    cleaner_api = MockAPI()

@app.route('/')
def dashboard():
    """Main dashboard page"""
    try:
        system_info = system_api.get_system_info()
        app_state['system_stats'] = system_info
        
        return render_template('dashboard.html', 
                             system_info=system_info,
                             app_state=app_state)
    except Exception as e:
        logger.error(f"Error loading dashboard: {e}")
        return render_template('error.html', error=str(e)) if Path('templates/error.html').exists() else f"<h1>Dashboard Error: {e}</h1>"

@app.route('/cleaner')
def cleaner():
    """Cleaner control panel page"""
    try:
        return render_template('cleaner.html', 
                             scan_results=app_state.get('last_scan_results'),
                             app_state=app_state)
    except Exception as e:
        return f"<h1>Cleaner Page Error: {e}</h1>"

@app.route('/settings')
def settings_page():
    """Settings management page"""
    try:
        current_settings = {
            'scan_paths': ['%APPDATA%', '%LOCALAPPDATA%', '%TEMP%'],
            'backup_enabled': True,
            'safe_mode': True,
            'max_file_age_days': 30,
            'min_file_size_mb': 1
        }
        return render_template('settings.html', settings=current_settings)
    except Exception as e:
        return f"<h1>Settings Page Error: {e}</h1>"

@app.route('/logs')
def logs():
    """Logs viewer page"""
    try:
        return render_template('logs.html')
    except Exception as e:
        return f"<h1>Logs Page Error: {e}</h1>"

# API Routes
@app.route('/api/health')
def api_health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'dry_run_mode': app_state['dry_run_mode'],
        'modules_loaded': app_state['modules_loaded'],
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/system/info')
def api_system_info():
    """Get system information"""
    try:
        info = system_api.get_system_info()
        return jsonify(info)
    except Exception as e:
        logger.error(f"API error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/scan/quick', methods=['POST'])
def api_quick_scan():
    """Quick system scan"""
    try:
        operation_id = f"quick_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        if app_state['dry_run_mode']:
            # Simulate scan in dry run mode
            results = scanner_api.quick_scan(operation_id)
            app_state['last_scan_results'] = results
            return jsonify(results)
        
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
        logger.error(f"Quick scan error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/settings', methods=['GET', 'POST'])
def api_settings():
    """Get or update settings"""
    if request.method == 'GET':
        current_settings = {
            'scan_paths': ['%APPDATA%', '%LOCALAPPDATA%', '%TEMP%'],
            'backup_enabled': True,
            'safe_mode': True,
            'max_file_age_days': 30,
            'min_file_size_mb': 1
        }
        return jsonify(current_settings)
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            # In a real implementation, save settings here
            logger.info(f"Settings update requested: {data}")
            return jsonify({'status': 'success', 'message': 'Settings updated'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

# WebSocket events
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    emit('connected', {
        'status': 'Connected to Ultra-Turbo AppData Cleaner',
        'dry_run_mode': app_state['dry_run_mode']
    })

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info('Client disconnected')

@socketio.on('request_system_stats')
def handle_system_stats_request():
    """Handle request for system statistics"""
    try:
        stats = system_api.get_system_info()
        emit('system_stats', stats)
    except Exception as e:
        emit('error', {'message': str(e)})

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return jsonify({'error': 'Page not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Set DRY_RUN mode if not already set
    if 'DRY_RUN' not in os.environ:
        os.environ['DRY_RUN'] = '1'
        app_state['dry_run_mode'] = True
        logger.info("🔒 DRY_RUN mode enabled for safety")
    
    print("🚀 Starting Ultra-Turbo AppData Cleaner Web Interface...")
    print(f"📱 Access at: http://localhost:5000")
    print(f"🔒 DRY_RUN Mode: {'ON' if app_state['dry_run_mode'] else 'OFF'}")
    print(f"📦 Modules Loaded: {'YES' if app_state['modules_loaded'] else 'NO (using mocks)'}")
    
    try:
        socketio.run(app, debug=True, host='0.0.0.0', port=5000)
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        # Fallback to basic Flask server
        app.run(debug=True, host='0.0.0.0', port=5000)