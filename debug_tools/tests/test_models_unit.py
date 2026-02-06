"""
Unit tests for data models.

Tests the data model classes to ensure they correctly validate inputs,
calculate properties, and handle edge cases.
"""

import pytest
from datetime import datetime
from debug_tools.models import (
    FileIssue,
    DependencyIssue,
    ConfigIssue,
    DiagnosticReport,
    BuildResult,
    FixReport
)


class TestFileIssue:
    """Tests for FileIssue data model."""
    
    def test_valid_file_issue_creation(self):
        """Test creating a valid FileIssue."""
        issue = FileIssue(
            issue_type='large_file',
            path='/path/to/large_file.pdf',
            details='File is 15MB, exceeds 10MB threshold',
            severity='warning',
            fix_available=True
        )
        
        assert issue.issue_type == 'large_file'
        assert issue.path == '/path/to/large_file.pdf'
        assert issue.severity == 'warning'
        assert issue.fix_available is True
    
    def test_invalid_issue_type_raises_error(self):
        """Test that invalid issue_type raises ValueError."""
        with pytest.raises(ValueError, match="Invalid issue_type"):
            FileIssue(
                issue_type='invalid_type',
                path='/path/to/file',
                details='Some details',
                severity='warning',
                fix_available=False
            )
    
    def test_invalid_severity_raises_error(self):
        """Test that invalid severity raises ValueError."""
        with pytest.raises(ValueError, match="Invalid severity"):
            FileIssue(
                issue_type='large_file',
                path='/path/to/file',
                details='Some details',
                severity='invalid_severity',
                fix_available=False
            )
    
    def test_all_valid_issue_types(self):
        """Test all valid issue types can be created."""
        valid_types = ['symlink', 'large_file', 'cache_dir', 'gitignore_violation']
        
        for issue_type in valid_types:
            issue = FileIssue(
                issue_type=issue_type,
                path='/path/to/file',
                details='Test',
                severity='info',
                fix_available=False
            )
            assert issue.issue_type == issue_type
    
    def test_all_valid_severities(self):
        """Test all valid severities can be created."""
        valid_severities = ['critical', 'warning', 'info']
        
        for severity in valid_severities:
            issue = FileIssue(
                issue_type='large_file',
                path='/path/to/file',
                details='Test',
                severity=severity,
                fix_available=False
            )
            assert issue.severity == severity


class TestDependencyIssue:
    """Tests for DependencyIssue data model."""
    
    def test_valid_dependency_issue_creation(self):
        """Test creating a valid DependencyIssue."""
        issue = DependencyIssue(
            lambda_function='user_login',
            package_name='invalid-package-name!',
            issue_type='invalid_name',
            details='Package name contains invalid characters',
            suggested_fix='Use valid package name: invalid_package_name'
        )
        
        assert issue.lambda_function == 'user_login'
        assert issue.package_name == 'invalid-package-name!'
        assert issue.issue_type == 'invalid_name'
        assert issue.suggested_fix is not None
    
    def test_dependency_issue_without_suggested_fix(self):
        """Test creating DependencyIssue without suggested fix."""
        issue = DependencyIssue(
            lambda_function='user_login',
            package_name='some-package',
            issue_type='incompatible',
            details='Package not compatible with Python 3.14'
        )
        
        assert issue.suggested_fix is None
    
    def test_invalid_issue_type_raises_error(self):
        """Test that invalid issue_type raises ValueError."""
        with pytest.raises(ValueError, match="Invalid issue_type"):
            DependencyIssue(
                lambda_function='user_login',
                package_name='package',
                issue_type='invalid_type',
                details='Details'
            )
    
    def test_all_valid_issue_types(self):
        """Test all valid issue types can be created."""
        valid_types = ['invalid_name', 'invalid_version', 'conflict', 'incompatible']
        
        for issue_type in valid_types:
            issue = DependencyIssue(
                lambda_function='test_function',
                package_name='test-package',
                issue_type=issue_type,
                details='Test'
            )
            assert issue.issue_type == issue_type


class TestConfigIssue:
    """Tests for ConfigIssue data model."""
    
    def test_valid_config_issue_creation(self):
        """Test creating a valid ConfigIssue."""
        issue = ConfigIssue(
            issue_type='missing_path',
            location='line 45',
            details='CodeUri path does not exist: nonexistent_function/',
            suggested_fix='Create directory or fix CodeUri path'
        )
        
        assert issue.issue_type == 'missing_path'
        assert issue.location == 'line 45'
        assert issue.suggested_fix is not None
    
    def test_invalid_issue_type_raises_error(self):
        """Test that invalid issue_type raises ValueError."""
        with pytest.raises(ValueError, match="Invalid issue_type"):
            ConfigIssue(
                issue_type='invalid_type',
                location='line 1',
                details='Details'
            )
    
    def test_all_valid_issue_types(self):
        """Test all valid issue types can be created."""
        valid_types = ['missing_path', 'duplicate_function', 'invalid_runtime', 'env_config']
        
        for issue_type in valid_types:
            issue = ConfigIssue(
                issue_type=issue_type,
                location='line 1',
                details='Test'
            )
            assert issue.issue_type == issue_type


