"""
Shared utility functions for diagnostic tools.

This module provides common functions used across multiple diagnostic scripts
for file operations, logging, and formatting.
"""

import os
import logging
from pathlib import Path
from typing import List, Optional
from datetime import datetime


# Configure logging
logger = logging.getLogger(__name__)


def get_lambda_directories() -> List[str]:
    """
    Get list of all Lambda function directories in the project.
    
    Returns:
        List of directory paths for Lambda functions
        
    Notes:
        Identifies Lambda directories by looking for directories containing
        an app.py or handler file and requirements.txt.
    """
    project_root = get_project_root()
    lambda_dirs = []
    
    # Common Lambda function directory names
    potential_dirs = [
        'user_registration',
        'user_login',
        'password_recovery',
        'tax_document_generation'
    ]
    
    for dir_name in potential_dirs:
        dir_path = os.path.join(project_root, dir_name)
        if os.path.isdir(dir_path):
            # Verify it looks like a Lambda directory
            has_handler = any(
                os.path.exists(os.path.join(dir_path, f))
                for f in ['app.py', 'lambda_function.py', 'handler.py']
            )
            has_requirements = os.path.exists(os.path.join(dir_path, 'requirements.txt'))
            
            if has_handler or has_requirements:
                lambda_dirs.append(dir_path)
                logger.debug(f"Found Lambda directory: {dir_path}")
    
    return lambda_dirs


def get_project_root() -> str:
    """
    Get the project root directory.
    
    Returns:
        Absolute path to project root
        
    Notes:
        Assumes the project root contains template.yaml
    """
    # Start from current file location and search upward
    current = Path(__file__).resolve().parent
    
    while current != current.parent:
        if (current / 'template.yaml').exists():
            return str(current)
        current = current.parent
    
    # Fallback to current working directory
    return os.getcwd()


def get_template_path() -> str:
    """
    Get path to template.yaml file.
    
    Returns:
        Absolute path to template.yaml
        
    Raises:
        FileNotFoundError: If template.yaml is not found
    """
    project_root = get_project_root()
    template_path = os.path.join(project_root, 'template.yaml')
    
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"template.yaml not found at {template_path}")
    
    return template_path


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.
    
    Args:
        size_bytes: File size in bytes
        
    Returns:
        Formatted string (e.g., "1.5 MB", "500 KB")
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def is_cache_directory(dir_name: str) -> bool:
    """
    Check if directory name matches cache directory patterns.
    
    Args:
        dir_name: Directory name to check
        
    Returns:
        True if directory is a cache directory
    """
    cache_patterns = {
        '__pycache__',
        '.pytest_cache',
        '.aws-sam',
        'node_modules',
        '.mypy_cache',
        '.tox',
        '.coverage',
        'htmlcov',
        '.hypothesis'
    }
    return dir_name in cache_patterns


def create_timestamp_string() -> str:
    """
    Create timestamp string for filenames.
    
    Returns:
        Timestamp string in format YYYYMMDD_HHMMSS
    """
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def ensure_directory_exists(directory: str) -> None:
    """
    Ensure directory exists, creating it if necessary.
    
    Args:
        directory: Path to directory
    """
    os.makedirs(directory, exist_ok=True)


def safe_read_file(filepath: str, encoding: str = 'utf-8') -> Optional[str]:
    """
    Safely read file contents with error handling.
    
    Args:
        filepath: Path to file to read
        encoding: File encoding (default: utf-8)
        
    Returns:
        File contents as string, or None if read fails
    """
    try:
        with open(filepath, 'r', encoding=encoding) as f:
            return f.read()
    except UnicodeDecodeError:
        # Try with latin-1 encoding as fallback
        try:
            with open(filepath, 'r', encoding='latin-1') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to read {filepath} with latin-1: {e}")
            return None
    except Exception as e:
        logger.error(f"Failed to read {filepath}: {e}")
        return None


def safe_write_file(filepath: str, content: str, encoding: str = 'utf-8') -> bool:
    """
    Safely write content to file with error handling.
    
    Args:
        filepath: Path to file to write
        content: Content to write
        encoding: File encoding (default: utf-8)
        
    Returns:
        True if write succeeded, False otherwise
    """
    try:
        with open(filepath, 'w', encoding=encoding) as f:
            f.write(content)
        return True
    except Exception as e:
        logger.error(f"Failed to write {filepath}: {e}")
        return False


def get_relative_path(filepath: str, base_path: Optional[str] = None) -> str:
    """
    Get relative path from base path.
    
    Args:
        filepath: Absolute or relative file path
        base_path: Base path (default: project root)
        
    Returns:
        Relative path from base
    """
    if base_path is None:
        base_path = get_project_root()
    
    try:
        return os.path.relpath(filepath, base_path)
    except ValueError:
        # Paths on different drives on Windows
        return filepath


def setup_logging(verbose: bool = False) -> None:
    """
    Set up logging configuration.
    
    Args:
        verbose: If True, set log level to DEBUG
    """
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
