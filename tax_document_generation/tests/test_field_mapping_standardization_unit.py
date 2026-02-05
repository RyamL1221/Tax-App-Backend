"""
Unit tests for standardized field mapping configuration.

Tests specific field mappings, edge cases, validation, and metadata access.

Requirements: 1.1, 2.1, 2.4, 2.5, 6.1, 6.2, 6.3, 6.4
"""

import pytest
from tax_document_generation.field_mapper import FieldMapper


class TestSpecificFieldMappings:
    """Test that specific fields map to expected PDF field names."""
    
    def test_payer_name_mapping(self):
        """Test that payerName maps to correct PDF field."""
        mapper = FieldMapper("1099-DIV")
        pdf_field = mapper.map_field("payerName")
        assert pdf_field == "topmostSubform[0].Copy1[0].LeftCol[0].f2_2[0]"
    
    def test_payer_tin_mapping(self):
        """Test that payerTIN maps to correct PDF field."""
        mapper = FieldMapper("1099-DIV")
        pdf_field = mapper.map_field("payerTIN")
        assert pdf_field == "topmostSubform[0].Copy1[0].LeftCol[0].f2_3[0]"
    
    def test_recipient_name_mapping(self):
        """Test that recipientName maps to correct PDF field."""
        mapper = FieldMapper("1099-DIV")
        pdf_field = mapper.map_field("recipientName")
        assert pdf_field == "topmostSubform[0].Copy1[0].LeftCol[0].f2_5[0]"
    
    def test_recipient_tin_mapping(self):
        """Test that recipientTIN maps to correct PDF field."""
        mapper = FieldMapper("1099-DIV")
        pdf_field = mapper.map_field("recipientTIN")
        assert pdf_field == "topmostSubform[0].Copy1[0].LeftCol[0].f2_4[0]"
    
    def test_total_ordinary_dividends_mapping(self):
        """Test that totalOrdinaryDividends maps to correct PDF field (Box 1a)."""
        mapper = FieldMapper("1099-DIV")
        pdf_field = mapper.map_field("totalOrdinaryDividends")
        assert pdf_field == "topmostSubform[0].Copy1[0].RghtCol[0].f2_9[0]"
    
    def test_qualified_dividends_mapping(self):
        """Test that qualifiedDividends maps to correct PDF field (Box 1b)."""
        mapper = FieldMapper("1099-DIV")
        pdf_field = mapper.map_field("qualifiedDividends")
        assert pdf_field == "topmostSubform[0].Copy1[0].RghtCol[0].f2_10[0]"
    
    def test_federal_income_tax_withheld_mapping(self):
        """Test that federalIncomeTaxWithheld maps to correct PDF field (Box 4)."""
        mapper = FieldMapper("1099-DIV")
        pdf_field = mapper.map_field("federalIncomeTaxWithheld")
        assert pdf_field == "topmostSubform[0].Copy1[0].RghtCol[0].f2_18[0]"


class TestEdgeCases:
    """Test edge cases for field mapping."""
    
    def test_empty_form_data(self):
        """Test that empty form data returns empty mapping."""
        mapper = FieldMapper("1099-DIV")
        result = mapper.map_all_fields({})
        assert result == {}
    
    def test_single_field_form_data(self):
        """Test mapping with single field."""
        mapper = FieldMapper("1099-DIV")
        form_data = {"payerName": "Test Corp"}
        result = mapper.map_all_fields(form_data)
        
        # Should generate 3 copies (Copy1, Copy2, CopyB)
        assert len(result) == 3
        
        # All copies should have the same value
        assert "topmostSubform[0].Copy1[0].LeftCol[0].f2_2[0]" in result
        assert "topmostSubform[0].Copy2[0].LeftCol[0].f2_2[0]" in result
        assert "topmostSubform[0].CopyB[0].LeftCol[0].f2_2[0]" in result
        
        assert result["topmostSubform[0].Copy1[0].LeftCol[0].f2_2[0]"] == "Test Corp"
        assert result["topmostSubform[0].Copy2[0].LeftCol[0].f2_2[0]"] == "Test Corp"
        assert result["topmostSubform[0].CopyB[0].LeftCol[0].f2_2[0]"] == "Test Corp"
    
    def test_all_required_fields(self):
        """Test mapping with all required fields."""
        mapper = FieldMapper("1099-DIV")
        form_data = {
            "calendarYear": "2024",
            "payerName": "Example Corporation",
            "payerTIN": "12-3456789",
            "recipientName": "John Doe",
            "recipientTIN": "123-45-6789",
            "totalOrdinaryDividends": "1000.00"
        }
        result = mapper.map_all_fields(form_data)
        
        # Should generate 3 copies for each of 6 fields = 18 total
        assert len(result) == 18
        
        # Verify all values are present
        for field_name, value in form_data.items():
            pdf_field = mapper.map_field(field_name)
            assert pdf_field is not None
            
            # Check all three copies
            copy1_field = pdf_field
            copy2_field = pdf_field.replace("Copy1[0]", "Copy2[0]")
            copyb_field = pdf_field.replace("Copy1[0]", "CopyB[0]")
            
            assert result[copy1_field] == value
            assert result[copy2_field] == value
            assert result[copyb_field] == value


