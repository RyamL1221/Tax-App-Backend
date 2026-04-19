"""
Property-based test for bug condition exploration: FROM_EMAIL silent failure.

Feature: fix-forgot-password-email
Property 1: Bug Condition - Unverified FROM_EMAIL Causes Silent Email Failure

**Validates: Requirements 1.1, 1.3, 1.4, 2.3, 2.4**

This test encodes the EXPECTED behavior after the fix:
- _send_with_retry returns a 3-tuple (success, message_id, error_code)
- send_reset_email propagates the 3-tuple
- template.yaml has FROM_EMAIL parameterized via !Ref FromEmail

On UNFIXED code, these assertions FAIL because:
- _send_with_retry returns only a 2-tuple (False, None) with no error code
- template.yaml has FROM_EMAIL hardcoded to "noreply@example.com"

The failure confirms the bug exists.
"""

import os
import re
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch
from hypothesis import given, strategies as st, settings
from botocore.exceptions import ClientError
from password_recovery.email_service import EmailService


# Strategy: SES error codes that occur when FROM_EMAIL is unverified
ses_from_email_error_codes = st.sampled_from([
    'MailFromDomainNotVerified',
    'MessageRejected',
])


# Strategy: generate valid recipient emails
@st.composite
def valid_recipient_emails(draw):
    """Generate valid recipient email addresses."""
    local_chars = 'abcdefghijklmnopqrstuvwxyz0123456789'
    local = draw(st.text(alphabet=local_chars, min_size=3, max_size=15))
    domain = draw(st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=3, max_size=10))
    tld = draw(st.sampled_from(['com', 'org', 'net', 'io']))
    return f"{local}@{domain}.{tld}"


# Strategy: generate reset tokens
@st.composite
def reset_tokens(draw):
    """Generate reset tokens (base64-like strings)."""
    chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+/='
    return draw(st.text(alphabet=chars, min_size=32, max_size=64))


class TestFromEmailBugConditionProperty:
    """
    Bug condition exploration tests.

    These tests encode the EXPECTED behavior (3-tuple return with error code).
    On unfixed code, they MUST FAIL — confirming the bug exists.
    """

    @given(
        recipient_email=valid_recipient_emails(),
        token=reset_tokens(),
        error_code=ses_from_email_error_codes,
    )
    @settings(max_examples=10, deadline=None)
    def test_send_with_retry_returns_error_code_on_ses_rejection(
        self, recipient_email, token, error_code
    ):
        """
        Property: _send_with_retry returns 3-tuple (False, None, error_code)
        when SES rejects with MailFromDomainNotVerified or MessageRejected.

        On UNFIXED code, _send_with_retry returns only (False, None) — a 2-tuple.
        Asserting a 3-tuple will FAIL, confirming the bug: no error code is
        propagated for handler-level logging.

        **Validates: Requirements 1.4, 2.4**
        """
        mock_ses = Mock()
        mock_ses.send_email.side_effect = ClientError(
            {'Error': {'Code': error_code, 'Message': f'SES error: {error_code}'}},
            'SendEmail'
        )

        service = EmailService(
            ses_client=mock_ses,
            from_email='noreply@example.com',
            base_url='https://example.com',
            ses_region='us-east-1',
        )

        result = service._send_with_retry(
            recipient_email=recipient_email,
            subject='Password Reset Request',
            body_text='Reset your password',
            body_html='<p>Reset your password</p>',
            max_retries=0,  # No retries for permanent errors
        )

        # EXPECTED behavior (after fix): 3-tuple with error code
        assert isinstance(result, tuple), f"Expected tuple, got {type(result)}"
        assert len(result) == 3, (
            f"Expected 3-tuple (success, message_id, error_code), "
            f"got {len(result)}-tuple: {result}"
        )
        success, message_id, returned_error_code = result
        assert success is False
        assert message_id is None
        assert returned_error_code == error_code, (
            f"Expected error_code '{error_code}', got '{returned_error_code}'"
        )

    @given(
        recipient_email=valid_recipient_emails(),
        token=reset_tokens(),
        error_code=ses_from_email_error_codes,
    )
    @settings(max_examples=10, deadline=None)
    def test_send_reset_email_propagates_error_code(
        self, recipient_email, token, error_code
    ):
        """
        Property: send_reset_email returns 3-tuple propagating error code
        from _send_with_retry when SES rejects the email.

        On UNFIXED code, send_reset_email returns (False, None) — a 2-tuple.
        Asserting a 3-tuple will FAIL, confirming the bug.

        **Validates: Requirements 1.1, 1.4, 2.4**
        """
        mock_ses = Mock()
        mock_ses.send_email.side_effect = ClientError(
            {'Error': {'Code': error_code, 'Message': f'SES error: {error_code}'}},
            'SendEmail'
        )

        service = EmailService(
            ses_client=mock_ses,
            from_email='noreply@example.com',
            base_url='https://example.com',
            ses_region='us-east-1',
        )
        expiration = datetime.now(timezone.utc) + timedelta(hours=1)

        result = service.send_reset_email(recipient_email, token, expiration)

        # EXPECTED behavior (after fix): 3-tuple with error code
        assert isinstance(result, tuple), f"Expected tuple, got {type(result)}"
        assert len(result) == 3, (
            f"Expected 3-tuple (success, message_id, error_code), "
            f"got {len(result)}-tuple: {result}"
        )
        success, message_id, returned_error_code = result
        assert success is False
        assert message_id is None
        assert returned_error_code == error_code

    def test_template_yaml_from_email_is_parameterized(self):
        """
        Verify template.yaml has FROM_EMAIL parameterized via !Ref FromEmail,
        not hardcoded to noreply@example.com.

        On UNFIXED code, FROM_EMAIL is hardcoded: FROM_EMAIL: "noreply@example.com"
        This test asserts it should be parameterized: FROM_EMAIL: !Ref FromEmail
        The assertion FAILS on unfixed code, confirming the root cause.

        **Validates: Requirements 1.3, 2.3**
        """
        template_path = os.path.join(
            os.path.dirname(__file__), '..', '..', '..', 'template.yaml'
        )
        template_path = os.path.normpath(template_path)

        with open(template_path, 'r') as f:
            content = f.read()

        # Check that a FromEmail parameter exists in the Parameters section
        assert 'FromEmail' in content, (
            "template.yaml is missing a 'FromEmail' CloudFormation parameter. "
            "FROM_EMAIL should be configurable via !Ref FromEmail, not hardcoded."
        )

        # Check that FROM_EMAIL references the parameter, not a hardcoded value
        # Look for the pattern: FROM_EMAIL: !Ref FromEmail
        has_ref_pattern = bool(re.search(r'FROM_EMAIL:\s*!Ref\s+FromEmail', content))
        assert has_ref_pattern, (
            "FROM_EMAIL in template.yaml is not parameterized via '!Ref FromEmail'. "
            "It appears to be hardcoded. Expected: FROM_EMAIL: !Ref FromEmail"
        )

        # Verify the hardcoded value is NOT present
        has_hardcoded = bool(
            re.search(r'FROM_EMAIL:\s*["\']noreply@example\.com["\']', content)
        )
        assert not has_hardcoded, (
            "FROM_EMAIL is still hardcoded to 'noreply@example.com' in template.yaml. "
            "This placeholder domain cannot be verified in SES."
        )
