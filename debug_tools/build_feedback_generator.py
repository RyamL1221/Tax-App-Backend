"""
Build feedback generator for SAM build verification.

This module provides functions to generate user-facing feedback messages
based on build verification results. It consolidates error messages,
provides actionable fix commands, and includes references to documentation.

Usage:
    from debug_tools.build_feedback_generator import (
        generate_build_feedback,
        format_build_error_message,
        format_build_success_message
    )
    
    # Generate feedback from BuildStatus
    feedback = generate_build_feedback(status, verbose=False)
    print(feedback)
"""

import logging
from typing import List, Optional
from datetime import datetime

from debug_tools.models import BuildStatus

logger = logging.getLogger(__name__)


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
        
    Example:
        >>> status = BuildStatus(exists=True, up_to_date=True, ...)
        >>> print(format_build_success_message(status))
        ✅ Build artifacts are valid for UserLoginFunction
    """
    msg = f"✅ Build artifacts are valid for {status.lambda_name}"
    
    if verbose:
        msg += f"\n   Build directory: .aws-sam/build/{status.lambda_name}"
        msg += f"\n   Handler file: {status.handler_file}"
        msg += f"\n   Source mtime: {datetime.fromtimestamp(status.source_mtime)}"
        if status.build_mtime:
            msg += f"\n   Build mtime: {datetime.fromtimestamp(status.build_mtime)}"
    
    return msg


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
        Error message with:
        - Description of the issue
        - SAM build command to run
        - Suggestion to check cache directories (if present)
        - Links to diagnostic tools
        
    Example:
        >>> status = BuildStatus(exists=False, ...)
        >>> print(format_build_error_message(status))
        ⚠️  Build issues for UserLoginFunction:
           • Build directory does not exist
           
           Fix: Run SAM build
           sam build --parameter-overrides Environment=local
           
           See: .kiro/steering/sam-build-guidelines.md
    """
    # Collect all issues
    issues = []
    
    if not status.exists:
        issues.append("Build directory does not exist")
    elif not status.up_to_date:
        issues.append("Build artifacts are older than source files")
    
    if status.exists and not status.handler_present:
        issues.append(f"Handler file '{status.handler_file}' not found in build artifacts")
    
    # Build error message
    msg = f"⚠️  Build issues for {status.lambda_name}:\n"
    for issue in issues:
        msg += f"   • {issue}\n"
    
    # Add cache directory warning if present
    if status.cache_dirs_present and status.cache_dirs_found:
        msg += f"\n   ⚠️  Cache directories found: {', '.join(status.cache_dirs_found)}\n"
        msg += "   Consider running cache cleanup first:\n"
        msg += "   python debug_tools/apply_fixes.py --remove-cache\n"
    
    # Add fix command
    msg += "\n   Fix: Run SAM build\n"
    msg += "   sam build --parameter-overrides Environment=local\n"
    
    # Add reference to guidelines
    msg += "\n   See: .kiro/steering/sam-build-guidelines.md\n"
    
    # Add diagnostic tool suggestions for specific scenarios
    if not status.exists:
        msg += "\n   If build has never been run, see setup guide:\n"
        msg += "   .kiro/steering/local-development.md\n"
    elif status.exists and not status.handler_present:
        msg += "\n   If build is failing, run diagnostics:\n"
        msg += "   python debug_tools/diagnose_build_hang.py\n"
        msg += "   python debug_tools/validate_dependencies.py\n"
    
    # Add verbose details if requested
    if verbose:
        msg += f"\n   Source mtime: {datetime.fromtimestamp(status.source_mtime)}"
        if status.build_mtime:
            msg += f"\n   Build mtime: {datetime.fromtimestamp(status.build_mtime)}"
        msg += f"\n   Build directory: .aws-sam/build/{status.lambda_name}"
    
    return msg


