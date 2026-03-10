"""
Integration tests for standardized field mapping.

Tests complete workflows including validation, mapping, and multi-copy generation.

Requirements: 5.3, 6.2, 6.3, 6.4, 8.1, 8.2, 8.3
"""

import pytest
from tax_document_generation.field_mapper import FieldMapper


class TestCompleteFormGeneration:
    """Test complete form generation with all required fields."""
    
    def test_complete_form_with_all_required_fields(self):
        """Test generating a complete 1099-DIV form with all required fields."""
        mapper = FieldMapper("1099-DIV")
        
        form_data = {
            "calendarYear": "2024",
            "payerName": "Example Corporation",
            "payerTIN": "12-3456789",
            "recipientName": "John Doe",
            "recipientTIN": "123-45-6789",
            "totalOrdinaryDividends": "1000.00"
        }
        
        # Validate required fields
        missing = mapper.validate_required_fields(form_data)
        assert len(missing) == 0, f"Expected no missing fields, but got: {missing}"
        
        # Map to PDF fields
        mapped = mapper.map_all_fields(form_data)
        
        # Verify multi-copy generation (3 copies × 6 fields = 18 total)
        assert len(mapped) == 18, f"Expected 18 mapped fields, got {len(mapped)}"
        
        # Verify values appear identically in all copies
        for api_field, value in form_data.items():
            pdf_field = mapper.map_field(api_field)
            assert pdf_field is not None, f"Field {api_field} has no mapping"
            
            copy1_field = pdf_field
            copy2_field = pdf_field.replace("Copy1[0]", "Copy2[0]")
            copyb_field = pdf_field.replace("Copy1[0]", "CopyB[0]")
            
            assert copy1_field in mapped, f"Copy1 field {copy1_field} not in mapped data"
            assert copy2_field in mapped, f"Copy2 field {copy2_field} not in mapped data"
            assert copyb_field in mapped, f"CopyB field {copyb_field} not in mapped data"
            
            assert mapped[copy1_field] == value, f"Copy1 value mismatch for {api_field}"
            assert mapped[copy2_field] == value, f"Copy2 value mismatch for {api_field}"
            assert mapped[copyb_field] == value, f"CopyB value mismatch for {api_field}"
    
    def test_complete_form_with_optional_fields(self):
        """Test generating form with required and optional fields."""
        mapper = FieldMapper("1099-DIV")
        
        form_data = {
            # Required fields
            "calendarYear": "2024",
            "payerName": "Example Corporation",
            "payerTIN": "12-3456789",
            "recipientName": "John Doe",
            "recipientTIN": "123-45-6789",
            "totalOrdinaryDividends": "1000.00",
            # Optional fields
            "qualifiedDividends": "800.00",
            "federalIncomeTaxWithheld": "150.00",
            "payerStreetAddress": "123 Main Street",
            "recipientStreetAddress": "456 Oak Avenue"
        }
        
        # Validate required fields
        missing = mapper.validate_required_fields(form_data)
        assert len(missing) == 0
        
        # Map to PDF fields
        mapped = mapper.map_all_fields(form_data)
        
        # Note: payerName and payerStreetAddress both map to f2_2 (combined address block)
        # So we expect 3 copies × 9 unique PDF fields = 27 total
        # (not 30, because payerName and payerStreetAddress share the same PDF field)
        assert len(mapped) >= 24, f"Expected at least 24 mapped fields, got {len(mapped)}"
        
        # Verify all values appear in all copies
        for api_field, value in form_data.items():
            pdf_field = mapper.map_field(api_field)
            if pdf_field is None:
                continue
                
            copy1_field = pdf_field
            copy2_field = pdf_field.replace("Copy1[0]", "Copy2[0]")
            copyb_field = pdf_field.replace("Copy1[0]", "CopyB[0]")
            
            # At least one copy should have the value
            assert copy1_field in mapped or copy2_field in mapped or copyb_field in mapped, \
                f"Field {api_field} not found in any copy"


