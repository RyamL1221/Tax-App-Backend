"""
SAM configuration validator.

This module validates template.yaml for misconfigurations that could cause
build hangs or failures. It checks CodeUri paths, function names, runtime
settings, and environment parameter configuration.
"""

import os
import logging
from typing import List, Dict, Any
import yaml

from models import ConfigIssue
from utils import get_template_path, get_project_root


logger = logging.getLogger(__name__)


# CloudFormation intrinsic function constructors for YAML parsing
def _cloudformation_constructor(loader, tag_suffix, node):
    """
    Generic constructor for CloudFormation intrinsic functions.
    
    This allows PyYAML to parse CloudFormation tags like !Ref, !GetAtt, !If, etc.
    without throwing errors. We convert them to dictionaries for validation.
    """
    if isinstance(node, yaml.ScalarNode):
        value = loader.construct_scalar(node)
    elif isinstance(node, yaml.SequenceNode):
        value = loader.construct_sequence(node)
    elif isinstance(node, yaml.MappingNode):
        value = loader.construct_mapping(node)
    else:
        value = None
    
    # Convert tag to function name (e.g., !Ref -> Ref, !GetAtt -> Fn::GetAtt)
    if tag_suffix == 'Ref':
        return {'Ref': value}
    elif tag_suffix in ['GetAtt', 'Join', 'Split', 'Select', 'Sub']:
        return {f'Fn::{tag_suffix}': value}
    elif tag_suffix in ['Equals', 'And', 'Or', 'Not', 'If']:
        return {f'Fn::{tag_suffix}': value}
    else:
        return {tag_suffix: value}


# Register CloudFormation intrinsic function constructors
yaml.add_multi_constructor('!', _cloudformation_constructor, Loader=yaml.SafeLoader)


def validate_sam_template() -> List[ConfigIssue]:
    """
    Validate template.yaml for issues.
    
    Returns:
        List of ConfigIssue objects describing problems found
        
    Raises:
        FileNotFoundError: If template.yaml is not found
        yaml.YAMLError: If template.yaml has invalid YAML syntax
    """
    logger.info("Validating SAM template configuration")
    issues = []
    
    try:
        template_path = get_template_path()
        logger.debug(f"Loading template from {template_path}")
        
        with open(template_path, 'r', encoding='utf-8') as f:
            template = yaml.safe_load(f)
        
        # Run all validation checks
        issues.extend(validate_code_uris(template))
        issues.extend(check_duplicate_functions(template))
        issues.extend(validate_runtime_settings(template))
        issues.extend(validate_environment_config(template))
        
        logger.info(f"Template validation complete. Found {len(issues)} issues.")
        
    except FileNotFoundError as e:
        logger.error(f"Template file not found: {e}")
        issues.append(ConfigIssue(
            issue_type='missing_path',
            location='template.yaml',
            details=str(e),
            suggested_fix='Ensure template.yaml exists in project root'
        ))
    except yaml.YAMLError as e:
        logger.error(f"Invalid YAML syntax in template: {e}")
        issues.append(ConfigIssue(
            issue_type='env_config',
            location=f'template.yaml line {getattr(e, "problem_mark", "unknown")}',
            details=f'Invalid YAML syntax: {str(e)}',
            suggested_fix='Fix YAML syntax errors in template.yaml'
        ))
    except Exception as e:
        logger.error(f"Unexpected error validating template: {e}", exc_info=True)
        issues.append(ConfigIssue(
            issue_type='env_config',
            location='template.yaml',
            details=f'Unexpected error: {str(e)}',
            suggested_fix='Review template.yaml for issues'
        ))
    
    return issues


