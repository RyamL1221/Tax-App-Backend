"""
Unit tests for requirements.txt file validation.

Tests that the password_recovery directory has a properly configured
requirements.txt file for SAM build dependency packaging.
"""

import os
import pytest


class TestRequirementsFileExistence:
    """Tests for requirements.txt file existence."""
    
    def test_requirements_file_exists(self):
        """
        Test that password_recovery/requirements.txt exists.
        
        **Validates: Requirements 1.1, 1.3**
        
        The password_recovery directory must contain a requirements.txt file
        so that SAM build knows which dependencies to package with the Lambda functions.
        Without this file, Lambda functions fail at runtime with import errors.
        """
        # Get the path to the password_recovery directory
        test_dir = os.path.dirname(os.path.abspath(__file__))
        password_recovery_dir = os.path.dirname(test_dir)
        requirements_path = os.path.join(password_recovery_dir, 'requirements.txt')
        
        # Verify the file exists
        assert os.path.exists(requirements_path), \
            f"requirements.txt file not found at {requirements_path}. " \
            "This file is required for SAM build to package Lambda dependencies."
        
        # Verify it's a file (not a directory)
        assert os.path.isfile(requirements_path), \
            f"{requirements_path} exists but is not a file"


class TestRequiredDependencies:
    """Tests for required dependencies presence in requirements.txt."""
    
    def test_required_dependencies_present(self):
        """
        Test that bcrypt, boto3, email-validator, and PyJWT are listed in requirements.txt.
        
        **Validates: Requirements 2.1, 2.2**
        
        The requirements.txt file must include all dependencies used by the password
        recovery Lambda functions:
        - bcrypt: for password hashing operations
        - boto3: for AWS service interactions (DynamoDB, SES)
        - email-validator: for email validation
        - PyJWT: for JWT token handling
        
        Without these dependencies, Lambda functions will fail at runtime with import errors.
        """
        # Get the path to requirements.txt
        test_dir = os.path.dirname(os.path.abspath(__file__))
        password_recovery_dir = os.path.dirname(test_dir)
        requirements_path = os.path.join(password_recovery_dir, 'requirements.txt')
        
        # Read the requirements file
        with open(requirements_path, 'r') as f:
            requirements_content = f.read()
        
        # Required dependencies
        required_dependencies = ['bcrypt', 'boto3', 'email-validator', 'PyJWT']
        
        # Check each required dependency is present
        for dependency in required_dependencies:
            assert dependency in requirements_content, \
                f"Required dependency '{dependency}' not found in requirements.txt. " \
                f"This dependency is required for password recovery Lambda functions to execute successfully."
        
        # Verify each dependency appears on its own line (not just as a substring)
        requirements_lines = [line.strip() for line in requirements_content.split('\n') if line.strip() and not line.strip().startswith('#')]
        
        for dependency in required_dependencies:
            # Check that the dependency appears at the start of at least one line
            found = any(line.startswith(dependency) for line in requirements_lines)
            assert found, \
                f"Required dependency '{dependency}' not found as a standalone entry in requirements.txt. " \
                f"Each dependency must be on its own line."


class TestFormatConsistency:
    """Tests for requirements.txt format consistency."""
    
    def test_format_consistency_with_user_login(self):
        """
        Test that password_recovery/requirements.txt follows the same format as user_login/requirements.txt.
        
        **Validates: Requirements 5.1**
        
        The requirements.txt file should follow the same format as other Lambda functions
        in the codebase (specifically user_login) to maintain consistency. This includes:
        - One dependency per line
        - Format: package>=version
        - Same dependencies with same version constraints
        - No extra whitespace or formatting differences
        
        Consistent formatting makes the codebase easier to maintain and ensures
        all Lambda functions use compatible dependency versions.
        """
        # Get the path to password_recovery/requirements.txt
        test_dir = os.path.dirname(os.path.abspath(__file__))
        password_recovery_dir = os.path.dirname(test_dir)
        password_recovery_requirements = os.path.join(password_recovery_dir, 'requirements.txt')
        
        # Get the path to user_login/requirements.txt
        project_root = os.path.dirname(password_recovery_dir)
        user_login_requirements = os.path.join(project_root, 'user_login', 'requirements.txt')
        
        # Read both files
        with open(password_recovery_requirements, 'r') as f:
            password_recovery_content = f.read()
        
        with open(user_login_requirements, 'r') as f:
            user_login_content = f.read()
        
        # Parse dependencies from both files (ignore empty lines and comments)
        def parse_requirements(content):
            """Parse requirements file into a set of (package, version_constraint) tuples."""
            dependencies = []
            for line in content.split('\n'):
                line = line.strip()
                if line and not line.startswith('#'):
                    # Parse package>=version format
                    if '>=' in line:
                        package, version = line.split('>=', 1)
                        dependencies.append((package.strip(), version.strip()))
                    else:
                        # Handle other formats if present
                        dependencies.append((line, None))
            return dependencies
        
        password_recovery_deps = parse_requirements(password_recovery_content)
        user_login_deps = parse_requirements(user_login_content)
        
        # Convert to dictionaries for easier comparison
        password_recovery_dict = {pkg: ver for pkg, ver in password_recovery_deps}
        user_login_dict = {pkg: ver for pkg, ver in user_login_deps}
        
        # Verify same dependencies are present
        password_recovery_packages = set(password_recovery_dict.keys())
        user_login_packages = set(user_login_dict.keys())
        
        assert password_recovery_packages == user_login_packages, \
            f"Dependencies differ between password_recovery and user_login. " \
            f"Missing in password_recovery: {user_login_packages - password_recovery_packages}. " \
            f"Extra in password_recovery: {password_recovery_packages - user_login_packages}. " \
            f"Both should have the same dependencies for consistency."
        
        # Verify version constraints match
        for package in password_recovery_packages:
            password_recovery_version = password_recovery_dict[package]
            user_login_version = user_login_dict[package]
            
            assert password_recovery_version == user_login_version, \
                f"Version constraint mismatch for '{package}': " \
                f"password_recovery has '{package}>={password_recovery_version}' " \
                f"but user_login has '{package}>={user_login_version}'. " \
                f"Version constraints should match for consistency across Lambda functions."
        
        # Verify format: each dependency should use >= operator
        for package, version in password_recovery_deps:
            assert version is not None, \
                f"Dependency '{package}' in password_recovery/requirements.txt " \
                f"does not have a version constraint. All dependencies should use " \
                f"the format 'package>=version' for consistency."
        
        # Verify one dependency per line (no multiple dependencies on same line)
        password_recovery_lines = [line.strip() for line in password_recovery_content.split('\n') 
                                   if line.strip() and not line.strip().startswith('#')]
        
        for line in password_recovery_lines:
            # Each line should have exactly one >= operator
            assert line.count('>=') == 1, \
                f"Line '{line}' in password_recovery/requirements.txt " \
                f"should contain exactly one dependency with >= operator. " \
                f"Each dependency must be on its own line."


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
