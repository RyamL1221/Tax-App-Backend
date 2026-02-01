"""
Property-based tests for incorrect password handling.

**Validates: Requirements 4.2**

Property 7: Incorrect password returns 401
For any user with a known password hash, providing an incorrect password
should return a 401 status code with a generic authentication error message.
"""

import bcrypt
import pytest
from hypothesis import given, settings, strategies as st, assume
from user_login.password_verifier import verify_password, InvalidCredentialsError


@settings(max_examples=100)
@given(
    correct_password=st.text(min_size=1, max_size=100),
    incorrect_password=st.text(min_size=1, max_size=100)
)
def test_incorrect_password_raises_invalid_credentials_error(correct_password, incorrect_password):
    """
    Property 7: Incorrect password returns 401
    
    For any password and a different incorrect password, verifying the incorrect
    password against the hash of the correct password should raise InvalidCredentialsError.
    
    This error should then be caught by the Lambda handler and converted to a 401
    response with a generic authentication error message.
    
    **Validates: Requirements 4.2**
    """
    # Bcrypt has a 72-byte limit, so truncate if necessary
    correct_password_bytes = correct_password.encode('utf-8')
    if len(correct_password_bytes) > 72:
        correct_password_bytes = correct_password_bytes[:72]
        correct_password = correct_password_bytes.decode('utf-8', errors='ignore')
    
    incorrect_password_bytes = incorrect_password.encode('utf-8')
    if len(incorrect_password_bytes) > 72:
        incorrect_password_bytes = incorrect_password_bytes[:72]
        incorrect_password = incorrect_password_bytes.decode('utf-8', errors='ignore')
    
    # Skip if passwords are the same after truncation
    assume(correct_password != incorrect_password)
    
    # Generate a bcrypt hash for the correct password
    # Use rounds=4 for faster testing (production uses 12)
    password_hash = bcrypt.hashpw(correct_password_bytes, bcrypt.gensalt(rounds=4)).decode('utf-8')
    
    # Verify with incorrect password should raise InvalidCredentialsError
    with pytest.raises(InvalidCredentialsError) as exc_info:
        verify_password(incorrect_password, password_hash)
    
    # Verify the error message is present
    assert str(exc_info.value), "InvalidCredentialsError should have an error message"


@settings(max_examples=100)
@given(password=st.text(alphabet=st.characters(min_codepoint=1, max_codepoint=127), min_size=1, max_size=72))
def test_correct_password_does_not_raise_error(password):
    """
    Property 7 (inverse): Correct password does not raise error
    
    For any password, verifying it against its own hash should succeed
    and not raise InvalidCredentialsError.
    
    **Validates: Requirements 4.2**
    """
    # Generate a bcrypt hash for the password (ASCII only, no truncation needed)
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=4)).decode('utf-8')
    
    # Verify with correct password should not raise an error
    result = verify_password(password, password_hash)
    
    # Should return True
    assert result is True, "Correct password should verify successfully"
