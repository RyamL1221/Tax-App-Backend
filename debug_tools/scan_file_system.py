"""
File system scanner for detecting problematic files and directories.

This module scans Lambda function directories to identify issues that could
cause SAM build hangs, including symlinks, large files, cache directories,
and .gitignore violations.
"""

import os
import logging
from pathlib import Path
from typing import List, Tuple
import fnmatch

from models import FileIssue
from utils import (
    get_lambda_directories,
    get_project_root,
    format_file_size,
    is_cache_directory,
    get_relative_path
)


logger = logging.getLogger(__name__)


def scan_lambda_directories() -> List[FileIssue]:
    """
    Scan all Lambda function directories for problematic files.
    
    This function orchestrates all file system checks across all Lambda
    directories and aggregates the results.
    
    Returns:
        List of FileIssue objects describing problems found
        
    Notes:
        - Scans each Lambda directory recursively
        - Detects symlinks, large files, cache directories, and .gitignore violations
        - Continues scanning even if individual checks fail
    """
    logger.info("Starting file system scan of Lambda directories")
    all_issues = []
    
    lambda_dirs = get_lambda_directories()
    logger.info(f"Found {len(lambda_dirs)} Lambda directories to scan")
    
    for lambda_dir in lambda_dirs:
        logger.debug(f"Scanning directory: {lambda_dir}")
        
        # Detect symlinks
        symlinks = detect_symlinks(lambda_dir)
        for symlink_path in symlinks:
            all_issues.append(FileIssue(
                issue_type='symlink',
                path=get_relative_path(symlink_path),
                details=f"Symlink detected: {os.path.basename(symlink_path)} -> {os.readlink(symlink_path) if os.path.exists(symlink_path) else 'broken'}",
                severity='critical',
                fix_available=False
            ))
        
        # Find large files
        large_files = find_large_files(lambda_dir)
        for file_path, size_bytes in large_files:
            all_issues.append(FileIssue(
                issue_type='large_file',
                path=get_relative_path(file_path),
                details=f"Large file detected: {format_file_size(size_bytes)} (threshold: 10 MB)",
                severity='warning',
                fix_available=True
            ))
        
        # Find cache directories
        cache_dirs = find_cache_directories(lambda_dir)
        for cache_dir in cache_dirs:
            all_issues.append(FileIssue(
                issue_type='cache_dir',
                path=get_relative_path(cache_dir),
                details=f"Cache directory detected: {os.path.basename(cache_dir)}",
                severity='warning',
                fix_available=True
            ))
        
        # Check .gitignore compliance
        gitignore_violations = check_gitignore_compliance(lambda_dir)
        for violation_path in gitignore_violations:
            all_issues.append(FileIssue(
                issue_type='gitignore_violation',
                path=get_relative_path(violation_path),
                details=f"File should be in .gitignore: {os.path.basename(violation_path)}",
                severity='info',
                fix_available=True
            ))
    
    logger.info(f"File system scan complete. Found {len(all_issues)} issues")
    return all_issues


def detect_symlinks(directory: str) -> List[str]:
    """
    Detect symlinks that could cause infinite loops.
    
    Symlinks can cause SAM build to hang if they create circular references
    or point to large directory trees outside the Lambda function.
    
    Args:
        directory: Directory to scan for symlinks
        
    Returns:
        List of symlink paths found
        
    Notes:
        - Scans recursively but does not follow symlinks
        - Returns absolute paths to symlinks
        - Handles permission errors gracefully
    """
    logger.debug(f"Detecting symlinks in {directory}")
    symlinks = []
    
    try:
        for root, dirs, files in os.walk(directory, followlinks=False):
            # Check directories for symlinks
            for dir_name in dirs:
                dir_path = os.path.join(root, dir_name)
                if os.path.islink(dir_path):
                    symlinks.append(dir_path)
                    logger.warning(f"Found symlink directory: {dir_path}")
            
            # Check files for symlinks
            for file_name in files:
                file_path = os.path.join(root, file_name)
                if os.path.islink(file_path):
                    symlinks.append(file_path)
                    logger.warning(f"Found symlink file: {file_path}")
    
    except PermissionError as e:
        logger.error(f"Permission denied scanning {directory}: {e}")
    except Exception as e:
        logger.error(f"Error scanning {directory} for symlinks: {e}")
    
    return symlinks


def find_large_files(directory: str, size_threshold_mb: int = 10) -> List[Tuple[str, int]]:
    """
    Find files larger than threshold that shouldn't be copied.
    
    Large files can cause SAM build to hang or take excessive time during
    the CopySource phase. Files over 10MB are typically not needed in Lambda
    deployments.
    
    Args:
        directory: Directory to scan for large files
        size_threshold_mb: Size threshold in megabytes (default: 10)
        
    Returns:
        List of tuples (file_path, size_in_bytes) for files exceeding threshold
        
    Notes:
        - Scans recursively
        - Returns absolute paths
        - Handles permission errors gracefully
        - Skips symlinks to avoid following them
    """
    logger.debug(f"Finding files larger than {size_threshold_mb} MB in {directory}")
    large_files = []
    threshold_bytes = size_threshold_mb * 1024 * 1024
    
    try:
        for root, dirs, files in os.walk(directory, followlinks=False):
            for file_name in files:
                file_path = os.path.join(root, file_name)
                
                # Skip symlinks
                if os.path.islink(file_path):
                    continue
                
                try:
                    size = os.path.getsize(file_path)
                    if size > threshold_bytes:
                        large_files.append((file_path, size))
                        logger.warning(f"Found large file: {file_path} ({format_file_size(size)})")
                except OSError as e:
                    logger.error(f"Error getting size of {file_path}: {e}")
    
    except PermissionError as e:
        logger.error(f"Permission denied scanning {directory}: {e}")
    except Exception as e:
        logger.error(f"Error scanning {directory} for large files: {e}")
    
    return large_files


