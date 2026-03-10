# Debug Tools

Diagnostic and debugging tools for SAM build issues and PDF tax form generation.

## Overview

This package provides standalone Python scripts for two main purposes:

1. **SAM Build Diagnostics**: Diagnose root causes of SAM build problems, verify build artifacts, and apply automated fixes.

2. **PDF Form Inspection**: Inspect, validate, and verify PDF tax form fields and generation output.

**SAM Build Features:**
- **Build Verification**: Check if build artifacts exist and are up-to-date
- **Build Diagnostics**: Identify root causes of build hangs
- **Dependency Validation**: Verify Lambda dependencies are correct
- **Configuration Validation**: Check SAM template configuration
- **Automated Fixes**: Apply fixes for common issues
- **Hook Integration**: Automatic verification on file save

**PDF Tools Features:**
- **Field Inspection**: List and analyze PDF form fields
- **Field Validation**: Validate field mappings and positions
- **Output Verification**: Verify generated PDF output
- **Generation Testing**: Test specific PDF generation features

## Structure

```
debug_tools/
├── __init__.py                      # Package initialization
├── models.py                        # Data models for reports and issues
├── utils.py                         # Shared utility functions
├── README.md                        # This file
│
│   # SAM Build Tools
├── verify_sam_build.py              # Build artifact verification
├── build_feedback_generator.py      # Feedback message generation
├── sam_template_parser.py           # SAM template parsing
├── diagnose_build_hang.py           # Build hang diagnostics
├── validate_dependencies.py         # Dependency validation
├── validate_sam_config.py           # SAM configuration validation
├── apply_fixes.py                   # Automated fix application
├── scan_file_system.py              # File system scanning utilities
│
│   # PDF Field Inspection Tools
├── inspect_pdf_fields.py            # List all PDF form fields
├── inspect_generated_pdf_fields.py  # Inspect generated PDF output
├── inspect_leftcol_fields.py        # Inspect left column fields
├── inspect_calendar_year_fields.py  # Inspect calendar year fields
├── inspect_voided_corrected_checkboxes.py  # Inspect checkbox fields
├── check_pdf_structure.py           # Analyze PDF structure
├── analyze_field_dimensions.py      # Analyze field dimensions
├── analyze_recipient_name_field.py  # Analyze recipient name field
├── analyze_checkbox_structure.py    # Analyze checkbox structure
├── research_checkbox_appearance.py  # Research checkbox appearance streams
│
│   # PDF Validation Tools
├── validate_field_mappings.py       # Validate field mappings
├── validate_field_positions.py      # Validate field positions
├── validate_comprehensive_schema.py # Validate comprehensive schema
├── validate_standardization.py      # Validate field standardization
│
│   # PDF Verification Tools
├── verify_checkbox_visibility.py    # Verify checkbox visibility
├── verify_calendar_year_in_pdf.py   # Verify calendar year rendering
├── verify_debug_pdf.py              # Verify debug PDF output
├── final_verification_test.py       # Final verification test suite
│
│   # PDF Generation Test Tools
├── generate_calendar_year_test_pdf.py  # Generate test PDF for calendar year
├── debug_calendar_year_generation.py   # Debug calendar year generation
├── test_calendar_year_fix.py           # Test calendar year fix
├── test_calendar_year_mapping.py       # Test calendar year mapping
├── test_field_positions.py             # Test field positions
├── test_checkbox_flattening_approach.py # Test checkbox flattening
├── test_flatten_checkbox_function.py   # Test flatten checkbox function
├── test_voided_corrected_visibility.py # Test voided/corrected visibility
│
│   # Build Verification Tests
├── test_timestamp_comparison.py     # Timestamp comparison tests
├── test_cache_detection.py          # Cache detection tests
├── test_cli_verification.py         # CLI verification tests
│
└── tests/                           # Unit tests
    ├── __init__.py
    ├── test_models_unit.py
    ├── test_utils_unit.py
    ├── test_apply_fixes_unit.py
    ├── test_validate_dependencies_unit.py
    └── test_validate_sam_config_unit.py
```

