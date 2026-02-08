#!/usr/bin/env python3
"""
Workspace Organization Verification Script.

This script verifies that the root directory contains only essential files
and reports any misplaced files with suggested destinations.

Usage:
    python scripts/verify_workspace_organization.py
    
    Or make it executable and run directly:
    chmod +x scripts/verify_workspace_organization.py
    ./scripts/verify_workspace_organization.py

The script will:
1. List all files in the root directory
2. Check each file against the essential files list
3. Report misplaced files with suggested destinations
4. Exit with code 0 if all files are properly placed, 1 otherwise
"""

import sys
from pathlib import Path
from typing import List, Tuple

# Add parent directory to path to import organization_rules
sys.path.insert(0, str(Path(__file__).parent))

from organization_rules import OrganizationRules


def list_root_directory_files() -> List[Path]:
    """
    List all files in the root directory (non-recursively).
    
    Excludes:
    - Directories
    - Hidden files (starting with .)
    - The .git directory
    
    Returns:
        List of Path objects for files in root directory
    """
    root_dir = Path(__file__).parent.parent
    
    files = []
    for item in root_dir.iterdir():
        # Skip directories
        if item.is_dir():
            continue
        
        # Skip hidden files (except .gitignore, .env.*, which are essential)
        if item.name.startswith('.') and item.name not in {'.gitignore', '.env', '.env.local', '.env.example'}:
            continue
        
        files.append(item)
    
    return sorted(files, key=lambda p: p.name)


def check_against_essential_files(files: List[Path], rules: OrganizationRules) -> List[Tuple[Path, bool, str]]:
    """
    Check files against the essential files list.
    
    Args:
        files: List of file paths to check
        rules: OrganizationRules instance
        
    Returns:
        List of tuples: (file_path, is_essential, message)
        - file_path: Path to the file
        - is_essential: True if file should be in root
        - message: Explanation or suggestion
    """
    results = []
    
    for file_path in files:
        is_valid, message = rules.validate_file_location(file_path.name)
        results.append((file_path, is_valid, message))
    
    return results


def suggest_destinations_for_misplaced_files(
    results: List[Tuple[Path, bool, str]], 
    rules: OrganizationRules
) -> List[Tuple[Path, str, str]]:
    """
    Generate destination suggestions for misplaced files.
    
    Args:
        results: Results from check_against_essential_files
        rules: OrganizationRules instance
        
    Returns:
        List of tuples: (file_path, suggested_destination, reason)
        Only includes misplaced files (is_essential=False)
    """
    suggestions = []
    
    for file_path, is_valid, message in results:
        if not is_valid:
            # Get suggested destination
            destination = rules.get_destination_for_file(file_path.name)
            
            # Get the rule that applies
            rule = rules.get_rule_for_file(file_path.name)
            reason = rule.description if rule else "No specific rule found"
            
            suggestions.append((file_path, destination, reason))
    
    return suggestions


def print_report(
    all_files: List[Path],
    results: List[Tuple[Path, bool, str]],
    suggestions: List[Tuple[Path, str, str]]
) -> None:
    """
    Print a formatted report of the verification results.
    
    Args:
        all_files: All files found in root directory
        results: Validation results for each file
        suggestions: Destination suggestions for misplaced files
    """
    print("=" * 80)
    print("WORKSPACE ORGANIZATION VERIFICATION REPORT")
    print("=" * 80)
    print()
    
    # Summary
    essential_count = sum(1 for _, is_valid, _ in results if is_valid)
    misplaced_count = len(all_files) - essential_count
    
    print(f"📊 SUMMARY")
    print(f"   Total files in root: {len(all_files)}")
    print(f"   Essential files: {essential_count}")
    print(f"   Misplaced files: {misplaced_count}")
    print()
    
    # Essential files (properly placed)
    if essential_count > 0:
        print(f"✅ ESSENTIAL FILES (Properly Placed)")
        print("-" * 80)
        for file_path, is_valid, message in results:
            if is_valid:
                print(f"   {message}")
        print()
    
    # Misplaced files
    if misplaced_count > 0:
        print(f"❌ MISPLACED FILES (Need Relocation)")
        print("-" * 80)
        for file_path, destination, reason in suggestions:
            print(f"   File: {file_path.name}")
            print(f"   Suggested destination: {destination}")
            print(f"   Reason: {reason}")
            print()
    
    # Final verdict
    print("=" * 80)
    if misplaced_count == 0:
        print("✅ RESULT: Root directory is clean! All files are properly placed.")
        print("=" * 80)
    else:
        print(f"❌ RESULT: Found {misplaced_count} misplaced file(s) in root directory.")
        print("=" * 80)
        print()
        print("📝 RECOMMENDED ACTIONS:")
        print()
        for file_path, destination, reason in suggestions:
            if destination == '.gitignore':
                print(f"   • Add {file_path.name} to .gitignore (temporary file)")
            elif destination == 'unknown':
                print(f"   • Manually review {file_path.name} (unable to determine location)")
            else:
                print(f"   • Move {file_path.name} to {destination}")
        print()


def main() -> int:
    """
    Main entry point for the verification script.
    
    Returns:
        Exit code: 0 if all files properly placed, 1 if misplaced files found
    """
    # Initialize organization rules
    rules = OrganizationRules()
    
    # List all files in root directory
    all_files = list_root_directory_files()
    
    # Check files against essential files list
    results = check_against_essential_files(all_files, rules)
    
    # Generate suggestions for misplaced files
    suggestions = suggest_destinations_for_misplaced_files(results, rules)
    
    # Print report
    print_report(all_files, results, suggestions)
    
    # Return exit code
    return 0 if len(suggestions) == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
