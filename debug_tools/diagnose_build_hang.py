"""
Main diagnostic script for SAM build hang issues.

This script orchestrates all diagnostic checks to identify root causes of
SAM build hangs during the PythonPipBuilder:CopySource phase. It coordinates
file system scanning, dependency validation, and SAM configuration validation,
then generates a comprehensive report with actionable recommendations.

Usage:
    python debug_tools/diagnose_build_hang.py [options]

Options:
    -v, --verbose       Enable verbose logging
    -j, --json          Output report in JSON format
    -o, --output FILE   Write report to file instead of stdout
    -h, --help          Show this help message
"""

import sys
import os
import json
import logging
import argparse
from datetime import datetime
from typing import Dict, Any

# Add debug_tools to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from models import DiagnosticReport, FileIssue, DependencyIssue, ConfigIssue
from utils import setup_logging, get_project_root
from scan_file_system import scan_lambda_directories
from validate_dependencies import validate_all_requirements
from validate_sam_config import validate_sam_template


logger = logging.getLogger(__name__)


def run_diagnostics() -> DiagnosticReport:
    """
    Run all diagnostic checks and return comprehensive report.
    
    This function coordinates execution of all diagnostic modules:
    1. File system scanning (symlinks, large files, cache directories)
    2. Dependency validation (package names, versions, conflicts)
    3. SAM configuration validation (CodeUri paths, runtime settings)
    
    Returns:
        DiagnosticReport containing all findings
        
    Notes:
        - Continues diagnostics even if individual checks fail
        - Aggregates all issues into a single report
        - Generates recommendations based on findings
        - Logs progress and errors during execution
    """
    logger.info("=" * 70)
    logger.info("Starting SAM Build Hang Diagnostics")
    logger.info("=" * 70)
    logger.info(f"Project root: {get_project_root()}")
    logger.info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("")
    
    # Initialize report
    report = DiagnosticReport(timestamp=datetime.now())
    
    # Phase 1: File System Scanning
    logger.info("Phase 1/3: Scanning file system...")
    try:
        file_issues = scan_lambda_directories()
        report.file_issues = file_issues
        logger.info(f"✓ File system scan complete: {len(file_issues)} issues found")
    except Exception as e:
        logger.error(f"✗ File system scan failed: {e}", exc_info=True)
        # Add error as a file issue
        report.file_issues.append(FileIssue(
            issue_type='cache_dir',
            path='<scan_error>',
            details=f'File system scan failed: {str(e)}',
            severity='critical',
            fix_available=False
        ))
    
    logger.info("")
    
    # Phase 2: Dependency Validation
    logger.info("Phase 2/3: Validating dependencies...")
    try:
        dependency_issues = validate_all_requirements()
        report.dependency_issues = dependency_issues
        logger.info(f"✓ Dependency validation complete: {len(dependency_issues)} issues found")
    except Exception as e:
        logger.error(f"✗ Dependency validation failed: {e}", exc_info=True)
        # Add error as a dependency issue
        report.dependency_issues.append(DependencyIssue(
            lambda_function='<validation_error>',
            package_name='<unknown>',
            issue_type='invalid_name',
            details=f'Dependency validation failed: {str(e)}',
            suggested_fix='Check requirements.txt files for syntax errors'
        ))
    
    logger.info("")
    
    # Phase 3: SAM Configuration Validation
    logger.info("Phase 3/3: Validating SAM configuration...")
    try:
        config_issues = validate_sam_template()
        report.config_issues = config_issues
        logger.info(f"✓ SAM configuration validation complete: {len(config_issues)} issues found")
    except Exception as e:
        logger.error(f"✗ SAM configuration validation failed: {e}", exc_info=True)
        # Add error as a config issue
        report.config_issues.append(ConfigIssue(
            issue_type='env_config',
            location='<validation_error>',
            details=f'SAM configuration validation failed: {str(e)}',
            suggested_fix='Check template.yaml for syntax errors'
        ))
    
    logger.info("")
    logger.info("=" * 70)
    
    # Generate summary and recommendations
    report.summary = _generate_summary(report)
    report.recommendations = _generate_recommendations(report)
    
    logger.info("Diagnostics complete!")
    logger.info(f"Total issues found: {report.total_issues}")
    logger.info(f"Critical issues: {report.critical_issues}")
    logger.info("=" * 70)
    
    return report