def validate_code_uris(template: Dict[str, Any]) -> List[ConfigIssue]:
    """
    Validate all CodeUri paths exist.
    
    Args:
        template: Parsed template.yaml dictionary
        
    Returns:
        List of ConfigIssue objects for missing paths
    """
    logger.debug("Validating CodeUri paths")
    issues = []
    project_root = get_project_root()
    
    # Get Resources section
    resources = template.get('Resources', {})
    
    for resource_name, resource_config in resources.items():
        # Check if this is a Lambda function
        resource_type = resource_config.get('Type', '')
        if resource_type != 'AWS::Serverless::Function':
            continue
        
        # Get CodeUri property
        properties = resource_config.get('Properties', {})
        code_uri = properties.get('CodeUri')
        
        if not code_uri:
            logger.warning(f"Function {resource_name} has no CodeUri specified")
            issues.append(ConfigIssue(
                issue_type='missing_path',
                location=f'Resources.{resource_name}.Properties',
                details=f'Function {resource_name} has no CodeUri specified',
                suggested_fix=f'Add CodeUri property to {resource_name}'
            ))
            continue
        
        # Check if path exists
        full_path = os.path.join(project_root, code_uri.rstrip('/'))
        if not os.path.exists(full_path):
            logger.warning(f"CodeUri path does not exist: {code_uri}")
            issues.append(ConfigIssue(
                issue_type='missing_path',
                location=f'Resources.{resource_name}.Properties.CodeUri',
                details=f'CodeUri path does not exist: {code_uri}',
                suggested_fix=f'Create directory {code_uri} or update CodeUri to correct path'
            ))
        elif not os.path.isdir(full_path):
            logger.warning(f"CodeUri path is not a directory: {code_uri}")
            issues.append(ConfigIssue(
                issue_type='missing_path',
                location=f'Resources.{resource_name}.Properties.CodeUri',
                details=f'CodeUri path is not a directory: {code_uri}',
                suggested_fix=f'Ensure {code_uri} is a directory, not a file'
            ))
        else:
            logger.debug(f"CodeUri path valid: {code_uri}")
    
    return issues


def check_duplicate_functions(template: Dict[str, Any]) -> List[ConfigIssue]:
    """
    Check for duplicate function names.
    
    Args:
        template: Parsed template.yaml dictionary
        
    Returns:
        List of ConfigIssue objects for duplicate function names
    """
    logger.debug("Checking for duplicate function names")
    issues = []
    
    # Get Resources section
    resources = template.get('Resources', {})
    
    # Track function names
    function_names = {}
    
    for resource_name, resource_config in resources.items():
        # Check if this is a Lambda function
        resource_type = resource_config.get('Type', '')
        if resource_type != 'AWS::Serverless::Function':
            continue
        
        # Check if we've seen this resource name before
        if resource_name in function_names:
            logger.warning(f"Duplicate function name found: {resource_name}")
            issues.append(ConfigIssue(
                issue_type='duplicate_function',
                location=f'Resources.{resource_name}',
                details=f'Duplicate function name: {resource_name}',
                suggested_fix=f'Rename one of the functions named {resource_name}'
            ))
        else:
            function_names[resource_name] = True
    
    logger.debug(f"Found {len(function_names)} unique function names")
    return issues


def validate_runtime_settings(template: Dict[str, Any]) -> List[ConfigIssue]:
    """
    Validate Runtime is set to python3.14.
    
    Args:
        template: Parsed template.yaml dictionary
        
    Returns:
        List of ConfigIssue objects for invalid runtime settings
    """
    logger.debug("Validating runtime settings")
    issues = []
    expected_runtime = 'python3.14'
    
    # Get Resources section
    resources = template.get('Resources', {})
    
    for resource_name, resource_config in resources.items():
        # Check if this is a Lambda function
        resource_type = resource_config.get('Type', '')
        if resource_type != 'AWS::Serverless::Function':
            continue
        
        # Get Runtime property
        properties = resource_config.get('Properties', {})
        runtime = properties.get('Runtime')
        
        if not runtime:
            logger.warning(f"Function {resource_name} has no Runtime specified")
            issues.append(ConfigIssue(
                issue_type='invalid_runtime',
                location=f'Resources.{resource_name}.Properties',
                details=f'Function {resource_name} has no Runtime specified',
                suggested_fix=f'Add Runtime: {expected_runtime} to {resource_name}'
            ))
        elif runtime != expected_runtime:
            logger.warning(f"Function {resource_name} has incorrect runtime: {runtime}")
            issues.append(ConfigIssue(
                issue_type='invalid_runtime',
                location=f'Resources.{resource_name}.Properties.Runtime',
                details=f'Function {resource_name} has runtime {runtime}, expected {expected_runtime}',
                suggested_fix=f'Change Runtime to {expected_runtime} for {resource_name}'
            ))
        else:
            logger.debug(f"Function {resource_name} has correct runtime: {runtime}")
    
    return issues


