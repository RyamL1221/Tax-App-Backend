#!/usr/bin/env python3
"""
Batch migrate all test files using git mv.
This preserves git history and is faster than individual moves.
"""

import subprocess
import sys
from pathlib import Path


def git_mv(source: str, dest: str) -> bool:
    """Execute git mv, creating parent directory if needed."""
    dest_path = Path(dest)
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    
    result = subprocess.run(['git', 'mv', source, dest], capture_output=True, text=True)
    if result.returncode == 0:
        return True
    else:
        # File might already be moved or not exist
        if not Path(source).exists():
            return True  # Already moved
        print(f"Error moving {source}: {result.stderr.strip()}")
        return False


def main():
    """Execute all migrations."""
    
    # Check if source files still exist (some already moved)
    source_check = Path("user_login/tests/test_response_structure_compatibility_property.py")
    if not source_check.exists():
        print("Some files already moved. Continuing with remaining files...")
    
    migrations = []
    
    # user_login remaining property tests
    for test in [
        'test_response_structure_compatibility_property',
        'test_password_presence_property',
        'test_validation_error_response_property',
        'test_password_verification_property',
        'test_failed_login_logging_property',
        'test_secret_key_length_validation_property',
        'test_jwt_token_format_property',
        'test_incorrect_password_property',
        'test_user_lookup_property',
        'test_jwt_payload_security_property',
        'test_authentication_error_response_property',
        'test_jwt_algorithm_consistency_property',
        'test_non_existent_user_property',
        'test_jwt_signature_verification_property',
        'test_error_logging_property',
        'test_jwt_payload_completeness_property',
        'test_email_validation_property',
    ]:
        migrations.append((f'user_login/tests/{test}.py', f'user_login/tests/property/{test}.py'))
    
    # user_login unit tests
    for test in [
        'test_token_generator_unit',
        'test_validator_unit',
        'test_password_verifier_unit',
        'test_response_formatter_unit',
    ]:
        migrations.append((f'user_login/tests/{test}.py', f'user_login/tests/unit/{test}.py'))
    
    # user_registration
    migrations.extend([
        ('user_registration/tests/test_user_repository_unit.py', 'user_registration/tests/unit/test_user_repository_unit.py'),
        ('user_registration/tests/test_response_formatter_properties.py', 'user_registration/tests/property/test_response_formatter_properties.py'),
        ('user_registration/tests/test_validator_properties.py', 'user_registration/tests/property/test_validator_properties.py'),
        ('user_registration/tests/test_password_hasher_properties.py', 'user_registration/tests/property/test_password_hasher_properties.py'),
        ('user_registration/tests/test_lambda_handler_integration.py', 'user_registration/tests/integration/test_lambda_handler_integration.py'),
        ('user_registration/tests/test_duplicate_email_detection_property.py', 'user_registration/tests/property/test_duplicate_email_detection_property.py'),
        ('user_registration/tests/test_user_data_persistence_property.py', 'user_registration/tests/property/test_user_data_persistence_property.py'),
        ('user_registration/tests/test_validator.py', 'user_registration/tests/integration/test_validator.py'),
        ('user_registration/tests/test_response_formatter_unit.py', 'user_registration/tests/unit/test_response_formatter_unit.py'),
        ('user_registration/tests/test_password_hasher_unit.py', 'user_registration/tests/unit/test_password_hasher_unit.py'),
        ('user_registration/tests/test_plaintext_never_stored_property.py', 'user_registration/tests/property/test_plaintext_never_stored_property.py'),
    ])
    
    print(f"Migrating {len(migrations)} files...")
    success = 0
    skipped = 0
    failed = 0
    
    for source, dest in migrations:
        if not Path(source).exists():
            skipped += 1
            continue
            
        if git_mv(source, dest):
            success += 1
            print(f"✓ {Path(source).name}")
        else:
            failed += 1
    
    print(f"\nResults: {success} moved, {skipped} skipped, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