## Command-Line Tools

### SAM Build Tools

#### 1. Build Verification (verify_sam_build.py)

**Purpose**: Verify that SAM build artifacts exist, are up-to-date, and contain required handler modules.

**Usage:**
```bash
# Check specific Lambda function
python debug_tools/verify_sam_build.py user_login

# Check all Lambda functions
python debug_tools/verify_sam_build.py --all

# Verbose output with timestamps
python debug_tools/verify_sam_build.py user_login --verbose
```

**What it checks:**
- Build directory exists (`.aws-sam/build/<LambdaName>`)
- Build artifacts are newer than source files
- Handler module is present in build directory
- Cache directories that might cause issues

**Example output:**
```bash
# Success
✅ Build artifacts are valid for UserLoginFunction

# Issues found
⚠️  Build issues for UserLoginFunction:
   • Build artifacts are older than source files
   
   Fix: Run SAM build
   sam build --parameter-overrides Environment=local
   
   See: .kiro/steering/sam-build-guidelines.md
```

**When to use:**
- After editing Lambda code, before testing
- When you get "Unable to import module" errors
- To verify build succeeded after running `sam build`
- As part of pre-deployment checks

**Exit codes:**
- `0`: All checks passed
- `1`: Build issues found
- `2`: Verification error (template parsing failed, etc.)

#### 2. Build Hang Diagnostics (diagnose_build_hang.py)

**Purpose**: Diagnose root causes of SAM build hangs.

**Usage:**
```bash
python debug_tools/diagnose_build_hang.py
```

**What it checks:**
- Cache directories in Lambda directories
- Large files that might slow builds
- Symlinks that might cause issues
- Dependency problems
- SAM configuration issues

#### 3. Dependency Validation (validate_dependencies.py)

**Purpose**: Validate Lambda function dependencies.

**Usage:**
```bash
python debug_tools/validate_dependencies.py
```

**What it checks:**
- `requirements.txt` exists for each Lambda
- No missing imports
- No version conflicts
- Compatible with Python 3.14

#### 4. SAM Configuration Validation (validate_sam_config.py)

**Purpose**: Validate SAM template configuration.

**Usage:**
```bash
python debug_tools/validate_sam_config.py
```

**What it checks:**
- Template syntax is valid
- Environment variables are configured
- CodeUri paths exist
- Parameter consistency

#### 5. Apply Automated Fixes (apply_fixes.py)

**Purpose**: Apply automated fixes for common issues.

**Usage:**
```bash
# Remove cache directories
python debug_tools/apply_fixes.py --remove-cache

# Fix all detected issues
python debug_tools/apply_fixes.py --all

# Dry run (show what would be fixed)
python debug_tools/apply_fixes.py --all --dry-run
```

### PDF Field Inspection Tools

These tools help inspect and analyze PDF form fields in tax documents (1099-DIV, etc.).

#### 1. Inspect PDF Fields (inspect_pdf_fields.py)

**Purpose**: List all form fields in a PDF template.

**Usage:**
```bash
python debug_tools/inspect_pdf_fields.py samples/1099-DIV.pdf
```

**What it shows:**
- Field names and types
- Field positions and dimensions
- Field values (if any)

#### 2. Inspect Generated PDF Fields (inspect_generated_pdf_fields.py)

**Purpose**: Inspect fields in a generated PDF output.

**Usage:**
```bash
python debug_tools/inspect_generated_pdf_fields.py samples/test-output.pdf
```

#### 3. Inspect Calendar Year Fields (inspect_calendar_year_fields.py)

**Purpose**: Inspect calendar year field positions across all form copies.

**Usage:**
```bash
python debug_tools/inspect_calendar_year_fields.py
```

#### 4. Inspect Voided/Corrected Checkboxes (inspect_voided_corrected_checkboxes.py)

