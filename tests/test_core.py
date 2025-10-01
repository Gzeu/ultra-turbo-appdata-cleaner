"""
Tests for core modules
"""

import pytest
import asyncio
from pathlib import Path

from core.scanner import FileScanner
from core.analyzer import FileAnalyzer, FileCategory, FileSafetyLevel
from core.safety import SafetyChecker
from core.progress import ProgressTracker, OperationStatus

class TestFileScanner:
    """Test FileScanner functionality"""
    
    def test_scanner_initialization(self, test_settings):
        scanner = FileScanner(test_settings)
        assert scanner is not None
        assert isinstance(scanner.excluded_extensions, set)
    
    @pytest.mark.asyncio
    async def test_scan_path_empty(self, test_settings, temp_dir):
        scanner = FileScanner(test_settings)
        results = await scanner.scan_path(str(temp_dir))
        assert isinstance(results, list)
    
    @pytest.mark.asyncio
    async def test_scan_path_with_files(self, test_settings, sample_files, temp_dir):
        scanner = FileScanner(test_settings)
        results = await scanner.scan_path(str(temp_dir))
        
        assert len(results) > 0
        assert all('path' in result for result in results)
        assert all('size' in result for result in results)
        assert all('name' in result for result in results)

class TestFileAnalyzer:
    """Test FileAnalyzer functionality"""
    
    def test_analyzer_initialization(self, test_settings):
        analyzer = FileAnalyzer(test_settings)
        assert analyzer is not None
        assert analyzer.patterns is not None
    
    def test_analyze_temp_file(self, test_settings, temp_dir):
        analyzer = FileAnalyzer(test_settings)
        
        # Create temp file
        temp_file = temp_dir / 'test.tmp'
        temp_file.write_text('test content')
        
        category, safety = analyzer.analyze_file(temp_file)
        assert category == FileCategory.TEMP
        assert safety in [FileSafetyLevel.VERY_SAFE, FileSafetyLevel.SAFE]
    
    def test_analyze_system_file(self, test_settings):
        analyzer = FileAnalyzer(test_settings)
        
        # System file path (simulated)
        system_path = Path('C:/Windows/System32/kernel32.dll')
        category, safety = analyzer.analyze_file(system_path)
        
        assert category == FileCategory.CRITICAL_SYSTEM
        assert safety == FileSafetyLevel.DANGEROUS
    
    @pytest.mark.asyncio
    async def test_analyze_files_batch(self, test_settings, sample_files):
        analyzer = FileAnalyzer(test_settings)
        
        # Prepare file info list
        file_infos = []
        for file_path in sample_files['temp_files']:
            file_infos.append({'path': str(file_path)})
        
        results = await analyzer.analyze_files(file_infos)
        
        assert len(results) == len(file_infos)
        assert all('category' in result for result in results)
        assert all('safety_level' in result for result in results)
        assert all('cleanable' in result for result in results)

class TestSafetyChecker:
    """Test SafetyChecker functionality"""
    
    def test_safety_checker_initialization(self, test_settings):
        safety_checker = SafetyChecker(test_settings)
        assert safety_checker is not None
        assert len(safety_checker.critical_processes) > 0
        assert len(safety_checker.protected_directories) > 0
    
    def test_is_safe_to_delete_temp_file(self, test_settings, sample_files):
        safety_checker = SafetyChecker(test_settings)
        
        temp_file_info = {
            'path': str(sample_files['temp_files'][0]),
            'safety_level': 1  # Very safe
        }
        
        assert safety_checker.is_safe_to_delete(temp_file_info) == True
    
    def test_is_safe_to_delete_system_file(self, test_settings):
        safety_checker = SafetyChecker(test_settings)
        
        system_file_info = {
            'path': 'C:/Windows/System32/kernel32.dll',
            'safety_level': 5  # Dangerous
        }
        
        assert safety_checker.is_safe_to_delete(system_file_info) == False

class TestProgressTracker:
    """Test ProgressTracker functionality"""
    
    def test_progress_tracker_initialization(self):
        tracker = ProgressTracker()
        assert tracker is not None
        assert len(tracker.operations) == 0
    
    def test_create_operation(self, progress_tracker):
        operation_id = 'test_op'
        operation_name = 'Test Operation'
        
        progress_info = progress_tracker.create_operation(operation_id, operation_name, 100)
        
        assert progress_info.operation_id == operation_id
        assert progress_info.operation_name == operation_name
        assert progress_info.total == 100
        assert operation_id in progress_tracker.operations
    
    def test_start_operation(self, progress_tracker):
        operation_id = 'test_start'
        
        result = progress_tracker.start_operation(operation_id, 50)
        assert result == True
        
        progress = progress_tracker.get_progress(operation_id)
        assert progress.status == OperationStatus.RUNNING
        assert progress.start_time is not None
    
    def test_update_progress(self, progress_tracker):
        operation_id = 'test_update'
        progress_tracker.start_operation(operation_id, 100)
        
        result = progress_tracker.update_progress(operation_id, 25, 'Processing file 25')
        assert result == True
        
        progress = progress_tracker.get_progress(operation_id)
        assert progress.current == 25
        assert progress.percentage == 25.0
        assert progress.current_item == 'Processing file 25'
    
    def test_complete_operation(self, progress_tracker):
        operation_id = 'test_complete'
        progress_tracker.start_operation(operation_id, 100)
        
        result = progress_tracker.complete_operation(operation_id, True)
        assert result == True
        
        progress = progress_tracker.get_progress(operation_id)
        assert progress.status == OperationStatus.COMPLETED
        assert progress.end_time is not None