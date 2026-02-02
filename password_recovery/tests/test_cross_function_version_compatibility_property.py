"""
Property-based test for cross-function version compatibility.

This test verifies that for any dependency that appears in both
password_recovery/requirements.txt and another Lambda function's requirements.txt,
the version constraints are compatible (no conflicting version requirements).
"""

import os
import re
import pytest


class TestCrossFunctionVersionCompatibilityProperty:
    """Property-based test for cross-function version compatibility."""
    
    def test_cross_function_version_compatibility(self):
        """
        **Validates: Requirements 5.3**
        Feature: fix-password-recovery-dependencies, Property 3: Cross-Function Version Compatibility
        
        For any dependency that appears in both password_recovery/requirements.txt
        and another Lambda function's requirements.txt (user_login, user_registration),
        the version constraints SHALL be compatible (no conflicting version requirements).
        
        This ensures consistency across the codebase and prevents version conflicts
        during development and testing. Compatible versions mean the intersection of
        version ranges is non-empty.
        """
        # Get the path to password_recovery directory
        test_dir = os.path.dirname(os.path.abspath(__file__))
        password_recovery_dir = os.path.dirname(test_dir)
        project_root = os.path.dirname(password_recovery_dir)
        
        # Define Lambda function directories to check
        lambda_functions = ['password_recovery', 'user_login', 'user_registration']
        
        # Parse requirements.txt from each Lambda function
        all_requirements = {}
        
        for function_name in lambda_functions:
            requirements_path = os.path.join(project_root, function_name, 'requirements.txt')
            
            # Skip if requirements.txt doesn't exist (some functions might not have it)
            if not os.path.exists(requirements_path):
                continue
            
            with open(requirements_path, 'r') as f:
                requirements_content = f.read()
            
            # Parse dependencies
            dependencies = {}
            for line in requirements_content.split('\n'):
                line = line.strip()
                if line and not line.startswith('#'):
                    # Parse package and version constraint
                    parsed = self._parse_dependency(line)
                    if parsed:
                        package_name, operator, version = parsed
                        dependencies[package_name.lower()] = {
                            'operator': operator,
                            'version': version,
                            'raw': line
                        }
            
            all_requirements[function_name] = dependencies
        
        # Property: For ANY dependency that appears in multiple Lambda functions,
        # the version constraints must be compatible
        
        # Get all unique package names across all Lambda functions
        all_packages = set()
        for deps in all_requirements.values():
            all_packages.update(deps.keys())
        
        # Check each package for version compatibility
        incompatibilities = []
        
        for package in all_packages:
            # Find which Lambda functions use this package
            functions_using_package = {}
            for function_name, deps in all_requirements.items():
                if package in deps:
                    functions_using_package[function_name] = deps[package]
            
            # If package is used by multiple functions, check compatibility
            if len(functions_using_package) > 1:
                is_compatible, reason = self._check_version_compatibility(
                    package, functions_using_package
                )
                
                if not is_compatible:
                    incompatibilities.append({
                        'package': package,
                        'reason': reason,
                        'functions': functions_using_package
                    })
        
        # Assert no incompatibilities found
        if incompatibilities:
            error_msg = "Version incompatibilities found across Lambda functions:\n\n"
            for incompat in incompatibilities:
                error_msg += f"Package: {incompat['package']}\n"
                error_msg += f"Reason: {incompat['reason']}\n"
                error_msg += "Versions by function:\n"
                for func, info in incompat['functions'].items():
                    error_msg += f"  - {func}: {info['raw']}\n"
                error_msg += "\n"
            
            error_msg += "All Lambda functions should use compatible version constraints "
            error_msg += "to ensure consistency across the codebase and prevent version conflicts."
            
            pytest.fail(error_msg)
        
        # Log success for visibility
        print(f"\n✓ Cross-function version compatibility verified:")
        print(f"  - Checked {len(lambda_functions)} Lambda functions")
        print(f"  - Found {len(all_packages)} unique packages")
        
        # Show shared packages
        shared_packages = [pkg for pkg in all_packages 
                          if sum(1 for deps in all_requirements.values() if pkg in deps) > 1]
        if shared_packages:
            print(f"  - {len(shared_packages)} packages shared across functions: {sorted(shared_packages)}")
            print(f"  - All shared packages have compatible version constraints")
    
    def _parse_dependency(self, line):
        """
        Parse a dependency line into (package_name, operator, version).
        
        Returns None if the line cannot be parsed.
        """
        # Match patterns like: package>=1.2.3, package==1.2.3, package<=1.2.3, etc.
        # Also handle package without version constraint
        
        # Try to match with version constraint
        match = re.match(r'^([a-zA-Z0-9_-]+)\s*(>=|==|<=|>|<|~=)\s*(.+)$', line)
        if match:
            package_name = match.group(1)
            operator = match.group(2)
            version = match.group(3).strip()
            return (package_name, operator, version)
        
        # Try to match package without version constraint
        match = re.match(r'^([a-zA-Z0-9_-]+)$', line)
        if match:
            package_name = match.group(1)
            return (package_name, None, None)
        
        return None
    
    def _check_version_compatibility(self, package, functions_using_package):
        """
        Check if version constraints across functions are compatible.
        
        Returns (is_compatible, reason) tuple.
        
        Compatible means the intersection of version ranges is non-empty.
        
        Rules:
        1. No constraint (any version) is compatible with any specific constraint
        2. Same operator with same version is compatible
        3. Different operators or versions may be incompatible
        
        For strict consistency, all functions should use the same constraint,
        but we allow mixing constrained and unconstrained as technically compatible.
        """
        # Extract all version constraints
        constraints = []
        for function_name, info in functions_using_package.items():
            constraints.append({
                'function': function_name,
                'operator': info['operator'],
                'version': info['version'],
                'raw': info['raw']
            })
        
        # Separate constraints into those with and without version specifications
        has_constraint = [c for c in constraints if c['operator'] is not None]
        no_constraint = [c for c in constraints if c['operator'] is None]
        
        # Case 1: No constraints at all (all functions use package without version)
        if not has_constraint:
            return (True, "No version constraints specified (all functions use package without version)")
        
        # Case 2: Some have constraints, others don't
        # This is technically compatible (no constraint = any version)
        # but we'll note it for consistency
        if has_constraint and no_constraint:
            # Check if the constrained versions are all compatible with each other
            # If they are, then the unconstrained ones are also compatible
            if len(has_constraint) > 1:
                # Check compatibility among constrained versions
                constrained_compatible, reason = self._check_constrained_compatibility(has_constraint)
                if not constrained_compatible:
                    return (False, reason)
            
            # All constrained versions are compatible, and unconstrained is compatible with anything
            functions_without = [c['function'] for c in no_constraint]
            return (True, f"Compatible (note: {functions_without} have no version constraint)")
        
        # Case 3: All have constraints - check for compatibility
        return self._check_constrained_compatibility(has_constraint)
    
    def _check_constrained_compatibility(self, constrained_list):
        """
        Check compatibility among constraints that all have version specifications.
        
        Returns (is_compatible, reason) tuple.
        """
        # Check if all constraints are identical (ideal case)
        raw_constraints = [c['raw'] for c in constrained_list]
        if len(set(raw_constraints)) == 1:
            return (True, "All constraints are identical")
        
        # Check if operators differ
        operators = [c['operator'] for c in constrained_list]
        if len(set(operators)) > 1:
            return (False, f"Conflicting version constraint operators: {set(operators)}. "
                          f"Cannot determine if version ranges overlap.")
        
        # Check if versions differ (with same operator)
        versions = [c['version'] for c in constrained_list]
        if len(set(versions)) > 1:
            operator = operators[0]
            
            # For >= operator, different versions create different lower bounds
            # The highest lower bound is the effective constraint
            # This is technically compatible but may indicate inconsistency
            if operator == '>=':
                return (False, f"Different minimum versions specified: {set(versions)}. "
                              f"Functions should use the same minimum version for consistency.")
            
            # For == operator, different versions are incompatible
            if operator == '==':
                return (False, f"Conflicting exact versions specified: {set(versions)}. "
                              f"These version constraints are incompatible.")
            
            # For other operators, flag as potentially incompatible
            return (False, f"Different versions specified with {operator} operator: {set(versions)}. "
                          f"Cannot determine compatibility.")
        
        # All constraints use the same operator and version
        return (True, f"All constraints use {operators[0]} {versions[0]}")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
