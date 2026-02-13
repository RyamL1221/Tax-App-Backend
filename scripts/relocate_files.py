"""
File Relocation Utilities for Workspace Organization.

This module provides utilities for moving files to their correct locations
according to workspace organization rules. It handles:
- Python script relocation
- PDF file relocation
- Text file evaluation and relocation
- Reference scanning and updating
- Operation logging

All operations are logged to docs/CHANGELOG_WORKSPACE_ORGANIZATION.md
"""

import os
import re
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

from scripts.organization_rules import OrganizationRules


@dataclass
class RelocationResult:
    """
    Result of a file relocation operation.
    
    Attributes:
        success: Whether the operation succeeded
        source_path: Original file path
        destination_path: New file path (or None if deleted)
        action: Type of action performed ("moved", "deleted", "skipped")
        message: Human-readable message about the operation
        references_updated: List of files where references were updated
    """
    success: bool
    source_path: str
    destination_path: Optional[str]
    action: str
    message: str
    references_updated: List[str] = None
    
    def __post_init__(self):
        if self.references_updated is None:
            self.references_updated = []


class FileRelocator:
    """
    Handles file relocation operations with reference tracking and logging.
    """
    
    def __init__(self, project_root: Optional[Path] = None, dry_run: bool = False):
        """
        Initialize the file relocator.
        
        Args:
            project_root: Root directory of the project (defaults to current directory's parent)
            dry_run: If True, simulate operations without actually moving files
        """
        if project_root is None:
            # Assume we're in scripts/ directory, go up one level
            project_root = Path(__file__).parent.parent
        
        self.project_root = Path(project_root).resolve()
        self.dry_run = dry_run
        self.rules = OrganizationRules()
        self.operations_log: List[RelocationResult] = []
    
    def relocate_python_script(
        self,
        script_path: str,
        context: Optional[dict] = None
    ) -> RelocationResult:
        """
        Relocate a Python script to the appropriate directory.
        
        This function determines the correct destination for a Python script
        based on its purpose (verification/validation utility or Lambda-specific)
        and moves it there, updating any references to the old location.
        
        Args:
            script_path: Path to the script (relative to project root)
            context: Optional context dictionary with additional information:
                - 'is_lambda_specific': bool - Is this Lambda-specific code?
                - 'lambda_function': str - Which Lambda function?
                - 'is_diagnostic': bool - Is this a diagnostic tool?
        
        Returns:
            RelocationResult with operation details
        
        Example:
            >>> relocator = FileRelocator()
            >>> result = relocator.relocate_python_script('verify_fields.py')
            >>> print(result.destination_path)
            'scripts/verify_fields.py'
        """
        if context is None:
            context = {}
        
        source = self.project_root / script_path
        
        # Check if source exists
        if not source.exists():
            return RelocationResult(
                success=False,
                source_path=script_path,
                destination_path=None,
                action="skipped",
                message=f"Source file does not exist: {script_path}"
            )
        
        # Check if it's already in the correct location
        if not self._is_in_root(script_path):
            return RelocationResult(
                success=True,
                source_path=script_path,
                destination_path=script_path,
                action="skipped",
                message=f"File is already in a subdirectory: {script_path}"
            )
        
        # Determine destination
        destination_dir = self.rules.get_destination_for_file(script_path, context)
        
        if destination_dir == '.':
            return RelocationResult(
                success=True,
                source_path=script_path,
                destination_path=script_path,
                action="skipped",
                message=f"File should remain in root: {script_path}"
            )
        
        if destination_dir == '.gitignore':
            return RelocationResult(
                success=False,
                source_path=script_path,
                destination_path=None,
                action="skipped",
                message=f"File is temporary and should be in .gitignore: {script_path}"
            )
        
        # Construct destination path
        filename = Path(script_path).name
        destination_path = Path(destination_dir) / filename
        destination = self.project_root / destination_path
        
        # Check if destination already exists
        if destination.exists():
            if self._files_are_identical(source, destination):
                return RelocationResult(
                    success=True,
                    source_path=script_path,
                    destination_path=str(destination_path),
                    action="skipped",
                    message=f"Identical file already exists at destination: {destination_path}"
                )
            else:
                # Add timestamp to avoid overwriting
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                stem = destination.stem
                suffix = destination.suffix
                destination_path = Path(destination_dir) / f"{stem}_{timestamp}{suffix}"
                destination = self.project_root / destination_path
        
        # Scan for references before moving
        references = self._scan_for_references(script_path)
        
        # Perform the move
        if not self.dry_run:
            # Create destination directory if needed
            destination.parent.mkdir(parents=True, exist_ok=True)
            
            # Move the file
            shutil.move(str(source), str(destination))
            
            # Update references
            updated_files = self._update_references(
                script_path,
                str(destination_path),
                references
            )
        else:
            updated_files = []
        
        result = RelocationResult(
            success=True,
            source_path=script_path,
            destination_path=str(destination_path),
            action="moved",
            message=f"Moved {script_path} → {destination_path}",
            references_updated=updated_files
        )
        
        self.operations_log.append(result)
        return result
    
    def relocate_pdf_file(self, pdf_path: str) -> RelocationResult:
        """
        Move PDF file to samples directory.
        
        All PDF files (templates, test outputs, samples) should be in the
        samples/ directory according to workspace organization rules.
        
        Args:
            pdf_path: Path to PDF in root directory (relative to project root)
        
        Returns:
            RelocationResult with operation details
        
        Example:
            >>> relocator = FileRelocator()
            >>> result = relocator.relocate_pdf_file('test-output.pdf')
            >>> print(result.destination_path)
            'samples/test-output.pdf'
        """
        source = self.project_root / pdf_path
        
        # Check if source exists
        if not source.exists():
            return RelocationResult(
                success=False,
                source_path=pdf_path,
                destination_path=None,
                action="skipped",
                message=f"Source file does not exist: {pdf_path}"
            )
        
        # Check if it's already in samples/
        if pdf_path.startswith('samples/'):
            return RelocationResult(
                success=True,
                source_path=pdf_path,
                destination_path=pdf_path,
                action="skipped",
                message=f"File is already in samples/: {pdf_path}"
            )
        
        # Construct destination path
        filename = Path(pdf_path).name
        destination_path = Path('samples') / filename
        destination = self.project_root / destination_path
        
        # Check if destination already exists
        if destination.exists():
            if self._files_are_identical(source, destination):
                return RelocationResult(
                    success=True,
                    source_path=pdf_path,
                    destination_path=str(destination_path),
                    action="skipped",
                    message=f"Identical file already exists at destination: {destination_path}"
                )
            else:
                # Add timestamp to avoid overwriting
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                stem = destination.stem
                suffix = destination.suffix
                destination_path = Path('samples') / f"{stem}_{timestamp}{suffix}"
                destination = self.project_root / destination_path
        
        # Scan for references before moving
        references = self._scan_for_references(pdf_path)
        
        # Perform the move
        if not self.dry_run:
            # Create samples directory if needed
            destination.parent.mkdir(parents=True, exist_ok=True)
            
            # Move the file
            shutil.move(str(source), str(destination))
            
            # Update references
            updated_files = self._update_references(
                pdf_path,
                str(destination_path),
                references
            )
        else:
            updated_files = []
        
        result = RelocationResult(
            success=True,
            source_path=pdf_path,
            destination_path=str(destination_path),
            action="moved",
            message=f"Moved {pdf_path} → {destination_path}",
            references_updated=updated_files
        )
        
        self.operations_log.append(result)
        return result
    
    def evaluate_text_file(
        self,
        text_path: str,
        auto_decide: bool = False
    ) -> Tuple[str, str, str]:
        """
        Evaluate text file and determine action.
        
        This function analyzes a text file to determine if it contains valuable
        documentation (should be moved to docs/) or is obsolete (should be deleted).
        
        Args:
            text_path: Path to text file (relative to project root)
            auto_decide: If True, automatically decide based on heuristics.
                        If False, return recommendation for manual review.
        
        Returns:
            Tuple of (action, destination, rationale)
            - action: "move", "delete", or "review"
            - destination: Target path if moving, empty if deleting/reviewing
            - rationale: Explanation of the decision
        
        Example:
            >>> relocator = FileRelocator()
            >>> action, dest, reason = relocator.evaluate_text_file('output.txt')
            >>> print(f"{action}: {reason}")
            'delete: Temporary debug output with no unique value'
        """
        source = self.project_root / text_path
        
        # Check if source exists
        if not source.exists():
            return "skip", "", f"Source file does not exist: {text_path}"
        
        # Read file content for analysis
        try:
            with open(source, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            return "review", "", f"Unable to read file: {e}"
        
        filename = Path(text_path).name
        file_size = len(content)
        
        # Heuristics for automatic decision
        is_debug_output = any(pattern in filename.lower() for pattern in [
            '_output', '_report', '_findings', '_analysis', 'debug_', 'inspect_'
        ])
        
        is_temporary = self.rules.is_temporary_file(text_path)
        
        has_documentation_markers = any(marker in content for marker in [
            '# ', '## ', '### ',  # Markdown headers
            'Overview', 'Summary', 'Conclusion',
            'Documentation', 'Guide', 'Reference'
        ])
        
        is_small = file_size < 1000  # Less than 1KB
        is_large = file_size > 100000  # More than 100KB
        
        # Decision logic
        if is_temporary:
            return (
                "delete",
                "",
                "Temporary file matching .gitignore patterns"
            )
        
        if is_debug_output and not has_documentation_markers:
            if auto_decide:
                return (
                    "delete",
                    "",
                    "Debug output file with no documentation value"
                )
            else:
                return (
                    "review",
                    "",
                    "Appears to be debug output - review for value before deleting"
                )
        
        if has_documentation_markers:
            # Determine appropriate docs subdirectory
            if any(keyword in content.lower() for keyword in [
                'field', 'mapping', 'architecture', 'design', 'structure'
            ]):
                dest = "docs/architecture/"
            elif any(keyword in content.lower() for keyword in [
                'test', 'verification', 'validation', 'result'
            ]):
                dest = "docs/testing/"
            elif any(keyword in content.lower() for keyword in [
                'setup', 'install', 'configuration', 'development'
            ]):
                dest = "docs/development/"
            else:
                dest = "docs/"
            
            destination = dest + filename.replace('.txt', '.md')
            
            return (
                "move",
                destination,
                "Contains documentation that should be preserved"
            )
        
        if is_small:
            if auto_decide:
                return (
                    "delete",
                    "",
                    "Small file with no clear documentation value"
                )
            else:
                return (
                    "review",
                    "",
                    "Small file - review content before deciding"
                )
        
        if is_large:
            return (
                "review",
                "",
                "Large file - manual review recommended to assess value"
            )
        
        # Default: recommend review
        return (
            "review",
            "",
            "Unable to automatically determine value - manual review needed"
        )
    
    def relocate_text_file(
        self,
        text_path: str,
        destination: str,
        rationale: str
    ) -> RelocationResult:
        """
        Move a text file to a specified destination.
        
        This is typically called after evaluate_text_file() determines the
        file should be moved.
        
        Args:
            text_path: Path to text file (relative to project root)
            destination: Destination path (relative to project root)
            rationale: Reason for the move
        
        Returns:
            RelocationResult with operation details
        """
        source = self.project_root / text_path
        
        # Check if source exists
        if not source.exists():
            return RelocationResult(
                success=False,
                source_path=text_path,
                destination_path=None,
                action="skipped",
                message=f"Source file does not exist: {text_path}"
            )
        
        destination_path = Path(destination)
        dest = self.project_root / destination_path
        
        # Check if destination already exists
        if dest.exists():
            if self._files_are_identical(source, dest):
                return RelocationResult(
                    success=True,
                    source_path=text_path,
                    destination_path=str(destination_path),
                    action="skipped",
                    message=f"Identical file already exists at destination: {destination_path}"
                )
            else:
                # Add timestamp to avoid overwriting
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                stem = dest.stem
                suffix = dest.suffix
                destination_path = dest.parent / f"{stem}_{timestamp}{suffix}"
                dest = self.project_root / destination_path
        
        # Scan for references before moving
        references = self._scan_for_references(text_path)
        
        # Perform the move
        if not self.dry_run:
            # Create destination directory if needed
            dest.parent.mkdir(parents=True, exist_ok=True)
            
            # Move the file
            shutil.move(str(source), str(dest))
            
            # Update references
            updated_files = self._update_references(
                text_path,
                str(destination_path),
                references
            )
        else:
            updated_files = []
        
        result = RelocationResult(
            success=True,
            source_path=text_path,
            destination_path=str(destination_path),
            action="moved",
            message=f"Moved {text_path} → {destination_path} ({rationale})",
            references_updated=updated_files
        )
        
        self.operations_log.append(result)
        return result
    
    def delete_file(self, file_path: str, rationale: str) -> RelocationResult:
        """
        Delete a file with logging.
        
        Args:
            file_path: Path to file to delete (relative to project root)
            rationale: Reason for deletion
        
        Returns:
            RelocationResult with operation details
        """
        source = self.project_root / file_path
        
        # Check if source exists
        if not source.exists():
            return RelocationResult(
                success=False,
                source_path=file_path,
                destination_path=None,
                action="skipped",
                message=f"File does not exist: {file_path}"
            )
        
        # Perform the deletion
        if not self.dry_run:
            source.unlink()
        
        result = RelocationResult(
            success=True,
            source_path=file_path,
            destination_path=None,
            action="deleted",
            message=f"Deleted {file_path} ({rationale})"
        )
        
        self.operations_log.append(result)
        return result
    
    def _is_in_root(self, file_path: str) -> bool:
        """Check if a file is in the root directory."""
        return len(Path(file_path).parts) == 1
    
    def _files_are_identical(self, path1: Path, path2: Path) -> bool:
        """
        Check if two files have identical content.
        
        Args:
            path1: First file path
            path2: Second file path
        
        Returns:
            True if files are identical, False otherwise
        """
        if not path1.exists() or not path2.exists():
            return False
        
        # Quick check: compare file sizes
        if path1.stat().st_size != path2.stat().st_size:
            return False
        
        # Compare content
        try:
            with open(path1, 'rb') as f1, open(path2, 'rb') as f2:
                return f1.read() == f2.read()
        except Exception:
            return False
    
    def _scan_for_references(self, file_path: str) -> List[Tuple[str, List[int]]]:
        """
        Scan codebase for references to a file path.
        
        Args:
            file_path: Path to search for
        
        Returns:
            List of tuples (file_path, line_numbers) where references were found
        """
        references = []
        filename = Path(file_path).name
        
        # Patterns to search for
        patterns = [
            file_path,  # Full path
            filename,   # Just filename
            file_path.replace('/', os.sep),  # OS-specific path
        ]
        
        # File extensions to search in
        search_extensions = {'.py', '.md', '.sh', '.yaml', '.yml', '.json', '.txt'}
        
        # Directories to skip
        skip_dirs = {'.git', '.aws-sam', '__pycache__', '.pytest_cache', 
                    '.hypothesis', 'node_modules', 'venv', '.venv'}
        
        # Search through project files
        for root, dirs, files in os.walk(self.project_root):
            # Skip certain directories
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            
            for file in files:
                if Path(file).suffix not in search_extensions:
                    continue
                
                file_full_path = Path(root) / file
                
                # Skip the file we're moving
                if file_full_path == self.project_root / file_path:
                    continue
                
                try:
                    with open(file_full_path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                    
                    matching_lines = []
                    for i, line in enumerate(lines, 1):
                        if any(pattern in line for pattern in patterns):
                            matching_lines.append(i)
                    
                    if matching_lines:
                        rel_path = file_full_path.relative_to(self.project_root)
                        references.append((str(rel_path), matching_lines))
                
                except Exception:
                    # Skip files that can't be read
                    continue
        
        return references
    
    def _update_references(
        self,
        old_path: str,
        new_path: str,
        references: List[Tuple[str, List[int]]]
    ) -> List[str]:
        """
        Update references to a file in other files.
        
        Args:
            old_path: Old file path
            new_path: New file path
            references: List of (file_path, line_numbers) with references
        
        Returns:
            List of files that were updated
        """
        updated_files = []
        
        for ref_file, line_numbers in references:
            file_path = self.project_root / ref_file
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Replace old path with new path
                old_filename = Path(old_path).name
                new_filename = Path(new_path).name
                
                # Try multiple replacement strategies
                modified = content
                modified = modified.replace(old_path, new_path)
                modified = modified.replace(old_path.replace('/', os.sep), 
                                          new_path.replace('/', os.sep))
                
                # If only filename changed, be more careful
                if old_filename != new_filename:
                    # Use word boundaries to avoid partial matches
                    modified = re.sub(
                        r'\b' + re.escape(old_filename) + r'\b',
                        new_filename,
                        modified
                    )
                
                # Only write if content changed
                if modified != content:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(modified)
                    updated_files.append(str(ref_file))
            
            except Exception as e:
                # Log error but continue with other files
                print(f"Warning: Could not update references in {ref_file}: {e}")
        
        return updated_files
    
    def get_operations_summary(self) -> str:
        """
        Get a summary of all operations performed.
        
        Returns:
            Formatted string summarizing all operations
        """
        if not self.operations_log:
            return "No operations performed."
        
        summary = []
        summary.append("File Relocation Summary")
        summary.append("=" * 50)
        summary.append("")
        
        moved = [op for op in self.operations_log if op.action == "moved"]
        deleted = [op for op in self.operations_log if op.action == "deleted"]
        skipped = [op for op in self.operations_log if op.action == "skipped"]
        
        if moved:
            summary.append(f"Files Moved: {len(moved)}")
            for op in moved:
                summary.append(f"  • {op.source_path} → {op.destination_path}")
                if op.references_updated:
                    summary.append(f"    References updated in {len(op.references_updated)} files")
            summary.append("")
        
        if deleted:
            summary.append(f"Files Deleted: {len(deleted)}")
            for op in deleted:
                summary.append(f"  • {op.source_path}")
            summary.append("")
        
        if skipped:
            summary.append(f"Files Skipped: {len(skipped)}")
            for op in skipped:
                summary.append(f"  • {op.source_path}: {op.message}")
            summary.append("")
        
        return "\n".join(summary)


def main():
    """
    Command-line interface for file relocation utilities.
    
    Usage:
        python scripts/relocate_files.py <command> <file_path> [options]
    
    Commands:
        python - Relocate a Python script
        pdf - Relocate a PDF file
        text - Evaluate a text file
        delete - Delete a file
    """
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python scripts/relocate_files.py <command> <file_path> [options]")
        print("\nCommands:")
        print("  python <file>     - Relocate a Python script")
        print("  pdf <file>        - Relocate a PDF file")
        print("  text <file>       - Evaluate a text file")
        print("  delete <file>     - Delete a file with logging")
        print("\nOptions:")
        print("  --dry-run         - Simulate operations without making changes")
        sys.exit(1)
    
    command = sys.argv[1]
    file_path = sys.argv[2]
    dry_run = '--dry-run' in sys.argv
    
    relocator = FileRelocator(dry_run=dry_run)
    
    if command == 'python':
        result = relocator.relocate_python_script(file_path)
    elif command == 'pdf':
        result = relocator.relocate_pdf_file(file_path)
    elif command == 'text':
        action, dest, rationale = relocator.evaluate_text_file(file_path, auto_decide=False)
        print(f"Recommendation: {action}")
        if dest:
            print(f"Destination: {dest}")
        print(f"Rationale: {rationale}")
        sys.exit(0)
    elif command == 'delete':
        rationale = input("Reason for deletion: ")
        result = relocator.delete_file(file_path, rationale)
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
    
    print(result.message)
    if result.references_updated:
        print(f"Updated references in {len(result.references_updated)} files:")
        for ref_file in result.references_updated:
            print(f"  • {ref_file}")
    
    print("\n" + relocator.get_operations_summary())


if __name__ == '__main__':
    main()
