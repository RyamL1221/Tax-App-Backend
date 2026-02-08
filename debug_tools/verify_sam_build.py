"""
Build verification utility for SAM Lambda functions.

This module provides functions to verify that SAM build artifacts exist,
are up-to-date, and contain the required handler modules. It helps prevent
runtime import errors by catching build issues during development.

Usage:
    # Check a specific Lambda function
    python debug_tools/verify_sam_build.py user_login

    # Check all Lambda functions
    python debug_tools/verify_sam_build.py --all

    # Verbose output with timestamps
    python debug_tools/verify_sam_build.py user_login --verbose
"""

import os
import sys
import logging
import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Dict, Tuple

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from debug_tools.utils import (
    get_project_root,
    get_template_path,
    get_lambda_directories,
    is_cache_directory,
    setup_logging
)
from debug_tools.models import BuildStatus, LambdaConfig
from debug_tools.sam_template_parser import (
    parse_sam_template,
    extract_handler_info,
    get_lambda_name_from_dir
)
from debug_tools.build_feedback_generator import (
    generate_build_feedback,
    format_multiple_lambda_summary
)

logger = logging.getLogger(__name__)


def get_source_modification_time(lambda_dir: str) -> float:
    """
    Get the most recent modification time of any Python file in Lambda directory.
    
    Args:
        lambda_dir: Path to Lambda directory
        
    Returns:
        Unix timestamp of most recent modification
        
    Raises:
        FileNotFoundError: If directory doesn't exist
        ValueError: If no Python files found
    """
    if not os.path.isdir(lambda_dir):
        raise FileNotFoundError(f"Lambda directory not found: {lambda_dir}")
    
    max_mtime = 0.0
    python_files_found = 0
    
    # Walk through directory, excluding tests and cache directories
    for root, dirs, files in os.walk(lambda_dir):
        # Skip cache directories
        dirs[:] = [d for d in dirs if not is_cache_directory(d)]
        
        # Skip tests directory
        if 'tests' in root.split(os.sep):
            continue
        
        for filename in files:
            if filename.endswith('.py'):
                filepath = os.path.join(root, filename)
                try:
                    mtime = os.path.getmtime(filepath)
                    max_mtime = max(max_mtime, mtime)
                    python_files_found += 1
                    logger.debug(f"Checked {filepath}: mtime={mtime}")
                except OSError as e:
                    logger.warning(f"Failed to get mtime for {filepath}: {e}")
    
    if python_files_found == 0:
        raise ValueError(f"No Python files found in {lambda_dir}")
    
    logger.debug(f"Found {python_files_found} Python files, max mtime: {max_mtime}")
    return max_mtime


def get_build_modification_time(lambda_name: str) -> Optional[float]:
    """
    Get modification time of build artifacts for a Lambda function.
    
    Args:
        lambda_name: Lambda function name from template
        
    Returns:
        Unix timestamp of build directory, or None if not found
    """
    project_root = get_project_root()
    build_dir = os.path.join(project_root, '.aws-sam', 'build', lambda_name)
    
    if not os.path.isdir(build_dir):
        logger.debug(f"Build directory not found: {build_dir}")
        return None
    
    try:
        mtime = os.path.getmtime(build_dir)
        logger.debug(f"Build directory mtime: {mtime}")
        return mtime
    except OSError as e:
        logger.warning(f"Failed to get mtime for {build_dir}: {e}")
        return None


def check_handler_present(lambda_name: str, handler_file: str) -> bool:
    """
    Check if handler module exists in build directory.
    
    Args:
        lambda_name: Lambda function name from template
        handler_file: Handler filename (e.g., 'app.py')
        
    Returns:
        True if handler file exists in build directory
    """
    project_root = get_project_root()
    build_dir = os.path.join(project_root, '.aws-sam', 'build', lambda_name)
    handler_path = os.path.join(build_dir, handler_file)
    
    exists = os.path.isfile(handler_path)
    logger.debug(f"Handler check: {handler_path} exists={exists}")
    return exists


def check_cache_directories(lambda_dir: str) -> Tuple[bool, List[str]]:
    """
    Check for cache directories in Lambda directory.
    
    Args:
        lambda_dir: Path to Lambda directory
        
    Returns:
        Tuple of (cache_present, cache_dirs_found)
    """
    cache_dirs_found = []
    
    if not os.path.isdir(lambda_dir):
        return False, cache_dirs_found
    
    # Check for common cache directories
    cache_patterns = ['__pycache__', '.pytest_cache', '.hypothesis']
    
    for cache_dir in cache_patterns:
        cache_path = os.path.join(lambda_dir, cache_dir)
        if os.path.isdir(cache_path):
            cache_dirs_found.append(cache_dir)
            logger.debug(f"Found cache directory: {cache_path}")
    
    return len(cache_dirs_found) > 0, cache_dirs_found


