"""
Automated fix tool for resolving SAM build hang issues.

This module provides functions to automatically fix common issues that cause
SAM build hangs, including removing cache directories, updating .gitignore,
and creating backups before making changes.
"""

import os
import shutil
import logging
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from models import DiagnosticReport, FileIssue, FixReport
from utils import (
    get_project_root,
    ensure_directory_exists,
    safe_read_file,
    safe_write_file,
    create_timestamp_string,
    get_relative_path
)


logger = logging.getLogger(__name__)


def apply_all_fixes(report: DiagnosticReport, dry_run: bool = True) -> FixReport:
    """
    Apply fixes for all detected issues in the diagnostic report.
    
    This function orchestrates the application of all available automated fixes
    based on the issues found in the diagnostic report. It creates a backup
    before making any changes and tracks the success/failure of each fix.
    
    Args:
        report: Diagnostic report containing detected issues
        dry_run: If True, only show what would be fixed without making changes
        
    Returns:
        FixReport describing what was fixed and the results
        
    Notes:
        - Creates backup before making any changes (unless dry_run=True)
        - Continues applying fixes even if some fail
        - Logs detailed information about each fix attempt
        - Symlinks are reported but not automatically fixed
    """
    logger.info(f"Starting fix application (dry_run={dry_run})")
    
    fix_report = FixReport(dry_run=dry_run)
    
    if not report.has_issues:
        logger.info("No issues to fix")
        fix_report.details.append("No issues found in diagnostic report")
        return fix_report
    
    # Create backup before making changes (unless dry_run)
    if not dry_run:
        try:
            backup_path = create_backup()
            fix_report.backup_path = backup_path
            fix_report.details.append(f"Created backup at: {backup_path}")
            logger.info(f"Backup created at: {backup_path}")
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            fix_report.details.append(f"ERROR: Failed to create backup: {e}")
            fix_report.fixes_failed += 1
            # Don't proceed without backup
            return fix_report
    else:
        fix_report.details.append("DRY RUN: No backup created (no changes will be made)")
    
    # Collect fixable issues by type
    cache_dirs = [issue.path for issue in report.file_issues 
                  if issue.issue_type == 'cache_dir' and issue.fix_available]
    
    large_files = [issue.path for issue in report.file_issues 
                   if issue.issue_type == 'large_file' and issue.fix_available]
    
    gitignore_violations = [issue.path for issue in report.file_issues 
                           if issue.issue_type == 'gitignore_violation' and issue.fix_available]
    
    symlinks = [issue.path for issue in report.file_issues 
                if issue.issue_type == 'symlink']
    
    # Apply fixes for cache directories
    if cache_dirs:
        logger.info(f"Removing {len(cache_dirs)} cache directories")
        try:
            removed_count = remove_cache_directories(cache_dirs, dry_run=dry_run)
            fix_report.fixes_applied += removed_count
            if dry_run:
                fix_report.details.append(f"DRY RUN: Would remove {removed_count} cache directories")
            else:
                fix_report.details.append(f"Removed {removed_count} cache directories")
        except Exception as e:
            logger.error(f"Failed to remove cache directories: {e}")
            fix_report.fixes_failed += len(cache_dirs)
            fix_report.details.append(f"ERROR: Failed to remove cache directories: {e}")
    
    # Update .gitignore for large files and violations
    files_to_ignore = large_files + gitignore_violations
    if files_to_ignore:
        logger.info(f"Adding {len(files_to_ignore)} files to .gitignore")
        try:
            added_count = update_gitignore(files_to_ignore, dry_run=dry_run)
            fix_report.fixes_applied += added_count
            if dry_run:
                fix_report.details.append(f"DRY RUN: Would add {added_count} patterns to .gitignore")
            else:
                fix_report.details.append(f"Added {added_count} patterns to .gitignore")
        except Exception as e:
            logger.error(f"Failed to update .gitignore: {e}")
            fix_report.fixes_failed += len(files_to_ignore)
            fix_report.details.append(f"ERROR: Failed to update .gitignore: {e}")
    
    # Report symlinks (no automatic fix)
    if symlinks:
        fix_report.details.append(f"MANUAL ACTION REQUIRED: {len(symlinks)} symlinks detected")
        fix_report.details.append("Symlinks must be manually reviewed and removed:")
        for symlink in symlinks:
            fix_report.details.append(f"  - {symlink}")
    
    # Report dependency and config issues (no automatic fix yet)
    if report.dependency_issues:
        fix_report.details.append(f"MANUAL ACTION REQUIRED: {len(report.dependency_issues)} dependency issues")
        for issue in report.dependency_issues:
            if issue.suggested_fix:
                fix_report.details.append(f"  - {issue.lambda_function}/{issue.package_name}: {issue.suggested_fix}")
    
    if report.config_issues:
        fix_report.details.append(f"MANUAL ACTION REQUIRED: {len(report.config_issues)} configuration issues")
        for issue in report.config_issues:
            if issue.suggested_fix:
                fix_report.details.append(f"  - {issue.location}: {issue.suggested_fix}")
    
    logger.info(f"Fix application complete. Applied: {fix_report.fixes_applied}, Failed: {fix_report.fixes_failed}")
    return fix_report


