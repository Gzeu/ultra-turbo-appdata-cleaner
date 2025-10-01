"""
Tests for web interface
"""

import pytest
import json
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'web'))

from web.app import app
from web.api.system import SystemAPI
from web.api.scanner import ScannerAPI
from web.api.cleaner import CleanerAPI
from core.progress import ProgressTracker

class TestWebApp:
    """Test Flask web application"""
    
    @pytest.fixture
    def client(self):
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    def test_dashboard_route(self, client):
        """Test dashboard page loads"""
        response = client.get('/')
        assert response.status_code == 200
        assert b'Ultra-Turbo AppData Cleaner' in response.data
    
    def test_cleaner_route(self, client):
        """Test cleaner page loads"""
        response = client.get('/cleaner')
        assert response.status_code == 200
        assert b'System Cleaner' in response.data
    
    def test_settings_route(self, client):
        """Test settings page loads"""
        response = client.get('/settings')
        assert response.status_code == 200
        assert b'Application Settings' in response.data
    
    def test_logs_route(self, client):
        """Test logs page loads"""
        response = client.get('/logs')
        assert response.status_code == 200
        assert b'System Logs' in response.data

class TestSystemAPI:
    """Test System API functionality"""
    
    def test_system_api_initialization(self):
        api = SystemAPI()
        assert api is not None
        assert api.stats_cache == {}
    
    def test_get_system_info(self):
        api = SystemAPI()
        info = api.get_system_info()
        
        assert isinstance(info, dict)
        assert 'timestamp' in info
        assert 'system' in info
        assert 'memory' in info
        assert 'disk' in info
        assert 'cpu' in info
    
    def test_get_cleanup_potential(self):
        api = SystemAPI()
        potential = api.get_cleanup_potential()
        
        assert isinstance(potential, dict)
        if 'error' not in potential:
            assert 'estimated_cleanup_mb' in potential
            assert 'estimated_file_count' in potential

class TestScannerAPI:
    """Test Scanner API functionality"""
    
    def test_scanner_api_initialization(self, progress_tracker):
        api = ScannerAPI(progress_tracker)
        assert api is not None
        assert api.progress_tracker is not None
    
    def test_analyze_scan_results_empty(self, progress_tracker):
        api = ScannerAPI(progress_tracker)
        results = api._analyze_scan_results([])
        
        assert isinstance(results, dict)
        assert results['cleanable_count'] == 0
        assert results['cleanable_size'] == 0
    
    def test_analyze_scan_results_with_data(self, progress_tracker):
        api = ScannerAPI(progress_tracker)
        
        mock_files = [
            {
                'path': '/test/file1.tmp',
                'size': 1024,
                'cleanable': True,
                'category': 'temp',
                'safety_level': 1,
                'extension': '.tmp',
                'age_days': 5
            },
            {
                'path': '/test/file2.log',
                'size': 2048,
                'cleanable': False,
                'category': 'log',
                'safety_level': 3,
                'extension': '.log',
                'age_days': 15
            }
        ]
        
        results = api._analyze_scan_results(mock_files)
        
        assert results['cleanable_count'] == 1
        assert results['cleanable_size'] == 1024
        assert 'temp' in results['categories']
        assert 'log' in results['categories']
        assert '.tmp' in results['extensions']

class TestAPIEndpoints:
    """Test API endpoints"""
    
    @pytest.fixture
    def client(self):
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    def test_api_system_info_endpoint(self, client):
        """Test /api/system/info endpoint"""
        response = client.get('/api/system/info')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert isinstance(data, dict)
        if 'error' not in data:
            assert 'system' in data
            assert 'memory' in data
            assert 'disk' in data
    
    def test_api_settings_get(self, client):
        """Test GET /api/settings endpoint"""
        response = client.get('/api/settings')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert isinstance(data, dict)
        assert 'scan_paths' in data
        assert 'backup_enabled' in data
    
    def test_api_settings_post(self, client):
        """Test POST /api/settings endpoint"""
        test_settings = {
            'scan_paths': ['%TEMP%'],
            'backup_enabled': True,
            'safe_mode': True,
            'max_file_age_days': 14
        }
        
        response = client.post('/api/settings',
                              data=json.dumps(test_settings),
                              content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data.get('status') == 'success' or 'error' in data