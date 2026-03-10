"""
Property-based tests to verify no broken references to user_logout exist.

These tests verify that after removing the user_logout module, no Python files
in the codebase contain imports or references to user_logout modules.
Each property test runs with a minimum of 100 iterations.
"""

import os
import re
import pytest
from pathlib import Path
from hypothesis import given, settings, strategies as st
from typing import List


def get_all_python_files() -> List[Path]:
    """
    Get all Python files in the codebase, excluding certain directories.
    
    Returns:
        List of Path objects for all Python files
    """
    excluded_dirs = {
        '__pycache__', '.aws-sam', 'venv', '.hypothesis', 
        'localstack-data', '.git', '.pytest_cache', 'user_logout'
    }
    
    python_files = []
    project_root = Path(__file__).parent.parent
    
    for py_file in project_root.rglob('*.py'):
        # Check if any excluded directory is in the path
        if not any(excluded_dir in py_file.parts for excluded_dir in excluded_dirs):
            python_files.append(py_file)
    
    return python_files


def check_file_for_logout_references(file_path: Path) -> tuple[bool, List[str]]:
    """
    Check a Python file for references to user_logout modules.
    
    Args:
        file_path: Path to the Python file to check
        
    Returns:
        Tuple of (has_references, list_of_reference_lines)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
    except Exception as e:
        # If we can't read the file, skip it
        return False, []
    
    references = []
    
    # Pattern 1: Import statements
    # Matches: import user_logout, from user_logout import X, from user_logout.module import Y
    import_pattern = re.compile(r'^\s*(import\s+user_logout|from\s+user_logout[\.\s])')
    
    # Pattern 2: Direct references to user_logout in code
    # Matches: user_logout.something, "user_logout", 'user_logout'
    reference_pattern = re.compile(r'user_logout')
    
    for line_num, line in enumerate(lines, start=1):
        # Skip comments
        if line.strip().startswith('#'):
            continue
            
        # Check for import statements
        if import_pattern.search(line):
            references.append(f"Line {line_num}: {line.strip()}")
        # Check for other references (but be careful about false positives)
        elif reference_pattern.search(line):
            # Only flag if it's not in a comment or docstring context
            # and not this test file itself
            if 'user_logout' in line and 'test_no_broken_logout_references' not in str(file_path):
                references.append(f"Line {line_num}: {line.strip()}")
    
    return len(references) > 0, references


class TestNoBrokenLogoutReferencesProperty:
    """Property-based tests for verifying no broken references to user_logout."""
    
    @settings(max_examples=100, deadline=None)
    @given(file_index=st.integers(min_value=0, max_value=1000))
    def test_no_user_logout_imports_in_codebase(self, file_index):
        """
        **Validates: Requirements 5.4**
        Feature: remove-logout-endpoint, Property 1: No Broken References to Logout
        
        For any Python file in the codebase (excluding user_logout/ directory itself),
        that file should not contain import statements or references to user_logout modules.
        
        This test verifies that:
        1. No Python files import from user_logout
        2. No Python files reference user_logout modules
        3. The codebase is clean after logout removal
        4. No broken imports remain that would cause runtime errors
        """
        # Get all Python files in the codebase
        python_files = get_all_python_files()
        
        # If we don't have any files, that's a problem
        assert len(python_files) > 0, "Should have Python files in the codebase"
        
        # Use modulo to cycle through files if file_index exceeds the number of files
        # This ensures we test all files across the 100+ iterations
        file_to_check = python_files[file_index % len(python_files)]
        
        # Check the file for user_logout references
        has_references, reference_lines = check_file_for_logout_references(file_to_check)
        
        # Verification: File should not contain any references to user_logout
        assert not has_references, (
            f"File {file_to_check} contains references to user_logout module:\n" +
            "\n".join(reference_lines) +
            "\n\nThe user_logout module has been removed. Please update this file to remove references."
        )
    
    def test_all_python_files_scanned(self):
        """
        Verification test to ensure we're scanning all Python files in the codebase.
        
        This is not a property test, but a sanity check to verify our file discovery
        mechanism is working correctly.
        """
        python_files = get_all_python_files()
        
        # We should have a reasonable number of Python files
        assert len(python_files) > 10, \
            f"Expected to find more than 10 Python files, found {len(python_files)}"
        
        # Verify we're not including excluded directories
        for py_file in python_files:
            assert '__pycache__' not in str(py_file), \
                f"Should not include __pycache__ files: {py_file}"
            assert 'venv' not in str(py_file), \
                f"Should not include venv files: {py_file}"
            assert 'user_logout' not in str(py_file), \
                f"Should not include user_logout files: {py_file}"
    
    def test_comprehensive_scan_all_files(self):
        """
        Comprehensive test that explicitly checks all Python files at once.
        
        This provides a clear summary of any issues across the entire codebase.
        """
        python_files = get_all_python_files()
        files_with_references = []
        
        for py_file in python_files:
            has_references, reference_lines = check_file_for_logout_references(py_file)
            if has_references:
                files_with_references.append({
                    'file': py_file,
                    'references': reference_lines
                })
        
        # Verification: No files should have references to user_logout
        if files_with_references:
            error_message = "Found references to user_logout in the following files:\n\n"
            for item in files_with_references:
                error_message += f"{item['file']}:\n"
                for ref in item['references']:
                    error_message += f"  {ref}\n"
                error_message += "\n"
            
            pytest.fail(error_message)
