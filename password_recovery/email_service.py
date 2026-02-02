"""
Email service for password recovery.

This module handles sending password reset emails using AWS SES (Simple Email Service).
"""

import os
import logging
from datetime import datetime
from typing import Optional
import boto3
from botocore.exceptions import ClientError


logger = logging.getLogger(__name__)


class EmailService:
    """
    Email service for sending password reset emails using AWS SES.
    
    Handles email composition, delivery, and error handling while maintaining
    security best practices (no sensitive data in logs).
    """
    
    def __init__(self, ses_client=None, from_email=None, base_url=None):
        """
        Initialize the email service.
        
        Args:
            ses_client: Optional boto3 SES client (for testing)
            from_email: Optional sender email address (defaults to env var)
            base_url: Optional base URL for reset links (defaults to env var)
        """
        self.ses = ses_client or boto3.client('ses')
        self.from_email = from_email or os.environ.get('FROM_EMAIL', 'noreply@example.com')
        self.base_url = base_url or os.environ.get('BASE_URL', 'https://example.com')
        logger.debug(f"EmailService initialized with from_email: {self.from_email}")
    
    def send_reset_email(
        self, 
        recipient_email: str, 
        reset_token: str,
        expiration: datetime
    ) -> bool:
        """
        Sends a password reset email with a reset link.
        
        Args:
            recipient_email: User's email address
            reset_token: Plaintext token (base64-encoded)
            expiration: Token expiration time
            
        Returns:
            True if email was sent successfully, False otherwise
            
        Email contains:
        - Reset link: {BASE_URL}/reset-password?token={reset_token}
        - Expiration time
        - Security notice (if you didn't request this, ignore it)
        
        Examples:
            >>> service = EmailService()
            >>> from datetime import datetime, timedelta
            >>> expiration = datetime.utcnow() + timedelta(hours=1)
            >>> success = service.send_reset_email(
            ...     "user@example.com",
            ...     "abc123token",
            ...     expiration
            ... )
            >>> if success:
            ...     print("Email sent successfully")
        """
        try:
            # Format expiration time for display
            expiration_str = expiration.strftime('%Y-%m-%d %H:%M:%S UTC')
            
            # Build reset link
            reset_link = f"{self.base_url}/reset-password?token={reset_token}"
            
            # Compose email
            subject = "Password Reset Request"
            body_text = self._compose_text_body(reset_link, expiration_str)
            body_html = self._compose_html_body(reset_link, expiration_str)
            
            # Send email via SES
            response = self.ses.send_email(
                Source=self.from_email,
                Destination={
                    'ToAddresses': [recipient_email]
                },
                Message={
                    'Subject': {
                        'Data': subject,
                        'Charset': 'UTF-8'
                    },
                    'Body': {
                        'Text': {
                            'Data': body_text,
                            'Charset': 'UTF-8'
                        },
                        'Html': {
                            'Data': body_html,
                            'Charset': 'UTF-8'
                        }
                    }
                }
            )
            
            message_id = response.get('MessageId', 'unknown')
            logger.info(f"Password reset email sent successfully. MessageId: {message_id}")
            return True
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            logger.error(f"SES error sending reset email: {error_code}")
            # Don't log recipient email or token for security
            return False
            
        except Exception as e:
            logger.error(f"Unexpected error sending reset email: {type(e).__name__}")
            # Don't log details that might contain sensitive data
            return False
    
    def _compose_text_body(self, reset_link: str, expiration_str: str) -> str:
        """
        Composes the plain text email body.
        
        Args:
            reset_link: The password reset link
            expiration_str: Formatted expiration time
            
        Returns:
            Plain text email body
        """
        return f"""Hello,

You have requested to reset your password. Please click the link below to set a new password:

{reset_link}

This link will expire at {expiration_str}.

If you did not request a password reset, please ignore this email. Your password will remain unchanged.

For security reasons, never share this link with anyone.

Best regards,
The Security Team
"""
    
    def _compose_html_body(self, reset_link: str, expiration_str: str) -> str:
        """
        Composes the HTML email body.
        
        Args:
            reset_link: The password reset link
            expiration_str: Formatted expiration time
            
        Returns:
            HTML email body
        """
        return f"""<!DOCTYPE html>
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
            This link will expire at {expiration_str}.
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
