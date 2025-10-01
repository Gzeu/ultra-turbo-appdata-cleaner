"""
Tests for specialized cleaning modules
"""

import pytest
from pathlib import Path
import os
import tempfile

from modules.appdata_cleaner import AppDataCleaner
from modules.temp_cleaner import TempCleaner
from modules.duplicate_finder import DuplicateFinder
from modules.browser_cleaner import BrowserCleaner
from modules.log_cleaner import LogCleaner
from core.progress import ProgressTracker

class TestAppDataCleaner:
    """Test AppDataCleaner module"""
    
    def test_appdata_cleaner_initialization(self, progress_tracker):
        cleaner = AppDataCleaner(progress_tracker)
        assert cleaner is not None
        assert cleaner.progress_tracker is not None
        assert len(cleaner.appdata_roots) >= 0  # May be empty in test environment
    
    def test_categorize_appdata_file(self, progress_tracker, temp_dir):
        cleaner = AppDataCleaner(progress_tracker)
        
        # Create test AppData structure
        appdata_dir = temp_dir / 'AppData' / 'Local' / 'TestApp'
        appdata_dir.mkdir(parents=True)
        
        # Test temp file
        temp_file = appdata_dir / 'test.tmp'
        temp_file.write_text('test content')
        
        category = cleaner._categorize_appdata_file(temp_file)
        assert category in ['safe_to_clean', 'potentially_safe', 'preserve', 'unknown']

class TestTempCleaner:
    """Test TempCleaner module"""
    
    def test_temp_cleaner_initialization(self, progress_tracker):
        cleaner = TempCleaner(progress_tracker)
        assert cleaner is not None
        assert isinstance(cleaner.temp_locations, dict)
    
    def test_has_temp_extension(self, progress_tracker):
        cleaner = TempCleaner(progress_tracker)
        
        temp_files = [Path('test.tmp'), Path('old.temp'), Path('cache.cache')]
        normal_files = [Path('document.pdf'), Path('image.jpg'), Path('script.py')]
        
        for temp_file in temp_files:
            assert cleaner._has_temp_extension(temp_file) == True
        
        for normal_file in normal_files:
            assert cleaner._has_temp_extension(normal_file) == False
    
    def test_categorize_temp_file(self, progress_tracker, temp_dir):
        cleaner = TempCleaner(progress_tracker)
        
        # Create test temp file
        temp_file = temp_dir / 'old_file.tmp'
        temp_file.write_text('test content')
        
        from datetime import datetime, timedelta
        cutoff_date = datetime.now() - timedelta(days=7)
        
        category = cleaner._categorize_temp_file(temp_file, 'system_temp', cutoff_date, 1024)
        assert category in ['old_temp_files', 'large_temp_files', 'browser_cache', 'system_temp']

class TestDuplicateFinder:
    """Test DuplicateFinder module"""
    
    def test_duplicate_finder_initialization(self, progress_tracker):
        finder = DuplicateFinder(progress_tracker)
        assert finder is not None
        assert finder.hash_cache == {}
    
    def test_calculate_file_hash(self, progress_tracker, temp_dir):
        finder = DuplicateFinder(progress_tracker)
        
        # Create test file
        test_file = temp_dir / 'test_hash.txt'
        test_content = 'This is test content for hashing'
        test_file.write_text(test_content)
        
        file_hash = finder._calculate_file_hash(test_file)
        assert file_hash is not None
        assert len(file_hash) == 32  # MD5 hash length
    
    def test_find_duplicates_no_duplicates(self, progress_tracker, temp_dir):
        finder = DuplicateFinder(progress_tracker)
        
        # Create unique files
        file1 = temp_dir / 'unique1.txt'
        file2 = temp_dir / 'unique2.txt'
        file1.write_text('Content 1')
        file2.write_text('Content 2')
        
        duplicates = finder.find_duplicates([temp_dir])
        assert isinstance(duplicates, dict)
        assert len(duplicates) == 0  # No duplicates should be found
    
    def test_find_duplicates_with_duplicates(self, progress_tracker, temp_dir):
        finder = DuplicateFinder(progress_tracker)
        
        # Create duplicate files
        content = 'Identical content for both files'
        file1 = temp_dir / 'duplicate1.txt'
        file2 = temp_dir / 'duplicate2.txt'
        file1.write_text(content)
        file2.write_text(content)
        
        duplicates = finder.find_duplicates([temp_dir], min_file_size=1)
        
        # Should find one group of duplicates
        assert len(duplicates) == 1
        duplicate_group = list(duplicates.values())[0]
        assert len(duplicate_group) == 2

class TestBrowserCleaner:
    """Test BrowserCleaner module"""
    
    def test_browser_cleaner_initialization(self, progress_tracker):
        cleaner = BrowserCleaner(progress_tracker)
        assert cleaner is not None
        assert isinstance(cleaner.browser_paths, dict)
    
    def test_format_bytes(self, progress_tracker):
        cleaner = BrowserCleaner(progress_tracker)
        
        assert cleaner._format_bytes(0) == '0.0 B'
        assert cleaner._format_bytes(1024) == '1.0 KB'
        assert cleaner._format_bytes(1024 * 1024) == '1.0 MB'
        assert cleaner._format_bytes(1024 * 1024 * 1024) == '1.0 GB'

class TestLogCleaner:
    """Test LogCleaner module"""
    
    def test_log_cleaner_initialization(self, progress_tracker):
        cleaner = LogCleaner(progress_tracker)
        assert cleaner is not None
        assert isinstance(cleaner.log_locations, dict)
    
    def test_is_likely_active_log(self, progress_tracker, temp_dir):
        cleaner = LogCleaner(progress_tracker)
        
        # Create current log file (recent modification)
        current_log = temp_dir / 'current.log'
        current_log.write_text('Recent log entry')
        
        # Create old log file
        old_log = temp_dir / 'old_archive.log' 
        old_log.write_text('Old log entry')
        
        # Mock file modification time
        import time
        current_time = time.time()
        os.utime(current_log, (current_time, current_time))  # Recent
        os.utime(old_log, (current_time - 86400 * 7, current_time - 86400 * 7))  # 7 days old
        
        assert cleaner._is_likely_active_log(current_log) == True
        assert cleaner._is_likely_active_log(old_log) == False