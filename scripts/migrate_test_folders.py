#!/usr/bin/env python3
"""
Test Folder Migration Script

This script reorganizes test files from a flat naming-convention structure
to a hierarchical subdirectory structure organized by test type.

Usage:
    python scripts/migrate_test_folders.py [--dry-run]
"""

import os
import sys
import re
from pathlib import Path
from typing import List, Dict, Tuple
from dataclasses import dataclass
from enum import Enum


class TestCategory(Enum):
    """Test file categories."""
    UNIT = "unit"
    PROPERTY = "property"
    INTEGRATION = "integration"
    REGRESSION = "regression"
    MANUAL = "manual"
    UTILITY = "utility"


@dataclass
class TestFile:
    """Represents a test file to be migrated."""
    path: Path
    category: TestCategory
    new_path: Path


def categorize_file(file_path: Path) -> TestCategory:
    """
    Determine the category for a test file.
    
    Args:
        file_path: Path to the test file
        
    Returns:
        TestCategory enum
    """
    # Check if in manual/ directory
    if "manual" in file_path.parts:
        return TestCategory.MANUAL
    
    # Check if utility file (not a test file)
    filename = file_path.name
    if not filename.startswith("test_"):
        return TestCategory.UTILITY
    
    # Check filename suffix
    stem = file_path.stem
    if stem.endswith("_unit"):
        return TestCategory.UNIT
    elif stem.endswith("_property"):
        return TestCategory.PROPERTY
    elif stem.endswith("_integration"):
        return TestCategory.INTEGRATION
    elif stem.endswith("_regression"):
        return TestCategory.REGRESSION
    
    # If no suffix, analyze content
    try:
        content = file_path.read_text()
        
        # Count indicators
        property_count = content.count("@given") + content.count("from hypothesis import")
        integration_count = content.count("lambda_handler") + content.count("@mock_")
        unit_count = content.count("@patch") + content.count("Mock(")
        regression_count = content.count("regression") + content.count("bug fix")
        
        # Determine predominant type
        counts = {
            TestCategory.PROPERTY: property_count,
            TestCategory.INTEGRATION: integration_count,
            TestCategory.UNIT: unit_count,
            TestCategory.REGRESSION: regression_count
        }
        
        max_category = max(counts, key=counts.get)
        max_count = counts[max_category]
        
        # If clear majority (>50% of total), use that category
        total = sum(counts.values())
        if total > 0 and max_count / total > 0.5:
            return max_category
        
        # Default to integration if ambiguous
        return TestCategory.INTEGRATION
        
    except Exception as e:
        print(f"Warning: Could not analyze {file_path}: {e}")
        return TestCategory.INTEGRATION


def find_test_files(base_dir: Path) -> List[Path]:
    """Find all test files in a directory."""
    test_files = []
    
    # Find all test_*.py files
    for test_file in base_dir.glob("test_*.py"):
        if test_file.is_file():
            test_files.append(test_file)
    
    return test_files


def build_migration_plan(test_dirs: List[Path]) -> List[TestFile]:
    """
    Build a plan for all file relocations.
    
    Args:
        test_dirs: List of test directories to process
        
    Returns:
        List of TestFile objects with migration details
    """
    migrations = []
    
    for test_dir in test_dirs:
        if not test_dir.exists():
            continue
            
        test_files = find_test_files(test_dir)
        
        for file_path in test_files:
            category = categorize_file(file_path)
            
            # Skip utilities and manual tests
            if category in (TestCategory.UTILITY, TestCategory.MANUAL):
                continue
            
            # Determine new path
            subdir = category.value
            new_path = test_dir / subdir / file_path.name
            
            migrations.append(TestFile(
                path=file_path,
                category=category,
                new_path=new_path
            ))
    
    return migrations


def create_directories(migrations: List[TestFile]) -> None:
    """Create subdirectories and __init__.py files."""
    created_dirs = set()
    
    for migration in migrations:
        parent_dir = migration.new_path.parent
        
        if parent_dir not in created_dirs:
            parent_dir.mkdir(parents=True, exist_ok=True)
            
            # Create __init__.py
            init_file = parent_dir / "__init__.py"
            if not init_file.exists():
                init_file.write_text("")
                print(f"Created {init_file}")
            
            created_dirs.add(parent_dir)


def print_migration_plan(migrations: List[TestFile]) -> None:
    """Print the migration plan."""
    print("\n" + "="*80)
    print("MIGRATION PLAN")
    print("="*80)
    
    by_category = {}
    for migration in migrations:
        category = migration.category.value
        if category not in by_category:
            by_category[category] = []
        by_category[category].append(migration)
    
    for category, files in sorted(by_category.items()):
        print(f"\n{category.upper()} ({len(files)} files):")
        for migration in files[:5]:  # Show first 5
            print(f"  {migration.path} -> {migration.new_path}")
        if len(files) > 5:
            print(f"  ... and {len(files) - 5} more")
    
    print(f"\nTotal files to migrate: {len(migrations)}")
    print("="*80 + "\n")


def main():
    """Main migration execution."""
    dry_run = "--dry-run" in sys.argv
    
    # Define test directories to process
    test_dirs = [
        Path("user_login/tests"),
        Path("user_registration/tests"),
        Path("password_recovery/tests"),
        Path("tax_document_generation/tests"),
        Path("document_download/tests"),
        Path("debug_tools/tests"),
        Path("tests"),
    ]
    
    print("Test Folder Migration Script")
    print("="*80)
    
    # Build migration plan
    migrations = build_migration_plan(test_dirs)
    
    if not migrations:
        print("No files to migrate!")
        return 0
    
    # Print plan
    print_migration_plan(migrations)
    
    if dry_run:
        print("DRY RUN - No files will be moved")
        return 0
    
    # Confirm
    response = input("Proceed with migration? (yes/no): ")
    if response.lower() not in ("yes", "y"):
        print("Migration cancelled")
        return 1
    
    # Create directories
    print("\nCreating subdirectories...")
    create_directories(migrations)
    
    # Print instructions for using smartRelocate
    print("\n" + "="*80)
    print("MIGRATION READY")
    print("="*80)
    print("\nDirectories created. Now use Kiro's smartRelocate to move files:")
    print("\nFor each file, run:")
    print("  smartRelocate(source='old/path', destination='new/path')")
    print("\nOr use the generated commands below:\n")
    
    for migration in migrations:
        print(f"# {migration.category.value}")
        print(f"smartRelocate('{migration.path}', '{migration.new_path}')")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
