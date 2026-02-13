"""
Data models for diagnostic reports and issues.

This module defines the data structures used throughout the diagnostic tools
to represent findings, issues, and results.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class FileIssue:
    """
    Represents a file system issue detected during scanning.
    
    Attributes:
        issue_type: Type of issue ('symlink', 'large_file', 'cache_dir', 'gitignore_violation')
        path: Path to the problematic file or directory
        details: Human-readable description of the issue
        severity: Severity level ('critical', 'warning', 'info')
        fix_available: Whether an automated fix is available
    """
    issue_type: str
    path: str
    details: str
    severity: str
    fix_available: bool
    
    def __post_init__(self):
        """Validate issue_type and severity values."""
        valid_types = {'symlink', 'large_file', 'cache_dir', 'gitignore_violation'}
        if self.issue_type not in valid_types:
            raise ValueError(f"Invalid issue_type: {self.issue_type}. Must be one of {valid_types}")
        
        valid_severities = {'critical', 'warning', 'info'}
        if self.severity not in valid_severities:
            raise ValueError(f"Invalid severity: {self.severity}. Must be one of {valid_severities}")


@dataclass
class DependencyIssue:
    """
    Represents a dependency validation issue.
    
    Attributes:
        lambda_function: Name of the Lambda function with the issue
        package_name: Name of the problematic package
        issue_type: Type of issue ('invalid_name', 'invalid_version', 'conflict', 'incompatible')
        details: Human-readable description of the issue
        suggested_fix: Optional suggestion for fixing the issue
    """
    lambda_function: str
    package_name: str
    issue_type: str
    details: str
    suggested_fix: Optional[str] = None
    
    def __post_init__(self):
        """Validate issue_type values."""
        valid_types = {'invalid_name', 'invalid_version', 'conflict', 'incompatible'}
        if self.issue_type not in valid_types:
            raise ValueError(f"Invalid issue_type: {self.issue_type}. Must be one of {valid_types}")


@dataclass
class ConfigIssue:
    """
    Represents a SAM configuration issue.
    
    Attributes:
        issue_type: Type of issue ('missing_path', 'duplicate_function', 'invalid_runtime', 'env_config')
        location: Location in template.yaml (line number or section name)
        details: Human-readable description of the issue
        suggested_fix: Optional suggestion for fixing the issue
    """
    issue_type: str
    location: str
    details: str
    suggested_fix: Optional[str] = None
    
    def __post_init__(self):
        """Validate issue_type values."""
        valid_types = {'missing_path', 'duplicate_function', 'invalid_runtime', 'env_config'}
        if self.issue_type not in valid_types:
            raise ValueError(f"Invalid issue_type: {self.issue_type}. Must be one of {valid_types}")


@dataclass
class DiagnosticReport:
    """
    Comprehensive diagnostic report containing all findings.
    
    Attributes:
        file_issues: List of file system issues detected
        dependency_issues: List of dependency validation issues
        config_issues: List of SAM configuration issues
        timestamp: When the diagnostic was run
        summary: High-level summary of findings
        recommendations: List of recommended actions to resolve issues
    """
    file_issues: List[FileIssue] = field(default_factory=list)
    dependency_issues: List[DependencyIssue] = field(default_factory=list)
    config_issues: List[ConfigIssue] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    summary: str = ""
    recommendations: List[str] = field(default_factory=list)
    
    @property
    def total_issues(self) -> int:
        """Return total number of issues found."""
        return len(self.file_issues) + len(self.dependency_issues) + len(self.config_issues)
    
    @property
    def critical_issues(self) -> int:
        """Return number of critical issues found."""
        critical_file_issues = sum(1 for issue in self.file_issues if issue.severity == 'critical')
        # All dependency and config issues are considered critical
        return critical_file_issues + len(self.dependency_issues) + len(self.config_issues)
    
    @property
    def has_issues(self) -> bool:
        """Return True if any issues were found."""
        return self.total_issues > 0


@dataclass
class BuildResult:
    """
    Result of build verification.
    
    Attributes:
        success: Whether the build completed successfully
        duration_seconds: How long the build took
        output: Captured stdout/stderr from build process
        errors: List of error messages encountered
        artifacts_verified: Whether build artifacts were verified
        dependencies_verified: Whether dependencies were verified
    """
    success: bool
    duration_seconds: float
    output: str
    errors: List[str] = field(default_factory=list)
    artifacts_verified: bool = False
    dependencies_verified: bool = False
    
    @property
    def fully_verified(self) -> bool:
        """Return True if build succeeded and all verifications passed."""
        return self.success and self.artifacts_verified and self.dependencies_verified


@dataclass
class FixReport:
    """
    Report of fixes applied by the automated fix tool.
    
    Attributes:
        fixes_applied: Number of fixes successfully applied
        fixes_failed: Number of fixes that failed
        backup_path: Path to backup created before fixes
        details: List of detailed descriptions of each fix
        dry_run: Whether this was a dry run (no actual changes)
    """
    fixes_applied: int = 0
    fixes_failed: int = 0
    backup_path: Optional[str] = None
    details: List[str] = field(default_factory=list)
    dry_run: bool = False
    
    @property
    def success_rate(self) -> float:
        """Return percentage of successful fixes."""
        total = self.fixes_applied + self.fixes_failed
        if total == 0:
            return 0.0
        return (self.fixes_applied / total) * 100.0


@dataclass
class BuildStatus:
    """
    Status of SAM build artifacts for a Lambda function.
    
    Attributes:
        exists: Whether .aws-sam/build/<LambdaName> directory exists
        up_to_date: Whether build artifacts are newer than source files
        handler_present: Whether handler module exists in build directory
        lambda_name: Lambda function name from template (e.g., 'UserLoginFunction')
        lambda_dir: Lambda source directory (e.g., 'user_login')
        handler_file: Handler filename (e.g., 'app.py')
        source_mtime: Most recent modification time of source files
        build_mtime: Modification time of build directory, None if not exists
        error_message: Error message if verification failed
        cache_dirs_present: Whether cache directories exist in Lambda directory
        cache_dirs_found: List of cache directories found
    """
    exists: bool
    up_to_date: bool
    handler_present: bool
    lambda_name: str
    lambda_dir: str
    handler_file: str
    source_mtime: float
    build_mtime: Optional[float]
    error_message: Optional[str] = None
    cache_dirs_present: bool = False
    cache_dirs_found: List[str] = field(default_factory=list)
    
    @property
    def is_valid(self) -> bool:
        """Return True if build is valid (exists, up-to-date, handler present)."""
        return self.exists and self.up_to_date and self.handler_present
    
    @property
    def needs_build(self) -> bool:
        """Return True if build is needed."""
        return not self.exists or not self.up_to_date or not self.handler_present


@dataclass
class LambdaConfig:
    """
    Configuration for a Lambda function from SAM template.
    
    Attributes:
        name: Function name (e.g., 'UserLoginFunction')
        code_uri: CodeUri from template (e.g., 'user_login/')
        handler: Full handler string (e.g., 'app.lambda_handler')
        handler_file: Handler filename (e.g., 'app.py')
        handler_function: Handler function name (e.g., 'lambda_handler')
    """
    name: str
    code_uri: str
    handler: str
    handler_file: str
    handler_function: str
