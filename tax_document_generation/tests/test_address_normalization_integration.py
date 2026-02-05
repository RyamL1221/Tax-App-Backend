"""
Integration tests for address normalization in input validator.

Tests that the input validator properly integrates with the address normalizer
to support both legacy combined address format and new separate format.

Requirements: 6.1, 6.2
"""

import pytest
from tax_document_generation.input_validator import validate_form_data
from tax_document_generation.exceptions import ValidationError


class TestAddressNormalizationIntegration:
    """Integration tests for address normalization in validator."""
    
    def test_combined_payer_address_format(self):
        """Test that combined payer address format is normalized and validated."""
        form_data = {
            'payerName': 'Test Corporation',
            'payerTIN': '12-3456789',
            'payerCity': 'New York, NY 10001',  # Combined format
            'recipientName': 'John Doe',
            'recipientTIN': '123-45-6789',
            'totalOrdinaryDividends': 1000.00
        }
        
        # Should not raise any exception
        validate_form_data('1099-DIV', form_data)
    
    def test_separate_payer_address_format(self):
        """Test that separate payer address format works correctly."""
        form_data = {
            'payerName': 'Test Corporation',
            'payerTIN': '12-3456789',
            'payerCity': 'New York',
            'payerState': 'NY',
            'payerZip': '10001',
            'recipientName': 'John Doe',
            'recipientTIN': '123-45-6789',
            'totalOrdinaryDividends': 1000.00
        }
        
        # Should not raise any exception
        validate_form_data('1099-DIV', form_data)
    
    def test_combined_recipient_address_format(self):
        """Test that combined recipient address format is normalized and validated."""
        form_data = {
            'payerName': 'Test Corporation',
            'payerTIN': '12-3456789',
            'recipientName': 'John Doe',
            'recipientTIN': '123-45-6789',
            'recipientCity': 'Los Angeles, CA 90001',  # Combined format
            'totalOrdinaryDividends': 1000.00
        }
        
        # Should not raise any exception
        validate_form_data('1099-DIV', form_data)
    
    def test_separate_recipient_address_format(self):
        """Test that separate recipient address format works correctly."""
        form_data = {
            'payerName': 'Test Corporation',
            'payerTIN': '12-3456789',
            'recipientName': 'John Doe',
            'recipientTIN': '123-45-6789',
            'recipientCity': 'Los Angeles',
            'recipientState': 'CA',
            'recipientZip': '90001',
            'totalOrdinaryDividends': 1000.00
        }
        
        # Should not raise any exception
        validate_form_data('1099-DIV', form_data)
    
    def test_mixed_address_formats(self):
        """Test that mixed address formats work (payer combined, recipient separate)."""
        form_data = {
            'payerName': 'Test Corporation',
            'payerTIN': '12-3456789',
            'payerCity': 'New York, NY 10001',  # Combined format
            'recipientName': 'John Doe',
            'recipientTIN': '123-45-6789',
            'recipientCity': 'Los Angeles',  # Separate format
            'recipientState': 'CA',
            'recipientZip': '90001',
            'totalOrdinaryDividends': 1000.00
        }
        
        # Should not raise any exception
        validate_form_data('1099-DIV', form_data)
    
    def test_explicit_values_take_precedence(self):
        """Test that explicit state/zip values take precedence over combined format."""
        form_data = {
            'payerName': 'Test Corporation',
            'payerTIN': '12-3456789',
            'payerCity': 'New York, NY 10001',  # Combined format
            'payerState': 'CA',  # Explicit value should take precedence
            'payerZip': '90210',  # Explicit value should take precedence
            'recipientName': 'John Doe',
            'recipientTIN': '123-45-6789',
            'totalOrdinaryDividends': 1000.00
        }
        
        # Should not raise any exception
        # The validator should use the explicit CA and 90210 values
        validate_form_data('1099-DIV', form_data)
    
    def test_both_addresses_combined_format(self):
        """Test that both payer and recipient can use combined format."""
        form_data = {
            'payerName': 'Test Corporation',
            'payerTIN': '12-3456789',
            'payerCity': 'New York, NY 10001',  # Combined format
            'recipientName': 'John Doe',
            'recipientTIN': '123-45-6789',
            'recipientCity': 'Los Angeles, CA 90001',  # Combined format
            'totalOrdinaryDividends': 1000.00
        }
        
        # Should not raise any exception
        validate_form_data('1099-DIV', form_data)
    
    def test_extended_zip_code_in_combined_format(self):
        """Test that extended ZIP codes (ZIP+4) work in combined format."""
        form_data = {
            'payerName': 'Test Corporation',
            'payerTIN': '12-3456789',
            'payerCity': 'New York, NY 10001-1234',  # Extended ZIP
            'recipientName': 'John Doe',
            'recipientTIN': '123-45-6789',
            'totalOrdinaryDividends': 1000.00
        }
        
        # Should not raise any exception
        validate_form_data('1099-DIV', form_data)
    
    def test_multi_word_city_in_combined_format(self):
        """Test that multi-word city names work in combined format."""
        form_data = {
            'payerName': 'Test Corporation',
            'payerTIN': '12-3456789',
            'payerCity': 'San Francisco, CA 94102',  # Multi-word city
            'recipientName': 'John Doe',
            'recipientTIN': '123-45-6789',
            'totalOrdinaryDividends': 1000.00
        }
        
        # Should not raise any exception
        validate_form_data('1099-DIV', form_data)
    
    def test_normalization_does_not_affect_required_fields(self):
        """Test that normalization doesn't interfere with required field validation."""
        form_data = {
            'payerName': 'Test Corporation',
            'payerTIN': '12-3456789',
            'payerCity': 'New York, NY 10001',
            'recipientName': 'John Doe',
            # Missing recipientTIN (required field)
            'totalOrdinaryDividends': 1000.00
        }
        
        # Should raise ValidationError for missing required field
        with pytest.raises(ValidationError) as exc_info:
            validate_form_data('1099-DIV', form_data)
        
        assert 'recipientTIN' in str(exc_info.value)
    
    def test_normalization_preserves_other_fields(self):
        """Test that normalization doesn't affect non-address fields."""
        form_data = {
            'payerName': 'Test Corporation',
            'payerTIN': '12-3456789',
            'payerCity': 'New York, NY 10001',
            'recipientName': 'John Doe',
            'recipientTIN': '123-45-6789',
            'totalOrdinaryDividends': 1000.00,
            'qualifiedDividends': 800.00,
            'accountNumber': 'ACC-12345'
        }
        
        # Should not raise any exception
        validate_form_data('1099-DIV', form_data)
