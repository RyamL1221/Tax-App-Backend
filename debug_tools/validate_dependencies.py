"""
Dependency validation for Lambda function requirements.txt files.

This module validates Python dependencies across all Lambda functions to detect
issues that could cause SAM build hangs or failures.
"""

import os
import re
import logging
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

from models import DependencyIssue
from utils import get_lambda_directories, safe_read_file


logger = logging.getLogger(__name__)


@dataclass
class Requirement:
    """
    Represents a parsed requirement from requirements.txt.
    
    Attributes:
        package_name: Name of the package
        version_spec: Version specification (e.g., "==1.0.0", ">=1.0,<2.0")
        raw_line: Original line from requirements.txt
        line_number: Line number in the file
    """
    package_name: str
    version_spec: str
    raw_line: str
    line_number: int


def validate_all_requirements() -> List[DependencyIssue]:
    """
    Validate all requirements.txt files in Lambda directories.
    
    This function orchestrates all dependency validation checks:
    1. Parse all requirements.txt files
    2. Validate package names
    3. Validate version syntax
    4. Check for version conflicts across functions
    
    Returns:
        List of DependencyIssue objects describing problems found
        
    Notes:
        - Continues validation even if individual checks fail
        - Aggregates all issues into a single list
        - Logs progress and errors during validation
    """
    logger.info("Starting dependency validation")
    issues = []
    
    # Get all Lambda directories
    lambda_dirs = get_lambda_directories()
    if not lambda_dirs:
        logger.warning("No Lambda directories found")
        return issues
    
    logger.info(f"Found {len(lambda_dirs)} Lambda directories to validate")
    
    # Parse all requirements files
    all_requirements: Dict[str, List[Requirement]] = {}
    for lambda_dir in lambda_dirs:
        lambda_name = os.path.basename(lambda_dir)
        requirements_path = os.path.join(lambda_dir, 'requirements.txt')
        
        if not os.path.exists(requirements_path):
            logger.warning(f"No requirements.txt found in {lambda_name}")
            continue
        
        try:
            requirements = parse_requirements_file(requirements_path)
            all_requirements[lambda_name] = requirements
            logger.debug(f"Parsed {len(requirements)} requirements from {lambda_name}")
        except Exception as e:
            logger.error(f"Failed to parse {requirements_path}: {e}")
            issues.append(DependencyIssue(
                lambda_function=lambda_name,
                package_name="<parse_error>",
                issue_type="invalid_name",
                details=f"Failed to parse requirements.txt: {str(e)}",
                suggested_fix="Check file format and encoding"
            ))
    
    # Validate package names for each Lambda function
    for lambda_name, requirements in all_requirements.items():
        invalid_names = validate_package_names(requirements)
        for package_name, error in invalid_names:
            issues.append(DependencyIssue(
                lambda_function=lambda_name,
                package_name=package_name,
                issue_type="invalid_name",
                details=error,
                suggested_fix="Use valid PyPI package name (alphanumeric, hyphens, underscores only)"
            ))
    
    # Validate version syntax for each Lambda function
    for lambda_name, requirements in all_requirements.items():
        invalid_versions = validate_version_syntax(requirements)
        for package_name, version_spec, error in invalid_versions:
            issues.append(DependencyIssue(
                lambda_function=lambda_name,
                package_name=package_name,
                issue_type="invalid_version",
                details=f"Invalid version specification '{version_spec}': {error}",
                suggested_fix="Use PEP 440 version syntax (e.g., ==1.0.0, >=1.0,<2.0, ~=1.0)"
            ))
    
    # Check for version conflicts across functions
    conflicts = check_version_conflicts(all_requirements)
    for package_name, conflict_details in conflicts:
        # Create an issue for each Lambda function involved in the conflict
        for lambda_name in conflict_details['functions']:
            issues.append(DependencyIssue(
                lambda_function=lambda_name,
                package_name=package_name,
                issue_type="conflict",
                details=conflict_details['message'],
                suggested_fix=f"Standardize to a single version across all functions: {conflict_details['versions']}"
            ))
    
    logger.info(f"Dependency validation complete: {len(issues)} issues found")
    return issues


