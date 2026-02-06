"""
Unit tests for VOIDED and CORRECTED checkbox field mappings.

This module tests that the voided and corrected fields are correctly mapped
to their PDF field names and that copy variants are generated for all copies.

Requirements: 1.1, 1.4, 2.1, 2.4, 3.3, 3.4, 3.5, 3.6
"""

import pytest
from tax_document_generation.field_mapper import FieldMapper


class TestVoidedFieldMapping:
    """Test voided checkbox field mapping."""
    
    def test_voided_maps_to_correct_copy1_field(self):
        """Test that voided field maps to correct Copy1 PDF field name."""
        mapper = FieldMapper("1099-DIV")
        pdf_field = mapper.map_field("voided")
        
        expected = "topmostSubform[0].Copy1[0].CopyHeader[0].c2_1[0]"
        assert pdf_field == expected, f"Expected {expected}, got {pdf_field}"
    
    def test_voided_generates_copya_variant(self):
        """Test that voided field generates CopyA variant."""
        mapper = FieldMapper("1099-DIV")
        form_data = {"voided": True}
        mapped_data = mapper.map_all_fields(form_data)
        
        copya_field = "topmostSubform[0].CopyA[0].CopyHeader[0].c1_1[0]"
        assert copya_field in mapped_data, f"CopyA variant not found: {copya_field}"
        assert mapped_data[copya_field] == True
    
    def test_voided_generates_copy1_variant(self):
        """Test that voided field generates Copy1 variant."""
        mapper = FieldMapper("1099-DIV")
        form_data = {"voided": True}
        mapped_data = mapper.map_all_fields(form_data)
        
        copy1_field = "topmostSubform[0].Copy1[0].CopyHeader[0].c2_1[0]"
        assert copy1_field in mapped_data, f"Copy1 variant not found: {copy1_field}"
        assert mapped_data[copy1_field] == True
    
    def test_voided_generates_copy2_variant(self):
        """Test that voided field generates Copy2 variant."""
        mapper = FieldMapper("1099-DIV")
        form_data = {"voided": True}
        mapped_data = mapper.map_all_fields(form_data)
        
        copy2_field = "topmostSubform[0].Copy2[0].CopyHeader[0].c2_1[0]"
        assert copy2_field in mapped_data, f"Copy2 variant not found: {copy2_field}"
        assert mapped_data[copy2_field] == True
    
    def test_voided_generates_copyb_variant(self):
        """Test that voided field generates CopyB variant (will be silently skipped in PDF)."""
        mapper = FieldMapper("1099-DIV")
        form_data = {"voided": True}
        mapped_data = mapper.map_all_fields(form_data)
        
        # CopyB doesn't have VOIDED checkbox in the PDF, but field mapper generates the name
        copyb_field = "topmostSubform[0].CopyB[0].CopyHeader[0].c2_1[0]"
        assert copyb_field in mapped_data, f"CopyB variant not found: {copyb_field}"
        assert mapped_data[copyb_field] == True


class TestCorrectedFieldMapping:
    """Test corrected checkbox field mapping."""
    
    def test_corrected_maps_to_correct_copy1_field(self):
        """Test that corrected field maps to correct Copy1 PDF field name."""
        mapper = FieldMapper("1099-DIV")
        pdf_field = mapper.map_field("corrected")
        
        expected = "topmostSubform[0].Copy1[0].CopyHeader[0].c2_1[1]"
        assert pdf_field == expected, f"Expected {expected}, got {pdf_field}"
    
    def test_corrected_generates_copya_variant(self):
        """Test that corrected field generates CopyA variant."""
        mapper = FieldMapper("1099-DIV")
        form_data = {"corrected": True}
        mapped_data = mapper.map_all_fields(form_data)
        
        copya_field = "topmostSubform[0].CopyA[0].CopyHeader[0].c1_1[1]"
        assert copya_field in mapped_data, f"CopyA variant not found: {copya_field}"
        assert mapped_data[copya_field] == True
    
    def test_corrected_generates_copy1_variant(self):
        """Test that corrected field generates Copy1 variant."""
        mapper = FieldMapper("1099-DIV")
        form_data = {"corrected": True}
        mapped_data = mapper.map_all_fields(form_data)
        
        copy1_field = "topmostSubform[0].Copy1[0].CopyHeader[0].c2_1[1]"
        assert copy1_field in mapped_data, f"Copy1 variant not found: {copy1_field}"
        assert mapped_data[copy1_field] == True
    
    def test_corrected_generates_copy2_variant(self):
        """Test that corrected field generates Copy2 variant."""
        mapper = FieldMapper("1099-DIV")
        form_data = {"corrected": True}
        mapped_data = mapper.map_all_fields(form_data)
        
        copy2_field = "topmostSubform[0].Copy2[0].CopyHeader[0].c2_1[1]"
        assert copy2_field in mapped_data, f"Copy2 variant not found: {copy2_field}"
        assert mapped_data[copy2_field] == True
    
    def test_corrected_generates_copyb_variant(self):
        """Test that corrected field generates CopyB variant."""
        mapper = FieldMapper("1099-DIV")
        form_data = {"corrected": True}
        mapped_data = mapper.map_all_fields(form_data)
        
        # CopyB has CORRECTED checkbox (c2_1[1] on CopyB is CORRECTED)
        copyb_field = "topmostSubform[0].CopyB[0].CopyHeader[0].c2_1[1]"
        assert copyb_field in mapped_data, f"CopyB variant not found: {copyb_field}"
        assert mapped_data[copyb_field] == True


class TestBothCheckboxesMapping:
    """Test mapping when both checkboxes are provided."""
    
    def test_both_checkboxes_map_correctly(self):
        """Test that both voided and corrected map to correct fields."""
        mapper = FieldMapper("1099-DIV")
        form_data = {"voided": True, "corrected": True}
        mapped_data = mapper.map_all_fields(form_data)
        
        # Check Copy1 fields
        voided_copy1 = "topmostSubform[0].Copy1[0].CopyHeader[0].c2_1[0]"
        corrected_copy1 = "topmostSubform[0].Copy1[0].CopyHeader[0].c2_1[1]"
        
        assert voided_copy1 in mapped_data
        assert corrected_copy1 in mapped_data
        assert mapped_data[voided_copy1] == True
        assert mapped_data[corrected_copy1] == True
    
    def test_false_values_map_correctly(self):
        """Test that false values are correctly mapped."""
        mapper = FieldMapper("1099-DIV")
        form_data = {"voided": False, "corrected": False}
        mapped_data = mapper.map_all_fields(form_data)
        
        # Check Copy1 fields
        voided_copy1 = "topmostSubform[0].Copy1[0].CopyHeader[0].c2_1[0]"
        corrected_copy1 = "topmostSubform[0].Copy1[0].CopyHeader[0].c2_1[1]"
        
        assert voided_copy1 in mapped_data
        assert corrected_copy1 in mapped_data
        assert mapped_data[voided_copy1] == False
        assert mapped_data[corrected_copy1] == False