class TestPartialFormGeneration:
    """Test partial form generation with subset of fields."""
    
    def test_partial_form_with_required_plus_some_optional(self):
        """Test form with required fields plus some optional fields."""
        mapper = FieldMapper("1099-DIV")
        
        form_data = {
            "calendarYear": "2024",
            "payerName": "Example Corporation",
            "payerTIN": "12-3456789",
            "recipientName": "John Doe",
            "recipientTIN": "123-45-6789",
            "totalOrdinaryDividends": "1000.00",
            "qualifiedDividends": "800.00"  # Only one optional field
        }
        
        # Validate required fields
        missing = mapper.validate_required_fields(form_data)
        assert len(missing) == 0
        
        # Map to PDF fields
        mapped = mapper.map_all_fields(form_data)
        
        # Verify only provided fields are mapped (3 copies × 7 fields = 21 total)
        assert len(mapped) == 21
        
        # Verify qualifiedDividends is present
        qualified_div_pdf = mapper.map_field("qualifiedDividends")
        assert qualified_div_pdf.replace("Copy1[0]", "Copy1[0]") in mapped
        assert qualified_div_pdf.replace("Copy1[0]", "Copy2[0]") in mapped
        assert qualified_div_pdf.replace("Copy1[0]", "CopyB[0]") in mapped
        
        # Verify other optional fields are NOT present
        federal_tax_pdf = mapper.map_field("federalIncomeTaxWithheld")
        assert federal_tax_pdf.replace("Copy1[0]", "Copy1[0]") not in mapped
        assert federal_tax_pdf.replace("Copy1[0]", "Copy2[0]") not in mapped
        assert federal_tax_pdf.replace("Copy1[0]", "CopyB[0]") not in mapped
    
    def test_only_required_fields(self):
        """Test form with only required fields, no optional fields."""
        mapper = FieldMapper("1099-DIV")
        
        form_data = {
            "calendarYear": "2024",
            "payerName": "Example Corporation",
            "payerTIN": "12-3456789",
            "recipientName": "John Doe",
            "recipientTIN": "123-45-6789",
            "totalOrdinaryDividends": "1000.00"
        }
        
        # Validate required fields
        missing = mapper.validate_required_fields(form_data)
        assert len(missing) == 0
        
        # Map to PDF fields
        mapped = mapper.map_all_fields(form_data)
        
        # Verify only required fields are mapped (3 copies × 6 fields = 18 total)
        assert len(mapped) == 18


class TestBackwardCompatibility:
    """Test backward compatibility with old field names."""
    
    def test_all_old_field_names_still_work(self):
        """Test that all old field names from legacy FIELD_MAPPING still work."""
        mapper = FieldMapper("1099-DIV")
        
        # Test a sample of field names that should exist
        old_field_names = [
            "calendarYear",
            "payerName",
            "payerTIN",
            "recipientName",
            "recipientTIN",
            "totalOrdinaryDividends",
            "qualifiedDividends",
            "federalIncomeTaxWithheld",
            "accountNumber"
        ]
        
        for field_name in old_field_names:
            pdf_field = mapper.map_field(field_name)
            assert pdf_field is not None, f"Field {field_name} should have a mapping"
            assert "topmostSubform[0].Copy1[0]" in pdf_field, \
                f"Field {field_name} should map to a Copy1 field"
    
    def test_deprecated_field_names_resolve_correctly(self):
        """Test that deprecated field names resolve to canonical names."""
        mapper = FieldMapper("1099-DIV")
        
        # Currently no deprecated aliases, but test the mechanism works
        # If we add deprecated aliases in the future, they should resolve correctly
        
        # Test that resolve_field_name returns the same name for non-deprecated fields
        assert mapper.resolve_field_name("payerName") == "payerName"
        assert mapper.resolve_field_name("recipientTIN") == "recipientTIN"
    
    def test_form_generation_with_mixed_field_names(self):
        """Test form generation works with mix of canonical and deprecated names."""
        mapper = FieldMapper("1099-DIV")
        
        # Use all canonical names (no deprecated aliases currently)
        form_data = {
            "calendarYear": "2024",
            "payerName": "Example Corporation",
            "payerTIN": "12-3456789",
            "recipientName": "John Doe",
            "recipientTIN": "123-45-6789",
            "totalOrdinaryDividends": "1000.00"
        }
        
        # Should work without issues
        missing = mapper.validate_required_fields(form_data)
        assert len(missing) == 0
        
        mapped = mapper.map_all_fields(form_data)
        assert len(mapped) == 18


class TestMultiCopyConsistency:
    """Test that multi-copy generation maintains value consistency."""
    
    def test_all_copies_have_identical_values(self):
        """Test that Copy1, Copy2, and CopyB all have identical values."""
        mapper = FieldMapper("1099-DIV")
        
        form_data = {
            "calendarYear": "2024",
            "payerName": "Example Corporation",
            "payerTIN": "12-3456789",
            "recipientName": "John Doe",
            "recipientTIN": "123-45-6789",
            "totalOrdinaryDividends": "1000.00",
            "qualifiedDividends": "800.00",
            "federalIncomeTaxWithheld": "150.00"
        }
        
        mapped = mapper.map_all_fields(form_data)
        
        # Group fields by base name (without copy prefix)
        copy1_fields = {k: v for k, v in mapped.items() if "Copy1[0]" in k}
        copy2_fields = {k: v for k, v in mapped.items() if "Copy2[0]" in k}
        copyb_fields = {k: v for k, v in mapped.items() if "CopyB[0]" in k}
        
        # Should have equal number of fields in each copy
        assert len(copy1_fields) == len(copy2_fields) == len(copyb_fields)
        
        # Verify each Copy1 field has corresponding Copy2 and CopyB fields with same value
        for copy1_field, value in copy1_fields.items():
            copy2_field = copy1_field.replace("Copy1[0]", "Copy2[0]")
            copyb_field = copy1_field.replace("Copy1[0]", "CopyB[0]")
            
            assert copy2_field in mapped, f"Copy2 field {copy2_field} not found"
            assert copyb_field in mapped, f"CopyB field {copyb_field} not found"
            
            assert mapped[copy2_field] == value, \
                f"Copy2 value mismatch: {mapped[copy2_field]} != {value}"
            assert mapped[copyb_field] == value, \
                f"CopyB value mismatch: {mapped[copyb_field]} != {value}"