**Purpose**: Inspect VOID and CORRECTED checkbox fields.

**Usage:**
```bash
python debug_tools/inspect_voided_corrected_checkboxes.py
```

#### 5. Analyze Field Dimensions (analyze_field_dimensions.py)

**Purpose**: Analyze field dimensions for font size calculations.

**Usage:**
```bash
python debug_tools/analyze_field_dimensions.py samples/1099-DIV.pdf
```

#### 6. Analyze Checkbox Structure (analyze_checkbox_structure.py)

**Purpose**: Analyze checkbox field structure and appearance streams.

**Usage:**
```bash
python debug_tools/analyze_checkbox_structure.py
```

#### 7. Check PDF Structure (check_pdf_structure.py)

**Purpose**: Analyze overall PDF structure and form hierarchy.

**Usage:**
```bash
python debug_tools/check_pdf_structure.py samples/1099-DIV.pdf
```

### PDF Validation Tools

These tools validate field mappings and configurations.

#### 1. Validate Field Mappings (validate_field_mappings.py)

**Purpose**: Validate that field mappings match actual PDF fields.

**Usage:**
```bash
python debug_tools/validate_field_mappings.py
```

**What it checks:**
- All mapped fields exist in PDF
- No duplicate mappings
- Field names are correct

#### 2. Validate Field Positions (validate_field_positions.py)

**Purpose**: Validate field positions are correct.

**Usage:**
```bash
python debug_tools/validate_field_positions.py
```

#### 3. Validate Comprehensive Schema (validate_comprehensive_schema.py)

**Purpose**: Validate the comprehensive 1099-DIV schema.

**Usage:**
```bash
python debug_tools/validate_comprehensive_schema.py
```

#### 4. Validate Standardization (validate_standardization.py)

**Purpose**: Validate field name standardization.

**Usage:**
```bash
python debug_tools/validate_standardization.py
```

### PDF Verification Tools

These tools verify PDF generation output.

#### 1. Verify Checkbox Visibility (verify_checkbox_visibility.py)

**Purpose**: Verify checkboxes are visible in generated PDFs.

**Usage:**
```bash
python debug_tools/verify_checkbox_visibility.py samples/test-output.pdf
```

#### 2. Verify Calendar Year in PDF (verify_calendar_year_in_pdf.py)

**Purpose**: Verify calendar year renders correctly in all copies.

**Usage:**
```bash
python debug_tools/verify_calendar_year_in_pdf.py samples/test-output.pdf
```

#### 3. Final Verification Test (final_verification_test.py)

**Purpose**: Run comprehensive verification tests on generated PDFs.

**Usage:**
```bash
python debug_tools/final_verification_test.py
```

### PDF Generation Test Tools

These tools test specific PDF generation features.

#### 1. Generate Calendar Year Test PDF (generate_calendar_year_test_pdf.py)

**Purpose**: Generate a test PDF to verify calendar year rendering.

**Usage:**
```bash
python debug_tools/generate_calendar_year_test_pdf.py
```

#### 2. Debug Calendar Year Generation (debug_calendar_year_generation.py)

**Purpose**: Debug calendar year field generation issues.

**Usage:**
```bash
python debug_tools/debug_calendar_year_generation.py
```

#### 3. Test Checkbox Flattening (test_checkbox_flattening_approach.py)

**Purpose**: Test checkbox flattening approach for Adobe compatibility.

**Usage:**
```bash
python debug_tools/test_checkbox_flattening_approach.py
```

## Data Models

### BuildStatus (NEW)

Status of SAM build artifacts for a Lambda function:

```python
@dataclass
class BuildStatus:
    exists: bool                    # Build directory exists
    up_to_date: bool               # Build newer than source
    handler_present: bool          # Handler module in build
    lambda_name: str               # Lambda function name
    lambda_dir: str                # Source directory
    handler_file: str              # Handler filename
    source_mtime: float            # Source modification time
    build_mtime: Optional[float]   # Build modification time
    cache_dirs_present: bool       # Cache directories found
    cache_dirs_found: List[str]    # List of cache directories
    error_message: Optional[str]   # Error if verification failed
    
    @property
    def is_valid(self) -> bool:
        """Check if build is valid (exists, up-to-date, handler present)."""
        return (
            self.exists and 
            self.up_to_date and 
            self.handler_present and 
            not self.error_message
        )
```

### LambdaConfig (NEW)

Configuration for a Lambda function from SAM template:

```python
@dataclass
class LambdaConfig:
    name: str              # Function name (e.g., 'UserLoginFunction')
    code_uri: str          # CodeUri from template
    handler: str           # Full handler string (e.g., 'app.lambda_handler')
    handler_file: str      # Handler filename (e.g., 'app.py')
    handler_function: str  # Handler function name (e.g., 'lambda_handler')
```

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

## Module APIs

### verify_sam_build.py

**Core Functions:**

```python
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

def get_build_modification_time(lambda_name: str) -> Optional[float]:
    """
    Get modification time of build artifacts for a Lambda function.
    
    Args:
        lambda_name: Lambda function name from template
        
    Returns:
        Unix timestamp of build directory, or None if not found
    """

def check_handler_present(lambda_name: str, handler_file: str) -> bool:
    """
    Check if handler module exists in build directory.
    
    Args:
        lambda_name: Lambda function name from template
        handler_file: Handler filename (e.g., 'app.py')
        
    Returns:
        True if handler file exists in build directory
    """

def check_cache_directories(lambda_dir: str) -> Tuple[bool, List[str]]:
    """
    Check for cache directories in Lambda directory.
    
    Args:
        lambda_dir: Path to Lambda directory
        
    Returns:
        Tuple of (cache_present, cache_dirs_found)
    """

def verify_all_lambdas(verbose: bool = False) -> Dict[str, BuildStatus]:
    """
    Verify build artifacts for all Lambda functions.
    
    Args:
        verbose: Include detailed output
        
    Returns:
        Dictionary mapping Lambda directory names to BuildStatus objects
    """
```

### build_feedback_generator.py

**Core Functions:**

```python
def generate_build_feedback(
    status: BuildStatus,
    verbose: bool = False
) -> str:
    """
    Generate consolidated feedback message for build verification.
    
    This is the main entry point for generating user-facing feedback.
    
    Args:
        status: BuildStatus object from check_build_artifacts()
        verbose: Include detailed timestamps and paths
        
    Returns:
        Formatted feedback message with issues, fix commands, and references
    """

def format_build_success_message(
    status: BuildStatus,
    verbose: bool = False
) -> str:
    """
    Format success message for valid build artifacts.
    
    Args:
        status: BuildStatus object with valid build
        verbose: Include detailed timestamps and paths
        
    Returns:
        Brief confirmation message
    """

def format_build_error_message(
    status: BuildStatus,
    verbose: bool = False
) -> str:
    """
    Format error message for build issues.
    
    Args:
        status: BuildStatus object with build issues
        verbose: Include detailed timestamps and paths
        
    Returns:
        Error message with fix commands and documentation references
    """

def format_multiple_lambda_summary(
    results: dict,
    verbose: bool = False
) -> str:
    """
    Format summary for multiple Lambda function checks.
    
    Args:
        results: Dictionary mapping Lambda directory names to BuildStatus objects
        verbose: Include detailed output for each Lambda
        
    Returns:
        Formatted summary with individual results and overall statistics
    """
```

### sam_template_parser.py

**Core Functions:**