def generate_build_feedback(
    status: BuildStatus,
    verbose: bool = False
) -> str:
    """
    Generate consolidated feedback message for build verification.
    
    This is the main entry point for generating user-facing feedback.
    It handles both success and error cases, providing appropriate
    messages with actionable guidance.
    
    Args:
        status: BuildStatus object from check_build_artifacts()
        verbose: Include detailed timestamps and paths
        
    Returns:
        Formatted feedback message with:
        - Issues found (if any)
        - Actionable fix commands
        - References to documentation
        - Brief confirmation if all checks pass
        
    Example:
        >>> from debug_tools.verify_sam_build import check_build_artifacts
        >>> status = check_build_artifacts("user_login")
        >>> feedback = generate_build_feedback(status)
        >>> print(feedback)
    """
    # Handle error messages from verification
    if status.error_message:
        msg = f"❌ Error: {status.error_message}"
        
        # Add helpful context based on error type
        if "not found in template" in status.error_message:
            msg += "\n\n   Verify that the directory name matches the CodeUri in template.yaml"
            msg += "\n   See: template.yaml"
        elif "Failed to parse template" in status.error_message:
            msg += "\n\n   Validate template syntax:\n"
            msg += "   sam validate --template template.yaml"
        
        return msg
    
    # Check if build is valid
    if status.is_valid:
        return format_build_success_message(status, verbose=verbose)
    
    # Build has issues
    return format_build_error_message(status, verbose=verbose)


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
        
    Example:
        >>> results = verify_all_lambdas()
        >>> summary = format_multiple_lambda_summary(results)
        >>> print(summary)
    """
    if not results:
        return "No Lambda functions found to check."
    
    # Generate individual results
    output_lines = []
    for dir_name, status in results.items():
        feedback = generate_build_feedback(status, verbose=verbose)
        output_lines.append(feedback)
        output_lines.append("")  # Blank line between results
    
    # Generate summary statistics
    total = len(results)
    valid = sum(1 for s in results.values() if s.is_valid)
    errors = sum(1 for s in results.values() if s.error_message)
    
    summary = f"Summary: {valid}/{total} Lambda functions have valid build artifacts"
    if errors > 0:
        summary += f" ({errors} errors)"
    
    output_lines.append(summary)
    
    return "\n".join(output_lines)


def format_cache_warning(cache_dirs: List[str]) -> str:
    """
    Format warning message for cache directories.
    
    Args:
        cache_dirs: List of cache directory names found
        
    Returns:
        Formatted warning message with cleanup command
        
    Example:
        >>> warning = format_cache_warning(['__pycache__', '.pytest_cache'])
        >>> print(warning)
        ⚠️  Cache directories found: __pycache__, .pytest_cache
        Consider running cache cleanup:
        python debug_tools/apply_fixes.py --remove-cache
    """
    if not cache_dirs:
        return ""
    
    msg = f"⚠️  Cache directories found: {', '.join(cache_dirs)}\n"
    msg += "Consider running cache cleanup:\n"
    msg += "python debug_tools/apply_fixes.py --remove-cache"
    
    return msg


def format_build_command(environment: str = "local") -> str:
    """
    Format SAM build command for given environment.
    
    Args:
        environment: Target environment ('local' or 'production')
        
    Returns:
        Formatted SAM build command
        
    Example:
        >>> cmd = format_build_command("local")
        >>> print(cmd)
        sam build --parameter-overrides Environment=local
    """
    return f"sam build --parameter-overrides Environment={environment}"


def format_diagnostic_suggestions(status: BuildStatus) -> str:
    """
    Format diagnostic tool suggestions based on build status.
    
    Args:
        status: BuildStatus object
        
    Returns:
        Formatted suggestions for diagnostic tools to run
        
    Example:
        >>> suggestions = format_diagnostic_suggestions(status)
        >>> print(suggestions)
        Run diagnostics:
        python debug_tools/diagnose_build_hang.py
        python debug_tools/validate_dependencies.py
    """
    suggestions = []
    
    if not status.exists:
        suggestions.append("If this is first-time setup:")
        suggestions.append(".kiro/steering/local-development.md")
    
    if status.exists and not status.handler_present:
        suggestions.append("If build is failing, run diagnostics:")
        suggestions.append("python debug_tools/diagnose_build_hang.py")
        suggestions.append("python debug_tools/validate_dependencies.py")
    
    if status.cache_dirs_present:
        suggestions.append("Check for cache directory issues:")
        suggestions.append("python debug_tools/apply_fixes.py --remove-cache")
    
    if not suggestions:
        return ""
    
    return "\n".join(suggestions)


# Validation: Requirements 3.1, 3.3, 3.4, 4.2
# This module provides consolidated feedback message generation (3.1),
# error message formatting with commands and references (3.3, 3.4),
# and brief confirmation messages for successful validation (4.2).
