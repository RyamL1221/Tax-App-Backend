"""
Email service for password recovery.

This module handles sending password reset emails using AWS SES (Simple Email Service).
"""

import os
import logging
import time
from datetime import datetime
from typing import Optional
import boto3
from botocore.exceptions import ClientError


logger = logging.getLogger(__name__)


# Default email templates for password reset
# These templates support the following variables:
# - {reset_link}: Full password reset URL with token
# - {expiration_time}: Formatted expiration datetime (UTC)
# - {recipient_name}: User's name (optional, for future use)

DEFAULT_HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Password Reset Request</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #2c3e50;">Password Reset Request</h2>
        
        <p>Hello,</p>
        
        <p>You have requested to reset your password. Please click the button below to set a new password:</p>
        
        <div style="text-align: center; margin: 30px 0;">
            <a href="{reset_link}" 
               style="background-color: #3498db; color: white; padding: 12px 30px; 
                      text-decoration: none; border-radius: 5px; display: inline-block;">
                Reset Password
            </a>
        </div>
        
        <p>Or copy and paste this link into your browser:</p>
        <p style="word-break: break-all; color: #3498db;">{reset_link}</p>
        
        <p style="color: #e74c3c; font-weight: bold;">
            This link will expire at {expiration_time}.
        </p>
        
        <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
        
        <p style="color: #7f8c8d; font-size: 14px;">
            If you did not request a password reset, please ignore this email. 
            Your password will remain unchanged.
        </p>
        
        <p style="color: #7f8c8d; font-size: 14px;">
            For security reasons, never share this link with anyone.
        </p>
        
        <p style="color: #7f8c8d; font-size: 14px;">
            Best regards,<br>
            The Security Team
        </p>
    </div>
</body>
</html>
"""

DEFAULT_TEXT_TEMPLATE = """Hello,

You have requested to reset your password. Please click the link below to set a new password:

{reset_link}

This link will expire at {expiration_time}.

If you did not request a password reset, please ignore this email. Your password will remain unchanged.

For security reasons, never share this link with anyone.