```python
def parse_sam_template(template_path: str = "template.yaml") -> Dict[str, LambdaConfig]:
    """
    Parse SAM template and extract Lambda function configurations.
    
    Args:
        template_path: Path to template.yaml
        
    Returns:
        Dictionary mapping Lambda function names to configurations
        
    Raises:
        FileNotFoundError: If template file not found
        yaml.YAMLError: If template is invalid YAML
    """

def extract_handler_info(handler_string: str) -> Tuple[str, str]:
    """
    Extract handler file and function from handler string.
    
    Args:
        handler_string: Handler in format "module.function"
        
    Returns:
        Tuple of (handler_file, handler_function)
        
    Example:
        "app.lambda_handler" -> ("app.py", "lambda_handler")
    """

def get_lambda_name_from_dir(lambda_dir: str, template_config: Dict) -> Optional[str]:
    """
    Find Lambda function name from directory path.
    
    Args:
        lambda_dir: Directory path (e.g., "user_login")
        template_config: Parsed template configuration
        
    Returns:
        Lambda function name (e.g., "UserLoginFunction") or None if not found
    """
```

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

## Usage Examples

### Example 1: Check Build Before Testing

```bash
# Edit Lambda code
vim user_login/app.py

# Verify build is up-to-date before testing
python debug_tools/verify_sam_build.py user_login

# If stale, rebuild
sam build --parameter-overrides Environment=local

# Verify again
python debug_tools/verify_sam_build.py user_login
```

### Example 2: Pre-Deployment Verification

```bash
# Check all Lambda functions before deployment
python debug_tools/verify_sam_build.py --all

# If any issues, fix them
sam build --parameter-overrides Environment=production

# Verify again
python debug_tools/verify_sam_build.py --all
```

### Example 3: Troubleshooting Runtime Import Errors

```bash
# Lambda fails with "Unable to import module 'app'"
# Check build artifacts
python debug_tools/verify_sam_build.py tax_document_generation

# Output shows:
# ⚠️  Build issues for TaxDocumentGenerationFunction:
#    • Handler file 'app.py' not found in build artifacts

# Run diagnostics
python debug_tools/diagnose_build_hang.py

# Clean cache and rebuild
python debug_tools/apply_fixes.py --remove-cache
sam build --parameter-overrides Environment=local

# Verify fix
python debug_tools/verify_sam_build.py tax_document_generation
```

### Example 4: Programmatic Usage

```python
from debug_tools.verify_sam_build import check_build_artifacts
from debug_tools.build_feedback_generator import generate_build_feedback

# Check specific Lambda
status = check_build_artifacts("user_login")

# Generate feedback
feedback = generate_build_feedback(status, verbose=False)
print(feedback)

# Check if valid
if status.is_valid:
    print("✅ Build is valid")
else:
    print("❌ Build has issues")
    if not status.up_to_date:
        print("   Need to rebuild")
```

### Example 5: Hook Integration

The check-lambda-imports hook automatically runs build verification when you save Lambda files:

```python
# In .kiro/hooks/check-lambda-imports.kiro.hook
# The hook automatically:
# 1. Checks import patterns
# 2. Runs verify_sam_build.py
# 3. Consolidates feedback

# Example workflow:
# 1. Edit user_login/app.py
# 2. Save file
# 3. Hook triggers automatically
# 4. Receive consolidated feedback:

"""
⚠️  Issues found in user_login/app.py:

Build Issues:
• Build artifacts are older than source files

Fix build:
sam build --parameter-overrides Environment=local

See: .kiro/steering/sam-build-guidelines.md
"""
```

### Example 6: Verbose Output for Debugging

```bash
# Get detailed timestamps and paths
python debug_tools/verify_sam_build.py user_login --verbose

# Output includes:
# ✅ Build artifacts are valid for UserLoginFunction
#    Build directory: .aws-sam/build/UserLoginFunction
#    Handler file: app.py
#    Source mtime: 2024-01-15 10:30:45
#    Build mtime: 2024-01-15 10:35:20
```

### Example 7: Checking Multiple Lambdas