def remove_cache_directories(directories: List[str], dry_run: bool = False) -> int:
    """
    Remove cache directories that shouldn't be in Lambda deployments.
    
    Cache directories like __pycache__, .pytest_cache, and .aws-sam can cause
    build issues and should be removed before running SAM build.
    
    Args:
        directories: List of cache directory paths to remove
        dry_run: If True, only log what would be removed without actually removing
        
    Returns:
        Number of directories successfully removed (or would be removed if dry_run)
        
    Notes:
        - Uses shutil.rmtree to recursively remove directories
        - Continues removing even if some fail
        - Logs each removal attempt
        - Handles permission errors gracefully
    """
    logger.info(f"Removing {len(directories)} cache directories (dry_run={dry_run})")
    removed_count = 0
    project_root = get_project_root()
    
    for dir_path in directories:
        # Convert relative paths to absolute
        if not os.path.isabs(dir_path):
            dir_path = os.path.join(project_root, dir_path)
        
        if not os.path.exists(dir_path):
            logger.warning(f"Directory does not exist: {dir_path}")
            continue
        
        if not os.path.isdir(dir_path):
            logger.warning(f"Not a directory: {dir_path}")
            continue
        
        try:
            if dry_run:
                logger.info(f"DRY RUN: Would remove directory: {get_relative_path(dir_path)}")
                removed_count += 1
            else:
                logger.info(f"Removing directory: {get_relative_path(dir_path)}")
                shutil.rmtree(dir_path)
                removed_count += 1
                logger.info(f"Successfully removed: {get_relative_path(dir_path)}")
        except PermissionError as e:
            logger.error(f"Permission denied removing {dir_path}: {e}")
        except Exception as e:
            logger.error(f"Failed to remove {dir_path}: {e}")
    
    return removed_count


def update_gitignore(files: List[str], dry_run: bool = False) -> int:
    """
    Add problematic files and patterns to .gitignore.
    
    Files that cause build issues (large files, cache files) should be added
    to .gitignore to prevent them from being committed and included in builds.
    
    Args:
        files: List of file paths to add to .gitignore
        dry_run: If True, only show what would be added without modifying .gitignore
        
    Returns:
        Number of patterns successfully added to .gitignore
        
    Notes:
        - Converts file paths to .gitignore patterns
        - Avoids adding duplicate patterns
        - Creates .gitignore if it doesn't exist
        - Adds patterns in a dedicated section with header comment
        - Preserves existing .gitignore content
    """
    logger.info(f"Updating .gitignore with {len(files)} patterns (dry_run={dry_run})")
    
    project_root = get_project_root()
    gitignore_path = os.path.join(project_root, '.gitignore')
    
    # Read existing .gitignore content
    existing_content = ""
    existing_patterns = set()
    
    if os.path.exists(gitignore_path):
        content = safe_read_file(gitignore_path)
        if content:
            existing_content = content
            # Extract existing patterns (ignore comments and empty lines)
            for line in content.split('\n'):
                line = line.strip()
                if line and not line.startswith('#'):
                    existing_patterns.add(line)
    
    # Convert file paths to .gitignore patterns
    patterns_to_add = set()
    for file_path in files:
        pattern = _file_path_to_gitignore_pattern(file_path, project_root)
        if pattern and pattern not in existing_patterns:
            patterns_to_add.add(pattern)
    
    if not patterns_to_add:
        logger.info("No new patterns to add to .gitignore")
        return 0
    
    # Build new .gitignore content
    new_content = existing_content
    
    # Add header comment if adding patterns
    if patterns_to_add:
        if new_content and not new_content.endswith('\n'):
            new_content += '\n'
        
        new_content += '\n# Patterns added by SAM build diagnostic tool\n'
        new_content += f'# Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n'
        
        for pattern in sorted(patterns_to_add):
            new_content += f'{pattern}\n'
    
    if dry_run:
        logger.info(f"DRY RUN: Would add {len(patterns_to_add)} patterns to .gitignore:")
        for pattern in sorted(patterns_to_add):
            logger.info(f"  {pattern}")
        return len(patterns_to_add)
    else:
        # Write updated .gitignore
        if safe_write_file(gitignore_path, new_content):
            logger.info(f"Successfully added {len(patterns_to_add)} patterns to .gitignore")
            return len(patterns_to_add)
        else:
            logger.error("Failed to write .gitignore")
            return 0


