"""
Test script for timestamp comparison utilities in verify_sam_build.py

This script tests the timestamp comparison functions to ensure they:
1. Correctly detect source file modification times
2. Correctly detect build artifact modification times
3. Handle missing files gracefully
4. Compare timestamps accurately
"""

import os
import sys
import tempfile
import shutil
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from debug_tools.verify_sam_build import (
    get_source_modification_time,
    get_build_modification_time,
    check_build_artifacts
)
from debug_tools.utils import get_project_root


def test_source_modification_time_basic():
    """Test basic source modification time detection."""
    print("\n=== Test 1: Basic Source Modification Time ===")
    
    # Test with user_login directory
    try:
        mtime = get_source_modification_time("user_login")
        print(f"✅ Successfully got source mtime for user_login: {mtime}")
        assert mtime > 0, "Modification time should be positive"
        print(f"   Timestamp: {mtime}")
        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False


def test_source_modification_time_missing_dir():
    """Test handling of missing directory."""
    print("\n=== Test 2: Missing Directory Handling ===")
    
    try:
        mtime = get_source_modification_time("nonexistent_lambda")
        print(f"❌ Should have raised FileNotFoundError, got: {mtime}")
        return False
    except FileNotFoundError as e:
        print(f"✅ Correctly raised FileNotFoundError: {e}")
        return True
    except Exception as e:
        print(f"❌ Unexpected exception: {e}")
        return False


