"""
Unit tests for apply_fixes module.

Tests the automated fix tool functions including cache directory removal,
.gitignore updates, backup creation, and dry-run mode.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# Add debug_tools to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from models import DiagnosticReport, FileIssue, DependencyIssue, ConfigIssue
from apply_fixes import (
    apply_all_fixes,
    remove_cache_directories,
    update_gitignore,
    create_backup,
    _file_path_to_gitignore_pattern
)


class TestRemoveCacheDirectories:
    """Test cache directory removal functionality."""
    
    def test_remove_single_cache_directory(self, tmp_path):
        """Test removing a single cache directory."""
        # Create cache directory
        cache_dir = tmp_path / "__pycache__"
        cache_dir.mkdir()
        (cache_dir / "test.pyc").write_text("test")
        
        assert cache_dir.exists()
        
        # Remove cache directory
        removed = remove_cache_directories([str(cache_dir)], dry_run=False)
        
        assert removed == 1
        assert not cache_dir.exists()
    
    def test_remove_multiple_cache_directories(self, tmp_path):
        """Test removing multiple cache directories."""
        # Create multiple cache directories
        cache_dirs = []
        for name in ["__pycache__", ".pytest_cache", ".aws-sam"]:
            cache_dir = tmp_path / name
            cache_dir.mkdir()
            cache_dirs.append(str(cache_dir))
        
        # Remove all cache directories
        removed = remove_cache_directories(cache_dirs, dry_run=False)
        
        assert removed == 3
        for cache_dir in cache_dirs:
            assert not os.path.exists(cache_dir)
    
    def test_dry_run_does_not_remove(self, tmp_path):
        """Test that dry-run mode doesn't actually remove directories."""
        # Create cache directory
        cache_dir = tmp_path / "__pycache__"
        cache_dir.mkdir()
        
        # Dry run
        removed = remove_cache_directories([str(cache_dir)], dry_run=True)
        
        assert removed == 1
        assert cache_dir.exists()  # Should still exist
    
    def test_handles_nonexistent_directory(self, tmp_path):
        """Test handling of nonexistent directory."""
        nonexistent = tmp_path / "does_not_exist"
        
        # Should not raise error
        removed = remove_cache_directories([str(nonexistent)], dry_run=False)
        
        assert removed == 0
    
    def test_handles_file_instead_of_directory(self, tmp_path):
        """Test handling when path is a file, not a directory."""
        # Create file instead of directory
        file_path = tmp_path / "test.txt"
        file_path.write_text("test")
        
        # Should not raise error
        removed = remove_cache_directories([str(file_path)], dry_run=False)
        
        assert removed == 0
        assert file_path.exists()  # File should not be removed


