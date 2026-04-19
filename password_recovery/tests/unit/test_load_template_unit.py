"""
Unit tests for EmailService._load_template method.

Tests template loading, validation, and error handling.
"""

import pytest
import logging
from unittest.mock import Mock, patch
from password_recovery.email_service import EmailService


def test_load_template_returns_dict_with_html_and_text_keys():
    """Test that _load_template returns a dict with 'html' and 'text' keys."""
    # Create EmailService with mocked SES client
    mock_ses = Mock()
    service = EmailService(
        ses_client=mock_ses,
        from_email='test@example.com',
        base_url='http://localhost:3000',
        ses_region='us-east-1'
    )
    
    # Load template
    templates = service._load_template('password_reset')
    
    # Verify structure
    assert isinstance(templates, dict)
    assert 'html' in templates
    assert 'text' in templates
    assert isinstance(templates['html'], str)
    assert isinstance(templates['text'], str)


def test_load_template_contains_required_variables():
    """Test that loaded templates contain required variables."""
    # Create EmailService with mocked SES client
    mock_ses = Mock()
    service = EmailService(
        ses_client=mock_ses,
        from_email='test@example.com',
        base_url='http://localhost:3000',
        ses_region='us-east-1'
    )
    
    # Load template
    templates = service._load_template('password_reset')
    
    # Verify required variables are present
    required_vars = ['{reset_link}', '{expiration_time}']
    
    for var in required_vars:
        assert var in templates['html'], f"HTML template missing {var}"
        assert var in templates['text'], f"Text template missing {var}"


def test_load_template_logs_warning_for_missing_variables(caplog):
    """Test that _load_template logs warnings if required variables are missing."""
    # Create EmailService with mocked SES client
    mock_ses = Mock()
    service = EmailService(
        ses_client=mock_ses,
        from_email='test@example.com',
        base_url='http://localhost:3000',
        ses_region='us-east-1'
    )
    
    # Mock the DEFAULT_HTML_TEMPLATE and DEFAULT_TEXT_TEMPLATE to be missing variables
    with patch('password_recovery.email_service.DEFAULT_HTML_TEMPLATE', 'Hello {name}'):
        with patch('password_recovery.email_service.DEFAULT_TEXT_TEMPLATE', 'Hello {name}'):
            with caplog.at_level(logging.WARNING):
                templates = service._load_template('password_reset')
            
            # Verify warnings were logged
            assert any('HTML template missing required variable: {reset_link}' in record.message 
                      for record in caplog.records)
            assert any('HTML template missing required variable: {expiration_time}' in record.message 
                      for record in caplog.records)
            assert any('Text template missing required variable: {reset_link}' in record.message 
                      for record in caplog.records)
            assert any('Text template missing required variable: {expiration_time}' in record.message 
                      for record in caplog.records)


def test_load_template_returns_templates_even_with_missing_variables():
    """Test that _load_template returns templates even if variables are missing (graceful degradation)."""
    # Create EmailService with mocked SES client
    mock_ses = Mock()
    service = EmailService(
        ses_client=mock_ses,
        from_email='test@example.com',
        base_url='http://localhost:3000',
        ses_region='us-east-1'
    )
    
    # Mock templates with missing variables
    with patch('password_recovery.email_service.DEFAULT_HTML_TEMPLATE', 'Hello {name}'):
        with patch('password_recovery.email_service.DEFAULT_TEXT_TEMPLATE', 'Hello {name}'):
            templates = service._load_template('password_reset')
            
            # Verify templates are still returned (graceful degradation)
            assert isinstance(templates, dict)
            assert 'html' in templates
            assert 'text' in templates
            assert templates['html'] == 'Hello {name}'
            assert templates['text'] == 'Hello {name}'


def test_load_template_accepts_template_name_parameter():
    """Test that _load_template accepts template_name parameter (for future use)."""
    # Create EmailService with mocked SES client
    mock_ses = Mock()
    service = EmailService(
        ses_client=mock_ses,
        from_email='test@example.com',
        base_url='http://localhost:3000',
        ses_region='us-east-1'
    )
    
    # Load template with different names (currently all return same templates)
    templates1 = service._load_template('password_reset')
    templates2 = service._load_template('welcome')
    templates3 = service._load_template('notification')
    
    # All should return valid templates (currently the same)
    assert isinstance(templates1, dict)
    assert isinstance(templates2, dict)
    assert isinstance(templates3, dict)


def test_load_template_html_content_is_valid():
    """Test that HTML template contains valid HTML structure."""
    # Create EmailService with mocked SES client
    mock_ses = Mock()
    service = EmailService(
        ses_client=mock_ses,
        from_email='test@example.com',
        base_url='http://localhost:3000',
        ses_region='us-east-1'
    )
    
    # Load template
    templates = service._load_template('password_reset')
    html = templates['html']
    
    # Verify HTML structure
    assert '<!DOCTYPE html>' in html
    assert '<html>' in html
    assert '</html>' in html
    assert '<body' in html
    assert '</body>' in html


def test_load_template_text_content_is_plain_text():
    """Test that text template is plain text (no HTML tags)."""
    # Create EmailService with mocked SES client
    mock_ses = Mock()
    service = EmailService(
        ses_client=mock_ses,
        from_email='test@example.com',
        base_url='http://localhost:3000',
        ses_region='us-east-1'
    )
    
    # Load template
    templates = service._load_template('password_reset')
    text = templates['text']
    
    # Verify no HTML tags in text template
    assert '<html>' not in text
    assert '<body>' not in text
    assert '<div>' not in text
    assert '<p>' not in text