def parse_requirements_file(filepath: str) -> List[Requirement]:
    """
    Parse requirements.txt file into structured requirements.
    
    Args:
        filepath: Path to requirements.txt file
        
    Returns:
        List of Requirement objects
        
    Notes:
        - Skips empty lines and comments (lines starting with #)
        - Handles various requirement formats (package, package==version, package>=version)
        - Preserves line numbers for error reporting
        - Handles inline comments (e.g., "package==1.0  # comment")
    """
    content = safe_read_file(filepath)
    if content is None:
        raise ValueError(f"Could not read {filepath}")
    
    requirements = []
    lines = content.splitlines()
    
    for line_num, line in enumerate(lines, start=1):
        # Remove inline comments
        if '#' in line:
            line = line[:line.index('#')]
        
        # Strip whitespace
        line = line.strip()
        
        # Skip empty lines
        if not line:
            continue
        
        # Skip comment-only lines (already handled above, but be safe)
        if line.startswith('#'):
            continue
        
        # Parse the requirement
        # Pattern: package_name followed by optional version specifier
        # Examples: boto3, boto3==1.26.0, boto3>=1.26.0,<2.0.0
        match = re.match(r'^([a-zA-Z0-9_\-\.]+)(.*)$', line)
        if match:
            package_name = match.group(1)
            version_spec = match.group(2).strip()
            
            requirements.append(Requirement(
                package_name=package_name,
                version_spec=version_spec,
                raw_line=line,
                line_number=line_num
            ))
        else:
            # If we can't parse it, still create a requirement with the full line as package name
            # This will be caught by validate_package_names
            requirements.append(Requirement(
                package_name=line,
                version_spec="",
                raw_line=line,
                line_number=line_num
            ))
    
    return requirements


def validate_package_names(requirements: List[Requirement]) -> List[Tuple[str, str]]:
    """
    Validate package names follow PyPI naming conventions.
    
    Args:
        requirements: List of Requirement objects to validate
        
    Returns:
        List of tuples (package_name, error_message) for invalid names
        
    Notes:
        PyPI package names must:
        - Contain only alphanumeric characters, hyphens, underscores, and periods
        - Not start or end with special characters
        - Be at least 1 character long
        
    Examples:
        Valid: boto3, PyYAML, python-dateutil, requests_oauthlib
        Invalid: -boto3, boto3-, boto3!, @package, ""
    """
    invalid_names = []
    
    # PyPI naming pattern: alphanumeric, hyphens, underscores, periods
    # Must not start or end with special characters
    valid_pattern = re.compile(r'^[a-zA-Z0-9]([a-zA-Z0-9_\-\.]*[a-zA-Z0-9])?$')
    
    for req in requirements:
        package_name = req.package_name
        
        # Check if empty
        if not package_name:
            invalid_names.append((package_name, "Package name cannot be empty"))
            continue
        
        # Check against pattern
        if not valid_pattern.match(package_name):
            error = "Package name must contain only alphanumeric characters, hyphens, underscores, and periods"
            if package_name[0] in '-_.':
                error = "Package name cannot start with special characters"
            elif package_name[-1] in '-_.':
                error = "Package name cannot end with special characters"
            elif not all(c.isalnum() or c in '-_.' for c in package_name):
                error = "Package name contains invalid characters"
            
            invalid_names.append((package_name, error))
    
    return invalid_names


def validate_version_syntax(requirements: List[Requirement]) -> List[Tuple[str, str, str]]:
    """
    Validate version specifications follow PEP 440 syntax.
    
    Args:
        requirements: List of Requirement objects to validate
        
    Returns:
        List of tuples (package_name, version_spec, error_message) for invalid versions
        
    Notes:
        PEP 440 version specifiers include:
        - Exact version: ==1.0.0
        - Greater/less than: >=1.0.0, <=2.0.0, >1.0, <2.0
        - Compatible release: ~=1.0.0 (equivalent to >=1.0.0,<2.0.0)
        - Compound: >=1.0,<2.0 or >=1.0.0,!=1.5.0,<2.0.0
        - No version specifier is also valid (latest version)
        
    Examples:
        Valid: ==1.0.0, >=1.0, <2.0, >=1.0,<2.0, ~=1.0.0, "" (no version)
        Invalid: =1.0.0, >>1.0, 1.0.0 (missing operator), >=1.0.0.0.0
    """
    invalid_versions = []
    
    # PEP 440 version specifier pattern
    # Operators: ==, !=, <=, >=, <, >, ~=
    # Version: digits separated by dots, optional pre-release/post-release/dev suffixes
    version_pattern = re.compile(
        r'^(==|!=|<=|>=|<|>|~=)\s*'  # Operator
        r'(\d+(\.\d+)*'  # Version number (e.g., 1, 1.0, 1.0.0)
        r'([a-zA-Z0-9\-\+\.]*)?)'  # Optional pre/post/dev suffixes
    )
    
    for req in requirements:
        version_spec = req.version_spec
        
        # Empty version spec is valid (means latest version)
        if not version_spec:
            continue
        
        # Split by comma for compound specifiers (e.g., ">=1.0,<2.0")
        parts = [part.strip() for part in version_spec.split(',')]
        
        for part in parts:
            if not part:
                continue
            
            # Check if part matches PEP 440 pattern
            if not version_pattern.match(part):
                error = "Version specifier must follow PEP 440 format (e.g., ==1.0.0, >=1.0, ~=1.0.0)"
                
                # Provide more specific error messages
                if not any(op in part for op in ['==', '!=', '<=', '>=', '<', '>', '~=']):
                    error = "Version specifier missing operator (use ==, >=, <, etc.)"
                elif part.startswith('=') and not part.startswith('=='):
                    error = "Use '==' for exact version match, not '='"
                elif '>>' in part or '<<' in part:
                    error = "Invalid operator (use >=, <=, not >>, <<)"
                
                invalid_versions.append((req.package_name, version_spec, error))
                break  # Only report once per requirement
    
    return invalid_versions