```bash
# Check all Lambda functions with summary
python debug_tools/verify_sam_build.py --all

# Output:
# ✅ Build artifacts are valid for UserLoginFunction
# 
# ✅ Build artifacts are valid for UserRegistrationFunction
# 
# ⚠️  Build issues for TaxDocumentGenerationFunction:
#    • Build artifacts are older than source files
# 
# Summary: 2/3 Lambda functions have valid build artifacts
```

### Example 8: Integration with CI/CD

```bash
#!/bin/bash
# pre-deploy.sh

# Verify all builds before deployment
python debug_tools/verify_sam_build.py --all

# Exit with error if any builds are invalid
if [ $? -ne 0 ]; then
    echo "❌ Build verification failed"
    exit 1
fi

echo "✅ All builds verified"
sam deploy --parameter-overrides Environment=production
```

## Hook Integration

### Automatic Verification on File Save

The `check-lambda-imports` hook integrates build verification with import pattern checking:

**Hook Configuration:**
```json
{
  "enabled": true,
  "name": "Check Lambda Import Patterns and Build Status",
  "when": {
    "type": "fileEdited",
    "patterns": [
      "user_login/*.py",
      "user_registration/*.py",
      "password_recovery/*.py",
      "tax_document_generation/*.py",
      "document_download/*.py"
    ]
  }
}
```

**What the hook does:**

1. **Import Pattern Check**: Verifies production code uses direct imports
2. **Build Verification**: Runs `verify_sam_build.py` to check artifacts
3. **Consolidated Feedback**: Combines results into single message

**Example consolidated feedback:**

```
⚠️  Issues found in user_login/app.py:

Import Issues:
• Line 5: "from user_login.exceptions import ValidationError" 
  should be "from exceptions import ValidationError"

Build Issues:
• Build artifacts are older than source files

Fix import patterns:
[offer to fix automatically]

Fix build:
sam build --parameter-overrides Environment=local

See: .kiro/steering/lambda-import-patterns.md
See: .kiro/steering/sam-build-guidelines.md
```

**Benefits:**
- Catch build issues immediately when editing code
- No need to remember to run verification manually
- Consolidated feedback for all issues
- Actionable fix commands provided

### Hook Implementation

The hook uses the build verification modules:

```python
import sys
import os
sys.path.insert(0, os.path.join(os.getcwd(), 'debug_tools'))

from verify_sam_build import check_build_artifacts
from build_feedback_generator import generate_build_feedback

# Extract Lambda directory from file path
file_path = "user_login/app.py"
lambda_dir = file_path.split('/')[0]

# Check build artifacts
status = check_build_artifacts(lambda_dir)
feedback = generate_build_feedback(status, verbose=False)

# Combine with import check results
# ... consolidate feedback ...
```

## Troubleshooting Common Issues

### Issue 1: "Unable to import module 'app'" at Runtime

**Symptoms:**
- Lambda works locally but fails in AWS
- Error: "Unable to import module 'app'"
- Build completed without errors

**Diagnosis:**
```bash
python debug_tools/verify_sam_build.py <lambda_dir>
```

**Possible causes:**
1. Build artifacts are stale (source newer than build)
2. Handler module missing from build directory
3. Build failed silently

**Solution:**
```bash
# Rebuild
sam build --parameter-overrides Environment=local

# Verify fix
python debug_tools/verify_sam_build.py <lambda_dir>
```

### Issue 2: Build Artifacts Older Than Source

**Symptoms:**
```
⚠️  Build issues for UserLoginFunction:
   • Build artifacts are older than source files
```

**Cause:** Source code was edited after last build

**Solution:**
```bash
sam build --parameter-overrides Environment=local
```

### Issue 3: Handler File Not Found in Build

**Symptoms:**
```
⚠️  Build issues for UserLoginFunction:
   • Handler file 'app.py' not found in build artifacts
```

**Possible causes:**
1. Build failed silently
2. Cache directories causing build issues
3. Import errors preventing build

