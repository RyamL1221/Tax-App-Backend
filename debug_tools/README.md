# Debug Tools

Diagnostic and fix tools for identifying and resolving SAM build hangs during the PythonPipBuilder:CopySource phase.

## Overview

This package provides standalone Python scripts to diagnose root causes of SAM build hangs and apply automated fixes for common issues. The tools can be run independently to analyze the project structure, validate configurations, and verify builds complete successfully.

## Structure

```
debug_tools/
├── __init__.py                  # Package initialization
├── models.py                    # Data models for reports and issues
├── utils.py                     # Shared utility functions
├── README.md                    # This file
└── tests/                       # Unit tests
    ├── __init__.py
    ├── test_models_unit.py      # Tests for data models
    └── test_utils_unit.py       # Tests for utility functions
```

## Data Models

### DiagnosticReport
Comprehensive report containing all diagnostic findings:
- `file_issues`: List of file system issues
- `dependency_issues`: List of dependency validation issues
- `config_issues`: List of SAM configuration issues
- `summary`: High-level summary of findings
- `recommendations`: List of recommended actions

### FileIssue
Represents a file system issue:
- `issue_type`: Type of issue (symlink, large_file, cache_dir, gitignore_violation)
- `path`: Path to problematic file/directory
- `severity`: Severity level (critical, warning, info)
- `fix_available`: Whether automated fix is available

### DependencyIssue
Represents a dependency validation issue:
- `lambda_function`: Name of Lambda function with issue
- `package_name`: Name of problematic package
- `issue_type`: Type of issue (invalid_name, invalid_version, conflict, incompatible)
- `suggested_fix`: Optional suggestion for fixing

### ConfigIssue
Represents a SAM configuration issue:
- `issue_type`: Type of issue (missing_path, duplicate_function, invalid_runtime, env_config)
- `location`: Location in template.yaml
- `suggested_fix`: Optional suggestion for fixing

### BuildResult
Result of build verification:
- `success`: Whether build completed successfully
- `duration_seconds`: Build duration
- `artifacts_verified`: Whether build artifacts were verified
- `dependencies_verified`: Whether dependencies were verified

### FixReport
Report of fixes applied:
- `fixes_applied`: Number of successful fixes
- `fixes_failed`: Number of failed fixes
- `backup_path`: Path to backup created before fixes
- `dry_run`: Whether this was a dry run

## Utility Functions

### File Operations
- `get_lambda_directories()`: Get list of all Lambda function directories
- `get_project_root()`: Get project root directory
- `get_template_path()`: Get path to template.yaml
- `format_file_size()`: Format file size in human-readable format
- `is_cache_directory()`: Check if directory is a cache directory

### File I/O
- `safe_read_file()`: Safely read file with error handling
- `safe_write_file()`: Safely write file with error handling
- `get_relative_path()`: Get relative path from base

### Utilities
- `create_timestamp_string()`: Create timestamp for filenames
- `ensure_directory_exists()`: Ensure directory exists
- `setup_logging()`: Configure logging

## Usage

### Running Tests

```bash
# Run all tests
pytest debug_tools/tests/ -v

# Run specific test file
pytest debug_tools/tests/test_models_unit.py -v

# Run with coverage
pytest debug_tools/tests/ --cov=debug_tools --cov-report=html
```

### Using Data Models

```python
from debug_tools.models import DiagnosticReport, FileIssue

# Create a file issue
issue = FileIssue(
    issue_type='large_file',
    path='/path/to/large_file.pdf',
    details='File is 15MB, exceeds 10MB threshold',
    severity='warning',
    fix_available=True
)

# Create diagnostic report
report = DiagnosticReport(
    file_issues=[issue],
    summary='Found 1 issue',
    recommendations=['Add large file to .gitignore']
)

print(f"Total issues: {report.total_issues}")
print(f"Critical issues: {report.critical_issues}")
```

### Using Utilities

```python
from debug_tools.utils import (
    get_lambda_directories,
    format_file_size,
    is_cache_directory
)

# Get all Lambda directories
lambda_dirs = get_lambda_directories()
print(f"Found {len(lambda_dirs)} Lambda functions")

# Format file size
size = format_file_size(15728640)  # "15.0 MB"

# Check if directory is cache
if is_cache_directory('__pycache__'):
    print("This is a cache directory")
```

## Development

### Adding New Models

1. Define the dataclass in `models.py`
2. Add validation in `__post_init__` if needed
3. Add properties for computed values
4. Write unit tests in `tests/test_models_unit.py`

### Adding New Utilities

1. Add function to `utils.py` with type hints and docstring
2. Follow PEP 8 style guide
3. Write unit tests in `tests/test_utils_unit.py`
4. Update this README with usage examples

## Requirements

- Python 3.14+
- pytest (for testing)
- hypothesis (for property-based testing)

## Related Documentation

- [Build Hang Resolution Guide](../docs/development/BUILD_HANG_RESOLUTION.md) (to be created)
- [Quick Reference](../.kiro/steering/quick-reference.md)
- [Code Style Guidelines](../.kiro/steering/code-style.md)