def check_build_artifacts(lambda_dir: str) -> BuildStatus:
    """
    Check if SAM build artifacts exist and are up-to-date for a Lambda function.
    
    Args:
        lambda_dir: Path to Lambda directory (e.g., "user_login")
        
    Returns:
        BuildStatus object containing verification results
        
    Raises:
        FileNotFoundError: If template.yaml not found
        ValueError: If Lambda function not in template
    """
    # Normalize lambda_dir to absolute path
    if not os.path.isabs(lambda_dir):
        project_root = get_project_root()
        lambda_dir = os.path.join(project_root, lambda_dir)
    
    # Get directory name for lookup
    dir_name = os.path.basename(lambda_dir.rstrip('/'))
    
    logger.info(f"Checking build artifacts for: {dir_name}")
    
    # Parse template to get Lambda configuration
    try:
        template_config = parse_sam_template()
    except Exception as e:
        error_msg = f"Failed to parse template.yaml: {e}"
        logger.error(error_msg)
        return BuildStatus(
            exists=False,
            up_to_date=False,
            handler_present=False,
            lambda_name="",
            lambda_dir=dir_name,
            handler_file="",
            source_mtime=0.0,
            build_mtime=None,
            error_message=error_msg
        )
    
    # Find Lambda function name from directory
    lambda_name = get_lambda_name_from_dir(dir_name, template_config)
    if not lambda_name:
        error_msg = f"Lambda function for directory '{dir_name}' not found in template.yaml"
        logger.error(error_msg)
        return BuildStatus(
            exists=False,
            up_to_date=False,
            handler_present=False,
            lambda_name="",
            lambda_dir=dir_name,
            handler_file="",
            source_mtime=0.0,
            build_mtime=None,
            error_message=error_msg
        )
    
    config = template_config[lambda_name]
    logger.info(f"Found Lambda function: {lambda_name}")
    logger.debug(f"Handler: {config.handler}, File: {config.handler_file}")
    
    # Check for cache directories
    cache_present, cache_dirs = check_cache_directories(lambda_dir)
    
    # Get source modification time
    try:
        source_mtime = get_source_modification_time(lambda_dir)
    except Exception as e:
        error_msg = f"Failed to get source modification time: {e}"
        logger.error(error_msg)
        return BuildStatus(
            exists=False,
            up_to_date=False,
            handler_present=False,
            lambda_name=lambda_name,
            lambda_dir=dir_name,
            handler_file=config.handler_file,
            source_mtime=0.0,
            build_mtime=None,
            error_message=error_msg,
            cache_dirs_present=cache_present,
            cache_dirs_found=cache_dirs
        )
    
    # Get build modification time
    build_mtime = get_build_modification_time(lambda_name)
    
    # Check if build directory exists
    exists = build_mtime is not None
    
    # Check if build is up-to-date
    up_to_date = False
    if exists and build_mtime is not None:
        up_to_date = build_mtime >= source_mtime
        logger.debug(f"Build mtime: {build_mtime}, Source mtime: {source_mtime}, Up-to-date: {up_to_date}")
    
    # Check if handler is present
    handler_present = False
    if exists:
        handler_present = check_handler_present(lambda_name, config.handler_file)
    
    return BuildStatus(
        exists=exists,
        up_to_date=up_to_date,
        handler_present=handler_present,
        lambda_name=lambda_name,
        lambda_dir=dir_name,
        handler_file=config.handler_file,
        source_mtime=source_mtime,
        build_mtime=build_mtime,
        cache_dirs_present=cache_present,
        cache_dirs_found=cache_dirs
    )


def verify_all_lambdas(verbose: bool = False) -> Dict[str, BuildStatus]:
    """
    Verify build artifacts for all Lambda functions.
    
    Args:
        verbose: Include detailed output
        
    Returns:
        Dictionary mapping Lambda directory names to BuildStatus objects
    """
    lambda_dirs = get_lambda_directories()
    results = {}
    
    for lambda_dir in lambda_dirs:
        dir_name = os.path.basename(lambda_dir)
        try:
            status = check_build_artifacts(lambda_dir)
            results[dir_name] = status
        except Exception as e:
            logger.error(f"Failed to check {dir_name}: {e}")
            results[dir_name] = BuildStatus(
                exists=False,
                up_to_date=False,
                handler_present=False,
                lambda_name="",
                lambda_dir=dir_name,
                handler_file="",
                source_mtime=0.0,
                build_mtime=None,
                error_message=str(e)
            )
    
    return results


def main():
    """Command-line interface for build verification."""
    parser = argparse.ArgumentParser(
        description='Verify SAM build artifacts for Lambda functions',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check specific Lambda function
  python debug_tools/verify_sam_build.py user_login

  # Check all Lambda functions
  python debug_tools/verify_sam_build.py --all

  # Verbose output with timestamps
  python debug_tools/verify_sam_build.py user_login --verbose
        """
    )
    
    parser.add_argument(
        'lambda_dir',
        nargs='?',
        help='Lambda directory to check (e.g., user_login)'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Check all Lambda functions'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose output with timestamps and paths'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(verbose=args.verbose)
    
    # Validate arguments
    if not args.all and not args.lambda_dir:
        parser.error("Either specify a lambda_dir or use --all")
    
    if args.all and args.lambda_dir:
        parser.error("Cannot specify both lambda_dir and --all")
    
    try:
        if args.all:
            # Check all Lambda functions
            print("Checking all Lambda functions...\n")
            results = verify_all_lambdas(verbose=args.verbose)
            
            # Print results using feedback generator
            summary = format_multiple_lambda_summary(results, verbose=args.verbose)
            print(summary)
            
            # Exit with appropriate code
            all_valid = all(s.is_valid for s in results.values())
            sys.exit(0 if all_valid else 1)
        
        else:
            # Check specific Lambda function
            status = check_build_artifacts(args.lambda_dir)
            feedback = generate_build_feedback(status, verbose=args.verbose)
            print(feedback)
            
            # Exit with appropriate code
            sys.exit(0 if status.is_valid else 1)
    
    except Exception as e:
        logger.error(f"Verification failed: {e}", exc_info=args.verbose)
        print(f"\n❌ Error: {e}")
        sys.exit(2)


if __name__ == '__main__':
    main()
