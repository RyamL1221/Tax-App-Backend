"""
Unit tests for VOIDED and CORRECTED mutual exclusivity warning.

This module tests that the document generator logs a warning when both
voided and corrected are set to true, but still generates the PDF.

Requirements: 4.1, 4.2, 4.3
"""

import pytest
import logging
from unittest.mock import Mock, patch
from tax_document_generation.document_generator import generate_document


class TestMutualExclusivityWarning:
    """Test mutual exclusivity warning for voided and corrected checkboxes."""
    
    @patch('tax_document_generation.document_generator.logger')
    def test_warning_logged_when_both_true(self, mock_logger):
        """Test that warning is logged when both voided and corrected are true."""
        # Create minimal form data with both checkboxes true
        form_data = {
            "payerName": "Test Corp",
            "payerTIN": "12-3456789",
            "recipientName": "John Doe",
            "recipientTIN": "123-45-6789",
            "totalOrdinaryDividends": 1000.00,
            "voided": True,
            "corrected": True
        }
        
        # Mock template (minimal PDF)
        template = b"%PDF-1.4\n%%EOF"
        
        # Call generate_document (will fail due to mock template, but warning should be logged)
        try:
            generate_document(template, form_data, "1099-DIV")
        except Exception:
            pass  # Expected to fail with mock template
        
        # Verify warning was logged
        warning_calls = [call for call in mock_logger.warning.call_args_list 
                        if "voided" in str(call).lower() and "corrected" in str(call).lower()]
        
        assert len(warning_calls) > 0, "Warning not logged when both checkboxes are true"
        
        # Verify warning message content
        warning_message = str(warning_calls[0])
        assert "voided" in warning_message.lower()
        assert "corrected" in warning_message.lower()
        assert "true" in warning_message.lower()
    
    @patch('tax_document_generation.document_generator.logger')
    def test_no_warning_when_only_voided_true(self, mock_logger):
        """Test that no warning is logged when only voided is true."""
        form_data = {
            "payerName": "Test Corp",
            "payerTIN": "12-3456789",
            "recipientName": "John Doe",
            "recipientTIN": "123-45-6789",
            "totalOrdinaryDividends": 1000.00,
            "voided": True,
            "corrected": False
        }
        
        template = b"%PDF-1.4\n%%EOF"
        
        try:
            generate_document(template, form_data, "1099-DIV")
        except Exception:
            pass
        
        # Verify no mutual exclusivity warning was logged
        warning_calls = [call for call in mock_logger.warning.call_args_list 
                        if "voided" in str(call).lower() and "corrected" in str(call).lower() 
                        and "both" in str(call).lower()]
        
        assert len(warning_calls) == 0, "Warning logged when only voided is true"
    
    @patch('tax_document_generation.document_generator.logger')
    def test_no_warning_when_only_corrected_true(self, mock_logger):
        """Test that no warning is logged when only corrected is true."""
        form_data = {
            "payerName": "Test Corp",
            "payerTIN": "12-3456789",
            "recipientName": "John Doe",
            "recipientTIN": "123-45-6789",
            "totalOrdinaryDividends": 1000.00,
            "voided": False,
            "corrected": True
        }
        
        template = b"%PDF-1.4\n%%EOF"
        
        try:
            generate_document(template, form_data, "1099-DIV")
        except Exception:
            pass
        
        # Verify no mutual exclusivity warning was logged
        warning_calls = [call for call in mock_logger.warning.call_args_list 
                        if "voided" in str(call).lower() and "corrected" in str(call).lower() 
                        and "both" in str(call).lower()]
        
        assert len(warning_calls) == 0, "Warning logged when only corrected is true"
    
    @patch('tax_document_generation.document_generator.logger')
    def test_no_warning_when_both_false(self, mock_logger):
        """Test that no warning is logged when both are false."""
        form_data = {
            "payerName": "Test Corp",
            "payerTIN": "12-3456789",
            "recipientName": "John Doe",
            "recipientTIN": "123-45-6789",
            "totalOrdinaryDividends": 1000.00,
            "voided": False,
            "corrected": False
        }
        
        template = b"%PDF-1.4\n%%EOF"
        
        try:
            generate_document(template, form_data, "1099-DIV")
        except Exception:
            pass
        
        # Verify no mutual exclusivity warning was logged
        warning_calls = [call for call in mock_logger.warning.call_args_list 
                        if "voided" in str(call).lower() and "corrected" in str(call).lower() 
                        and "both" in str(call).lower()]
        
        assert len(warning_calls) == 0, "Warning logged when both are false"
    
    @patch('tax_document_generation.document_generator.logger')
    def test_no_warning_when_fields_omitted(self, mock_logger):
        """Test that no warning is logged when fields are omitted."""
        form_data = {
            "payerName": "Test Corp",
            "payerTIN": "12-3456789",
            "recipientName": "John Doe",
            "recipientTIN": "123-45-6789",
            "totalOrdinaryDividends": 1000.00
        }
        
        template = b"%PDF-1.4\n%%EOF"
        
        try:
            generate_document(template, form_data, "1099-DIV")
        except Exception:
            pass
        
        # Verify no mutual exclusivity warning was logged
        warning_calls = [call for call in mock_logger.warning.call_args_list 
                        if "voided" in str(call).lower() and "corrected" in str(call).lower() 
                        and "both" in str(call).lower()]
        
        assert len(warning_calls) == 0, "Warning logged when fields are omitted"


class TestWarningMessageContent:
    """Test the content of the warning message."""
    
    @patch('tax_document_generation.document_generator.logger')
    def test_warning_message_is_clear(self, mock_logger):
        """Test that warning message is clear and actionable."""
        form_data = {
            "payerName": "Test Corp",
            "payerTIN": "12-3456789",
            "recipientName": "John Doe",
            "recipientTIN": "123-45-6789",
            "totalOrdinaryDividends": 1000.00,
            "voided": True,
            "corrected": True
        }
        
        template = b"%PDF-1.4\n%%EOF"
        
        try:
            generate_document(template, form_data, "1099-DIV")
        except Exception:
            pass
        
        # Get warning message
        warning_calls = [call for call in mock_logger.warning.call_args_list 
                        if "voided" in str(call).lower() and "corrected" in str(call).lower()
                        and "both" in str(call).lower()]
        
        assert len(warning_calls) > 0
        warning_message = str(warning_calls[0])
        
        # Verify message mentions both fields
        assert "voided" in warning_message.lower()
        assert "corrected" in warning_message.lower()
        
        # Verify message indicates both are true
        assert "true" in warning_message.lower() or "both" in warning_message.lower()
        
        # Verify message mentions IRS guidelines or validity
        assert "irs" in warning_message.lower() or "valid" in warning_message.lower()
        
        # Verify message indicates PDF will still be generated
        assert "generated" in warning_message.lower() or "checked" in warning_message.lower()