**Diagnosis:**
```bash
# Check for cache directories
python debug_tools/verify_sam_build.py <lambda_dir> --verbose

# Run full diagnostics
python debug_tools/diagnose_build_hang.py
```

**Solution:**
```bash
# Clean cache
python debug_tools/apply_fixes.py --remove-cache

# Rebuild
sam build --parameter-overrides Environment=local

# Verify
python debug_tools/verify_sam_build.py <lambda_dir>
```

### Issue 4: Build Directory Doesn't Exist

**Symptoms:**
```
⚠️  Build issues for UserLoginFunction:
   • Build directory does not exist
```

**Cause:** SAM build has never been run

**Solution:**
```bash
# First-time build
sam build --parameter-overrides Environment=local

# Verify
python debug_tools/verify_sam_build.py <lambda_dir>
```

### Issue 5: Lambda Function Not Found in Template

**Symptoms:**
```
❌ Error: Lambda function for directory 'user_login' not found in template.yaml
```

**Possible causes:**
1. Directory name doesn't match CodeUri in template
2. Lambda function not defined in template.yaml

**Solution:**
```bash
# Check template configuration
python debug_tools/validate_sam_config.py

# Verify CodeUri matches directory name
grep -A 5 "CodeUri:" template.yaml
```

### Issue 6: Cache Directories Causing Issues

**Symptoms:**
```
⚠️  Build issues for UserLoginFunction:
   • Build artifacts are older than source files
   
   ⚠️  Cache directories found: __pycache__, .pytest_cache
```

**Cause:** Cache directories can interfere with SAM build

**Solution:**
```bash
# Remove cache directories
python debug_tools/apply_fixes.py --remove-cache

# Rebuild
sam build --parameter-overrides Environment=local
```

### Issue 7: Template Parsing Failed

**Symptoms:**
```
❌ Error: Failed to parse template.yaml: ...
```

**Cause:** Invalid YAML syntax in template

**Solution:**
```bash
# Validate template
sam validate --template template.yaml

# Check for syntax errors
python debug_tools/validate_sam_config.py
```

## Testing

### Running Tests

```bash
# Run all tests
pytest debug_tools/tests/ -v

# Run specific test file
pytest debug_tools/tests/test_models_unit.py -v

# Run build verification tests
pytest debug_tools/tests/test_timestamp_comparison.py -v
pytest debug_tools/tests/test_cache_detection.py -v
pytest debug_tools/tests/test_cli_verification.py -v

# Run with coverage
pytest debug_tools/tests/ --cov=debug_tools --cov-report=html
```

### Test Coverage

The debug_tools package includes comprehensive tests:

- **Unit Tests**: Test individual functions and data models
- **Property-Based Tests**: Test universal properties across many inputs
- **Integration Tests**: Test complete workflows
- **CLI Tests**: Test command-line interface

**Test files:**
- `test_models_unit.py`: Data model tests
- `test_utils_unit.py`: Utility function tests
- `test_timestamp_comparison.py`: Timestamp comparison property tests
- `test_cache_detection.py`: Cache directory detection tests
- `test_cli_verification.py`: CLI interface tests

### Using Data Models

