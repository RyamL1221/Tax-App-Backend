"""
Integration tests for EmailService with real AWS SES.

These tests use real AWS SES (not mocked) to verify email sending functionality
with actual AWS resources. Tests are skipped by default and must be explicitly
run with: pytest -m integration

Requirements:
1. AWS credentials configured (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
2. Sender email verified in SES (FROM_EMAIL environment variable)
3. SES_REGION environment variable set (e.g., 'us-east-1')
4. BASE_URL environment variable set

To run these tests:
    pytest password_recovery/tests/test_email_service_aws_integration.py -m integration -v

Note: These tests will send actual emails via AWS SES and may incur AWS charges.
"""

import os
import pytest
import boto3
from datetime import datetime, timedelta
from botocore.exceptions import ClientError, NoCredentialsError

from password_recovery.email_service import EmailService


# Skip all tests in this module unless explicitly run with -m integration
pytestmark = pytest.mark.integration


@pytest.fixture
def aws_credentials_available():
    """
    Check if AWS credentials are available.
    
    Returns True if credentials are configured, False otherwise.
    """
    try:
        # Try to create a boto3 session to check for credentials
        session = boto3.Session()
        credentials = session.get_credentials()
        return credentials is not None
    except (NoCredentialsError, Exception):
        return False


@pytest.fixture
def ses_configuration():
    """
    Get SES configuration from environment variables.
    
    Returns dict with SES configuration or None if not configured.
    """
    from_email = os.environ.get('FROM_EMAIL')
    ses_region = os.environ.get('SES_REGION')
    base_url = os.environ.get('BASE_URL')
    
    if not all([from_email, ses_region, base_url]):
        return None
    
    return {
        'from_email': from_email,
        'ses_region': ses_region,
        'base_url': base_url
    }


@pytest.fixture
def real_ses_client(ses_configuration):
    """
    Create a real SES client (not mocked) for integration testing.
    
    Skips test if SES configuration is not available.
    """
    if ses_configuration is None:
        pytest.skip("SES configuration not available (FROM_EMAIL, SES_REGION, BASE_URL required)")
    
    return boto3.client('ses', region_name=ses_configuration['ses_region'])


@pytest.fixture
def sender_email_verified(real_ses_client, ses_configuration):
    """
    Verify that the sender email is verified in SES.
    
    Skips test if sender email is not verified.
    """
    try:
        # Get list of verified email addresses
        response = real_ses_client.list_verified_email_addresses()
        verified_emails = response.get('VerifiedEmailAddresses', [])
        
        sender_email = ses_configuration['from_email']
        
        if sender_email not in verified_emails:
            pytest.skip(
                f"Sender email {sender_email} is not verified in SES. "
                f"Please verify the email address in AWS SES console before running this test."
            )
        
        return True
        
    except ClientError as e:
        pytest.skip(f"Unable to check SES email verification: {e}")


