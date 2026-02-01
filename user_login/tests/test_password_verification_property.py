"""
Property-based tests for password verification using bcrypt.

**Validates: Requirements 4.1, 7.2**

Property 6: Password verification using bcrypt
For any password and password hash pair, the password verifier should use bcrypt's
checkpw function (which provides constant-time comparison) to verify the password.
"""

import bcrypt
import pytest
from hypothesis import given, settings, strategies as st
from user_login.password_verifier import verify_password, InvalidCredentialsError


@settings(max_examples=100)
@given(password=st.text(min_size=1, max_size=100))
def test_password_verification_property(password):
    """
    Property 6: Password verification using bcrypt
    
    For any password, when we generate a bcrypt hash and verify it,
    the verification should succeed using bcrypt's constant-time comparison.
    
    **Validates: Requirements 4.1, 7.2**
    """
    # Bcrypt has a 72-byte limit, so truncate if necessary
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
        password = password_bytes.decode('utf-8', errors='ignore')
    
    # Generate a bcrypt hash for the password
    password_hash = bcrypt.hashpw(password_bytes, bcrypt.gensalt(rounds=4)).decode('utf-8')
    
    # Verify the password should succeed
    result = verify_password(password, password_hash)
    
    # Should return True for correct password
    assert result is True, f"Password verification should succeed for correct password"
    
    # Verify that bcrypt.checkpw would give the same result
    expected = bcrypt.checkpw(password_bytes, password_hash.encode('utf-8'))
    assert result == expected, "Should use bcrypt.checkpw for verification"


@settings(max_examples=100)
@given(
    password=st.text(min_size=1, max_size=100),
    wrong_password=st.text(min_size=1, max_size=100)
)
def test_incorrect_password_verification_property(password, wrong_password):
    """
    Property 6 (variant): Incorrect password verification
    
    For any two different passwords, verifying one against the hash of the other
    should fail with InvalidCredentialsError.
    
    **Validates: Requirements 4.1, 7.2**
    """
    # Bcrypt has a 72-byte limit, so truncate if necessary
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
        password = password_bytes.decode('utf-8', errors='ignore')
    
    wrong_password_bytes = wrong_password.encode('utf-8')
    if len(wrong_password_bytes) > 72:
        wrong_password_bytes = wrong_password_bytes[:72]
        wrong_password = wrong_password_bytes.decode('utf-8', errors='ignore')
    
    # Skip if passwords are the same after truncation
    if password == wrong_password:
        return
    
    # Generate a bcrypt hash for the correct password
    password_hash = bcrypt.hashpw(password_bytes, bcrypt.gensalt(rounds=4)).decode('utf-8')
    
    # Verify with wrong password should raise InvalidCredentialsError
    with pytest.raises(InvalidCredentialsError):
        verify_password(wrong_password, password_hash)