```python
from debug_tools.models import BuildStatus, LambdaConfig

# Create BuildStatus
status = BuildStatus(
    exists=True,
    up_to_date=True,
    handler_present=True,
    lambda_name="UserLoginFunction",
    lambda_dir="user_login",
    handler_file="app.py",
    source_mtime=1705320645.0,
    build_mtime=1705320700.0,
    cache_dirs_present=False,
    cache_dirs_found=[]
)

# Check if valid
if status.is_valid:
    print("✅ Build is valid")

# Create LambdaConfig
config = LambdaConfig(
    name="UserLoginFunction",
    code_uri="user_login/",
    handler="app.lambda_handler",
    handler_file="app.py",
    handler_function="lambda_handler"
)
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

### Adding New Verification Tools

1. Create new module in `debug_tools/`
2. Follow existing patterns (verify_sam_build.py as reference)
3. Add CLI interface with argparse
4. Write comprehensive tests
5. Update this README with usage examples
6. Update sam-build-guidelines.md if relevant

## Best Practices

### When to Use Build Verification

**Always verify before:**
- Testing Lambda functions locally
- Deploying to AWS
- Committing code changes
- Running integration tests

**Automatic verification:**
- Enable check-lambda-imports hook for automatic verification on save
- Add to CI/CD pipeline for pre-deployment checks

### Interpreting Results

**✅ Valid build:**
- Build directory exists
- Build artifacts newer than source
- Handler module present
- No action needed

**⚠️ Stale build:**
- Build artifacts older than source
- Action: Run `sam build`

**❌ Missing build:**
- Build directory doesn't exist
- Action: Run `sam build` (first-time setup)

**❌ Handler missing:**
- Build exists but handler not found
- Action: Check for build errors, clean cache, rebuild

### Performance Considerations

- Build verification is fast (< 1 second per Lambda)
- Safe to run frequently
- Minimal overhead when integrated with hooks
- Use `--all` flag sparingly (checks all Lambdas)

### Error Handling

All tools follow consistent error handling:
- Exit code 0: Success
- Exit code 1: Validation failed (issues found)
- Exit code 2: Error (tool failure, not validation failure)

## Requirements

- Python 3.14+
- pytest (for testing)
- hypothesis (for property-based testing)
- PyYAML (for template parsing)
- PyMuPDF/fitz (for PDF inspection tools)

## Related Documentation

### SAM Build Documentation
- [SAM Build Guidelines](../.kiro/steering/sam-build-guidelines.md) - Comprehensive build guide
- [Lambda Import Patterns](../.kiro/steering/lambda-import-patterns.md) - Import pattern rules
- [Local Development](../.kiro/steering/local-development.md) - LocalStack setup
- [Quick Reference](../.kiro/steering/quick-reference.md) - Command quick reference
- [Code Style Guidelines](../.kiro/steering/code-style.md) - Code style rules

### PDF Generation Documentation
- [PDF Generation Guide](../.kiro/steering/pdf-generation.md) - PDF tax form generation overview
- [1099-DIV Field Reference](../docs/architecture/1099-DIV_FIELD_REFERENCE.md) - Complete field reference
- [Checkbox Appearance Research](../docs/architecture/CHECKBOX_APPEARANCE_RESEARCH_FINDINGS.md) - Checkbox research findings
- [Full Field Inspection](../docs/architecture/FULL_FIELD_INSPECTION.txt) - Complete field inspection output

## Summary

The debug_tools package provides comprehensive build verification, diagnostics, and PDF inspection tools:

**SAM Build Features:**
- ✅ Verify build artifacts are up-to-date
- ✅ Check handler modules are present
- ✅ Detect cache directories
- ✅ Provide actionable fix commands
- ✅ Integrate with development workflow via hooks
- ✅ Support both CLI and programmatic usage

**PDF Tools Features:**
- ✅ Inspect PDF form fields and structure
- ✅ Validate field mappings and positions
- ✅ Verify generated PDF output
- ✅ Test specific PDF generation features
- ✅ Debug checkbox and calendar year issues

**Quick Start - SAM Build:**
```bash
# Check specific Lambda
python debug_tools/verify_sam_build.py user_login

# Check all Lambdas
python debug_tools/verify_sam_build.py --all

# If issues found, rebuild
sam build --parameter-overrides Environment=local
```

**Quick Start - PDF Inspection:**
```bash
# List all PDF fields
python debug_tools/inspect_pdf_fields.py samples/1099-DIV.pdf

# Validate field mappings
python debug_tools/validate_field_mappings.py

# Verify generated output
python debug_tools/verify_checkbox_visibility.py samples/test-output.pdf
```

**Hook Integration:**
- Automatic verification on file save
- Consolidated feedback with import checks
- No manual intervention needed
