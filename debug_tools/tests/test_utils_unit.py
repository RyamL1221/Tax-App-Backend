"""
Unit tests for utility functions.

Tests the shared utility functions used across diagnostic tools.
"""

import os
import pytest
import tempfile
from pathlib import Path
from debug_tools.utils import (
    format_file_size,
    is_cache_directory,
    create_timestamp_string,
    safe_read_file,
    safe_write_file,
    get_relative_path
)


class TestFormatFileSize:
    """Tests for format_file_size function."""
    
    def test_bytes(self):
        """Test formatting bytes."""
        assert format_file_size(500) == "500.0 B"
        assert format_file_size(1023) == "1023.0 B"
    
    def test_kilobytes(self):
        """Test formatting kilobytes."""
        assert format_file_size(1024) == "1.0 KB"
        assert format_file_size(1536) == "1.5 KB"
        assert format_file_size(10240) == "10.0 KB"
    
    def test_megabytes(self):
        """Test formatting megabytes."""
        assert format_file_size(1048576) == "1.0 MB"
        assert format_file_size(10485760) == "10.0 MB"
        assert format_file_size(15728640) == "15.0 MB"
    
    def test_gigabytes(self):
        """Test formatting gigabytes."""
        assert format_file_size(1073741824) == "1.0 GB"
        assert format_file_size(2147483648) == "2.0 GB"
    
    def test_zero_bytes(self):
        """Test formatting zero bytes."""
        assert format_file_size(0) == "0.0 B"


class TestIsCacheDirectory:
    """Tests for is_cache_directory function."""
    
    def test_pycache_directory(self):
        """Test __pycache__ is identified as cache directory."""
        assert is_cache_directory('__pycache__')
    
    def test_pytest_cache_directory(self):
        """Test .pytest_cache is identified as cache directory."""
        assert is_cache_directory('.pytest_cache')
    
    def test_aws_sam_directory(self):
        """Test .aws-sam is identified as cache directory."""
        assert is_cache_directory('.aws-sam')
    
    def test_node_modules_directory(self):
        """Test node_modules is identified as cache directory."""
        assert is_cache_directory('node_modules')
    
    def test_mypy_cache_directory(self):
        """Test .mypy_cache is identified as cache directory."""
        assert is_cache_directory('.mypy_cache')
    
    def test_hypothesis_directory(self):
        """Test .hypothesis is identified as cache directory."""
        assert is_cache_directory('.hypothesis')
    
    def test_regular_directory(self):
        """Test regular directory is not identified as cache."""
        assert not is_cache_directory('src')
        assert not is_cache_directory('tests')
        assert not is_cache_directory('user_login')
        assert not is_cache_directory('my_module')
    
    def test_partial_match_not_cache(self):
        """Test partial matches are not identified as cache."""
        assert not is_cache_directory('__pycache__backup')
        assert not is_cache_directory('my__pycache__')
        assert not is_cache_directory('.pytest_cache_old')


class TestCreateTimestampString:
    """Tests for create_timestamp_string function."""
    
    def test_timestamp_format(self):
        """Test timestamp string has correct format."""
        timestamp = create_timestamp_string()
        
        # Should be in format YYYYMMDD_HHMMSS
        assert len(timestamp) == 15
        assert timestamp[8] == '_'
        
        # Should be all digits except underscore
        assert timestamp[:8].isdigit()
        assert timestamp[9:].isdigit()
    
    def test_timestamp_is_current(self):
        """Test timestamp represents current time."""
        from datetime import datetime
        
        timestamp = create_timestamp_string()
        year = timestamp[:4]
        month = timestamp[4:6]
        day = timestamp[6:8]
        
        now = datetime.now()
        assert year == str(now.year)
        assert month == f"{now.month:02d}"
        assert day == f"{now.day:02d}"


class TestSafeReadFile:
    """Tests for safe_read_file function."""
    
    def test_read_valid_utf8_file(self):
        """Test reading a valid UTF-8 file."""
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False) as f:
            f.write('Hello, World!\nThis is a test.')
            temp_path = f.name
        
        try:
            content = safe_read_file(temp_path)
            assert content == 'Hello, World!\nThis is a test.'
        finally:
            os.unlink(temp_path)
    
    def test_read_nonexistent_file(self):
        """Test reading a nonexistent file returns None."""
        content = safe_read_file('/nonexistent/path/to/file.txt')
        assert content is None
    
    def test_read_file_with_unicode(self):
        """Test reading file with unicode characters."""
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False) as f:
            f.write('Hello 世界! 🌍')
            temp_path = f.name
        
        try:
            content = safe_read_file(temp_path)
            assert content == 'Hello 世界! 🌍'
        finally:
            os.unlink(temp_path)


class TestSafeWriteFile:
    """Tests for safe_write_file function."""
    
    def test_write_valid_file(self):
        """Test writing to a valid file."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name
        
        try:
            success = safe_write_file(temp_path, 'Test content')
            assert success
            
            with open(temp_path, 'r', encoding='utf-8') as f:
                content = f.read()
            assert content == 'Test content'
        finally:
            os.unlink(temp_path)
    
    def test_write_file_with_unicode(self):
        """Test writing file with unicode characters."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name
        
        try:
            success = safe_write_file(temp_path, 'Hello 世界! 🌍')
            assert success
            
            with open(temp_path, 'r', encoding='utf-8') as f:
                content = f.read()
            assert content == 'Hello 世界! 🌍'
        finally:
            os.unlink(temp_path)
    
    def test_write_to_invalid_path(self):
        """Test writing to invalid path returns False."""
        success = safe_write_file('/nonexistent/directory/file.txt', 'content')
        assert not success


class TestGetRelativePath:
    """Tests for get_relative_path function."""
    
    def test_relative_path_from_parent(self):
        """Test getting relative path from parent directory."""
        base = '/home/user/project'
        filepath = '/home/user/project/src/module.py'
        
        result = get_relative_path(filepath, base)
        assert result == 'src/module.py' or result == 'src\\module.py'
    
    def test_relative_path_same_directory(self):
        """Test getting relative path for file in same directory."""
        base = '/home/user/project'
        filepath = '/home/user/project/file.txt'
        
        result = get_relative_path(filepath, base)
        assert result == 'file.txt'
    
    def test_relative_path_with_parent_dirs(self):
        """Test getting relative path that goes up directories."""
        base = '/home/user/project/src'
        filepath = '/home/user/project/tests/test.py'
        
        result = get_relative_path(filepath, base)
        # Should contain .. to go up one level
        assert '..' in result