class TestEmailServiceAWSIntegration:
    """
    Integration tests for EmailService with real AWS SES.
    
    These tests verify that the EmailService can successfully send emails
    using real AWS SES infrastructure. They are marked with @pytest.mark.integration
    and are skipped by default.
    
    **Validates: Requirements 7.3, 7.7**
    """
    
    def test_send_reset_email_with_real_ses(
        self,
        aws_credentials_available,
        ses_configuration,
        sender_email_verified
    ):
        """
        Test sending password reset email with real AWS SES.
        
        This test:
        1. Creates EmailService with real SES client (not mocked)
        2. Sends a password reset email to the verified sender address
        3. Verifies that a MessageId is returned
        4. Verifies that the operation succeeds
        
        Note: This test sends an actual email via AWS SES and may incur charges.
        The email is sent to the same address as the sender (FROM_EMAIL) to avoid
        sending test emails to external addresses.
        
        **Validates: Requirements 7.3, 7.7**
        """
        # Skip if AWS credentials not available
        if not aws_credentials_available:
            pytest.skip("AWS credentials not configured")
        
        # Create EmailService with real SES client (no mocking)
        service = EmailService(
            from_email=ses_configuration['from_email'],
            base_url=ses_configuration['base_url'],
            ses_region=ses_configuration['ses_region']
        )
        
        # Prepare test data
        recipient_email = ses_configuration['from_email']  # Send to self to avoid external emails
        reset_token = 'test-token-integration-12345'
        expiration = datetime.utcnow() + timedelta(hours=1)
        
        # Send email via real AWS SES
        success, message_id = service.send_reset_email(
            recipient_email=recipient_email,
            reset_token=reset_token,
            expiration=expiration
        )
        
        # Verify success
        assert success is True, "Email send should succeed with real AWS SES"
        
        # Verify MessageId is returned
        assert message_id is not None, "MessageId should be returned on successful send"
        assert isinstance(message_id, str), "MessageId should be a string"
        assert len(message_id) > 0, "MessageId should not be empty"
        
        print(f"\n✅ Email sent successfully via AWS SES")
        print(f"   MessageId: {message_id}")
        print(f"   Recipient: {recipient_email}")
        print(f"   Check your inbox for the password reset email")
    
    def test_send_email_with_unverified_sender_fails(
        self,
        aws_credentials_available,
        ses_configuration
    ):
        """
        Test that sending email with unverified sender email fails gracefully.
        
        This test verifies that the EmailService handles the case where the
        sender email is not verified in SES. This is a common error in development
        and should be handled gracefully with appropriate error logging.
        
        Note: This test uses a fake unverified email address and expects failure.
        
        **Validates: Requirements 7.7**
        """
        # Skip if AWS credentials not available
        if not aws_credentials_available:
            pytest.skip("AWS credentials not configured")
        
        # Create EmailService with unverified sender email
        unverified_email = 'unverified-sender@example-fake-domain-12345.com'
        service = EmailService(
            ses_client=boto3.client('ses', region_name=ses_configuration['ses_region']),
            from_email=unverified_email,
            base_url=ses_configuration['base_url'],
            ses_region=ses_configuration['ses_region']
        )
        
        # Prepare test data
        recipient_email = ses_configuration['from_email']
        reset_token = 'test-token-unverified-sender'
        expiration = datetime.utcnow() + timedelta(hours=1)
        
        # Attempt to send email (should fail)
        success, message_id = service.send_reset_email(
            recipient_email=recipient_email,
            reset_token=reset_token,
            expiration=expiration
        )
        
        # Verify failure
        assert success is False, "Email send should fail with unverified sender"
        assert message_id is None, "MessageId should be None on failure"
        
        print(f"\n✅ Unverified sender email correctly rejected by SES")
    
    def test_send_email_with_invalid_recipient_fails(
        self,
        aws_credentials_available,
        ses_configuration,
        sender_email_verified
    ):
        """
        Test that sending email to invalid recipient address fails gracefully.
        
        This test verifies that the EmailService validates email addresses
        before attempting to send, and handles invalid addresses appropriately.
        
        **Validates: Requirements 7.7**
        """
        # Skip if AWS credentials not available
        if not aws_credentials_available:
            pytest.skip("AWS credentials not configured")
        
        # Create EmailService with real SES client
        service = EmailService(
            from_email=ses_configuration['from_email'],
            base_url=ses_configuration['base_url'],
            ses_region=ses_configuration['ses_region']
        )
        
        # Prepare test data with invalid recipient email
        invalid_recipient = 'not-a-valid-email'
        reset_token = 'test-token-invalid-recipient'
        expiration = datetime.utcnow() + timedelta(hours=1)
        
        # Attempt to send email (should fail validation)
        success, message_id = service.send_reset_email(
            recipient_email=invalid_recipient,
            reset_token=reset_token,
            expiration=expiration
        )
        
        # Verify failure
        assert success is False, "Email send should fail with invalid recipient"
        assert message_id is None, "MessageId should be None on failure"
        
        print(f"\n✅ Invalid recipient email correctly rejected")
    
    def test_send_email_returns_valid_message_id_format(
        self,
        aws_credentials_available,
        ses_configuration,
        sender_email_verified
    ):
        """
        Test that successful email send returns a valid SES MessageId format.
        
        SES MessageIds have a specific format that can be validated. This test
        verifies that the returned MessageId matches the expected format.
        
        **Validates: Requirements 7.3, 7.7**
        """
        # Skip if AWS credentials not available
        if not aws_credentials_available:
            pytest.skip("AWS credentials not configured")
        
        # Create EmailService with real SES client
        service = EmailService(
            from_email=ses_configuration['from_email'],
            base_url=ses_configuration['base_url'],
            ses_region=ses_configuration['ses_region']
        )
        
        # Prepare test data
        recipient_email = ses_configuration['from_email']
        reset_token = 'test-token-message-id-format'
        expiration = datetime.utcnow() + timedelta(hours=1)
        
        # Send email via real AWS SES
        success, message_id = service.send_reset_email(
            recipient_email=recipient_email,
            reset_token=reset_token,
            expiration=expiration
        )
        
        # Verify success
        assert success is True, "Email send should succeed"
        assert message_id is not None, "MessageId should be returned"
        
        # Verify MessageId format (SES MessageIds are typically long alphanumeric strings)
        assert isinstance(message_id, str), "MessageId should be a string"
        assert len(message_id) > 10, "MessageId should be reasonably long"
        
        # SES MessageIds typically contain alphanumeric characters and hyphens
        import re
        assert re.match(r'^[a-zA-Z0-9\-]+$', message_id), \
            "MessageId should contain only alphanumeric characters and hyphens"
        
        print(f"\n✅ Valid MessageId format received: {message_id}")