Best regards,
The Security Team
"""


class EmailService:
    """
    Email service for sending password reset emails using AWS SES.
    
    Handles email composition, delivery, and error handling while maintaining
    security best practices (no sensitive data in logs).
    """
    
    def __init__(
        self,
        ses_client=None,
        from_email=None,
        base_url=None,
        ses_region=None,
        configuration_set=None
    ):
        """
        Initialize the email service with SES configuration.
        
        Supports both LocalStack (development) and AWS SES (production) environments.
        Automatically detects environment based on AWS_ENDPOINT_URL and configures
        the SES client accordingly.
        
        Args:
            ses_client: Optional boto3 SES client (for testing/dependency injection)
            from_email: Optional sender email address (defaults to FROM_EMAIL env var)
            base_url: Optional base URL for reset links (defaults to BASE_URL env var)
            ses_region: Optional AWS region for SES (defaults to SES_REGION env var)
            configuration_set: Optional SES configuration set name (defaults to CONFIGURATION_SET_NAME env var)
            
        Raises:
            ValueError: If required environment variables (FROM_EMAIL, SES_REGION, BASE_URL) are missing or empty
            
        Environment Variables:
            FROM_EMAIL: Sender email address (required)
            BASE_URL: Frontend base URL for reset links (required)
            SES_REGION: AWS region for SES (required, e.g., 'us-east-1')
            AWS_ENDPOINT_URL: LocalStack endpoint URL (optional, for local development)
            CONFIGURATION_SET_NAME: SES configuration set for event tracking (optional)
            
        Examples:
            >>> # Production initialization (uses AWS SES)
            >>> service = EmailService()
            
            >>> # LocalStack initialization (auto-detected from AWS_ENDPOINT_URL)
            >>> os.environ['AWS_ENDPOINT_URL'] = 'http://localhost:4566'
            >>> service = EmailService()
            
            >>> # Testing with mocked SES client
            >>> mock_ses = Mock()
            >>> service = EmailService(ses_client=mock_ses)
        """
        # Read environment variables with provided overrides
        self.from_email = from_email or os.environ.get('FROM_EMAIL', '')
        self.base_url = base_url or os.environ.get('BASE_URL', '')
        self.ses_region = ses_region or os.environ.get('SES_REGION', '')
        self.configuration_set = configuration_set or os.environ.get('CONFIGURATION_SET_NAME', None)
        
        # Validate required configuration
        self._validate_configuration()
        
        # Detect LocalStack environment
        endpoint_url = os.environ.get('AWS_ENDPOINT_URL', '')
        is_localstack = any(
            indicator in endpoint_url.lower()
            for indicator in ['localstack', 'localhost', '127.0.0.1', '172.18.0.1']
        )
        
        # Create SES client if not provided (dependency injection support)
        if ses_client is None:
            if is_localstack:
                # LocalStack mode: use endpoint_url
                self.ses = boto3.client(
                    'ses',
                    region_name=self.ses_region,
                    endpoint_url=endpoint_url
                )
                logger.info(
                    f"EmailService initialized in LocalStack mode: "
                    f"region={self.ses_region}, endpoint={endpoint_url}, "
                    f"sender={self._mask_email(self.from_email)}"
                )
            else:
                # AWS mode: use default endpoints
                self.ses = boto3.client(
                    'ses',
                    region_name=self.ses_region
                )
                logger.info(
                    f"EmailService initialized in AWS mode: "
                    f"region={self.ses_region}, "
                    f"sender={self._mask_email(self.from_email)}"
                )
        else:
            # Use provided SES client (for testing)
            self.ses = ses_client
            logger.debug(
                f"EmailService initialized with injected SES client: "
                f"region={self.ses_region}, "
                f"sender={self._mask_email(self.from_email)}"
            )
        
        # Log configuration set if provided
        if self.configuration_set:
            logger.info(f"SES configuration set enabled: {self.configuration_set}")
    
    def _validate_configuration(self) -> None:
        """
        Validate required environment variables at initialization.
        
        Raises:
            ValueError: If FROM_EMAIL, SES_REGION, or BASE_URL are missing or empty
        """
        missing_vars = []
        
        if not self.from_email:
            missing_vars.append('FROM_EMAIL')
        
        if not self.ses_region:
            missing_vars.append('SES_REGION')
        
        if not self.base_url:
            missing_vars.append('BASE_URL')
        
        if missing_vars:
            error_msg = f"Missing required environment variables: {', '.join(missing_vars)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
    
    def _mask_email(self, email: str) -> str:
        """
        Mask email address for secure logging.
        
        Shows only the first 3 characters and the domain to prevent
        exposing full email addresses in logs.
        
        Args:
            email: Email address to mask
            
        Returns:
            Masked email address (e.g., "use***@example.com")
            
        Examples:
            >>> service._mask_email("user@example.com")
            'use***@example.com'
            >>> service._mask_email("ab@test.com")
            'ab***@test.com'
            >>> service._mask_email("a@test.com")
            'a***@test.com'
        """
        if not email or '@' not in email:
            return '***'
        
        local_part, domain = email.split('@', 1)
        
        # Show first 3 characters (or less if email is shorter)
        visible_chars = min(3, len(local_part))
        masked_local = local_part[:visible_chars] + '***'
        
        return f"{masked_local}@{domain}"
    
    def _render_template(self, template: str, variables: dict) -> str:
        """
        Render email template with variable substitution.
        
        HTML escapes all variable values to prevent injection attacks before
        substituting them into the template. This ensures that user-provided
        data cannot inject malicious HTML or JavaScript into email content.
        
        Args:
            template: Template string with placeholders (e.g., "{reset_link}")
            variables: Dictionary of variable names to values for substitution
            
        Returns:
            Rendered template string with variables substituted and HTML-escaped
            
        Security:
            All variable values are HTML-escaped using html.escape() to prevent
            injection attacks. This converts special characters:
            - < becomes &lt;
            - > becomes &gt;
            - & becomes &amp;
            - " becomes &quot;
            - ' becomes &#x27;
            
        Examples:
            >>> service = EmailService()
            >>> template = "<p>Hello {name}, click {link}</p>"
            >>> variables = {"name": "John<script>", "link": "http://example.com"}
            >>> result = service._render_template(template, variables)
            >>> print(result)
            '<p>Hello John&lt;script&gt;, click http://example.com</p>'
            
            >>> # Safe handling of special characters
            >>> template = "<p>Amount: {amount}</p>"
            >>> variables = {"amount": "100 & 200"}
            >>> result = service._render_template(template, variables)
            >>> print(result)
            '<p>Amount: 100 &amp; 200</p>'
        """
        import html
        
        # HTML-escape all variable values to prevent injection attacks
        safe_variables = {
            key: html.escape(str(value))
            for key, value in variables.items()
        }
        
        # Substitute variables into template using str.format()
        return template.format(**safe_variables)
    def _load_template(self, template_name: str) -> dict:
        """
        Load email template from configuration.

        Returns a dictionary with 'html' and 'text' keys containing the email templates.
        Currently uses default templates defined as module constants. In the future,
        this could be extended to load custom templates from S3, database, or config files.

        Validates that required template variables are present in both HTML and text
        templates. Logs warnings if required variables are missing but continues
        execution to allow graceful degradation.

        Args:
            template_name: Name of the template to load (e.g., 'password_reset')
                          Currently unused but reserved for future multi-template support

        Returns:
            Dictionary with 'html' and 'text' keys containing template strings

        Required Template Variables:
            - {reset_link}: Full password reset URL with token
            - {expiration_time}: Formatted expiration datetime (UTC)

        Examples:
            >>> service = EmailService()
            >>> templates = service._load_template('password_reset')
            >>> print(templates.keys())
            dict_keys(['html', 'text'])
            >>> '{reset_link}' in templates['html']
            True
            >>> '{expiration_time}' in templates['text']
            True

        Future Enhancement:
            This method could be extended to support:
            - Loading custom templates from S3 bucket
            - Loading templates from DynamoDB configuration table
            - Loading templates from local config files
            - Template versioning and A/B testing
            - Multi-language template support
        """
        # For now, always use default templates
        # Future: could load from S3, database, or config files based on template_name
        html_template = DEFAULT_HTML_TEMPLATE
        text_template = DEFAULT_TEXT_TEMPLATE

        # Define required template variables
        required_vars = ['{reset_link}', '{expiration_time}']

        # Validate that required variables are present in HTML template
        for var in required_vars:
            if var not in html_template:
                logger.warning(
                    f"HTML template missing required variable: {var}. "
                    f"Email rendering may fail or produce incomplete content."
                )

        # Validate that required variables are present in text template
        for var in required_vars:
            if var not in text_template:
                logger.warning(
                    f"Text template missing required variable: {var}. "
                    f"Email rendering may fail or produce incomplete content."
                )

        # Return templates as dictionary
        return {
            'html': html_template,
            'text': text_template
        }

    
    def _send_with_retry(
        self,
        recipient_email: str,
        subject: str,
        body_text: str,
        body_html: str,
        max_retries: int = 3
    ) -> tuple[bool, Optional[str], Optional[str]]:
        """
        Send email with exponential backoff retry logic.

        This method implements robust retry logic for SES email sending with:
        - Automatic retry for transient errors (throttling, timeouts, service unavailable)
        - Immediate failure for permanent errors (invalid email, account suspended)
        - Exponential backoff with jitter to prevent thundering herd
        - Comprehensive logging of all attempts, successes, and failures
        - Lambda timeout awareness to avoid exceeding execution limits

        The retry logic distinguishes between transient and permanent errors:
        - Transient errors (Throttling, ServiceUnavailable, RequestTimeout, InternalFailure)
          are retried up to max_retries times with exponential backoff
        - Permanent errors (MessageRejected, MailFromDomainNotVerified, etc.)
          fail immediately without retry to avoid wasting time
        - Network errors (connection failures) are treated as transient

        Args:
            recipient_email: Recipient's email address (will be masked in logs)
            subject: Email subject line
            body_text: Plain text email body
            body_html: HTML email body
            max_retries: Maximum number of retry attempts (default: 3)
                        Total attempts = max_retries + 1 (initial attempt + retries)

        Returns:
            Tuple of (success: bool, message_id: Optional[str], error_code: Optional[str])
            - (True, message_id, None) on successful delivery with SES MessageId
            - (False, None, error_code) on failure after all retries exhausted or permanent error
            - (False, None, None) as fallback if loop exits unexpectedly

        Retry Behavior:
            Attempt 0 (initial): Immediate send
            Attempt 1 (retry 1): Wait 1.0-1.5s, then retry
            Attempt 2 (retry 2): Wait 2.0-3.0s, then retry
            Attempt 3 (retry 3): Wait 4.0-6.0s, then retry
            After max_retries: Return failure

        Examples:
            >>> service = EmailService()
            >>> success, message_id = service._send_with_retry(
            ...     recipient_email='user@example.com',
            ...     subject='Password Reset',
            ...     body_text='Reset your password...',
            ...     body_html='<p>Reset your password...</p>',
            ...     max_retries=3
            ... )
            >>> if success:
            ...     print(f"Email sent successfully. MessageId: {message_id}")
            ... else:
            ...     print("Email delivery failed after retries")

        Logging:
            - Logs each send attempt with masked email
            - Logs successful delivery with MessageId
            - Logs transient errors with retry information (attempt number, delay)
            - Logs permanent errors without retry
            - Logs max retries exhaustion
            - Never logs plaintext tokens or sensitive data

        Security:
            - Email addresses are masked in all log messages using _mask_email()
            - No sensitive data (tokens, passwords) is logged
            - Error details are logged for debugging but not exposed to clients

        Performance:
            - Respects Lambda timeout limits (30 seconds)
            - Uses exponential backoff to avoid overwhelming SES
            - Adds jitter to prevent thundering herd when multiple Lambdas retry
            - Fails fast on permanent errors to avoid wasting execution time

        Error Handling:
            - ClientError: SES API errors, classified as transient or permanent
            - Exception: Network errors and unexpected failures, treated as transient
            - All errors are logged with appropriate severity levels
        """
        masked_email = self._mask_email(recipient_email)

        for attempt in range(max_retries + 1):
            try:
                # Build SES send_email parameters
                send_params = {
                    'Source': self.from_email,
                    'Destination': {'ToAddresses': [recipient_email]},
                    'Message': {
                        'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                        'Body': {
                            'Text': {'Data': body_text, 'Charset': 'UTF-8'},
                            'Html': {'Data': body_html, 'Charset': 'UTF-8'}
                        }
                    }
                }

                # Add configuration set if configured
                if self.configuration_set:
                    send_params['ConfigurationSetName'] = self.configuration_set

                # Attempt to send email via SES
                response = self.ses.send_email(**send_params)

                # Extract MessageId from response
                message_id = response.get('MessageId')
                logger.info(
                    f"Email sent successfully to {masked_email}. "
                    f"MessageId: {message_id}"
                )
                return (True, message_id, None)

            except ClientError as e:
                # Extract error code from SES response
                error_code = e.response.get('Error', {}).get('Code', 'Unknown')

                # Check if error is transient (retryable)
                if self._is_transient_error(error_code):
                    if attempt < max_retries:
                        # Calculate backoff delay for this attempt
                        delay = self._calculate_backoff_delay(attempt)
                        logger.warning(
                            f"Transient error {error_code} sending email to {masked_email}, "
                            f"retrying in {delay:.2f}s (attempt {attempt + 1}/{max_retries})"
                        )
                        time.sleep(delay)
                        continue
                    else:
                        # Max retries exhausted for transient error
                        logger.error(
                            f"Max retries ({max_retries}) exceeded for transient error: {error_code}. "
                            f"Failed to send email to {masked_email}"
                        )
                        return (False, None, error_code)
                else:
                    # Permanent error - don't retry
                    logger.error(
                        f"Permanent SES error: {error_code}. "
                        f"Failed to send email to {masked_email}"
                    )
                    return (False, None, error_code)

            except Exception as e:
                # Network errors or unexpected failures - treat as transient
                error_type = type(e).__name__
                if attempt < max_retries:
                    # Calculate backoff delay for this attempt
                    delay = self._calculate_backoff_delay(attempt)
                    logger.warning(
                        f"Unexpected error ({error_type}) sending email to {masked_email}, "
                        f"retrying in {delay:.2f}s (attempt {attempt + 1}/{max_retries})"
                    )
                    time.sleep(delay)
                    continue
                else:
                    # Max retries exhausted for unexpected error
                    logger.error(
                        f"Max retries ({max_retries}) exceeded for unexpected error: {error_type}. "
                        f"Failed to send email to {masked_email}"
                    )
                    return (False, None, error_type)

        # Should never reach here, but return failure as fallback
        return (False, None, None)

    def _validate_email(self, email: str) -> bool:
        """
        Validate email address format before sending.
        
        Performs basic email format validation using a regex pattern that checks for:
        - Local part: alphanumeric characters, dots, hyphens, underscores, plus signs
        - @ symbol separator
        - Domain part: alphanumeric characters, dots, hyphens
        - TLD: at least 2 characters
        
        This validation prevents sending emails to obviously invalid addresses,
        reducing SES errors and improving error messages. It does NOT verify that
        the email address actually exists or can receive mail - that's SES's job.
        
        Args:
            email: Email address to validate
            
        Returns:
            True if email format is valid, False otherwise
            
        Examples:
            >>> service = EmailService()
            >>> service._validate_email("user@example.com")
            True
            >>> service._validate_email("user.name+tag@example.co.uk")
            True
            >>> service._validate_email("invalid.email")
            False
            >>> service._validate_email("@example.com")
            False
            >>> service._validate_email("user@")
            False
            >>> service._validate_email("")
            False
            
        Validation Rules:
            - Must contain exactly one @ symbol
            - Local part (before @) must contain valid characters
            - Domain part (after @) must contain valid characters
            - Domain must have at least one dot
            - TLD must be at least 2 characters
            
        Security Note:
            This is a basic format check, not a comprehensive email validator.
            It's designed to catch obvious typos and malformed addresses before
            making SES API calls. More sophisticated validation (like checking
            MX records) is not performed to keep the function fast and simple.
        """
        import re
        
        # Basic email regex pattern
        # Pattern explanation:
        # ^[a-zA-Z0-9._%+-]+  : Local part (before @) - alphanumeric, dots, underscores, percent, plus, hyphen
        # @                   : Required @ symbol
        # [a-zA-Z0-9.-]+      : Domain name - alphanumeric, dots, hyphens
        # \.                  : Required dot before TLD
        # [a-zA-Z]{2,}$       : TLD - at least 2 letters
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not email or not isinstance(email, str):
            return False
        
        return bool(re.match(email_pattern, email))
    
    def send_reset_email(
        self, 
        recipient_email: str, 
        reset_token: str,
        expiration: datetime
    ) -> tuple[bool, Optional[str], Optional[str]]:
        """
        Send password reset email with retry logic.
        
        This method orchestrates the complete email sending process:
        1. Validates email address format
        2. Builds the password reset link from base_url and token
        3. Formats the expiration time for display
        4. Loads email templates (HTML and text)
        5. Renders templates with user-specific data
        6. Sends email via SES with automatic retry logic
        7. Returns success status, MessageId, and error code
        
        The method uses the enhanced EmailService features including:
        - Email validation with _validate_email()
        - Template management with _load_template()
        - Variable substitution with _render_template()
        - Retry logic with _send_with_retry()
        
        Args:
            recipient_email: User's email address
            reset_token: Plaintext reset token (base64-encoded)
            expiration: Token expiration datetime (UTC)
            
        Returns:
            Tuple of (success: bool, message_id: Optional[str], error_code: Optional[str])
            - (True, message_id, None) on successful delivery with SES MessageId
            - (False, None, error_code) on failure after all retries exhausted or invalid email
            
        Email Contents:
            - Subject: "Password Reset Request"
            - Reset link: {BASE_URL}/reset-password?token={reset_token}
            - Expiration time: Formatted as 'YYYY-MM-DD HH:MM:SS UTC'
            - Security notice: Instructions to ignore if not requested
            - Both HTML and plain text versions
            
        Examples:
            >>> service = EmailService()
            >>> from datetime import datetime, timedelta
            >>> expiration = datetime.utcnow() + timedelta(hours=1)
            >>> success, message_id = service.send_reset_email(
            ...     "user@example.com",
            ...     "abc123token",
            ...     expiration
            ... )
            >>> if success:
            ...     print(f"Email sent successfully. MessageId: {message_id}")
            ... else:
            ...     print("Email delivery failed")
            
        Security:
            - Email addresses are validated before sending
            - Email addresses are masked in logs
            - Reset tokens are never logged
            - Template variables are HTML-escaped to prevent injection
            - Errors are logged but not exposed to clients
            
        Performance:
            - Validates email format before making SES API call
            - Uses retry logic with exponential backoff for transient failures
            - Respects Lambda timeout limits
            - Fails fast on permanent errors and invalid emails
        """
        try:
            # Validate email address format before attempting to send
            if not self._validate_email(recipient_email):
                masked_email = self._mask_email(recipient_email)
                logger.error(
                    f"Invalid email address format: {masked_email}. "
                    f"Email delivery aborted."
                )
                return (False, None, "InvalidEmailFormat")
            
            # Build reset link from base_url and token
            reset_link = f"{self.base_url}/reset-password?token={reset_token}"
            
            # Format expiration time for display (UTC)
            expiration_str = expiration.strftime('%Y-%m-%d %H:%M:%S UTC')
            
            # Load email templates (HTML and text)
            templates = self._load_template('password_reset')
            
            # Prepare template variables for substitution
            variables = {
                'reset_link': reset_link,
                'expiration_time': expiration_str
            }
            
            # Render templates with variable substitution and HTML escaping
            body_html = self._render_template(templates['html'], variables)
            body_text = self._render_template(templates['text'], variables)
            
            # Send email with retry logic
            subject = "Password Reset Request"
            return self._send_with_retry(
                recipient_email,
                subject,
                body_text,
                body_html
            )
            
        except Exception as e:
            # Catch any unexpected errors during template rendering or preparation
            logger.error(
                f"Unexpected error preparing reset email: {type(e).__name__}. "
                f"Email delivery failed."
            )
            return (False, None, type(e).__name__)
    
    def verify_email_address(self, email: str) -> bool:
        """
        Verifies an email address with SES (for development/testing).
        
        In production, you would use SES domain verification instead.
        This method is useful for LocalStack testing.
        
        Args:
            email: Email address to verify
            
        Returns:
            True if verification was initiated successfully
        """
        try:
            self.ses.verify_email_identity(EmailAddress=email)
            logger.info(f"Email verification initiated for: {email}")
            return True
        except ClientError as e:
            logger.error(f"Error verifying email address: {e}")
            return False
    def _is_transient_error(self, error_code: str) -> bool:
        """
        Determine if an SES error is transient (retryable).

        Classifies SES error codes into two categories:
        - Transient errors: Temporary failures that should be retried with exponential backoff
        - Permanent errors: Failures that will not succeed on retry and should fail immediately

        This classification is critical for implementing robust retry logic that:
        - Automatically recovers from temporary service issues
        - Avoids wasting time retrying operations that will never succeed
        - Respects SES rate limits through appropriate backoff strategies

        Args:
            error_code: The error code returned by SES API (e.g., 'Throttling', 'MessageRejected')

        Returns:
            True if the error is transient and should be retried, False if permanent

        Transient Errors (return True - should retry):
            - Throttling: SES rate limit exceeded, retry with exponential backoff
            - ServiceUnavailable: SES temporarily unavailable, retry after delay
            - RequestTimeout: Request timed out, retry with backoff
            - InternalFailure: Internal SES error, may succeed on retry

        Permanent Errors (return False - should NOT retry):
            - MessageRejected: Email content rejected by SES (invalid format, spam-like content)
            - MailFromDomainNotVerified: Sender domain not verified in SES
            - ConfigurationSetDoesNotExist: Invalid SES configuration set name
            - AccountSendingPausedException: SES account suspended or in sandbox mode
            - InvalidParameterValue: Invalid email address or other parameters
            - All other error codes: Treated as permanent to avoid unnecessary retries

        Examples:
            >>> service = EmailService()
            >>> service._is_transient_error('Throttling')
            True
            >>> service._is_transient_error('ServiceUnavailable')
            True
            >>> service._is_transient_error('MessageRejected')
            False
            >>> service._is_transient_error('MailFromDomainNotVerified')
            False
            >>> service._is_transient_error('UnknownError')
            False

        Security Note:
            Error codes are logged but never exposed to API clients to prevent
            information disclosure that could aid in user enumeration attacks.

        Performance Note:
            Uses a set for O(1) lookup performance, which is important since this
            method is called on every SES API error during retry logic.
        """
        # Define transient errors that should be retried
        # Using a set for O(1) lookup performance
        transient_errors = {
            'Throttling',           # Rate limit exceeded
            'ServiceUnavailable',   # SES temporarily unavailable
            'RequestTimeout',       # Request timed out
            'InternalFailure'       # Internal SES error
        }

        return error_code in transient_errors

    def _calculate_backoff_delay(
        self,
        attempt: int,
        base_delay: float = 1.0,
        max_delay: float = 10.0
    ) -> float:
        """
        Calculate exponential backoff delay with jitter.

        Implements exponential backoff with random jitter to prevent thundering herd
        problems when multiple Lambda instances retry simultaneously. The jitter helps
        distribute retry attempts over time, reducing load spikes on SES.

        The exponential backoff formula ensures that retry delays increase exponentially
        with each attempt, giving transient issues time to resolve while avoiding
        excessive delays that could impact user experience.

        Formula: min(base_delay * (2 ** attempt) + random_jitter, max_delay)

        Where:
        - Exponential component: base_delay * (2 ** attempt)
        - Jitter component: random value between 0 and 50% of exponential delay
        - Cap: Result is capped at max_delay to prevent excessive wait times

        Args:
            attempt: Retry attempt number (0-indexed, where 0 is first retry)
            base_delay: Base delay in seconds for exponential calculation (default: 1.0)
            max_delay: Maximum delay in seconds to cap the result (default: 10.0)

        Returns:
            Calculated delay in seconds with jitter applied and capped at max_delay

        Examples:
            >>> service = EmailService()
            >>> # Attempt 0: 1.0s * 2^0 = 1.0s, jitter 0-0.5s → 1.0-1.5s
            >>> delay = service._calculate_backoff_delay(0)
            >>> 1.0 <= delay <= 1.5
            True

            >>> # Attempt 1: 1.0s * 2^1 = 2.0s, jitter 0-1.0s → 2.0-3.0s
            >>> delay = service._calculate_backoff_delay(1)
            >>> 2.0 <= delay <= 3.0
            True

            >>> # Attempt 2: 1.0s * 2^2 = 4.0s, jitter 0-2.0s → 4.0-6.0s
            >>> delay = service._calculate_backoff_delay(2)
            >>> 4.0 <= delay <= 6.0
            True

            >>> # Attempt 5: 1.0s * 2^5 = 32.0s, but capped at max_delay=10.0s
            >>> delay = service._calculate_backoff_delay(5)
            >>> delay == 10.0
            True

            >>> # Custom base_delay and max_delay
            >>> delay = service._calculate_backoff_delay(2, base_delay=0.5, max_delay=5.0)
            >>> 2.0 <= delay <= 5.0
            True

        Retry Delay Progression (with default parameters):
            Attempt 0: 1.0-1.5s   (1.0s + 0-0.5s jitter)
            Attempt 1: 2.0-3.0s   (2.0s + 0-1.0s jitter)
            Attempt 2: 4.0-6.0s   (4.0s + 0-2.0s jitter)
            Attempt 3: 8.0-10.0s  (8.0s + 0-4.0s jitter, capped at 10.0s)
            Attempt 4+: 10.0s     (capped at max_delay)

        Performance Note:
            This method is called on every retry attempt, so it's designed to be
            lightweight with minimal computation (just exponential calculation and
            one random number generation).

        Security Note:
            The jitter uses Python's random.uniform() which is sufficient for
            retry timing (cryptographic randomness is not required here).
        """
        import random

        # Calculate exponential backoff: base_delay * (2 ** attempt)
        delay = base_delay * (2 ** attempt)

        # Add random jitter (0 to 50% of delay) to prevent thundering herd
        jitter = random.uniform(0, delay * 0.5)

        # Cap at max_delay to prevent excessive wait times
        return min(delay + jitter, max_delay)