class TestDiagnosticReport:
    """Tests for DiagnosticReport data model."""
    
    def test_empty_diagnostic_report(self):
        """Test creating an empty diagnostic report."""
        report = DiagnosticReport()
        
        assert report.total_issues == 0
        assert report.critical_issues == 0
        assert not report.has_issues
        assert len(report.file_issues) == 0
        assert len(report.dependency_issues) == 0
        assert len(report.config_issues) == 0
    
    def test_diagnostic_report_with_issues(self):
        """Test diagnostic report with various issues."""
        file_issue = FileIssue(
            issue_type='large_file',
            path='/path/to/file',
            details='Large file',
            severity='warning',
            fix_available=True
        )
        
        dep_issue = DependencyIssue(
            lambda_function='user_login',
            package_name='bad-package',
            issue_type='invalid_name',
            details='Invalid package name'
        )
        
        config_issue = ConfigIssue(
            issue_type='missing_path',
            location='line 10',
            details='Path not found'
        )
        
        report = DiagnosticReport(
            file_issues=[file_issue],
            dependency_issues=[dep_issue],
            config_issues=[config_issue],
            summary='Found 3 issues',
            recommendations=['Fix the issues']
        )
        
        assert report.total_issues == 3
        assert report.has_issues
        assert len(report.recommendations) == 1
    
    def test_critical_issues_count(self):
        """Test counting critical issues."""
        critical_file = FileIssue(
            issue_type='symlink',
            path='/path/to/link',
            details='Symlink detected',
            severity='critical',
            fix_available=False
        )
        
        warning_file = FileIssue(
            issue_type='large_file',
            path='/path/to/file',
            details='Large file',
            severity='warning',
            fix_available=True
        )
        
        dep_issue = DependencyIssue(
            lambda_function='user_login',
            package_name='bad-package',
            issue_type='invalid_name',
            details='Invalid'
        )
        
        report = DiagnosticReport(
            file_issues=[critical_file, warning_file],
            dependency_issues=[dep_issue]
        )
        
        # 1 critical file issue + 1 dependency issue (all deps are critical)
        assert report.critical_issues == 2
    
    def test_timestamp_is_set(self):
        """Test that timestamp is automatically set."""
        report = DiagnosticReport()
        
        assert isinstance(report.timestamp, datetime)
        assert report.timestamp <= datetime.now()


class TestBuildResult:
    """Tests for BuildResult data model."""
    
    def test_successful_build_result(self):
        """Test creating a successful build result."""
        result = BuildResult(
            success=True,
            duration_seconds=45.5,
            output='Build completed successfully',
            artifacts_verified=True,
            dependencies_verified=True
        )
        
        assert result.success
        assert result.duration_seconds == 45.5
        assert result.fully_verified
        assert len(result.errors) == 0
    
    def test_failed_build_result(self):
        """Test creating a failed build result."""
        result = BuildResult(
            success=False,
            duration_seconds=120.0,
            output='Build failed',
            errors=['Error 1', 'Error 2']
        )
        
        assert not result.success
        assert not result.fully_verified
        assert len(result.errors) == 2
    
    def test_build_success_but_not_verified(self):
        """Test build succeeded but verification failed."""
        result = BuildResult(
            success=True,
            duration_seconds=50.0,
            output='Build completed',
            artifacts_verified=False,
            dependencies_verified=True
        )
        
        assert result.success
        assert not result.fully_verified


class TestFixReport:
    """Tests for FixReport data model."""
    
    def test_empty_fix_report(self):
        """Test creating an empty fix report."""
        report = FixReport()
        
        assert report.fixes_applied == 0
        assert report.fixes_failed == 0
        assert report.success_rate == 0.0
        assert not report.dry_run
    
    def test_fix_report_with_successful_fixes(self):
        """Test fix report with successful fixes."""
        report = FixReport(
            fixes_applied=5,
            fixes_failed=0,
            backup_path='/backups/backup_20240101_120000',
            details=['Fixed issue 1', 'Fixed issue 2', 'Fixed issue 3', 'Fixed issue 4', 'Fixed issue 5']
        )
        
        assert report.fixes_applied == 5
        assert report.success_rate == 100.0
        assert report.backup_path is not None
    
    def test_fix_report_with_failures(self):
        """Test fix report with some failures."""
        report = FixReport(
            fixes_applied=3,
            fixes_failed=2,
            details=['Fixed 1', 'Fixed 2', 'Fixed 3', 'Failed 1', 'Failed 2']
        )
        
        assert report.fixes_applied == 3
        assert report.fixes_failed == 2
        assert report.success_rate == 60.0
    
    def test_dry_run_fix_report(self):
        """Test dry run fix report."""
        report = FixReport(
            fixes_applied=0,
            fixes_failed=0,
            details=['Would fix issue 1', 'Would fix issue 2'],
            dry_run=True
        )
        
        assert report.dry_run
        assert len(report.details) == 2
