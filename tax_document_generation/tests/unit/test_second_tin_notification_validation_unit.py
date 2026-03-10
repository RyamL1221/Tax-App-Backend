"""
Unit tests for secondTinNotification boolean value handling.

Tests verify that the input validator correctly handles boolean values
for the secondTinNotification field.

Requirements: 5.1, 5.2, 5.3
"""

import pytest
from tax_document_generation.input_validator import validate_form_data
from tax_document_generation.exceptions import ValidationError


class TestSecondTinNotificationValidation:
    """Test secondTinNotification boolean value handling."""
    
    def get_minimal_form_data(self):
        """Get minimal valid form data for 1099-DIV."""
        return {
            "calendarYear": "2024",
            "payerName": "Test Corp",
            "payerTIN": "12-3456789",
            "recipientName": "John Doe",
            "recipientTIN": "123-45-6789",
            "totalOrdinaryDividends": 1000.00
        }
    
    def test_true_value_accepted(self):
        """Test that true value is accepted for secondTinNotification."""
        form_data = self.get_minimal_form_data()
        form_data["secondTinNotification"] = True
        
        # Should not raise ValidationError
        validate_form_data("1099-DIV", form_data)
    
    def test_false_value_accepted(self):
        """Test that false value is accepted for secondTinNotification."""
        form_data = self.get_minimal_form_data()
        form_data["secondTinNotification"] = False
        
        # Should not raise ValidationError
        validate_form_data("1099-DIV", form_data)
    
    def test_missing_field_handled_gracefully(self):
        """Test that missing secondTinNotification field is handled gracefully."""
        form_data = self.get_minimal_form_data()
        # Don't include secondTinNotification
        
        # Should not raise ValidationError (field is optional)
        validate_form_data("1099-DIV", form_data)
    
    def test_string_true_rejected(self):
        """Test that string 'true' is rejected (must be boolean)."""
        form_data = self.get_minimal_form_data()
        form_data["secondTinNotification"] = "true"
        
        # Should raise ValidationError
        with pytest.raises(ValidationError) as exc_info:
            validate_form_data("1099-DIV", form_data)
        
        assert "secondTinNotification" in str(exc_info.value)
        assert "bool" in str(exc_info.value)
    
    def test_string_false_rejected(self):
        """Test that string 'false' is rejected (must be boolean)."""
        form_data = self.get_minimal_form_data()
        form_data["secondTinNotification"] = "false"
        
        # Should raise ValidationError
        with pytest.raises(ValidationError) as exc_info:
            validate_form_data("1099-DIV", form_data)
        
        assert "secondTinNotification" in str(exc_info.value)
        assert "bool" in str(exc_info.value)
    
    def test_integer_one_rejected(self):
        """Test that integer 1 is rejected (must be boolean)."""
        form_data = self.get_minimal_form_data()
        form_data["secondTinNotification"] = 1
        
        # Should raise ValidationError
        with pytest.raises(ValidationError) as exc_info:
            validate_form_data("1099-DIV", form_data)
        
        assert "secondTinNotification" in str(exc_info.value)
        assert "bool" in str(exc_info.value)
    
    def test_integer_zero_rejected(self):
        """Test that integer 0 is rejected (must be boolean)."""
        form_data = self.get_minimal_form_data()
        form_data["secondTinNotification"] = 0
        
        # Should raise ValidationError
        with pytest.raises(ValidationError) as exc_info:
            validate_form_data("1099-DIV", form_data)
        
        assert "secondTinNotification" in str(exc_info.value)
        assert "bool" in str(exc_info.value)
    
    def test_none_value_rejected(self):
        """Test that None value is rejected (must be boolean)."""
        form_data = self.get_minimal_form_data()
        form_data["secondTinNotification"] = None
        
        # Should raise ValidationError
        with pytest.raises(ValidationError) as exc_info:
            validate_form_data("1099-DIV", form_data)
        
        assert "secondTinNotification" in str(exc_info.value)
        assert "bool" in str(exc_info.value)
    
    def test_combined_with_other_checkboxes(self):
        """Test that secondTinNotification works with other checkbox fields."""
        form_data = self.get_minimal_form_data()
        form_data["secondTinNotification"] = True
        form_data["voided"] = False
        form_data["corrected"] = True
        form_data["fatcaFilingRequirement"] = False
        
        # Should not raise ValidationError
        validate_form_data("1099-DIV", form_data)