def validate_environment_config(template: Dict[str, Any]) -> List[ConfigIssue]:
    """
    Validate Environment parameter configuration.
    
    Args:
        template: Parsed template.yaml dictionary
        
    Returns:
        List of ConfigIssue objects for environment configuration issues
    """
    logger.debug("Validating environment parameter configuration")
    issues = []
    
    # Check if Parameters section exists
    parameters = template.get('Parameters', {})
    
    if 'Environment' not in parameters:
        logger.warning("Environment parameter not defined in template")
        issues.append(ConfigIssue(
            issue_type='env_config',
            location='Parameters',
            details='Environment parameter not defined in template',
            suggested_fix='Add Environment parameter with AllowedValues: [local, production]'
        ))
        return issues
    
    # Validate Environment parameter configuration
    env_param = parameters['Environment']
    
    # Check Type
    if env_param.get('Type') != 'String':
        logger.warning("Environment parameter Type should be String")
        issues.append(ConfigIssue(
            issue_type='env_config',
            location='Parameters.Environment.Type',
            details=f'Environment parameter Type is {env_param.get("Type")}, should be String',
            suggested_fix='Set Environment parameter Type to String'
        ))
    
    # Check AllowedValues
    allowed_values = env_param.get('AllowedValues', [])
    expected_values = ['local', 'production']
    
    if set(allowed_values) != set(expected_values):
        logger.warning(f"Environment parameter AllowedValues incorrect: {allowed_values}")
        issues.append(ConfigIssue(
            issue_type='env_config',
            location='Parameters.Environment.AllowedValues',
            details=f'Environment parameter AllowedValues is {allowed_values}, expected {expected_values}',
            suggested_fix=f'Set AllowedValues to {expected_values}'
        ))
    
    # Check if Conditions section exists and has IsLocal condition
    conditions = template.get('Conditions', {})
    
    if 'IsLocal' not in conditions:
        logger.warning("IsLocal condition not defined in template")
        issues.append(ConfigIssue(
            issue_type='env_config',
            location='Conditions',
            details='IsLocal condition not defined in template',
            suggested_fix='Add IsLocal condition: !Equals [!Ref Environment, local]'
        ))
    
    # Validate Lambda functions use AWS_ENDPOINT_URL with IsLocal condition
    resources = template.get('Resources', {})
    
    for resource_name, resource_config in resources.items():
        # Check if this is a Lambda function
        resource_type = resource_config.get('Type', '')
        if resource_type != 'AWS::Serverless::Function':
            continue
        
        # Get Environment Variables
        properties = resource_config.get('Properties', {})
        environment = properties.get('Environment', {})
        variables = environment.get('Variables', {})
        
        # Check if AWS_ENDPOINT_URL is configured
        if 'AWS_ENDPOINT_URL' in variables:
            endpoint_url = variables['AWS_ENDPOINT_URL']
            
            # Check if it uses the IsLocal condition
            # In YAML, this would be: !If [IsLocal, "http://172.18.0.1:4566", !Ref "AWS::NoValue"]
            # After parsing, it becomes a dict with 'Fn::If' key
            if not isinstance(endpoint_url, dict) or 'Fn::If' not in endpoint_url:
                logger.warning(f"Function {resource_name} AWS_ENDPOINT_URL should use IsLocal condition")
                issues.append(ConfigIssue(
                    issue_type='env_config',
                    location=f'Resources.{resource_name}.Properties.Environment.Variables.AWS_ENDPOINT_URL',
                    details=f'Function {resource_name} AWS_ENDPOINT_URL should use IsLocal condition',
                    suggested_fix='Use !If [IsLocal, "http://172.18.0.1:4566", !Ref "AWS::NoValue"]'
                ))
    
    return issues


def main():
    """CLI entry point for SAM configuration validation."""
    import sys
    from utils import setup_logging
    
    # Set up logging
    setup_logging(verbose='-v' in sys.argv or '--verbose' in sys.argv)
    
    logger.info("Starting SAM configuration validation")
    
    try:
        issues = validate_sam_template()
        
        if not issues:
            print("\n✅ SAM configuration validation passed!")
            print("No issues found in template.yaml")
            return 0
        
        print(f"\n❌ SAM configuration validation found {len(issues)} issue(s):\n")
        
        # Group issues by type
        issues_by_type = {}
        for issue in issues:
            if issue.issue_type not in issues_by_type:
                issues_by_type[issue.issue_type] = []
            issues_by_type[issue.issue_type].append(issue)
        
        # Print issues grouped by type
        for issue_type, type_issues in issues_by_type.items():
            print(f"\n{issue_type.upper().replace('_', ' ')} ({len(type_issues)}):")
            for issue in type_issues:
                print(f"  Location: {issue.location}")
                print(f"  Details: {issue.details}")
                if issue.suggested_fix:
                    print(f"  Fix: {issue.suggested_fix}")
                print()
        
        return 1
        
    except Exception as e:
        logger.error(f"Validation failed with error: {e}", exc_info=True)
        print(f"\n❌ Validation failed: {e}")
        return 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