class TestUpdateGitignore:
    """Test .gitignore update functionality."""
    
    def test_add_patterns_to_new_gitignore(self, tmp_path, monkeypatch):
        """Test adding patterns to a new .gitignore file."""
        # Mock get_project_root to return tmp_path
        monkeypatch.setattr('apply_fixes.get_project_root', lambda: str(tmp_path))
        
        gitignore_path = tmp_path / ".gitignore"
        assert not gitignore_path.exists()
        
        # Add patterns
        files = [
            str(tmp_path / "large_file.bin"),
            str(tmp_path / "test.pyc")
        ]
        added = update_gitignore(files, dry_run=False)
        
        assert added == 2
        assert gitignore_path.exists()
        
        content = gitignore_path.read_text()
        assert "large_file.bin" in content
        assert "*.pyc" in content
    
    def test_add_patterns_to_existing_gitignore(self, tmp_path, monkeypatch):
        """Test adding patterns to existing .gitignore file."""
        # Mock get_project_root
        monkeypatch.setattr('apply_fixes.get_project_root', lambda: str(tmp_path))
        
        # Create existing .gitignore
        gitignore_path = tmp_path / ".gitignore"
        gitignore_path.write_text("# Existing patterns\n*.log\n")
        
        # Add new patterns
        files = [str(tmp_path / "test.pyc")]
        added = update_gitignore(files, dry_run=False)
        
        assert added == 1
        
        content = gitignore_path.read_text()
        assert "# Existing patterns" in content
        assert "*.log" in content
        assert "*.pyc" in content
    
    def test_avoids_duplicate_patterns(self, tmp_path, monkeypatch):
        """Test that duplicate patterns are not added."""
        # Mock get_project_root
        monkeypatch.setattr('apply_fixes.get_project_root', lambda: str(tmp_path))
        
        # Create .gitignore with existing pattern
        gitignore_path = tmp_path / ".gitignore"
        gitignore_path.write_text("*.pyc\n")
        
        # Try to add same pattern
        files = [str(tmp_path / "test.pyc")]
        added = update_gitignore(files, dry_run=False)
        
        assert added == 0  # No new patterns added
    
    def test_dry_run_does_not_modify_gitignore(self, tmp_path, monkeypatch):
        """Test that dry-run mode doesn't modify .gitignore."""
        # Mock get_project_root
        monkeypatch.setattr('apply_fixes.get_project_root', lambda: str(tmp_path))
        
        gitignore_path = tmp_path / ".gitignore"
        original_content = "# Original\n*.log\n"
        gitignore_path.write_text(original_content)
        
        # Dry run
        files = [str(tmp_path / "test.pyc")]
        added = update_gitignore(files, dry_run=True)
        
        assert added == 1  # Would add 1 pattern
        assert gitignore_path.read_text() == original_content  # Unchanged


class TestFilePathToGitignorePattern:
    """Test conversion of file paths to .gitignore patterns."""
    
    def test_cache_directory_pattern(self):
        """Test cache directory converts to wildcard pattern."""
        pattern = _file_path_to_gitignore_pattern("lambda/__pycache__", "/project")
        assert pattern == "__pycache__/"
    
    def test_pyc_file_pattern(self):
        """Test .pyc file converts to wildcard pattern."""
        pattern = _file_path_to_gitignore_pattern("lambda/test.pyc", "/project")
        assert pattern == "*.pyc"
    
    def test_ds_store_pattern(self):
        """Test .DS_Store file pattern."""
        pattern = _file_path_to_gitignore_pattern("lambda/.DS_Store", "/project")
        assert pattern == ".DS_Store"
    
    def test_large_file_pattern(self):
        """Test large file uses relative path."""
        pattern = _file_path_to_gitignore_pattern("/project/lambda/large.bin", "/project")
        assert pattern == "lambda/large.bin"


class TestCreateBackup:
    """Test backup creation functionality."""
    
    def test_create_backup_creates_directory(self, tmp_path, monkeypatch):
        """Test that backup creates .backups directory."""
        # Mock get_project_root
        monkeypatch.setattr('apply_fixes.get_project_root', lambda: str(tmp_path))
        
        # Create some files to backup
        (tmp_path / "test.txt").write_text("test content")
        
        # Create backup
        backup_path = create_backup(str(tmp_path))
        
        assert os.path.exists(backup_path)
        assert ".backups" in backup_path
        assert os.path.exists(os.path.join(backup_path, "test.txt"))
    
    def test_backup_excludes_cache_directories(self, tmp_path, monkeypatch):
        """Test that backup excludes cache directories."""
        # Mock get_project_root
        monkeypatch.setattr('apply_fixes.get_project_root', lambda: str(tmp_path))
        
        # Create cache directory
        cache_dir = tmp_path / "__pycache__"
        cache_dir.mkdir()
        (cache_dir / "test.pyc").write_text("test")
        
        # Create regular file
        (tmp_path / "test.txt").write_text("test")
        
        # Create backup
        backup_path = create_backup(str(tmp_path))
        
        # Backup should not include cache directory
        assert not os.path.exists(os.path.join(backup_path, "__pycache__"))
        assert os.path.exists(os.path.join(backup_path, "test.txt"))
    
    def test_backup_has_timestamp(self, tmp_path, monkeypatch):
        """Test that backup directory name includes timestamp."""
        # Mock get_project_root
        monkeypatch.setattr('apply_fixes.get_project_root', lambda: str(tmp_path))
        
        # Create backup
        backup_path = create_backup(str(tmp_path))
        
        # Check timestamp format in path
        backup_name = os.path.basename(backup_path)
        assert backup_name.startswith("backup_")
        assert len(backup_name) > len("backup_")


