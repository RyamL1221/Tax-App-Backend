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
