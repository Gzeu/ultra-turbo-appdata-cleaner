"""
Pytest configuration and fixtures
"""

import pytest
import tempfile
import shutil
from pathlib import Path
import sys
import os

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import Settings
from core.cleaner import CleanerEngine
from core.progress import ProgressTracker

@pytest.fixture
def temp_dir():
    """Create temporary directory for tests"""
    temp_path = Path(tempfile.mkdtemp(prefix='utac_test_'))
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)

@pytest.fixture
def test_settings():
    """Create test settings configuration"""
    test_config = {
        'scan_paths': [],
        'backup_enabled': False,
        'safe_mode': True,
        'max_file_age_days': 30,
        'min_file_size_mb': 0.001  # Very small for testing
    }
    return Settings()

@pytest.fixture
def progress_tracker():
    """Create progress tracker instance"""
    return ProgressTracker()

@pytest.fixture
def cleaner_engine(test_settings):
    """Create cleaner engine with test settings"""
    return CleanerEngine(test_settings)

@pytest.fixture
def sample_files(temp_dir):
    """Create sample files for testing"""
    files = {
        'temp_files': [],
        'cache_files': [],
        'log_files': [],
        'safe_files': [],
        'dangerous_files': []
    }
    
    # Create temp files
    temp_files = ['test.tmp', 'old_file.temp', 'cache.cache']
    for filename in temp_files:
        file_path = temp_dir / filename
        file_path.write_text(f'Test content for {filename}')
        files['temp_files'].append(file_path)
    
    # Create cache files
    cache_dir = temp_dir / 'cache'
    cache_dir.mkdir()
    cache_files = ['browser.cache', 'app.cache']
    for filename in cache_files:
        file_path = cache_dir / filename
        file_path.write_text(f'Cache content for {filename}')
        files['cache_files'].append(file_path)
    
    # Create log files
    log_files = ['application.log', 'debug.log']
    for filename in log_files:
        file_path = temp_dir / filename
        file_path.write_text(f'Log content for {filename}\n' * 100)
        files['log_files'].append(file_path)
    
    return files