def create_backup(directory: Optional[str] = None) -> str:
    """
    Create backup of project before making changes.
    
    Creates a timestamped backup of the project (or specified directory) in
    the .backups/ directory. This allows rollback if fixes cause issues.
    
    Args:
        directory: Directory to backup (default: project root)
        
    Returns:
        Path to created backup directory
        
    Raises:
        Exception: If backup creation fails
        
    Notes:
        - Creates .backups/ directory if it doesn't exist
        - Uses timestamp in backup directory name
        - Excludes .git, .aws-sam, and other large directories
        - Excludes cache directories and build artifacts
        - Logs backup progress
    """
    if directory is None:
        directory = get_project_root()
    
    logger.info(f"Creating backup of {directory}")
    
    # Create .backups directory
    project_root = get_project_root()
    backups_dir = os.path.join(project_root, '.backups')
    ensure_directory_exists(backups_dir)
    
    # Create timestamped backup directory
    timestamp = create_timestamp_string()
    backup_name = f"backup_{timestamp}"
    backup_path = os.path.join(backups_dir, backup_name)
    
    # Directories to exclude from backup
    exclude_dirs = {
        '.git',
        '.aws-sam',
        '__pycache__',
        '.pytest_cache',
        'node_modules',
        '.mypy_cache',
        '.tox',
        '.hypothesis',
        '.backups',
        'venv',
        'env',
        '.venv'
    }
    
    # File patterns to exclude
    exclude_patterns = {
        '*.pyc',
        '*.pyo',
        '*.pyd',
        '.DS_Store',
        'Thumbs.db',
        '*.swp',
        '*.swo',
        '*~'
    }
    
    try:
        logger.info(f"Creating backup at: {backup_path}")
        
        # Use shutil.copytree with ignore function
        def ignore_function(dir_path, names):
            ignored = []
            for name in names:
                # Ignore excluded directories
                if name in exclude_dirs:
                    ignored.append(name)
                    continue
                
                # Ignore files matching exclude patterns
                for pattern in exclude_patterns:
                    if Path(name).match(pattern):
                        ignored.append(name)
                        break
            
            return ignored
        
        shutil.copytree(directory, backup_path, ignore=ignore_function)
        logger.info(f"Backup created successfully at: {backup_path}")
        
        return backup_path
    
    except Exception as e:
        logger.error(f"Failed to create backup: {e}")
        raise