def _generate_summary(report: DiagnosticReport) -> str:
    """
    Generate high-level summary of diagnostic findings.
    
    Args:
        report: DiagnosticReport with all findings
        
    Returns:
        Human-readable summary string
    """
    if not report.has_issues:
        return "No issues detected. SAM build should complete successfully."
    
    summary_parts = []
    
    # File issues summary
    if report.file_issues:
        file_counts = {}
        for issue in report.file_issues:
            file_counts[issue.issue_type] = file_counts.get(issue.issue_type, 0) + 1
        
        file_summary = ", ".join([
            f"{count} {issue_type.replace('_', ' ')}"
            for issue_type, count in sorted(file_counts.items())
        ])
        summary_parts.append(f"File system: {file_summary}")
    
    # Dependency issues summary
    if report.dependency_issues:
        dep_counts = {}
        for issue in report.dependency_issues:
            dep_counts[issue.issue_type] = dep_counts.get(issue.issue_type, 0) + 1
        
        dep_summary = ", ".join([
            f"{count} {issue_type.replace('_', ' ')}"
            for issue_type, count in sorted(dep_counts.items())
        ])
        summary_parts.append(f"Dependencies: {dep_summary}")
    
    # Config issues summary
    if report.config_issues:
        config_counts = {}
        for issue in report.config_issues:
            config_counts[issue.issue_type] = config_counts.get(issue.issue_type, 0) + 1
        
        config_summary = ", ".join([
            f"{count} {issue_type.replace('_', ' ')}"
            for issue_type, count in sorted(config_counts.items())
        ])
        summary_parts.append(f"Configuration: {config_summary}")
    
    return f"Found {report.total_issues} issues. " + "; ".join(summary_parts)


def _generate_recommendations(report: DiagnosticReport) -> list:
    """
    Generate actionable recommendations based on findings.
    
    Args:
        report: DiagnosticReport with all findings
        
    Returns:
        List of recommendation strings
    """
    recommendations = []
    
    if not report.has_issues:
        recommendations.append("No issues detected. You can proceed with SAM build.")
        return recommendations
    
    # Critical issues first
    if report.critical_issues > 0:
        recommendations.append(
            f"⚠️  CRITICAL: {report.critical_issues} critical issues must be resolved before SAM build will succeed."
        )
    
    # File system recommendations
    symlinks = [i for i in report.file_issues if i.issue_type == 'symlink']
    if symlinks:
        recommendations.append(
            f"Remove {len(symlinks)} symlink(s) from Lambda directories. "
            "Symlinks can cause infinite loops during file copying."
        )
    
    cache_dirs = [i for i in report.file_issues if i.issue_type == 'cache_dir']
    if cache_dirs:
        recommendations.append(
            f"Remove {len(cache_dirs)} cache director(ies). "
            "Run: python debug_tools/apply_fixes.py --remove-cache"
        )
    
    large_files = [i for i in report.file_issues if i.issue_type == 'large_file']
    if large_files:
        recommendations.append(
            f"Add {len(large_files)} large file(s) to .gitignore. "
            "Files over 10MB should not be included in Lambda deployments."
        )
    
    gitignore_violations = [i for i in report.file_issues if i.issue_type == 'gitignore_violation']
    if gitignore_violations:
        recommendations.append(
            f"Add {len(gitignore_violations)} file(s) to .gitignore. "
            "Run: python debug_tools/apply_fixes.py --update-gitignore"
        )
    
    # Dependency recommendations
    invalid_names = [i for i in report.dependency_issues if i.issue_type == 'invalid_name']
    if invalid_names:
        recommendations.append(
            f"Fix {len(invalid_names)} invalid package name(s) in requirements.txt files. "
            "Package names must follow PyPI naming conventions."
        )
    
    invalid_versions = [i for i in report.dependency_issues if i.issue_type == 'invalid_version']
    if invalid_versions:
        recommendations.append(
            f"Fix {len(invalid_versions)} invalid version specification(s) in requirements.txt files. "
            "Use PEP 440 syntax (e.g., ==1.0.0, >=1.0,<2.0)."
        )
    
    conflicts = [i for i in report.dependency_issues if i.issue_type == 'conflict']
    if conflicts:
        # Get unique package names with conflicts
        conflict_packages = set(i.package_name for i in conflicts)
        recommendations.append(
            f"Resolve version conflicts for {len(conflict_packages)} package(s) across Lambda functions. "
            "Standardize to a single version for each package."
        )
    
    # Configuration recommendations
    missing_paths = [i for i in report.config_issues if i.issue_type == 'missing_path']
    if missing_paths:
        recommendations.append(
            f"Fix {len(missing_paths)} missing or invalid CodeUri path(s) in template.yaml. "
            "Ensure all Lambda function directories exist."
        )
    
    invalid_runtime = [i for i in report.config_issues if i.issue_type == 'invalid_runtime']
    if invalid_runtime:
        recommendations.append(
            f"Update {len(invalid_runtime)} Lambda function(s) to use Runtime: python3.14 in template.yaml."
        )
    
    duplicate_functions = [i for i in report.config_issues if i.issue_type == 'duplicate_function']
    if duplicate_functions:
        recommendations.append(
            f"Rename {len(duplicate_functions)} duplicate function name(s) in template.yaml. "
            "Each Lambda function must have a unique name."
        )
    
    env_config = [i for i in report.config_issues if i.issue_type == 'env_config']
    if env_config:
        recommendations.append(
            f"Fix {len(env_config)} environment configuration issue(s) in template.yaml. "
            "Ensure Environment parameter is properly configured."
        )
    
    # General recommendations
    if report.has_issues:
        recommendations.append(
            "\nAfter fixing issues, run: sam build --parameter-overrides Environment=local"
        )
        recommendations.append(
            "For automated fixes, run: python debug_tools/apply_fixes.py --dry-run (preview changes)"
        )
    
    return recommendations


