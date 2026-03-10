#!/usr/bin/env python3
"""
Execute Test Folder Migration

This script performs the actual file moves using git mv to preserve history.
It processes files in batches by Lambda function.
"""

import subprocess
import sys
from pathlib import Path
from typing import List, Tuple


def get_migrations() -> List[Tuple[str, str]]:
    """Return list of (source, destination) tuples for all migrations."""
    return [
        # user_login - property tests
        ('user_login/tests/test_request_processing_logging_property.py', 'user_login/tests/property/test_request_processing_logging_property.py'),
        ('user_login/tests/test_success_response_property.py', 'user_login/tests/property/test_success_response_property.py'),
        ('user_login/tests/test_logging_without_sensitive_data_property.py', 'user_login/tests/property/test_logging_without_sensitive_data_property.py'),
        ('user_login/tests/test_missing_fields_property.py', 'user_login/tests/property/test_missing_fields_property.py'),
        ('user_login/tests/test_cors_headers_property.py', 'user_login/tests/property/test_cors_headers_property.py'),
        ('user_login/tests/test_response_structure_compatibility_property.py', 'user_login/tests/property/test_response_structure_compatibility_property.py'),
        ('user_login/tests/test_password_presence_property.py', 'user_login/tests/property/test_password_presence_property.py'),
        ('user_login/tests/test_validation_error_response_property.py', 'user_login/tests/property/test_validation_error_response_property.py'),
        ('user_login/tests/test_password_verification_property.py', 'user_login/tests/property/test_password_verification_property.py'),
        ('user_login/tests/test_failed_login_logging_property.py', 'user_login/tests/property/test_failed_login_logging_property.py'),
        ('user_login/tests/test_secret_key_length_validation_property.py', 'user_login/tests/property/test_secret_key_length_validation_property.py'),
        ('user_login/tests/test_jwt_token_format_property.py', 'user_login/tests/property/test_jwt_token_format_property.py'),
        ('user_login/tests/test_incorrect_password_property.py', 'user_login/tests/property/test_incorrect_password_property.py'),
        ('user_login/tests/test_user_lookup_property.py', 'user_login/tests/property/test_user_lookup_property.py'),
        ('user_login/tests/test_jwt_payload_security_property.py', 'user_login/tests/property/test_jwt_payload_security_property.py'),
        ('user_login/tests/test_authentication_error_response_property.py', 'user_login/tests/property/test_authentication_error_response_property.py'),
        ('user_login/tests/test_jwt_algorithm_consistency_property.py', 'user_login/tests/property/test_jwt_algorithm_consistency_property.py'),
        ('user_login/tests/test_non_existent_user_property.py', 'user_login/tests/property/test_non_existent_user_property.py'),
        ('user_login/tests/test_jwt_signature_verification_property.py', 'user_login/tests/property/test_jwt_signature_verification_property.py'),
        ('user_login/tests/test_error_logging_property.py', 'user_login/tests/property/test_error_logging_property.py'),
        ('user_login/tests/test_jwt_payload_completeness_property.py', 'user_login/tests/property/test_jwt_payload_completeness_property.py'),
        ('user_login/tests/test_email_validation_property.py', 'user_login/tests/property/test_email_validation_property.py'),
        # user_login - unit tests
        ('user_login/tests/test_token_generator_unit.py', 'user_login/tests/unit/test_token_generator_unit.py'),
        ('user_login/tests/test_validator_unit.py', 'user_login/tests/unit/test_validator_unit.py'),
        ('user_login/tests/test_password_verifier_unit.py', 'user_login/tests/unit/test_password_verifier_unit.py'),
        ('user_login/tests/test_response_formatter_unit.py', 'user_login/tests/unit/test_response_formatter_unit.py'),
    ]


def execute_git_mv(source: str, dest: str) -> bool:
    """Execute git mv command."""
    try:
        # Ensure parent directory exists
        dest_path = Path(dest)
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Execute git mv
        result = subprocess.run(
            ['git', 'mv', source, dest],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            print(f"✓ {source} -> {dest}")
            return True
        else:
            print(f"✗ {source} -> {dest}")
            print(f"  Error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"✗ {source} -> {dest}")
        print(f"  Exception: {e}")
        return False


def main():
    """Execute migration."""
    migrations = get_migrations()
    
    print(f"Executing {len(migrations)} file moves...")
    print("="*80)
    
    success_count = 0
    fail_count = 0
    
    for source, dest in migrations:
        if execute_git_mv(source, dest):
            success_count += 1
        else:
            fail_count += 1
    
    print("="*80)
    print(f"\nResults:")
    print(f"  Success: {success_count}")
    print(f"  Failed: {fail_count}")
    print(f"  Total: {len(migrations)}")
    
    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