def find_cache_directories(directory: str) -> List[str]:
    """
    Find cache directories that shouldn't be copied.
    
    Cache directories like __pycache__, .pytest_cache, and .aws-sam should
    not be included in Lambda deployments and can cause build issues.
    
    Args:
        directory: Directory to scan for cache directories
        
    Returns:
        List of cache directory paths found
        
    Notes:
        - Scans recursively
        - Returns absolute paths
        - Detects common Python and build cache directories
        - Does not follow symlinks
    """
    logger.debug(f"Finding cache directories in {directory}")
    cache_dirs = []
    
    try:
        for root, dirs, files in os.walk(directory, followlinks=False):
            for dir_name in dirs:
                if is_cache_directory(dir_name):
                    dir_path = os.path.join(root, dir_name)
                    cache_dirs.append(dir_path)
                    logger.warning(f"Found cache directory: {dir_path}")
    
    except PermissionError as e:
        logger.error(f"Permission denied scanning {directory}: {e}")
    except Exception as e:
        logger.error(f"Error scanning {directory} for cache directories: {e}")
    
    return cache_dirs


def check_gitignore_compliance(directory: str) -> List[str]:
    """
    Find files that should be ignored but aren't in .gitignore.
    
    Files matching common ignore patterns (like *.pyc, .DS_Store) should be
    in .gitignore to prevent them from being included in the repository and
    Lambda deployments.
    
    Args:
        directory: Directory to check for .gitignore violations
        
    Returns:
        List of file paths that should be ignored
        
    Notes:
        - Checks against common ignore patterns
        - Returns absolute paths
        - Does not parse .gitignore file (uses hardcoded patterns)
        - Focuses on files that commonly cause build issues
    """
    logger.debug(f"Checking .gitignore compliance in {directory}")
    violations = []
    
    # Common patterns that should be ignored
    ignore_patterns = [
        '*.pyc',
        '*.pyo',
        '*.pyd',
        '.DS_Store',
        'Thumbs.db',
        '*.swp',
        '*.swo',
        '*~',
        '.env',
        '*.log',
        '*.egg-info',
        'dist/',
        'build/',
        '*.so',
        '*.dylib',
        '*.dll'
    ]
    
    try:
        for root, dirs, files in os.walk(directory, followlinks=False):
            # Skip cache directories
            dirs[:] = [d for d in dirs if not is_cache_directory(d)]
            
            for file_name in files:
                # Check if file matches any ignore pattern
                for pattern in ignore_patterns:
                    if fnmatch.fnmatch(file_name, pattern):
                        file_path = os.path.join(root, file_name)
                        violations.append(file_path)
                        logger.info(f"Found file that should be ignored: {file_path}")
                        break
    
    except PermissionError as e:
        logger.error(f"Permission denied scanning {directory}: {e}")
    except Exception as e:
        logger.error(f"Error checking .gitignore compliance in {directory}: {e}")
    
    return violations


def _parse_gitignore(gitignore_path: str) -> List[str]:
    """
    Parse .gitignore file and return list of patterns.
    
    This is a helper function for more advanced .gitignore compliance checking.
    Currently not used by check_gitignore_compliance() but available for
    future enhancements.
    
    Args:
        gitignore_path: Path to .gitignore file
        
    Returns:
        List of ignore patterns from .gitignore
        
    Notes:
        - Skips comments and empty lines
        - Does not handle negation patterns (!)
        - Does not handle directory-specific patterns
    """
    patterns = []
    
    try:
        with open(gitignore_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if line and not line.startswith('#'):
                    patterns.append(line)
    except FileNotFoundError:
        logger.debug(f".gitignore not found at {gitignore_path}")
    except Exception as e:
        logger.error(f"Error parsing .gitignore at {gitignore_path}: {e}")
    
    return patterns


def _matches_gitignore_pattern(filepath: str, pattern: str, base_path: str) -> bool:
    """
    Check if filepath matches a .gitignore pattern.
    
    This is a helper function for more advanced .gitignore compliance checking.
    Currently not used but available for future enhancements.
    
    Args:
        filepath: Path to file to check
        pattern: .gitignore pattern
        base_path: Base directory for relative patterns
        
    Returns:
        True if filepath matches pattern
        
    Notes:
        - Simplified matching, does not handle all .gitignore syntax
        - Does not handle negation patterns (!)
        - Does not handle ** glob patterns
    """
    # Get relative path from base
    try:
        rel_path = os.path.relpath(filepath, base_path)
    except ValueError:
        return False
    
    # Simple pattern matching
    if pattern.endswith('/'):
        # Directory pattern
        return fnmatch.fnmatch(rel_path + '/', pattern) or fnmatch.fnmatch(os.path.dirname(rel_path) + '/', pattern)
    else:
        # File pattern
        return fnmatch.fnmatch(rel_path, pattern) or fnmatch.fnmatch(os.path.basename(filepath), pattern)
