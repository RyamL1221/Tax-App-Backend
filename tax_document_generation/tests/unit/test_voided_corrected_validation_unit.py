"""
Unit tests for VOIDED and CORRECTED checkbox input validation.

This module tests that the input validator correctly handles voided and
corrected fields, accepting valid boolean values and rejecting invalid types.

Requirements: 1.1, 2.1, 5.1, 5.2
"""

import pytest
from tax_document_generation.input_validator import validate_form_data
from tax_document_generation.exceptions import ValidationError


class TestVoidedValidation:
    """Test voided field validation."""
    
    def test_voided_true_accepted(self):
        """Test that voided=True is accepted."""
        form_data = {
            "payerName": "Test Corp",
            "payerTIN": "12-3456789",
            "recipientName": "John Doe",
            "recipientTIN": "123-45-6789",
            "totalOrdinaryDividends": 1000.00,
            "voided": True
        }
        
        # Should not raise exception
        validate_form_data("1099-DIV", form_data)
    
    def test_voided_false_accepted(self):
        """Test that voided=False is accepted."""
        form_data = {
            "payerName": "Test Corp",
            "payerTIN": "12-3456789",
            "recipientName": "John Doe",
            "recipientTIN": "123-45-6789",
            "totalOrdinaryDividends": 1000.00,
            "voided": False
        }
        
        # Should not raise exception
        validate_form_data("1099-DIV", form_data)
    
    def test_voided_omitted_accepted(self):
        """Test that omitting voided field is accepted (optional field)."""
        form_data = {
            "payerName": "Test Corp",
            "payerTIN": "12-3456789",
            "recipientName": "John Doe",
            "recipientTIN": "123-45-6789",
            "totalOrdinaryDividends": 1000.00
        }
        
        # Should not raise exception
        validate_form_data("1099-DIV", form_data)
    
    def test_voided_string_rejected(self):
        """Test that voided with string value is rejected."""
        form_data = {
            "payerName": "Test Corp",
            "payerTIN": "12-3456789",
            "recipientName": "John Doe",
            "recipientTIN": "123-45-6789",
            "totalOrdinaryDividends": 1000.00,
            "voided": "invalid"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            validate_form_data("1099-DIV", form_data)
        
        assert "voided" in str(exc_info.value).lower()
        assert "bool" in str(exc_info.value).lower()
    
    def test_voided_number_rejected(self):
        """Test that voided with numeric value is rejected."""
        form_data = {
            "payerName": "Test Corp",
            "payerTIN": "12-3456789",
            "recipientName": "John Doe",
            "recipientTIN": "123-45-6789",
            "totalOrdinaryDividends": 1000.00,
            "voided": 1
        }
        
        with pytest.raises(ValidationError) as exc_info:
            validate_form_data("1099-DIV", form_data)
        
        assert "voided" in str(exc_info.value).lower()
        assert "bool" in str(exc_info.value).lower()


class TestCorrectedValidation:
    """Test corrected field validation."""
    
    def test_corrected_true_accepted(self):
        """Test that corrected=True is accepted."""
        form_data = {
            "payerName": "Test Corp",
            "payerTIN": "12-3456789",
            "recipientName": "John Doe",
            "recipientTIN": "123-45-6789",
            "totalOrdinaryDividends": 1000.00,
            "corrected": True
        }
        
        # Should not raise exception
        validate_form_data("1099-DIV", form_data)
    
    def test_corrected_false_accepted(self):
        """Test that corrected=False is accepted."""
        form_data = {
            "payerName": "Test Corp",
            "payerTIN": "12-3456789",
            "recipientName": "John Doe",
            "recipientTIN": "123-45-6789",
            "totalOrdinaryDividends": 1000.00,
            "corrected": False
        }
        
        # Should not raise exception
        validate_form_data("1099-DIV", form_data)
    
    def test_corrected_omitted_accepted(self):
        """Test that omitting corrected field is accepted (optional field)."""
        form_data = {
            "payerName": "Test Corp",
            "payerTIN": "12-3456789",
            "recipientName": "John Doe",
            "recipientTIN": "123-45-6789",
            "totalOrdinaryDividends": 1000.00
        }
        
        # Should not raise exception
        validate_form_data("1099-DIV", form_data)
    
    def test_corrected_string_rejected(self):
        """Test that corrected with string value is rejected."""
        form_data = {
            "payerName": "Test Corp",
            "payerTIN": "12-3456789",
            "recipientName": "John Doe",
            "recipientTIN": "123-45-6789",
            "totalOrdinaryDividends": 1000.00,
            "corrected": "invalid"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            validate_form_data("1099-DIV", form_data)
        
        assert "corrected" in str(exc_info.value).lower()
        assert "bool" in str(exc_info.value).lower()
    
    def test_corrected_number_rejected(self):
        """Test that corrected with numeric value is rejected."""
        form_data = {
            "payerName": "Test Corp",
            "payerTIN": "12-3456789",
            "recipientName": "John Doe",
            "recipientTIN": "123-45-6789",
            "totalOrdinaryDividends": 1000.00,
            "corrected": 0
        }
        
        with pytest.raises(ValidationError) as exc_info:
            validate_form_data("1099-DIV", form_data)
        
        assert "corrected" in str(exc_info.value).lower()
        assert "bool" in str(exc_info.value).lower()


class TestBothCheckboxesValidation:
    """Test validation when both checkboxes are provided."""
    
    def test_both_true_accepted(self):
        """Test that both voided=True and corrected=True are accepted."""
        form_data = {
            "payerName": "Test Corp",
            "payerTIN": "12-3456789",
            "recipientName": "John Doe",
            "recipientTIN": "123-45-6789",
            "totalOrdinaryDividends": 1000.00,
            "voided": True,
            "corrected": True
        }
        
        # Should not raise exception (warning is logged, not error)
        validate_form_data("1099-DIV", form_data)
    
    def test_both_false_accepted(self):
        """Test that both voided=False and corrected=False are accepted."""
        form_data = {
            "payerName": "Test Corp",
            "payerTIN": "12-3456789",
            "recipientName": "John Doe",
            "recipientTIN": "123-45-6789",
            "totalOrdinaryDividends": 1000.00,
            "voided": False,
            "corrected": False
        }
        
        # Should not raise exception
        validate_form_data("1099-DIV", form_data)
    
    def test_mixed_values_accepted(self):
        """Test that mixed boolean values are accepted."""
        form_data = {
            "payerName": "Test Corp",
            "payerTIN": "12-3456789",
            "recipientName": "John Doe",
            "recipientTIN": "123-45-6789",
            "totalOrdinaryDividends": 1000.00,
            "voided": True,
            "corrected": False
        }
        
        # Should not raise exception
        validate_form_data("1099-DIV", form_data)


class TestBackwardCompatibility:
    """Test backward compatibility with existing form data."""
    
    def test_existing_form_data_without_checkboxes_accepted(self):
        """Test that existing form data without new fields is accepted."""
        form_data = {
            "payerName": "Test Corp",
            "payerTIN": "12-3456789",
            "recipientName": "John Doe",
            "recipientTIN": "123-45-6789",
            "totalOrdinaryDividends": 1000.00,
            "qualifiedDividends": 800.00,
            "federalIncomeTaxWithheld": 150.00
        }
        
        # Should not raise exception
        validate_form_data("1099-DIV", form_data)
    
    def test_minimal_form_data_accepted(self):
        """Test that minimal form data (only required fields) is accepted."""
        form_data = {
            "payerName": "Test Corp",
            "payerTIN": "12-3456789",
            "recipientName": "John Doe",
            "recipientTIN": "123-45-6789",
            "totalOrdinaryDividends": 1000.00
        }
        
        # Should not raise exception
        validate_form_data("1099-DIV", form_data)
