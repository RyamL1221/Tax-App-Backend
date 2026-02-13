#!/usr/bin/env python3
"""
Test script to verify cache directory detection functionality.

This script tests the cache directory detection in verify_sam_build.py
to ensure it correctly identifies __pycache__, .pytest_cache, and .hypothesis
directories and includes appropriate cleanup suggestions in error messages.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from debug_tools.verify_sam_build import check_cache_directories
from debug_tools.build_feedback_generator import generate_build_feedback
from debug_tools.models import BuildStatus


def test_no_cache_directories():
    """Test detection when no cache directories exist."""
    print("Test 1: No cache directories")
    print("-" * 50)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a simple Lambda directory with no cache
        lambda_dir = os.path.join(tmpdir, "test_lambda")
        os.makedirs(lambda_dir)
        
        # Create some Python files
        with open(os.path.join(lambda_dir, "app.py"), "w") as f:
            f.write("# Lambda handler\n")
        
        cache_present, cache_dirs = check_cache_directories(lambda_dir)
        
        print(f"  Lambda dir: {lambda_dir}")
        print(f"  Cache present: {cache_present}")
        print(f"  Cache dirs found: {cache_dirs}")
        
        assert not cache_present, "Should not detect cache when none exist"
        assert len(cache_dirs) == 0, "Should find no cache directories"
        print("  ✅ PASSED\n")


def test_pycache_directory():
    """Test detection of __pycache__ directory."""
    print("Test 2: __pycache__ directory")
    print("-" * 50)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        lambda_dir = os.path.join(tmpdir, "test_lambda")
        os.makedirs(lambda_dir)
        
        # Create __pycache__ directory
        pycache_dir = os.path.join(lambda_dir, "__pycache__")
        os.makedirs(pycache_dir)
        
        cache_present, cache_dirs = check_cache_directories(lambda_dir)
        
        print(f"  Lambda dir: {lambda_dir}")
        print(f"  Cache present: {cache_present}")
        print(f"  Cache dirs found: {cache_dirs}")
        
        assert cache_present, "Should detect __pycache__"
        assert "__pycache__" in cache_dirs, "Should find __pycache__ in list"
        assert len(cache_dirs) == 1, "Should find exactly one cache directory"
        print("  ✅ PASSED\n")


def test_pytest_cache_directory():
    """Test detection of .pytest_cache directory."""
    print("Test 3: .pytest_cache directory")
    print("-" * 50)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        lambda_dir = os.path.join(tmpdir, "test_lambda")
        os.makedirs(lambda_dir)
        
        # Create .pytest_cache directory
        pytest_cache_dir = os.path.join(lambda_dir, ".pytest_cache")
        os.makedirs(pytest_cache_dir)
        
        cache_present, cache_dirs = check_cache_directories(lambda_dir)
        
        print(f"  Lambda dir: {lambda_dir}")
        print(f"  Cache present: {cache_present}")
        print(f"  Cache dirs found: {cache_dirs}")
        
        assert cache_present, "Should detect .pytest_cache"
        assert ".pytest_cache" in cache_dirs, "Should find .pytest_cache in list"
        assert len(cache_dirs) == 1, "Should find exactly one cache directory"
        print("  ✅ PASSED\n")


def test_hypothesis_directory():
    """Test detection of .hypothesis directory."""
    print("Test 4: .hypothesis directory")
    print("-" * 50)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        lambda_dir = os.path.join(tmpdir, "test_lambda")
        os.makedirs(lambda_dir)
        
        # Create .hypothesis directory
        hypothesis_dir = os.path.join(lambda_dir, ".hypothesis")
        os.makedirs(hypothesis_dir)
        
        cache_present, cache_dirs = check_cache_directories(lambda_dir)
        
        print(f"  Lambda dir: {lambda_dir}")
        print(f"  Cache present: {cache_present}")
        print(f"  Cache dirs found: {cache_dirs}")
        
        assert cache_present, "Should detect .hypothesis"
        assert ".hypothesis" in cache_dirs, "Should find .hypothesis in list"
        assert len(cache_dirs) == 1, "Should find exactly one cache directory"
        print("  ✅ PASSED\n")


def test_multiple_cache_directories():
    """Test detection of multiple cache directories."""
    print("Test 5: Multiple cache directories")
    print("-" * 50)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        lambda_dir = os.path.join(tmpdir, "test_lambda")
        os.makedirs(lambda_dir)
        
        # Create all three cache directories
        os.makedirs(os.path.join(lambda_dir, "__pycache__"))
        os.makedirs(os.path.join(lambda_dir, ".pytest_cache"))
        os.makedirs(os.path.join(lambda_dir, ".hypothesis"))
        
        cache_present, cache_dirs = check_cache_directories(lambda_dir)
        
        print(f"  Lambda dir: {lambda_dir}")
        print(f"  Cache present: {cache_present}")
        print(f"  Cache dirs found: {cache_dirs}")
        
        assert cache_present, "Should detect cache directories"
        assert len(cache_dirs) == 3, "Should find all three cache directories"
        assert "__pycache__" in cache_dirs, "Should find __pycache__"
        assert ".pytest_cache" in cache_dirs, "Should find .pytest_cache"
        assert ".hypothesis" in cache_dirs, "Should find .hypothesis"
        print("  ✅ PASSED\n")


def test_nonexistent_directory():
    """Test handling of nonexistent directory."""
    print("Test 6: Nonexistent directory")
    print("-" * 50)
    
    nonexistent_dir = "/tmp/nonexistent_lambda_dir_12345"
    
    cache_present, cache_dirs = check_cache_directories(nonexistent_dir)
    
    print(f"  Lambda dir: {nonexistent_dir}")
    print(f"  Cache present: {cache_present}")
    print(f"  Cache dirs found: {cache_dirs}")
    
    assert not cache_present, "Should not detect cache for nonexistent directory"
    assert len(cache_dirs) == 0, "Should find no cache directories"
    print("  ✅ PASSED\n")


def test_cache_cleanup_suggestion_in_error_message():
    """Test that cache cleanup suggestions appear in error messages."""
    print("Test 7: Cache cleanup suggestion in error message")
    print("-" * 50)
    
    # Create a BuildStatus with cache directories present
    status = BuildStatus(
        exists=False,
        up_to_date=False,
        handler_present=False,
        lambda_name="TestFunction",
        lambda_dir="test_lambda",
        handler_file="app.py",
        source_mtime=1234567890.0,
        build_mtime=None,
        cache_dirs_present=True,
        cache_dirs_found=["__pycache__", ".pytest_cache"]
    )
    
    message = generate_build_feedback(status, verbose=False)
    
    print("  Generated error message:")
    print("  " + "\n  ".join(message.split("\n")))
    print()
    
    # Verify the message contains cache warnings and cleanup suggestions
    assert "Cache directories found" in message, "Should mention cache directories"
    assert "__pycache__" in message, "Should list __pycache__"
    assert ".pytest_cache" in message, "Should list .pytest_cache"
    assert "apply_fixes.py --remove-cache" in message, "Should suggest cache cleanup command"
    assert "Consider running cache cleanup first" in message, "Should suggest cleanup before build"
    
    print("  ✅ PASSED - Message contains cache cleanup suggestions\n")


def test_no_cache_suggestion_when_no_cache():
    """Test that cache suggestions don't appear when no cache exists."""
    print("Test 8: No cache suggestion when no cache present")
    print("-" * 50)
    
    # Create a BuildStatus without cache directories
    status = BuildStatus(
        exists=False,
        up_to_date=False,
        handler_present=False,
        lambda_name="TestFunction",
        lambda_dir="test_lambda",
        handler_file="app.py",
        source_mtime=1234567890.0,
        build_mtime=None,
        cache_dirs_present=False,
        cache_dirs_found=[]
    )
    
    message = generate_build_feedback(status, verbose=False)
    
    print("  Generated error message:")
    print("  " + "\n  ".join(message.split("\n")))
    print()
    
    # Verify the message does NOT contain cache warnings
    assert "Cache directories found" not in message, "Should not mention cache directories"
    assert "apply_fixes.py --remove-cache" not in message, "Should not suggest cache cleanup"
    
    print("  ✅ PASSED - Message does not contain cache suggestions\n")