class TestApplyAllFixes:
    """Test the main apply_all_fixes function."""
    
    def test_apply_fixes_with_no_issues(self):
        """Test applying fixes when there are no issues."""
        report = DiagnosticReport()
        
        fix_report = apply_all_fixes(report, dry_run=True)
        
        assert fix_report.fixes_applied == 0
        assert fix_report.fixes_failed == 0
        assert "No issues" in fix_report.details[0]
    
    def test_apply_fixes_removes_cache_directories(self, tmp_path, monkeypatch):
        """Test that apply_all_fixes removes cache directories."""
        # Mock get_project_root
        monkeypatch.setattr('apply_fixes.get_project_root', lambda: str(tmp_path))
        
        # Create cache directory
        cache_dir = tmp_path / "__pycache__"
        cache_dir.mkdir()
        
        # Create diagnostic report with cache directory issue
        report = DiagnosticReport()
        report.file_issues.append(FileIssue(
            issue_type='cache_dir',
            path=str(cache_dir),
            details='Cache directory',
            severity='warning',
            fix_available=True
        ))
        
        # Apply fixes (not dry run)
        fix_report = apply_all_fixes(report, dry_run=False)
        
        assert fix_report.fixes_applied >= 1
        assert not cache_dir.exists()
    
    def test_apply_fixes_updates_gitignore(self, tmp_path, monkeypatch):
        """Test that apply_all_fixes updates .gitignore."""
        # Mock get_project_root
        monkeypatch.setattr('apply_fixes.get_project_root', lambda: str(tmp_path))
        
        # Create diagnostic report with large file issue
        report = DiagnosticReport()
        report.file_issues.append(FileIssue(
            issue_type='large_file',
            path=str(tmp_path / "large.bin"),
            details='Large file',
            severity='warning',
            fix_available=True
        ))
        
        # Apply fixes (not dry run)
        fix_report = apply_all_fixes(report, dry_run=False)
        
        assert fix_report.fixes_applied >= 1
        
        gitignore_path = tmp_path / ".gitignore"
        assert gitignore_path.exists()
        assert "large.bin" in gitignore_path.read_text()
    
    def test_dry_run_creates_no_backup(self, tmp_path, monkeypatch):
        """Test that dry-run mode doesn't create backup."""
        # Mock get_project_root
        monkeypatch.setattr('apply_fixes.get_project_root', lambda: str(tmp_path))
        
        # Create diagnostic report
        report = DiagnosticReport()
        report.file_issues.append(FileIssue(
            issue_type='cache_dir',
            path=str(tmp_path / "__pycache__"),
            details='Cache directory',
            severity='warning',
            fix_available=True
        ))
        
        # Apply fixes in dry-run mode
        fix_report = apply_all_fixes(report, dry_run=True)
        
        assert fix_report.backup_path is None
        assert fix_report.dry_run is True
    
    def test_reports_symlinks_for_manual_review(self):
        """Test that symlinks are reported but not automatically fixed."""
        report = DiagnosticReport()
        report.file_issues.append(FileIssue(
            issue_type='symlink',
            path='/path/to/symlink',
            details='Symlink detected',
            severity='critical',
            fix_available=False
        ))
        
        fix_report = apply_all_fixes(report, dry_run=True)
        
        # Check that symlinks are mentioned in details
        details_text = " ".join(fix_report.details)
        assert "symlink" in details_text.lower()
        assert "manual" in details_text.lower()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