def format_report_text(report: DiagnosticReport) -> str:
    """
    Format diagnostic report as human-readable text.
    
    Args:
        report: DiagnosticReport to format
        
    Returns:
        Formatted text report
    """
    lines = []
    
    # Header
    lines.append("=" * 70)
    lines.append("SAM BUILD HANG DIAGNOSTIC REPORT")
    lines.append("=" * 70)
    lines.append(f"Timestamp: {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Project: {get_project_root()}")
    lines.append("")
    
    # Summary
    lines.append("SUMMARY")
    lines.append("-" * 70)
    lines.append(report.summary)
    lines.append(f"Total issues: {report.total_issues}")
    lines.append(f"Critical issues: {report.critical_issues}")
    lines.append("")
    
    # File Issues
    if report.file_issues:
        lines.append("FILE SYSTEM ISSUES")
        lines.append("-" * 70)
        
        # Group by type
        issues_by_type = {}
        for issue in report.file_issues:
            if issue.issue_type not in issues_by_type:
                issues_by_type[issue.issue_type] = []
            issues_by_type[issue.issue_type].append(issue)
        
        for issue_type, issues in sorted(issues_by_type.items()):
            lines.append(f"\n{issue_type.upper().replace('_', ' ')} ({len(issues)}):")
            for issue in issues:
                lines.append(f"  [{issue.severity.upper()}] {issue.path}")
                lines.append(f"    {issue.details}")
                if issue.fix_available:
                    lines.append(f"    ✓ Automated fix available")
        lines.append("")
    
    # Dependency Issues
    if report.dependency_issues:
        lines.append("DEPENDENCY ISSUES")
        lines.append("-" * 70)
        
        # Group by Lambda function
        issues_by_function = {}
        for issue in report.dependency_issues:
            if issue.lambda_function not in issues_by_function:
                issues_by_function[issue.lambda_function] = []
            issues_by_function[issue.lambda_function].append(issue)
        
        for lambda_name, issues in sorted(issues_by_function.items()):
            lines.append(f"\n{lambda_name} ({len(issues)} issues):")
            for issue in issues:
                lines.append(f"  [{issue.issue_type.upper()}] {issue.package_name}")
                lines.append(f"    {issue.details}")
                if issue.suggested_fix:
                    lines.append(f"    Fix: {issue.suggested_fix}")
        lines.append("")
    
    # Configuration Issues
    if report.config_issues:
        lines.append("CONFIGURATION ISSUES")
        lines.append("-" * 70)
        
        # Group by type
        issues_by_type = {}
        for issue in report.config_issues:
            if issue.issue_type not in issues_by_type:
                issues_by_type[issue.issue_type] = []
            issues_by_type[issue.issue_type].append(issue)
        
        for issue_type, issues in sorted(issues_by_type.items()):
            lines.append(f"\n{issue_type.upper().replace('_', ' ')} ({len(issues)}):")
            for issue in issues:
                lines.append(f"  Location: {issue.location}")
                lines.append(f"  {issue.details}")
                if issue.suggested_fix:
                    lines.append(f"  Fix: {issue.suggested_fix}")
        lines.append("")
    
    # Recommendations
    if report.recommendations:
        lines.append("RECOMMENDATIONS")
        lines.append("-" * 70)
        for i, recommendation in enumerate(report.recommendations, 1):
            lines.append(f"{i}. {recommendation}")
        lines.append("")
    
    # Footer
    lines.append("=" * 70)
    if not report.has_issues:
        lines.append("✓ No issues detected. SAM build should complete successfully.")
    else:
        lines.append(f"✗ {report.total_issues} issues detected. Fix issues before running SAM build.")
    lines.append("=" * 70)
    
    return "\n".join(lines)