def check_version_conflicts(all_requirements: Dict[str, List[Requirement]]) -> List[Tuple[str, Dict]]:
    """
    Check for conflicting versions of the same package across Lambda functions.
    
    Args:
        all_requirements: Dictionary mapping Lambda function names to their requirements
        
    Returns:
        List of tuples (package_name, conflict_details) where conflict_details contains:
            - 'functions': List of Lambda functions with this package
            - 'versions': List of different version specifications
            - 'message': Human-readable conflict description
            
    Notes:
        - A conflict exists when the same package has different version specifications
        - Empty version specs (latest) are considered different from pinned versions
        - This helps identify potential dependency resolution issues during build
        
    Examples:
        Conflict: user_login has boto3==1.26.0, tax_document_generation has boto3==1.28.0
        No conflict: Both have boto3==1.26.0 or both have boto3 (no version)
    """
    conflicts = []
    
    # Build a map of package_name -> {lambda_function: version_spec}
    package_versions: Dict[str, Dict[str, str]] = {}
    
    for lambda_name, requirements in all_requirements.items():
        for req in requirements:
            package_name = req.package_name
            version_spec = req.version_spec if req.version_spec else "<latest>"
            
            if package_name not in package_versions:
                package_versions[package_name] = {}
            
            package_versions[package_name][lambda_name] = version_spec
    
    # Check for conflicts (same package with different versions)
    for package_name, versions_by_function in package_versions.items():
        unique_versions = set(versions_by_function.values())
        
        # If more than one unique version, we have a conflict
        if len(unique_versions) > 1:
            functions = list(versions_by_function.keys())
            versions = list(unique_versions)
            
            # Build detailed message
            version_details = [
                f"{func}: {versions_by_function[func]}"
                for func in functions
            ]
            message = (
                f"Package '{package_name}' has conflicting versions across Lambda functions: "
                f"{', '.join(version_details)}"
            )
            
            conflicts.append((package_name, {
                'functions': functions,
                'versions': versions,
                'message': message
            }))
    
    return conflicts


def main():
    """CLI entry point for dependency validation."""
    import sys
    from utils import setup_logging
    
    setup_logging(verbose='-v' in sys.argv or '--verbose' in sys.argv)
    
    print("Validating Lambda function dependencies...")
    print()
    
    issues = validate_all_requirements()
    
    if not issues:
        print("✓ No dependency issues found!")
        return 0
    
    print(f"✗ Found {len(issues)} dependency issues:\n")
    
    # Group issues by Lambda function
    issues_by_function: Dict[str, List[DependencyIssue]] = {}
    for issue in issues:
        if issue.lambda_function not in issues_by_function:
            issues_by_function[issue.lambda_function] = []
        issues_by_function[issue.lambda_function].append(issue)
    
    # Print issues grouped by function
    for lambda_name, function_issues in sorted(issues_by_function.items()):
        print(f"Lambda Function: {lambda_name}")
        print("-" * 60)
        
        for issue in function_issues:
            print(f"  Package: {issue.package_name}")
            print(f"  Type: {issue.issue_type}")
            print(f"  Details: {issue.details}")
            if issue.suggested_fix:
                print(f"  Suggested Fix: {issue.suggested_fix}")
            print()
    
    return 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
