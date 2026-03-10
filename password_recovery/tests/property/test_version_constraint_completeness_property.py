"""
Property-based test for version constraint completeness.

This test verifies that for any dependency listed in password_recovery/requirements.txt,
that dependency has a version constraint using the >= operator.
"""

import os
import pytest


class TestVersionConstraintCompletenessProperty:
    """Property-based test for version constraint completeness."""
    
    def test_version_constraint_completeness(self):
        """
        **Validates: Requirements 2.3, 5.2**
        Feature: fix-password-recovery-dependencies, Property 1: Version Constraint Completeness
        
        For any dependency listed in password_recovery/requirements.txt,
        that dependency SHALL have a version constraint using the >= operator.
        
        This ensures all dependencies have explicit version constraints for
        reproducible builds and compatibility. The >= operator allows patch
        and minor version updates while maintaining compatibility.
        """
        # Get the path to requirements.txt
        test_dir = os.path.dirname(os.path.abspath(__file__))
        password_recovery_dir = os.path.dirname(test_dir)
        requirements_path = os.path.join(password_recovery_dir, 'requirements.txt')
        
        # Read the requirements file
        with open(requirements_path, 'r') as f:
            requirements_content = f.read()
        
        # Parse all dependencies (non-empty, non-comment lines)
        dependencies = []
        for line in requirements_content.split('\n'):
            line = line.strip()
            # Skip empty lines and comments
            if line and not line.startswith('#'):
                dependencies.append(line)
        
        # Property: For ANY dependency, it must have a >= version constraint
        assert len(dependencies) > 0, \
            "requirements.txt should contain at least one dependency"
        
        for dependency in dependencies:
            # Check that the dependency has >= operator
            assert '>=' in dependency, \
                f"Dependency '{dependency}' does not have a version constraint using >=. " \
                f"All dependencies must use the format 'package>=version' for " \
                f"reproducible builds and compatibility."
            
            # Parse the dependency to verify format
            parts = dependency.split('>=')
            assert len(parts) == 2, \
                f"Dependency '{dependency}' has invalid format. " \
                f"Expected format: 'package>=version'"
            
            package_name = parts[0].strip()
            version = parts[1].strip()
            
            # Verify package name is not empty
            assert package_name, \
                f"Dependency '{dependency}' has empty package name. " \
                f"Format should be 'package>=version'"
            
            # Verify version is not empty
            assert version, \
                f"Dependency '{dependency}' has empty version. " \
                f"Format should be 'package>=version' with a specific version number"
            
            # Verify version looks like a version number (contains at least one digit)
            assert any(char.isdigit() for char in version), \
                f"Dependency '{dependency}' has invalid version '{version}'. " \
                f"Version should be a valid version number (e.g., '1.34.0')"
        
        # Property: Completeness check - verify all dependencies have constraints
        # Count dependencies with >= operator
        dependencies_with_constraints = [dep for dep in dependencies if '>=' in dep]
        
        assert len(dependencies_with_constraints) == len(dependencies), \
            f"Not all dependencies have version constraints. " \
            f"Found {len(dependencies)} dependencies but only " \
            f"{len(dependencies_with_constraints)} have >= constraints. " \
            f"All dependencies must specify version constraints."


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