class TestValidation:
    """Test validation methods."""
    
    def test_missing_required_fields_detected(self):
        """Test that missing required fields are detected."""
        mapper = FieldMapper("1099-DIV")
        form_data = {"payerName": "Test Corp"}  # Missing other required fields
        
        missing = mapper.validate_required_fields(form_data)
        
        # Should detect missing required fields
        assert "calendarYear" in missing
        assert "payerTIN" in missing
        assert "recipientName" in missing
        assert "recipientTIN" in missing
        assert "totalOrdinaryDividends" in missing
        
        # Should not include the provided field
        assert "payerName" not in missing
    
    def test_all_required_fields_present(self):
        """Test that form with all required fields passes validation."""
        mapper = FieldMapper("1099-DIV")
        form_data = {
            "calendarYear": "2024",
            "payerName": "Example Corporation",
            "payerTIN": "12-3456789",
            "recipientName": "John Doe",
            "recipientTIN": "123-45-6789",
            "totalOrdinaryDividends": "1000.00"
        }
        
        missing = mapper.validate_required_fields(form_data)
        
        # Should have no missing fields
        assert len(missing) == 0
    
    def test_optional_fields_dont_affect_validation(self):
        """Test that optional fields don't affect validation."""
        mapper = FieldMapper("1099-DIV")
        form_data = {
            "calendarYear": "2024",
            "payerName": "Example Corporation",
            "payerTIN": "12-3456789",
            "recipientName": "John Doe",
            "recipientTIN": "123-45-6789",
            "totalOrdinaryDividends": "1000.00",
            "qualifiedDividends": "800.00",  # Optional field
            "federalIncomeTaxWithheld": "150.00"  # Optional field
        }
        
        missing = mapper.validate_required_fields(form_data)
        
        # Should have no missing fields
        assert len(missing) == 0


class TestMetadataAccess:
    """Test metadata access methods."""
    
    def test_get_field_metadata_valid_field(self):
        """Test get_field_metadata() with valid field names."""
        mapper = FieldMapper("1099-DIV")
        
        metadata = mapper.get_field_metadata("payerName")
        assert metadata is not None
        assert metadata["required"] is True
        assert metadata["section"] == "payer"
        assert metadata["data_type"] == "string"
        
        metadata = mapper.get_field_metadata("qualifiedDividends")
        assert metadata is not None
        assert metadata["required"] is False
        assert metadata["irs_box"] == "1b"
        assert metadata["section"] == "dividends"
    
    def test_get_field_metadata_invalid_field(self):
        """Test get_field_metadata() with invalid field names."""
        mapper = FieldMapper("1099-DIV")
        
        metadata = mapper.get_field_metadata("nonexistentField")
        assert metadata is None
    
    def test_is_required_field_for_required_fields(self):
        """Test is_required_field() for required fields."""
        mapper = FieldMapper("1099-DIV")
        
        assert mapper.is_required_field("calendarYear") is True
        assert mapper.is_required_field("payerName") is True
        assert mapper.is_required_field("payerTIN") is True
        assert mapper.is_required_field("recipientName") is True
        assert mapper.is_required_field("recipientTIN") is True
        assert mapper.is_required_field("totalOrdinaryDividends") is True
    
    def test_is_required_field_for_optional_fields(self):
        """Test is_required_field() for optional fields."""
        mapper = FieldMapper("1099-DIV")
        
        assert mapper.is_required_field("qualifiedDividends") is False
        assert mapper.is_required_field("payerStreetAddress") is False
        assert mapper.is_required_field("federalIncomeTaxWithheld") is False
        assert mapper.is_required_field("accountNumber") is False
    
    def test_is_required_field_for_invalid_field(self):
        """Test is_required_field() for invalid field names."""
        mapper = FieldMapper("1099-DIV")
        
        assert mapper.is_required_field("nonexistentField") is False