def format_report_json(report: DiagnosticReport) -> str:
    """
    Format diagnostic report as JSON.
    
    Args:
        report: DiagnosticReport to format
        
    Returns:
        JSON string
    """
    data = {
        'timestamp': report.timestamp.isoformat(),
        'project_root': get_project_root(),
        'summary': report.summary,
        'total_issues': report.total_issues,
        'critical_issues': report.critical_issues,
        'has_issues': report.has_issues,
        'file_issues': [
            {
                'issue_type': issue.issue_type,
                'path': issue.path,
                'details': issue.details,
                'severity': issue.severity,
                'fix_available': issue.fix_available
            }
            for issue in report.file_issues
        ],
        'dependency_issues': [
            {
                'lambda_function': issue.lambda_function,
                'package_name': issue.package_name,
                'issue_type': issue.issue_type,
                'details': issue.details,
                'suggested_fix': issue.suggested_fix
            }
            for issue in report.dependency_issues
        ],
        'config_issues': [
            {
                'issue_type': issue.issue_type,
                'location': issue.location,
                'details': issue.details,
                'suggested_fix': issue.suggested_fix
            }
            for issue in report.config_issues
        ],
        'recommendations': report.recommendations
    }
    
    return json.dumps(data, indent=2)


def main():
    """CLI entry point for running diagnostics."""
    parser = argparse.ArgumentParser(
        description='Diagnose SAM build hang issues',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run diagnostics with default output
  python debug_tools/diagnose_build_hang.py
  
  # Run with verbose logging
  python debug_tools/diagnose_build_hang.py -v
  
  # Output as JSON
  python debug_tools/diagnose_build_hang.py --json
  
  # Save report to file
  python debug_tools/diagnose_build_hang.py -o diagnostic_report.txt
  
  # JSON output to file
  python debug_tools/diagnose_build_hang.py --json -o report.json
        """
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '-j', '--json',
        action='store_true',
        help='Output report in JSON format'
    )
    
    parser.add_argument(
        '-o', '--output',
        type=str,
        metavar='FILE',
        help='Write report to file instead of stdout'
    )
    
    args = parser.parse_args()
    
    # Set up logging
    setup_logging(verbose=args.verbose)
    
    try:
        # Run diagnostics
        report = run_diagnostics()
        
        # Format report
        if args.json:
            output = format_report_json(report)
        else:
            output = format_report_text(report)
        
        # Write output
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output)
            print(f"\nReport written to: {args.output}")
        else:
            print(output)
        
        # Exit with appropriate code
        return 0 if not report.has_issues else 1
        
    except KeyboardInterrupt:
        logger.info("\nDiagnostics interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Diagnostics failed with error: {e}", exc_info=True)
        print(f"\n✗ Diagnostics failed: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
