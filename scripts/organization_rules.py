"""
Organization Rules Engine for Workspace Organization.

This module provides programmatic access to workspace organization rules,
defining where different types of files should be placed in the project structure.

The rules match the guidelines defined in .kiro/steering/workspace-organization.md
and the structure documented in ORGANIZATION.md.
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List


@dataclass
class OrganizationRule:
    """
    Represents a file organization rule.
    
    Attributes:
        pattern: File pattern (e.g., "*.py", "test-output-*.pdf")
        destination: Target directory for files matching this pattern
        condition: Optional additional condition for rule application
        priority: Rule priority for resolving conflicts (higher = more specific)
        description: Human-readable description of the rule
    """
    pattern: str
    destination: str
    condition: Optional[str] = None
    priority: int = 0
    description: str = ""


class OrganizationRules:
    """
    Defines file placement rules for the workspace.
    
    This class encapsulates all the organization rules from the workspace
    organization steering file, providing methods to determine correct
    file placement and validate file locations.
    """
    
    # Essential files that MUST remain in root directory
    ESSENTIAL_ROOT_FILES = {
        # Project Documentation
        'README.md',
        'ORGANIZATION.md',
        'REORGANIZATION_SUMMARY.md',
        
        # Build and Configuration
        'Makefile',
        'template.yaml',
        'docker-compose.yml',
        'samconfig.toml',
        
        # Environment Configuration
        'env.json',
        '.env.example',
        '.env.local',
        '.env',
        
        # Version Control
        '.gitignore',
    }
    
    # Temporary file patterns that should be gitignored
    TEMPORARY_FILE_PATTERNS = [
        # Python cache
        r'__pycache__',
        r'\.pyc$',
        r'\.pyo$',
        r'\.pytest_cache',
        r'\.hypothesis',
        
        # Test outputs
        r'^test-output-.*\.pdf$',
        r'^test_output_.*\.pdf$',
        r'-test-output\.pdf$',
        
        # Debug/inspection outputs
        r'_output\.txt$',
        r'_report\.txt$',
        r'_findings\.txt$',
        r'_analysis\.txt$',
        
        # Temporary verification scripts in root
        r'^verify_.*\.py$',
        r'^test_.*\.py$',
        r'^inspect_.*\.py$',
        r'^debug_.*\.py$',
        
        # Build artifacts
        r'\.aws-sam',
        r'\.egg-info',
        r'^dist$',
        r'^build$',
    ]
    
    # Lambda function directories
    LAMBDA_FUNCTIONS = [
        'user_registration',
        'user_login',
        'password_recovery',
        'tax_document_generation',
        'document_download',
    ]
    
    def __init__(self):
        """Initialize the organization rules engine."""
        self.rules = self._build_rules()
    
    def _build_rules(self) -> List[OrganizationRule]:
        """
        Build the complete set of organization rules.
        
        Returns:
            List of OrganizationRule objects, ordered by priority
        """
        rules = []
        
        # High priority: Essential root files (stay in root)
        for filename in self.ESSENTIAL_ROOT_FILES:
            rules.append(OrganizationRule(
                pattern=filename,
                destination='.',
                priority=100,
                description=f"Essential root file: {filename}"
            ))
        
        # High priority: Kiro configuration files
        rules.append(OrganizationRule(
            pattern=r'\.kiro/specs/.*/(requirements|design|tasks)\.md$',
            destination='.kiro/specs/<feature-name>/',
            priority=90,
            description="Active spec files"
        ))
        
        rules.append(OrganizationRule(
            pattern=r'\.kiro/steering/.*\.md$',
            destination='.kiro/steering/',
            priority=90,
            description="Development guidelines"
        ))
        
        rules.append(OrganizationRule(
            pattern=r'\.kiro/hooks/.*\.kiro\.hook$',
            destination='.kiro/hooks/',
            priority=90,
            description="Agent hooks"
        ))
        
        # High priority: Lambda-specific files
        for lambda_func in self.LAMBDA_FUNCTIONS:
            rules.append(OrganizationRule(
                pattern=f'{lambda_func}/.*\\.py$',
                destination=f'{lambda_func}/',
                condition='lambda_specific',
                priority=85,
                description=f"Lambda-specific code for {lambda_func}"
            ))
            
            rules.append(OrganizationRule(
                pattern=f'{lambda_func}/tests/test_.*\\.py$',
                destination=f'{lambda_func}/tests/',
                priority=85,
                description=f"Lambda-specific tests for {lambda_func}"
            ))
        
        # Medium-high priority: Documentation by category
        rules.append(OrganizationRule(
            pattern=r'.*FIELD.*REFERENCE.*\.md$',
            destination='docs/architecture/',
            priority=70,
            description="Field reference documentation"
        ))
        
        rules.append(OrganizationRule(
            pattern=r'.*MAPPING.*\.md$',
            destination='docs/architecture/',
            priority=70,
            description="Field mapping documentation"
        ))
        
        rules.append(OrganizationRule(
            pattern=r'.*MIGRATION.*\.md$',
            destination='docs/architecture/',
            priority=70,
            description="Migration guides"
        ))
        
        rules.append(OrganizationRule(
            pattern=r'.*SETUP.*\.md$',
            destination='docs/development/',
            priority=70,
            description="Setup guides"
        ))
        
        rules.append(OrganizationRule(
            pattern=r'.*IMPORT.*PATTERN.*\.md$',
            destination='docs/development/',
            priority=70,
            description="Import pattern documentation"
        ))
        
        rules.append(OrganizationRule(
            pattern=r'.*QUICK.*REFERENCE.*\.md$',
            destination='docs/development/',
            priority=70,
            description="Quick reference guides"
        ))
        
        rules.append(OrganizationRule(
            pattern=r'TASK_.*\.md$',
            destination='docs/testing/',
            priority=70,
            description="Task verification documentation"
        ))
        
        rules.append(OrganizationRule(
            pattern=r'.*VERIFICATION.*\.md$',
            destination='docs/testing/',
            priority=70,
            description="Verification reports"
        ))
        
        rules.append(OrganizationRule(
            pattern=r'.*TEST.*RESULT.*\.md$',
            destination='docs/testing/',
            priority=70,
            description="Test results"
        ))
        
        rules.append(OrganizationRule(
            pattern=r'.*-example\.json$',
            destination='docs/examples/',
            priority=70,
            description="Example JSON payloads"
        ))
        
        rules.append(OrganizationRule(
            pattern=r'IMPLEMENTATION.*SUMMARY.*\.md$',
            destination='docs/specs/',
            priority=70,
            description="Implementation summaries"
        ))
        
        rules.append(OrganizationRule(
            pattern=r'CHANGELOG_.*\.md$',
            destination='docs/',
            priority=70,
            description="Project-wide changelogs"
        ))
        
        # Medium priority: Scripts and utilities
        rules.append(OrganizationRule(
            pattern=r'.*\.sh$',
            destination='scripts/',
            priority=60,
            description="Shell scripts"
        ))
        
        rules.append(OrganizationRule(
            pattern=r'verify_.*\.py$',
            destination='scripts/',
            priority=60,
            description="Verification scripts"
        ))
        
        rules.append(OrganizationRule(
            pattern=r'validate_.*\.py$',
            destination='scripts/',
            priority=60,
            description="Validation scripts"
        ))
        
        rules.append(OrganizationRule(
            pattern=r'generate_.*\.py$',
            destination='scripts/utils/',
            priority=60,
            description="Data generation scripts"
        ))
        
        # Medium priority: Debug tools
        rules.append(OrganizationRule(
            pattern=r'diagnose_.*\.py$',
            destination='debug_tools/',
            priority=60,
            description="Diagnostic tools"
        ))
        
        rules.append(OrganizationRule(
            pattern=r'debug_tools/.*\.py$',
            destination='debug_tools/',
            priority=60,
            description="Debug tools"
        ))
        
        rules.append(OrganizationRule(
            pattern=r'debug_tools/tests/test_.*\.py$',
            destination='debug_tools/tests/',
            priority=60,
            description="Debug tool tests"
        ))
        
        # Medium priority: PDF files
        rules.append(OrganizationRule(
            pattern=r'.*\.pdf$',
            destination='samples/',
            priority=50,
            description="PDF files (templates and test outputs)"
        ))
        
        # Medium priority: Lambda events
        rules.append(OrganizationRule(
            pattern=r'.*event.*\.json$',
            destination='events/',
            priority=50,
            description="Lambda event files"
        ))
        
        # Medium priority: Project-wide tests
        rules.append(OrganizationRule(
            pattern=r'tests/manual/test_.*\.py$',
            destination='tests/manual/',
            priority=50,
            description="Manual test scripts"
        ))
        
        rules.append(OrganizationRule(
            pattern=r'tests/integration/test_.*\.py$',
            destination='tests/integration/',
            priority=50,
            description="Integration tests"
        ))
        
        rules.append(OrganizationRule(
            pattern=r'tests/test_.*_property\.py$',
            destination='tests/',
            priority=50,
            description="Project-wide property tests"
        ))
        
        # Low priority: Generic fallbacks
        rules.append(OrganizationRule(
            pattern=r'.*\.md$',
            destination='docs/',
            priority=10,
            description="Generic documentation"
        ))
        
        rules.append(OrganizationRule(
            pattern=r'.*\.py$',
            destination='scripts/',
            priority=10,
            description="Generic Python scripts"
        ))
        
        # Sort by priority (highest first)
        rules.sort(key=lambda r: r.priority, reverse=True)
        
        return rules
    
    def is_essential_root_file(self, filename: str) -> bool:
        """
        Check if a file should remain in the root directory.
        
        Args:
            filename: Name of the file (not full path)
            
        Returns:
            True if file is essential and should stay in root, False otherwise
        """
        return filename in self.ESSENTIAL_ROOT_FILES
    
    def is_temporary_file(self, filepath: str) -> bool:
        """
        Check if a file is temporary and should be gitignored.
        
        Args:
            filepath: Path to the file (can be relative or just filename)
            
        Returns:
            True if file matches temporary file patterns, False otherwise
        """
        # Convert to Path for easier manipulation
        path = Path(filepath)
        filename = path.name
        
        # Check against all temporary file patterns
        for pattern in self.TEMPORARY_FILE_PATTERNS:
            if re.search(pattern, str(path)):
                return True
            if re.search(pattern, filename):
                return True
        
        return False
    
    def get_destination_for_file(self, filepath: str, context: Optional[dict] = None) -> str:
        """
        Determine the correct destination directory for a file.
        
        Args:
            filepath: Path to the file (relative to project root)
            context: Optional context dictionary with additional information:
                - 'is_lambda_specific': bool - Is this Lambda-specific code?
                - 'lambda_function': str - Which Lambda function?
                - 'is_diagnostic': bool - Is this a diagnostic tool?
                - 'is_manual_test': bool - Is this a manual test script?
        
        Returns:
            Suggested destination directory path
        """
        if context is None:
            context = {}
        
        # Convert to Path for easier manipulation
        path = Path(filepath)
        filename = path.name
        
        # Check if it's an essential root file
        if self.is_essential_root_file(filename):
            return '.'
        
        # Check if it's a temporary file (shouldn't be committed)
        if self.is_temporary_file(filepath):
            return '.gitignore'
        
        # Apply rules in priority order
        for rule in self.rules:
            # Check if pattern matches
            if self._matches_pattern(str(path), rule.pattern):
                # Check additional conditions if specified
                if rule.condition:
                    if not self._check_condition(rule.condition, context):
                        continue
                
                # Return destination (may need context substitution)
                return self._substitute_destination(rule.destination, context)
        
        # No rule matched - return generic suggestion based on file type
        if filename.endswith('.py'):
            return 'scripts/'
        elif filename.endswith('.md'):
            return 'docs/'
        elif filename.endswith('.pdf'):
            return 'samples/'
        elif filename.endswith('.json'):
            return 'events/'
        elif filename.endswith('.sh'):
            return 'scripts/'
        else:
            return 'unknown'
    
    def _matches_pattern(self, filepath: str, pattern: str) -> bool:
        """
        Check if a filepath matches a pattern.
        
        Args:
            filepath: File path to check
            pattern: Pattern to match (can be exact match or regex)
            
        Returns:
            True if pattern matches, False otherwise
        """
        # Exact match
        if filepath == pattern or Path(filepath).name == pattern:
            return True
        
        # Regex match
        try:
            if re.search(pattern, filepath):
                return True
        except re.error:
            # Invalid regex, treat as literal
            pass
        
        return False
    
    def _check_condition(self, condition: str, context: dict) -> bool:
        """
        Check if a condition is met based on context.
        
        Args:
            condition: Condition string to check
            context: Context dictionary with additional information
            
        Returns:
            True if condition is met, False otherwise
        """
        if condition == 'lambda_specific':
            return context.get('is_lambda_specific', False)
        elif condition == 'diagnostic':
            return context.get('is_diagnostic', False)
        elif condition == 'manual_test':
            return context.get('is_manual_test', False)
        
        return False
    
    def _substitute_destination(self, destination: str, context: dict) -> str:
        """
        Substitute placeholders in destination with context values.
        
        Args:
            destination: Destination path with possible placeholders
            context: Context dictionary with values for substitution
            
        Returns:
            Destination path with placeholders replaced
        """
        result = destination
        
        # Replace <feature-name> placeholder
        if '<feature-name>' in result and 'feature_name' in context:
            result = result.replace('<feature-name>', context['feature_name'])
        
        # Replace <lambda-function> placeholder
        if '<lambda-function>' in result and 'lambda_function' in context:
            result = result.replace('<lambda-function>', context['lambda_function'])
        
        return result
    
    def get_rule_for_file(self, filepath: str, context: Optional[dict] = None) -> Optional[OrganizationRule]:
        """
        Get the organization rule that applies to a file.
        
        Args:
            filepath: Path to the file
            context: Optional context dictionary
            
        Returns:
            OrganizationRule if a rule matches, None otherwise
        """
        if context is None:
            context = {}
        
        path = Path(filepath)
        
        # Check essential root files first
        if self.is_essential_root_file(path.name):
            return OrganizationRule(
                pattern=path.name,
                destination='.',
                priority=100,
                description=f"Essential root file: {path.name}"
            )
        
        # Apply rules in priority order
        for rule in self.rules:
            if self._matches_pattern(str(path), rule.pattern):
                if rule.condition:
                    if not self._check_condition(rule.condition, context):
                        continue
                return rule
        
        return None
    
    def validate_file_location(self, filepath: str, context: Optional[dict] = None) -> tuple[bool, str]:
        """
        Validate if a file is in the correct location.
        
        Args:
            filepath: Current path to the file
            context: Optional context dictionary
            
        Returns:
            Tuple of (is_valid, message)
            - is_valid: True if file is in correct location
            - message: Explanation or suggestion
        """
        if context is None:
            context = {}
        
        path = Path(filepath)
        
        # Get expected destination
        expected_dest = self.get_destination_for_file(filepath, context)
        
        # Check if file is in root directory
        if len(path.parts) == 1:
            # File is in root
            if self.is_essential_root_file(path.name):
                return True, f"✅ {path.name} is an essential root file"
            elif self.is_temporary_file(filepath):
                return False, f"⚠️  {path.name} is a temporary file and should be in .gitignore"
            else:
                return False, f"❌ {path.name} should be in {expected_dest}"
        
        # File is in a subdirectory - check if it matches expected destination
        current_dir = str(path.parent)
        
        if expected_dest == '.gitignore':
            return False, f"⚠️  {filepath} is a temporary file and should be in .gitignore"
        elif expected_dest == 'unknown':
            return False, f"❓ {filepath} - unable to determine correct location"
        elif current_dir.startswith(expected_dest.rstrip('/')):
            return True, f"✅ {filepath} is in the correct location"
        else:
            return False, f"❌ {filepath} should be in {expected_dest}"