def test_cache_suggestion_format():
    """Test the exact format of cache cleanup suggestions."""
    print("Test 9: Cache suggestion format verification")
    print("-" * 50)
    
    status = BuildStatus(
        exists=True,
        up_to_date=False,
        handler_present=True,
        lambda_name="TestFunction",
        lambda_dir="test_lambda",
        handler_file="app.py",
        source_mtime=1234567890.0,
        build_mtime=1234567800.0,  # Older than source
        cache_dirs_present=True,
        cache_dirs_found=["__pycache__", ".pytest_cache", ".hypothesis"]
    )
    
    message = generate_build_feedback(status, verbose=False)
    
    print("  Generated error message:")
    print("  " + "\n  ".join(message.split("\n")))
    print()
    
    # Verify specific format requirements
    lines = message.split("\n")
    
    # Check for cache warning section
    cache_warning_found = False
    cleanup_command_found = False
    
    for line in lines:
        if "Cache directories found:" in line:
            cache_warning_found = True
            # Verify all cache dirs are listed
            assert "__pycache__" in line, "Should list __pycache__"
            assert ".pytest_cache" in line, "Should list .pytest_cache"
            assert ".hypothesis" in line, "Should list .hypothesis"
        
        if "python debug_tools/apply_fixes.py --remove-cache" in line:
            cleanup_command_found = True
    
    assert cache_warning_found, "Should have cache warning line"
    assert cleanup_command_found, "Should have cleanup command"
    
    print("  ✅ PASSED - Cache suggestion format is correct\n")


def main():
    """Run all tests."""
    print("=" * 50)
    print("Cache Directory Detection Tests")
    print("=" * 50)
    print()
    
    tests = [
        test_no_cache_directories,
        test_pycache_directory,
        test_pytest_cache_directory,
        test_hypothesis_directory,
        test_multiple_cache_directories,
        test_nonexistent_directory,
        test_cache_cleanup_suggestion_in_error_message,
        test_no_cache_suggestion_when_no_cache,
        test_cache_suggestion_format,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"  ❌ FAILED: {e}\n")
            failed += 1
        except Exception as e:
            print(f"  ❌ ERROR: {e}\n")
            failed += 1
    
    print("=" * 50)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 50)
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
