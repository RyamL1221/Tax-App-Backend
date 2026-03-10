"""
Unit tests for VOIDED and CORRECTED checkbox field metadata.

This module tests that the metadata for voided and corrected fields
is correctly structured and contains the expected values.

Requirements: 1.1, 2.1, 5.1
"""

import pytest
from tax_document_generation.field_mappings.field_metadata import FIELD_METADATA


class TestVoidedMetadata:
    """Test voided field metadata."""
    
    def test_voided_metadata_exists(self):
        """Test that voided field has metadata entry."""
        assert "voided" in FIELD_METADATA, "voided field metadata not found"
    
    def test_voided_is_optional(self):
        """Test that voided field is marked as optional."""
        metadata = FIELD_METADATA["voided"]
        assert metadata["required"] == False, "voided should be optional"
    
    def test_voided_data_type_is_boolean(self):
        """Test that voided field data type is boolean."""
        metadata = FIELD_METADATA["voided"]
        assert metadata["data_type"] == "boolean", "voided data type should be boolean"
    
    def test_voided_section_is_header(self):
        """Test that voided field section is header."""
        metadata = FIELD_METADATA["voided"]
        assert metadata["section"] == "header", "voided section should be header"
    
    def test_voided_has_no_irs_box(self):
        """Test that voided field has no IRS box number."""
        metadata = FIELD_METADATA["voided"]
        assert metadata["irs_box"] is None, "voided should not have IRS box number"
    
    def test_voided_has_description(self):
        """Test that voided field has a description."""
        metadata = FIELD_METADATA["voided"]
        assert "description" in metadata
        assert len(metadata["description"]) > 0
        assert "VOIDED" in metadata["description"]
    
    def test_voided_has_example_value(self):
        """Test that voided field has an example value."""
        metadata = FIELD_METADATA["voided"]
        assert "example_value" in metadata
        assert metadata["example_value"] == "true"


class TestCorrectedMetadata:
    """Test corrected field metadata."""
    
    def test_corrected_metadata_exists(self):
        """Test that corrected field has metadata entry."""
        assert "corrected" in FIELD_METADATA, "corrected field metadata not found"
    
    def test_corrected_is_optional(self):
        """Test that corrected field is marked as optional."""
        metadata = FIELD_METADATA["corrected"]
        assert metadata["required"] == False, "corrected should be optional"
    
    def test_corrected_data_type_is_boolean(self):
        """Test that corrected field data type is boolean."""
        metadata = FIELD_METADATA["corrected"]
        assert metadata["data_type"] == "boolean", "corrected data type should be boolean"
    
    def test_corrected_section_is_header(self):
        """Test that corrected field section is header."""
        metadata = FIELD_METADATA["corrected"]
        assert metadata["section"] == "header", "corrected section should be header"
    
    def test_corrected_has_no_irs_box(self):
        """Test that corrected field has no IRS box number."""
        metadata = FIELD_METADATA["corrected"]
        assert metadata["irs_box"] is None, "corrected should not have IRS box number"
    
    def test_corrected_has_description(self):
        """Test that corrected field has a description."""
        metadata = FIELD_METADATA["corrected"]
        assert "description" in metadata
        assert len(metadata["description"]) > 0
        assert "CORRECTED" in metadata["description"]
    
    def test_corrected_has_example_value(self):
        """Test that corrected field has an example value."""
        metadata = FIELD_METADATA["corrected"]
        assert "example_value" in metadata
        assert metadata["example_value"] == "true"


class TestMetadataStructure:
    """Test metadata structure for both fields."""
    
    def test_voided_metadata_has_all_required_keys(self):
        """Test that voided metadata has all required keys."""
        metadata = FIELD_METADATA["voided"]
        required_keys = [
            "required", "irs_box", "description", "section",
            "data_type", "max_length", "validation_pattern", "example_value"
        ]
        
        for key in required_keys:
            assert key in metadata, f"voided metadata missing key: {key}"
    
    def test_corrected_metadata_has_all_required_keys(self):
        """Test that corrected metadata has all required keys."""
        metadata = FIELD_METADATA["corrected"]
        required_keys = [
            "required", "irs_box", "description", "section",
            "data_type", "max_length", "validation_pattern", "example_value"
        ]
        
        for key in required_keys:
            assert key in metadata, f"corrected metadata missing key: {key}"
    
    def test_both_fields_have_no_max_length(self):
        """Test that both fields have no max_length (boolean fields)."""
        assert FIELD_METADATA["voided"]["max_length"] is None
        assert FIELD_METADATA["corrected"]["max_length"] is None
    
    def test_both_fields_have_no_validation_pattern(self):
        """Test that both fields have no validation_pattern (boolean fields)."""
        assert FIELD_METADATA["voided"]["validation_pattern"] is None
        assert FIELD_METADATA["corrected"]["validation_pattern"] is None