def _file_path_to_gitignore_pattern(file_path: str, project_root: str) -> Optional[str]:
    """
    Convert file path to .gitignore pattern.
    
    This helper function converts absolute or relative file paths to appropriate
    .gitignore patterns. It handles different file types and creates patterns
    that will match the files effectively.
    
    Args:
        file_path: Path to file (absolute or relative)
        project_root: Project root directory
        
    Returns:
        .gitignore pattern string, or None if pattern cannot be created
        
    Notes:
        - Converts absolute paths to relative paths
        - Creates directory patterns for directories
        - Creates wildcard patterns for common file types
        - Handles special cases like cache directories
    """
    try:
        # Convert to relative path if absolute
        if os.path.isabs(file_path):
            rel_path = os.path.relpath(file_path, project_root)
        else:
            rel_path = file_path
        
        # Normalize path separators
        rel_path = rel_path.replace(os.sep, '/')
        
        # Get filename and extension
        filename = os.path.basename(rel_path)
        _, ext = os.path.splitext(filename)
        
        # Handle cache directories - use wildcard pattern
        cache_dir_names = {
            '__pycache__',
            '.pytest_cache',
            '.aws-sam',
            'node_modules',
            '.mypy_cache',
            '.tox',
            '.hypothesis'
        }
        
        if filename in cache_dir_names:
            return f'{filename}/'
        
        # Handle common file patterns
        if ext in {'.pyc', '.pyo', '.pyd'}:
            return f'*{ext}'
        
        if filename in {'.DS_Store', 'Thumbs.db'}:
            return filename
        
        if ext in {'.swp', '.swo'}:
            return f'*{ext}'
        
        # For large files or other files, use the relative path
        return rel_path
    
    except Exception as e:
        logger.error(f"Failed to convert {file_path} to .gitignore pattern: {e}")
        return None


def restore_from_backup(backup_path: str, target_directory: Optional[str] = None) -> bool:
    """
    Restore project from a backup.
    
    This function restores the project (or specified directory) from a backup
    created by create_backup(). Use this if fixes cause issues and you need
    to rollback.
    
    Args:
        backup_path: Path to backup directory to restore from
        target_directory: Directory to restore to (default: project root)
        
    Returns:
        True if restore succeeded, False otherwise
        
    Notes:
        - Validates backup exists before attempting restore
        - Creates backup of current state before restoring
        - Logs restore progress
        - This is a destructive operation - use with caution
    """
    if target_directory is None:
        target_directory = get_project_root()
    
    logger.info(f"Restoring from backup: {backup_path}")
    
    # Validate backup exists
    if not os.path.exists(backup_path):
        logger.error(f"Backup does not exist: {backup_path}")
        return False
    
    if not os.path.isdir(backup_path):
        logger.error(f"Backup path is not a directory: {backup_path}")
        return False
    
    try:
        # Create backup of current state before restoring
        logger.info("Creating backup of current state before restore")
        pre_restore_backup = create_backup(target_directory)
        logger.info(f"Pre-restore backup created at: {pre_restore_backup}")
        
        # Restore files from backup
        logger.info(f"Restoring files from {backup_path} to {target_directory}")
        
        # Copy files from backup to target
        for item in os.listdir(backup_path):
            source = os.path.join(backup_path, item)
            dest = os.path.join(target_directory, item)
            
            if os.path.isdir(source):
                if os.path.exists(dest):
                    shutil.rmtree(dest)
                shutil.copytree(source, dest)
            else:
                shutil.copy2(source, dest)
        
        logger.info("Restore completed successfully")
        return True
    
    except Exception as e:
        logger.error(f"Failed to restore from backup: {e}")
        return False


def main():
    """
    CLI entry point for applying fixes.
    
    This function provides a command-line interface for running the fix tool
    independently. It can be used to apply fixes from a previously generated
    diagnostic report.
    """
    import argparse
    import json
    from utils import setup_logging
    
    parser = argparse.ArgumentParser(
        description='Apply automated fixes for SAM build hang issues'
    )
    parser.add_argument(
        '--report',
        type=str,
        help='Path to diagnostic report JSON file'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be fixed without making changes'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(verbose=args.verbose)
    
    logger.info("SAM Build Fix Tool")
    logger.info("=" * 50)
    
    # Load diagnostic report
    if args.report:
        try:
            with open(args.report, 'r') as f:
                report_data = json.load(f)
            # TODO: Deserialize JSON to DiagnosticReport object
            logger.error("Loading from JSON not yet implemented")
            return
        except Exception as e:
            logger.error(f"Failed to load diagnostic report: {e}")
            return
    else:
        logger.error("No diagnostic report provided. Use --report to specify report file.")
        logger.info("Run diagnose_build_hang.py first to generate a diagnostic report.")
        return
    
    # Apply fixes
    # fix_report = apply_all_fixes(report, dry_run=args.dry_run)
    
    # Print results
    # TODO: Format and print fix report


if __name__ == '__main__':
    main()
