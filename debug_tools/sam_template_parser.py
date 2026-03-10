"""
SAM template parser for extracting Lambda function configurations.

This module provides functions to parse template.yaml and extract Lambda
function configurations including handler information, CodeUri paths, and
function names. It's used by build verification and other diagnostic tools.

Usage:
    from debug_tools.sam_template_parser import parse_sam_template
    
    # Parse template and get all Lambda configurations
    lambda_configs = parse_sam_template()
    
    # Extract handler info from handler string
    handler_file, handler_func = extract_handler_info("app.lambda_handler")
    
    # Find Lambda name from directory
    lambda_name = get_lambda_name_from_dir("user_login", lambda_configs)
"""

import os
import logging
from typing import Dict, Optional, Tuple
import yaml

from debug_tools.utils import get_template_path
from debug_tools.models import LambdaConfig

logger = logging.getLogger(__name__)


def parse_sam_template(template_path: Optional[str] = None) -> Dict[str, LambdaConfig]:
    """
    Parse SAM template and extract Lambda function configurations.
    
    Args:
        template_path: Path to template.yaml (default: auto-detect)
        
    Returns:
        Dictionary mapping Lambda function names to configurations:
        {
            "UserLoginFunction": LambdaConfig(...),
            ...
        }
        
    Raises:
        FileNotFoundError: If template file not found
        yaml.YAMLError: If template is invalid YAML
        ValueError: If template structure is invalid
    """
    if template_path is None:
        template_path = get_template_path()
    
    logger.debug(f"Parsing SAM template: {template_path}")
    
    # Add CloudFormation intrinsic function constructors
    def cf_constructor(loader, tag_suffix, node):
        """Generic constructor for CloudFormation intrinsic functions."""
        if isinstance(node, yaml.ScalarNode):
            return loader.construct_scalar(node)
        elif isinstance(node, yaml.SequenceNode):
            return loader.construct_sequence(node)
        elif isinstance(node, yaml.MappingNode):
            return loader.construct_mapping(node)
        return None
    
    # Register constructors for common CloudFormation intrinsic functions
    yaml.SafeLoader.add_multi_constructor('!', cf_constructor)
    
    try:
        with open(template_path, 'r') as f:
            template = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Failed to parse template.yaml: {e}")
    except FileNotFoundError:
        raise FileNotFoundError(f"Template file not found: {template_path}")
    
    if not isinstance(template, dict):
        raise ValueError("Template must be a dictionary")
    
    resources = template.get('Resources', {})
    if not resources:
        raise ValueError("No Resources section found in template")
    
    lambda_configs = {}
    
    for resource_name, resource_config in resources.items():
        if not isinstance(resource_config, dict):
            continue
        
        resource_type = resource_config.get('Type', '')
        if resource_type != 'AWS::Serverless::Function':
            continue
        
        properties = resource_config.get('Properties', {})
        if not properties:
            logger.warning(f"Lambda function {resource_name} has no Properties")
            continue
        
        code_uri = properties.get('CodeUri', '')
        handler = properties.get('Handler', '')
        
        if not code_uri or not handler:
            logger.warning(f"Lambda function {resource_name} missing CodeUri or Handler")
            continue
        
        # Extract handler file and function
        handler_file, handler_function = extract_handler_info(handler)
        
        lambda_config = LambdaConfig(
            name=resource_name,
            code_uri=code_uri,
            handler=handler,
            handler_file=handler_file,
            handler_function=handler_function
        )
        
        lambda_configs[resource_name] = lambda_config
        logger.debug(f"Found Lambda function: {resource_name} -> {code_uri}")
    
    if not lambda_configs:
        raise ValueError("No Lambda functions found in template")
    
    return lambda_configs


def extract_handler_info(handler_string: str) -> Tuple[str, str]:
    """
    Extract handler file and function from handler string.
    
    Args:
        handler_string: Handler in format "module.function" (e.g., "app.lambda_handler")
        
    Returns:
        Tuple of (handler_file, handler_function):
        - handler_file: "app.py"
        - handler_function: "lambda_handler"
        
    Examples:
        "app.lambda_handler" -> ("app.py", "lambda_handler")
        "handler.main" -> ("handler.py", "main")
        "forgot_password_handler.lambda_handler" -> ("forgot_password_handler.py", "lambda_handler")
    
    Raises:
        ValueError: If handler string format is invalid
    """
    if not handler_string or '.' not in handler_string:
        raise ValueError(f"Invalid handler format: {handler_string}. Expected 'module.function'")
    
    parts = handler_string.split('.')
    if len(parts) < 2:
        raise ValueError(f"Invalid handler format: {handler_string}. Expected 'module.function'")
    
    # Handler module is everything except the last part (function name)
    module_name = '.'.join(parts[:-1])
    function_name = parts[-1]
    
    # Convert module name to filename
    handler_file = f"{module_name}.py"
    
    return handler_file, function_name


def get_lambda_name_from_dir(lambda_dir: str, template_config: Dict[str, LambdaConfig]) -> Optional[str]:
    """
    Find Lambda function name from directory path.
    
    Args:
        lambda_dir: Directory path (e.g., "user_login" or "/path/to/user_login")
        template_config: Parsed template configuration
        
    Returns:
        Lambda function name (e.g., "UserLoginFunction") or None if not found
    """
    # Normalize directory path to just the directory name
    dir_name = os.path.basename(lambda_dir.rstrip('/'))
    
    logger.debug(f"Looking for Lambda function with directory: {dir_name}")
    
    # Search for matching CodeUri in template
    for lambda_name, config in template_config.items():
        # Normalize CodeUri (remove trailing slash)
        code_uri = config.code_uri.rstrip('/')
        
        # Check if CodeUri matches directory name
        if code_uri == dir_name or code_uri.endswith(f"/{dir_name}"):
            logger.debug(f"Found match: {lambda_name} -> {code_uri}")
            return lambda_name
    
    logger.warning(f"No Lambda function found for directory: {dir_name}")
    return None
