"""
Workspace Changelog Utilities for Workspace Organization.

This module provides utilities for logging file operations to the workspace
organization changelog. It integrates with the FileRelocator class to document:
- File moves with source and destination paths
- File deletions with rationale
- Before/after directory structure comparisons
- Operation summaries and statistics

All operations are logged to docs/CHANGELOG_WORKSPACE_ORGANIZATION.md
"""

import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Set


@dataclass
class DirectorySnapshot:
    """
    Snapshot of directory structure at a point in time.
    
    Attributes:
        timestamp: When the snapshot was taken
        root_files: List of files in root directory
        subdirectory_files: Dict mapping subdirectory to list of files
        total_files: Total number of files
        total_size: Total size in bytes
    """
    timestamp: str
    root_files: List[str]
    subdirectory_files: Dict[str, List[str]]
    total_files: int
    total_size: int


class WorkspaceChangelogWriter:
    """
    Handles writing file operations to the workspace organization changelog.
    """
    
    def __init__(
        self,
        changelog_path: Optional[Path] = None,
        project_root: Optional[Path] = None
    ):
        """
        Initialize the changelog writer.
        
        Args:
            changelog_path: Path to changelog file (defaults to docs/CHANGELOG_WORKSPACE_ORGANIZATION.md)
            project_root: Root directory of the project (defaults to current directory's parent)
        """
        if project_root is None:
            # Assume we're in scripts/ directory, go up one level
            project_root = Path(__file__).parent.parent
        
        self.project_root = Path(project_root).resolve()
        
        if changelog_path is None:
            changelog_path = self.project_root / 'docs' / 'CHANGELOG_WORKSPACE_ORGANIZATION.md'
        
        self.changelog_path = Path(changelog_path)
        
        # Ensure changelog exists
        if not self.changelog_path.exists():
            self._initialize_changelog()
    
    def _initialize_changelog(self):
        """Create a new changelog file with initial structure."""
        self.changelog_path.parent.mkdir(parents=True, exist_ok=True)
        
        initial_content = """# Workspace Organization Changelog

## Overview

This changelog documents all file relocations, deletions, and organizational changes made to maintain a clean and well-organized workspace structure.

---

## Guidelines Applied

### Root Directory Rules

**Essential Files Only**:
- README.md - Project overview
- ORGANIZATION.md - Project structure guide
- Makefile - Build and deployment commands
- template.yaml - SAM template
- docker-compose.yml - LocalStack configuration
- Configuration files (.gitignore, .env.example, etc.)

**Not Allowed in Root**:
- Temporary test output files
- Debug/inspection output files
- Verification scripts (belong in scripts/)
- Sample PDFs (belong in samples/)

### Documentation Organization

**docs/architecture/** - System design and field mappings
**docs/testing/** - Test results and verification reports
**docs/development/** - Setup guides and workflows
**docs/examples/** - Sample JSON payloads

### File Placement Decision Tree

1. **Is it a Python script?**
   - Utility/verification → `scripts/`
   - Lambda function → `<lambda_name>/`
   - Test → `<lambda_name>/tests/`

2. **Is it a PDF file?**
   - Sample/template → `samples/`
   - Test output → `samples/` (or delete if temporary)

3. **Is it a text file?**
   - Documentation → `docs/<category>/`
   - Debug output → Evaluate for value, likely delete
   - Configuration → Root (if essential)

4. **Is it temporary?**
   - Add to .gitignore
   - Delete after use

---

## References

- **Spec**: `.kiro/specs/workspace-organization/`
- **Steering File**: `.kiro/steering/workspace-organization.md`
- **Organization Guide**: `ORGANIZATION.md`
- **Documentation Index**: `docs/README.md`

"""
        
        with open(self.changelog_path, 'w', encoding='utf-8') as f:
            f.write(initial_content)
    
    def log_file_move(
        self,
        source_path: str,
        destination_path: str,
        rationale: str,
        references_updated: Optional[List[str]] = None,
        task_id: Optional[str] = None
    ) -> None:
        """
        Log a file move operation to the changelog.
        
        Args:
            source_path: Original file path (relative to project root)
            destination_path: New file path (relative to project root)
            rationale: Reason for the move
            references_updated: List of files where references were updated
            task_id: Optional task identifier (e.g., "Task 1.1")
        
        Example:
            >>> writer = WorkspaceChangelogWriter()
            >>> writer.log_file_move(
            ...     'verify_fields.py',
            ...     'scripts/verify_fields.py',
            ...     'Verification utility script',
            ...     references_updated=['README.md'],
            ...     task_id='Task 1.1'
            ... )
        """
        if references_updated is None:
            references_updated = []
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        entry = f"\n### File Move: {source_path} → {destination_path}\n\n"
        entry += f"**Date**: {timestamp}\n"
        
        if task_id:
            entry += f"**Task**: {task_id}\n"
        
        entry += f"**Rationale**: {rationale}\n\n"
        
        if references_updated:
            entry += "**References Updated**:\n"
            for ref_file in references_updated:
                entry += f"- {ref_file}\n"
            entry += "\n"
        
        entry += "---\n"
        
        self._append_to_changelog(entry)
    
    def log_file_deletion(
        self,
        file_path: str,
        rationale: str,
        file_size: Optional[int] = None,
        task_id: Optional[str] = None
    ) -> None:
        """
        Log a file deletion operation to the changelog.
        
        Args:
            file_path: Path to deleted file (relative to project root)
            rationale: Reason for deletion
            file_size: Size of deleted file in bytes (optional)
            task_id: Optional task identifier (e.g., "Task 1.3")
        
        Example:
            >>> writer = WorkspaceChangelogWriter()
            >>> writer.log_file_deletion(
            ...     'debug_output.txt',
            ...     'Obsolete debug output with no unique value',
            ...     file_size=45435,
            ...     task_id='Task 1.3'
            ... )
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        entry = f"\n### File Deletion: {file_path}\n\n"
        entry += f"**Date**: {timestamp}\n"
        
        if task_id:
            entry += f"**Task**: {task_id}\n"
        
        entry += f"**Rationale**: {rationale}\n"
        
        if file_size is not None:
            entry += f"**Size**: {self._format_size(file_size)}\n"
        
        entry += "\n---\n"
        
        self._append_to_changelog(entry)
    
    def log_operation_batch(
        self,
        operations: List[Dict],
        task_id: Optional[str] = None,
        summary: Optional[str] = None
    ) -> None:
        """
        Log a batch of file operations to the changelog.
        
        This is useful when multiple operations are performed together as part
        of a single task or workflow.
        
        Args:
            operations: List of operation dictionaries with keys:
                - action: "moved" or "deleted"
                - source_path: Original file path
                - destination_path: New file path (for moves)
                - rationale: Reason for operation
                - references_updated: List of updated files (for moves)
                - file_size: Size in bytes (for deletions)
            task_id: Optional task identifier
            summary: Optional summary text for the batch
        
        Example:
            >>> writer = WorkspaceChangelogWriter()
            >>> operations = [
            ...     {
            ...         'action': 'moved',
            ...         'source_path': 'script1.py',
            ...         'destination_path': 'scripts/script1.py',
            ...         'rationale': 'Utility script'
            ...     },
            ...     {
            ...         'action': 'deleted',
            ...         'source_path': 'debug.txt',
            ...         'rationale': 'Obsolete debug output',
            ...         'file_size': 1024
            ...     }
            ... ]
            >>> writer.log_operation_batch(operations, task_id='Task 1.0')
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        entry = f"\n## Batch Operation\n\n"
        entry += f"**Date**: {timestamp}\n"
        
        if task_id:
            entry += f"**Task**: {task_id}\n"
        
        if summary:
            entry += f"\n{summary}\n"
        
        entry += "\n### Operations\n\n"
        
        # Group operations by type
        moves = [op for op in operations if op.get('action') == 'moved']
        deletions = [op for op in operations if op.get('action') == 'deleted']
        
        if moves:
            entry += "#### Files Moved\n\n"
            for op in moves:
                entry += f"- `{op['source_path']}` → `{op['destination_path']}`\n"
                entry += f"  - Rationale: {op.get('rationale', 'N/A')}\n"
                
                refs = op.get('references_updated', [])
                if refs:
                    entry += f"  - References updated in {len(refs)} file(s)\n"
            
            entry += "\n"
        
        if deletions:
            entry += "#### Files Deleted\n\n"
            for op in deletions:
                entry += f"- `{op['source_path']}`\n"
                entry += f"  - Rationale: {op.get('rationale', 'N/A')}\n"
                
                size = op.get('file_size')
                if size is not None:
                    entry += f"  - Size: {self._format_size(size)}\n"
            
            entry += "\n"
        
        # Statistics
        entry += "### Statistics\n\n"
        entry += f"- Total operations: {len(operations)}\n"
        entry += f"- Files moved: {len(moves)}\n"
        entry += f"- Files deleted: {len(deletions)}\n"
        
        total_size = sum(op.get('file_size', 0) for op in deletions)
        if total_size > 0:
            entry += f"- Disk space freed: {self._format_size(total_size)}\n"
        
        entry += "\n---\n"
        
        self._append_to_changelog(entry)
    
    def generate_structure_comparison(
        self,
        before_snapshot: DirectorySnapshot,
        after_snapshot: DirectorySnapshot,
        task_id: Optional[str] = None
    ) -> str:
        """
        Generate a before/after directory structure comparison.
        
        Args:
            before_snapshot: Directory snapshot before operations
            after_snapshot: Directory snapshot after operations
            task_id: Optional task identifier
        
        Returns:
            Formatted comparison string
        
        Example:
            >>> writer = WorkspaceChangelogWriter()
            >>> before = writer.capture_directory_snapshot()
            >>> # ... perform operations ...
            >>> after = writer.capture_directory_snapshot()
            >>> comparison = writer.generate_structure_comparison(before, after)
            >>> print(comparison)
        """
        comparison = f"\n## Directory Structure Comparison\n\n"
        
        if task_id:
            comparison += f"**Task**: {task_id}\n\n"
        
        comparison += f"**Before** ({before_snapshot.timestamp}):\n"
        comparison += f"- Total files: {before_snapshot.total_files}\n"
        comparison += f"- Total size: {self._format_size(before_snapshot.total_size)}\n"
        comparison += f"- Root directory files: {len(before_snapshot.root_files)}\n\n"
        
        comparison += f"**After** ({after_snapshot.timestamp}):\n"
        comparison += f"- Total files: {after_snapshot.total_files}\n"
        comparison += f"- Total size: {self._format_size(after_snapshot.total_size)}\n"
        comparison += f"- Root directory files: {len(after_snapshot.root_files)}\n\n"
        
        # Calculate changes
        files_removed = before_snapshot.total_files - after_snapshot.total_files
        size_freed = before_snapshot.total_size - after_snapshot.total_size
        root_cleaned = len(before_snapshot.root_files) - len(after_snapshot.root_files)
        
        comparison += "### Changes\n\n"
        comparison += f"- Files removed from project: {files_removed}\n"
        comparison += f"- Disk space freed: {self._format_size(size_freed)}\n"
        comparison += f"- Root directory cleaned: {root_cleaned} file(s)\n\n"
        
        # Root directory details
        if root_cleaned > 0:
            comparison += "### Root Directory Cleanup\n\n"
            comparison += "**Files removed from root**:\n"
            
            removed_from_root = set(before_snapshot.root_files) - set(after_snapshot.root_files)
            for file in sorted(removed_from_root):
                comparison += f"- {file}\n"
            
            comparison += "\n"
            
            if after_snapshot.root_files:
                comparison += "**Files remaining in root**:\n"
                for file in sorted(after_snapshot.root_files):
                    comparison += f"- {file}\n"
                comparison += "\n"
        
        comparison += "---\n"
        
        return comparison
    
    def log_structure_comparison(
        self,
        before_snapshot: DirectorySnapshot,
        after_snapshot: DirectorySnapshot,
        task_id: Optional[str] = None
    ) -> None:
        """
        Log a before/after directory structure comparison to the changelog.
        
        Args:
            before_snapshot: Directory snapshot before operations
            after_snapshot: Directory snapshot after operations
            task_id: Optional task identifier
        """
        comparison = self.generate_structure_comparison(
            before_snapshot,
            after_snapshot,
            task_id
        )
        self._append_to_changelog(comparison)
    
    def capture_directory_snapshot(
        self,
        include_subdirs: Optional[Set[str]] = None
    ) -> DirectorySnapshot:
        """
        Capture a snapshot of the current directory structure.
        
        Args:
            include_subdirs: Set of subdirectories to include (defaults to common ones)
        
        Returns:
            DirectorySnapshot with current state
        
        Example:
            >>> writer = WorkspaceChangelogWriter()
            >>> snapshot = writer.capture_directory_snapshot()
            >>> print(f"Root files: {len(snapshot.root_files)}")
        """
        if include_subdirs is None:
            include_subdirs = {
                'docs', 'scripts', 'samples', 'debug_tools', 'tests',
                'user_login', 'user_registration', 'password_recovery',
                'tax_document_generation', 'document_download'
            }
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        root_files = []
        subdirectory_files = {}
        total_files = 0
        total_size = 0
        
        # Scan root directory
        for item in self.project_root.iterdir():
            if item.is_file():
                root_files.append(item.name)
                total_files += 1
                total_size += item.stat().st_size
        
        # Scan specified subdirectories
        for subdir in include_subdirs:
            subdir_path = self.project_root / subdir
            if not subdir_path.exists() or not subdir_path.is_dir():
                continue
            
            files = []
            for root, dirs, filenames in os.walk(subdir_path):
                # Skip certain directories
                dirs[:] = [d for d in dirs if d not in {
                    '.git', '__pycache__', '.pytest_cache', '.hypothesis',
                    'node_modules', 'venv', '.venv', '.aws-sam'
                }]
                
                for filename in filenames:
                    file_path = Path(root) / filename
                    rel_path = file_path.relative_to(subdir_path)
                    files.append(str(rel_path))
                    total_files += 1
                    total_size += file_path.stat().st_size
            
            subdirectory_files[subdir] = sorted(files)
        
        return DirectorySnapshot(
            timestamp=timestamp,
            root_files=sorted(root_files),
            subdirectory_files=subdirectory_files,
            total_files=total_files,
            total_size=total_size
        )
    
    def _append_to_changelog(self, content: str) -> None:
        """
        Append content to the changelog file.
        
        Args:
            content: Content to append
        """
        # Read existing content
        with open(self.changelog_path, 'r', encoding='utf-8') as f:
            existing = f.read()
        
        # Find the insertion point (after overview, before guidelines)
        # Look for the "---" separator before "## Guidelines Applied"
        guidelines_marker = "\n---\n\n## Guidelines Applied"
        
        if guidelines_marker in existing:
            # Insert before guidelines section
            parts = existing.split(guidelines_marker, 1)
            new_content = parts[0] + content + guidelines_marker + parts[1]
        else:
            # Append to end if structure is different
            new_content = existing + content
        
        # Write updated content
        with open(self.changelog_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
    
    def _format_size(self, size_bytes: int) -> str:
        """
        Format file size in human-readable format.
        
        Args:
            size_bytes: Size in bytes
        
        Returns:
            Formatted size string (e.g., "1.5 KB", "2.3 MB")
        """
        if size_bytes < 1024:
            return f"{size_bytes} bytes"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


def integrate_with_relocator(relocator, changelog_writer: WorkspaceChangelogWriter):
    """
    Integrate changelog writer with FileRelocator to automatically log operations.
    
    This function processes the operations log from a FileRelocator instance
    and writes them to the changelog.
    
    Args:
        relocator: FileRelocator instance with operations_log
        changelog_writer: WorkspaceChangelogWriter instance
    
    Example:
        >>> from relocate_files import FileRelocator
        >>> relocator = FileRelocator()
        >>> relocator.relocate_python_script('verify_fields.py')
        >>> 
        >>> writer = WorkspaceChangelogWriter()
        >>> integrate_with_relocator(relocator, writer)
    """
    operations = []
    
    for result in relocator.operations_log:
        if not result.success:
            continue
        
        if result.action == 'moved':
            operations.append({
                'action': 'moved',
                'source_path': result.source_path,
                'destination_path': result.destination_path,
                'rationale': result.message,
                'references_updated': result.references_updated
            })
        elif result.action == 'deleted':
            # Try to get file size if available
            file_size = None
            source_path = relocator.project_root / result.source_path
            if source_path.exists():
                file_size = source_path.stat().st_size
            
            operations.append({
                'action': 'deleted',
                'source_path': result.source_path,
                'rationale': result.message,
                'file_size': file_size
            })
    
    if operations:
        changelog_writer.log_operation_batch(operations)


def main():
    """
    Command-line interface for workspace changelog utilities.
    
    Usage:
        python scripts/workspace_changelog.py <command> [options]
    
    Commands:
        snapshot - Capture current directory snapshot
        compare <before_file> <after_file> - Compare two snapshots
        log-move <source> <dest> <rationale> - Log a file move
        log-delete <file> <rationale> - Log a file deletion
    """
    import sys
    import json
    
    if len(sys.argv) < 2:
        print("Usage: python scripts/workspace_changelog.py <command> [options]")
        print("\nCommands:")
        print("  snapshot                           - Capture current directory snapshot")
        print("  compare <before.json> <after.json> - Compare two snapshots")
        print("  log-move <source> <dest> <reason>  - Log a file move")
        print("  log-delete <file> <reason>         - Log a file deletion")
        sys.exit(1)
    
    command = sys.argv[1]
    writer = WorkspaceChangelogWriter()
    
    if command == 'snapshot':
        snapshot = writer.capture_directory_snapshot()
        
        # Save to file
        output_file = f"snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        snapshot_data = {
            'timestamp': snapshot.timestamp,
            'root_files': snapshot.root_files,
            'subdirectory_files': snapshot.subdirectory_files,
            'total_files': snapshot.total_files,
            'total_size': snapshot.total_size
        }
        
        with open(output_file, 'w') as f:
            json.dump(snapshot_data, f, indent=2)
        
        print(f"Snapshot saved to {output_file}")
        print(f"Total files: {snapshot.total_files}")
        print(f"Root files: {len(snapshot.root_files)}")
        print(f"Total size: {writer._format_size(snapshot.total_size)}")
    
    elif command == 'compare':
        if len(sys.argv) < 4:
            print("Usage: python scripts/workspace_changelog.py compare <before.json> <after.json>")
            sys.exit(1)
        
        before_file = sys.argv[2]
        after_file = sys.argv[3]
        
        # Load snapshots
        with open(before_file, 'r') as f:
            before_data = json.load(f)
        with open(after_file, 'r') as f:
            after_data = json.load(f)
        
        before = DirectorySnapshot(**before_data)
        after = DirectorySnapshot(**after_data)
        
        comparison = writer.generate_structure_comparison(before, after)
        print(comparison)
    
    elif command == 'log-move':
        if len(sys.argv) < 5:
            print("Usage: python scripts/workspace_changelog.py log-move <source> <dest> <reason>")
            sys.exit(1)
        
        source = sys.argv[2]
        dest = sys.argv[3]
        reason = sys.argv[4]
        
        writer.log_file_move(source, dest, reason)
        print(f"Logged move: {source} → {dest}")
    
    elif command == 'log-delete':
        if len(sys.argv) < 4:
            print("Usage: python scripts/workspace_changelog.py log-delete <file> <reason>")
            sys.exit(1)
        
        file_path = sys.argv[2]
        reason = sys.argv[3]
        
        writer.log_file_deletion(file_path, reason)
        print(f"Logged deletion: {file_path}")
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == '__main__':
    main()