def test_source_modification_time_no_python_files():
    """Test handling of directory with no Python files."""
    print("\n=== Test 3: No Python Files Handling ===")
    
    # Create temporary directory with no Python files
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a non-Python file
        test_file = os.path.join(tmpdir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("test")
        
        try:
            mtime = get_source_modification_time(tmpdir)
            print(f"❌ Should have raised ValueError, got: {mtime}")
            return False
        except ValueError as e:
            print(f"✅ Correctly raised ValueError: {e}")
            return True
        except Exception as e:
            print(f"❌ Unexpected exception: {e}")
            return False


def test_source_modification_time_excludes_tests():
    """Test that tests directory is excluded from timestamp check."""
    print("\n=== Test 4: Tests Directory Exclusion ===")
    
    # Create temporary directory structure
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create main Python file
        main_file = os.path.join(tmpdir, "app.py")
        with open(main_file, 'w') as f:
            f.write("# main file")
        
        time.sleep(0.1)  # Ensure different timestamps
        
        # Create tests directory with newer file
        tests_dir = os.path.join(tmpdir, "tests")
        os.makedirs(tests_dir)
        test_file = os.path.join(tests_dir, "test_app.py")
        with open(test_file, 'w') as f:
            f.write("# test file")
        
        try:
            mtime = get_source_modification_time(tmpdir)
            main_mtime = os.path.getmtime(main_file)
            test_mtime = os.path.getmtime(test_file)
            
            print(f"   Main file mtime: {main_mtime}")
            print(f"   Test file mtime: {test_mtime}")
            print(f"   Returned mtime: {mtime}")
            
            # The returned mtime should be from main file, not test file
            if abs(mtime - main_mtime) < 0.01:  # Allow small floating point difference
                print(f"✅ Correctly excluded tests directory")
                return True
            else:
                print(f"❌ Did not exclude tests directory")
                return False
        except Exception as e:
            print(f"❌ Unexpected exception: {e}")
            return False


def test_source_modification_time_excludes_cache():
    """Test that cache directories are excluded from timestamp check."""
    print("\n=== Test 5: Cache Directory Exclusion ===")
    
    # Create temporary directory structure
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create main Python file
        main_file = os.path.join(tmpdir, "app.py")
        with open(main_file, 'w') as f:
            f.write("# main file")
        
        time.sleep(0.1)  # Ensure different timestamps
        
        # Create __pycache__ directory with newer file
        cache_dir = os.path.join(tmpdir, "__pycache__")
        os.makedirs(cache_dir)
        cache_file = os.path.join(cache_dir, "app.cpython-314.pyc")
        with open(cache_file, 'w') as f:
            f.write("# cache file")
        
        try:
            mtime = get_source_modification_time(tmpdir)
            main_mtime = os.path.getmtime(main_file)
            cache_mtime = os.path.getmtime(cache_file)
            
            print(f"   Main file mtime: {main_mtime}")
            print(f"   Cache file mtime: {cache_mtime}")
            print(f"   Returned mtime: {mtime}")
            
            # The returned mtime should be from main file, not cache file
            if abs(mtime - main_mtime) < 0.01:  # Allow small floating point difference
                print(f"✅ Correctly excluded cache directory")
                return True
            else:
                print(f"❌ Did not exclude cache directory")
                return False
        except Exception as e:
            print(f"❌ Unexpected exception: {e}")
            return False


def test_build_modification_time_missing():
    """Test handling of missing build directory."""
    print("\n=== Test 6: Missing Build Directory Handling ===")
    
    try:
        mtime = get_build_modification_time("NonexistentFunction")
        if mtime is None:
            print(f"✅ Correctly returned None for missing build directory")
            return True
        else:
            print(f"❌ Should have returned None, got: {mtime}")
            return False
    except Exception as e:
        print(f"❌ Unexpected exception: {e}")
        return False


def test_build_modification_time_existing():
    """Test build modification time for existing build."""
    print("\n=== Test 7: Existing Build Directory ===")
    
    project_root = get_project_root()
    build_dir = os.path.join(project_root, '.aws-sam', 'build')
    
    if not os.path.isdir(build_dir):
        print(f"⚠️  Skipped: No .aws-sam/build directory found")
        print(f"   Run 'sam build' to create build artifacts")
        return True  # Not a failure, just skipped
    
    # Find first Lambda function in build directory
    lambda_dirs = [d for d in os.listdir(build_dir) 
                   if os.path.isdir(os.path.join(build_dir, d))]
    
    if not lambda_dirs:
        print(f"⚠️  Skipped: No Lambda functions in build directory")
        return True  # Not a failure, just skipped
    
    lambda_name = lambda_dirs[0]
    
    try:
        mtime = get_build_modification_time(lambda_name)
        if mtime is not None and mtime > 0:
            print(f"✅ Successfully got build mtime for {lambda_name}: {mtime}")
            return True
        else:
            print(f"❌ Invalid mtime returned: {mtime}")
            return False
    except Exception as e:
        print(f"❌ Unexpected exception: {e}")
        return False


def test_timestamp_comparison_logic():
    """Test the timestamp comparison logic in check_build_artifacts."""
    print("\n=== Test 8: Timestamp Comparison Logic ===")
    
    # Test with user_login if it exists
    try:
        status = check_build_artifacts("user_login")
        
        print(f"   Lambda: {status.lambda_name}")
        print(f"   Build exists: {status.exists}")
        print(f"   Source mtime: {status.source_mtime}")
        print(f"   Build mtime: {status.build_mtime}")
        print(f"   Up-to-date: {status.up_to_date}")
        
        # Verify logic consistency
        if status.exists and status.build_mtime is not None:
            expected_up_to_date = status.build_mtime >= status.source_mtime
            if status.up_to_date == expected_up_to_date:
                print(f"✅ Timestamp comparison logic is correct")
                return True
            else:
                print(f"❌ Timestamp comparison logic is incorrect")
                print(f"   Expected up_to_date: {expected_up_to_date}")
                print(f"   Actual up_to_date: {status.up_to_date}")
                return False
        elif not status.exists:
            if not status.up_to_date:
                print(f"✅ Correctly marked as not up-to-date when build doesn't exist")
                return True
            else:
                print(f"❌ Should be marked as not up-to-date when build doesn't exist")
                return False
        else:
            print(f"⚠️  Unexpected state: exists={status.exists}, build_mtime={status.build_mtime}")
            return True  # Not a failure, just unexpected
            
    except Exception as e:
        print(f"❌ Unexpected exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_multiple_python_files():
    """Test that the most recent modification time is returned."""
    print("\n=== Test 9: Multiple Python Files - Most Recent ===")
    
    # Create temporary directory with multiple Python files
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create first file
        file1 = os.path.join(tmpdir, "module1.py")
        with open(file1, 'w') as f:
            f.write("# module 1")
        
        time.sleep(0.1)  # Ensure different timestamps
        
        # Create second file (newer)
        file2 = os.path.join(tmpdir, "module2.py")
        with open(file2, 'w') as f:
            f.write("# module 2")
        
        time.sleep(0.1)  # Ensure different timestamps
        
        # Create third file (newest)
        file3 = os.path.join(tmpdir, "module3.py")
        with open(file3, 'w') as f:
            f.write("# module 3")
        
        try:
            mtime = get_source_modification_time(tmpdir)
            file3_mtime = os.path.getmtime(file3)
            
            print(f"   File 1 mtime: {os.path.getmtime(file1)}")
            print(f"   File 2 mtime: {os.path.getmtime(file2)}")
            print(f"   File 3 mtime: {file3_mtime}")
            print(f"   Returned mtime: {mtime}")
            
            # The returned mtime should be from the newest file
            if abs(mtime - file3_mtime) < 0.01:  # Allow small floating point difference
                print(f"✅ Correctly returned most recent modification time")
                return True
            else:
                print(f"❌ Did not return most recent modification time")
                return False
        except Exception as e:
            print(f"❌ Unexpected exception: {e}")
            return False


def run_all_tests():
    """Run all timestamp comparison tests."""
    print("=" * 70)
    print("TIMESTAMP COMPARISON UTILITIES TEST SUITE")
    print("=" * 70)
    
    tests = [
        test_source_modification_time_basic,
        test_source_modification_time_missing_dir,
        test_source_modification_time_no_python_files,
        test_source_modification_time_excludes_tests,
        test_source_modification_time_excludes_cache,
        test_build_modification_time_missing,
        test_build_modification_time_existing,
        test_timestamp_comparison_logic,
        test_multiple_python_files,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n❌ Test crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\nTotal tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    
    if passed == total:
        print("\n✅ All tests passed!")
        return 0
    else:
        print(f"\n❌ {total - passed} test(s) failed")
        return 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
