"""
Unit tests for secondTinNotification field metadata.

Tests verify that the metadata for secondTinNotification is correctly
configured with appropriate values.

Requirements: 4.1, 4.2, 4.3
"""

import pytest
from tax_document_generation.field_mapper import FieldMapper


class TestSecondTinNotificationMetadata:
    """Test secondTinNotification field metadata."""
    
    def test_metadata_exists(self):
        """Test that metadata exists for secondTinNotification."""
        mapper = FieldMapper("1099-DIV")
        metadata = mapper.get_field_metadata("secondTinNotification")
        
        assert metadata is not None, "Metadata should exist for secondTinNotification"
    
    def test_field_is_not_required(self):
        """Test that secondTinNotification is not required."""
        mapper = FieldMapper("1099-DIV")
        metadata = mapper.get_field_metadata("secondTinNotification")
        
        assert metadata["required"] == False, "secondTinNotification should not be required"
    
    def test_field_is_boolean_type(self):
        """Test that secondTinNotification has boolean data type."""
        mapper = FieldMapper("1099-DIV")
        metadata = mapper.get_field_metadata("secondTinNotification")
        
        assert metadata["data_type"] == "boolean", "secondTinNotification should be boolean type"
    
    def test_field_is_in_header_section(self):
        """Test that secondTinNotification is in header section."""
        mapper = FieldMapper("1099-DIV")
        metadata = mapper.get_field_metadata("secondTinNotification")
        
        assert metadata["section"] == "header", "secondTinNotification should be in header section"
    
    def test_field_has_no_irs_box(self):
        """Test that secondTinNotification has no IRS box number."""
        mapper = FieldMapper("1099-DIV")
        metadata = mapper.get_field_metadata("secondTinNotification")
        
        assert metadata["irs_box"] is None, "secondTinNotification should have no IRS box number"
    
    def test_field_has_clear_description(self):
        """Test that secondTinNotification has a clear description."""
        mapper = FieldMapper("1099-DIV")
        metadata = mapper.get_field_metadata("secondTinNotification")
        
        description = metadata["description"]
        description_lower = description.lower()
        assert description is not None, "Description should exist"
        assert len(description) > 0, "Description should not be empty"
        assert "2nd tin" in description_lower or "second tin" in description_lower, \
            "Description should mention 2nd TIN"
        assert "irs" in description_lower, "Description should mention IRS"
        assert "incorrect tin" in description_lower, "Description should mention incorrect TIN"
    
    def test_field_has_example_value(self):
        """Test that secondTinNotification has an example value."""
        mapper = FieldMapper("1099-DIV")
        metadata = mapper.get_field_metadata("secondTinNotification")
        
        example = metadata["example_value"]
        assert example is not None, "Example value should exist"
        assert example in ["true", "false"], "Example should be 'true' or 'false'"
    
    def test_is_required_field_returns_false(self):
        """Test that is_required_field returns False for secondTinNotification."""
        mapper = FieldMapper("1099-DIV")
        
        is_required = mapper.is_required_field("secondTinNotification")
        assert is_required == False, "secondTinNotification should not be required"
    
    def test_validate_required_fields_without_field(self):
        """Test that validate_required_fields doesn't require secondTinNotification."""
        mapper = FieldMapper("1099-DIV")
        
        # Minimal form data without secondTinNotification
        form_data = {
            "calendarYear": "2024",
            "payerName": "Test Corp",
            "payerTIN": "12-3456789",
            "recipientName": "John Doe",
            "recipientTIN": "123-45-6789",
            "totalOrdinaryDividends": "1000.00"
        }
        
        missing_fields = mapper.validate_required_fields(form_data)
        
        # secondTinNotification should NOT be in missing fields
        assert "secondTinNotification" not in missing_fields, \
            "secondTinNotification should not be required"
