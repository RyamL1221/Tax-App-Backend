"""
Property-based test for single dependency per line.

This test verifies that for any non-empty, non-comment line in requirements.txt,
that line declares exactly one package dependency.
"""

import os
import re
import pytest


class TestSingleDependencyPerLineProperty:
    """Property-based test for single dependency per line."""
    
    def test_single_dependency_per_line(self):
        """
        **Validates: Requirements 5.4**
        Feature: fix-password-recovery-dependencies, Property 4: Single Dependency Per Line
        
        For any non-empty, non-comment line in requirements.txt, that line
        SHALL declare exactly one package dependency.
        
        This follows pip requirements.txt format conventions and ensures the file
        is parseable by SAM build and pip. Multiple dependencies on a single line
        would violate the standard format and could cause build failures.
        """
        # Get the path to requirements.txt
        test_dir = os.path.dirname(os.path.abspath(__file__))
        password_recovery_dir = os.path.dirname(test_dir)
        requirements_path = os.path.join(password_recovery_dir, 'requirements.txt')
        
        # Read requirements.txt
        with open(requirements_path, 'r') as f:
            requirements_content = f.read()
        
        # Parse all non-empty, non-comment lines
        lines_to_check = []
        for line_num, line in enumerate(requirements_content.split('\n'), start=1):
            stripped_line = line.strip()
            
            # Skip empty lines
            if not stripped_line:
                continue
            
            # Skip comment lines (lines starting with #)
            if stripped_line.startswith('#'):
                continue
            
            # This is a non-empty, non-comment line that should have exactly one dependency
            lines_to_check.append({
                'line_num': line_num,
                'content': stripped_line,
                'original': line
            })
        
        # Property: For ANY non-empty, non-comment line, it must declare exactly one package
        violations = []
        
        for line_info in lines_to_check:
            line = line_info['content']
            line_num = line_info['line_num']
            
            # Check if the line declares exactly one package
            # A valid dependency line should match one of these patterns:
            # - package>=version
            # - package==version
            # - package<=version
            # - package>version
            # - package<version
            # - package~=version
            # - package (without version constraint)
            
            # Count how many package declarations are on this line
            # We'll look for multiple patterns that indicate separate packages
            
            # Pattern 1: Multiple version operators on the same line
            # e.g., "package1>=1.0 package2>=2.0" would have 2 >= operators
            # Note: Check compound operators first (>=, <=, ==, ~=) before single ones (>, <)
            # to avoid double-counting
            version_operators = ['>=', '==', '<=', '~=']
            operator_count = sum(line.count(op) for op in version_operators)
            
            # If no compound operators found, check for single operators
            if operator_count == 0:
                single_operators = ['>', '<']
                operator_count = sum(line.count(op) for op in single_operators)
            
            if operator_count > 1:
                violations.append({
                    'line_num': line_num,
                    'content': line,
                    'reason': f'Multiple version operators found ({operator_count}). Each line should have at most one package with version constraint.',
                    'operator_count': operator_count
                })
                continue
            
            # Pattern 2: Multiple whitespace-separated package names
            # This is tricky because version strings can have spaces in some formats
            # We'll check for common patterns that indicate multiple packages
            
            # Split by whitespace and check if we have multiple package-like tokens
            tokens = line.split()
            
            if len(tokens) > 1:
                # If we have multiple tokens, check if they look like separate packages
                # Valid single-package lines:
                # - "package>=1.0.0" (1 token)
                # - "package >= 1.0.0" (3 tokens but still one package)
                # - "package" (1 token)
                
                # Invalid multi-package lines:
                # - "package1 package2" (2 tokens, both look like packages)
                # - "package1>=1.0 package2>=2.0" (2 tokens with operators)
                
                # Check if we have multiple tokens that look like package names
                # A package name typically starts with a letter and contains alphanumeric, dash, underscore
                package_name_pattern = re.compile(r'^[a-zA-Z][a-zA-Z0-9_-]*$')
                
                # Count tokens that look like package names (not operators or versions)
                package_like_tokens = []
                all_version_operators = ['>=', '==', '<=', '~=', '>', '<']
                for token in tokens:
                    # Skip version operators
                    if token in all_version_operators:
                        continue
                    
                    # Skip version numbers (contain dots and digits)
                    if re.match(r'^[\d.]+$', token):
                        continue
                    
                    # Check if token looks like a package name
                    # Remove any trailing version operator
                    clean_token = token
                    all_version_operators = ['>=', '==', '<=', '~=', '>', '<']
                    for op in all_version_operators:
                        if op in clean_token:
                            clean_token = clean_token.split(op)[0]
                    
                    if package_name_pattern.match(clean_token):
                        package_like_tokens.append(clean_token)
                
                # If we found multiple package-like tokens, this is a violation
                if len(package_like_tokens) > 1:
                    violations.append({
                        'line_num': line_num,
                        'content': line,
                        'reason': f'Multiple package names found: {package_like_tokens}. Each line should declare exactly one package.',
                        'packages': package_like_tokens
                    })
                    continue
            
            # Pattern 3: Comma-separated packages (some formats allow this)
            # e.g., "package1, package2" or "package1>=1.0, package2>=2.0"
            if ',' in line:
                violations.append({
                    'line_num': line_num,
                    'content': line,
                    'reason': 'Comma found in line. Each package should be on its own line, not comma-separated.',
                })
                continue
            
            # Pattern 4: Semicolon-separated packages (some formats allow this)
            if ';' in line and not line.strip().endswith(';'):
                # Note: semicolons at the end are used for environment markers, which is valid
                # e.g., "package>=1.0; python_version >= '3.6'"
                # But semicolons in the middle indicate multiple packages
                semicolon_pos = line.index(';')
                # Check if there's content after the semicolon that looks like another package
                after_semicolon = line[semicolon_pos+1:].strip()
                if after_semicolon and not after_semicolon.startswith('python_version') and not after_semicolon.startswith('sys_platform'):
                    violations.append({
                        'line_num': line_num,
                        'content': line,
                        'reason': 'Semicolon found with content that may indicate multiple packages. Each package should be on its own line.',
                    })
                    continue
        
        # Assert no violations found
        if violations:
            error_msg = "Single dependency per line property violated:\n\n"
            for violation in violations:
                error_msg += f"Line {violation['line_num']}: {violation['content']}\n"
                error_msg += f"  Reason: {violation['reason']}\n\n"
            
            error_msg += "Each non-empty, non-comment line in requirements.txt must declare "
            error_msg += "exactly one package dependency. This follows pip requirements.txt format "
            error_msg += "conventions and ensures the file is parseable by SAM build and pip."
            
            pytest.fail(error_msg)
        
        # Verify we actually checked some lines (sanity check)
        assert len(lines_to_check) > 0, \
            "No non-empty, non-comment lines found in requirements.txt. " \
            "The file should contain at least some package dependencies."
        
        # Log success for visibility
        print(f"\n✓ Single dependency per line property verified:")
        print(f"  - Checked {len(lines_to_check)} non-empty, non-comment lines")
        print(f"  - All lines declare exactly one package dependency")
        print(f"  - File follows pip requirements.txt format conventions")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
