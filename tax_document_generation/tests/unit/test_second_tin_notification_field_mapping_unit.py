"""
Unit tests for secondTinNotification field mapping.

Tests verify that the secondTinNotification field is correctly mapped to the
PDF checkbox field on CopyA only.

Requirements: 1.2, 3.1
"""

import pytest
from tax_document_generation.field_mapper import FieldMapper


class TestSecondTinNotificationFieldMapping:
    """Test secondTinNotification field mapping."""
    
    def test_field_maps_to_copya_leftcol(self):
        """Test that secondTinNotification maps to CopyA LeftCol checkbox."""
        mapper = FieldMapper("1099-DIV")
        
        # Get the base mapping using map_field method
        pdf_field = mapper.map_field("secondTinNotification")
        
        # Verify it maps to CopyA LeftCol c1_4[0]
        assert pdf_field is not None
        assert "CopyA" in pdf_field
        assert "LeftCol" in pdf_field
        assert "c1_4[0]" in pdf_field
        assert pdf_field == "topmostSubform[0].CopyA[0].LeftCol[0].c1_4[0]"
    
    def test_field_is_in_leftcol_section(self):
        """Test that field is in the LeftCol section."""
        mapper = FieldMapper("1099-DIV")
        pdf_field = mapper.map_field("secondTinNotification")
        
        assert "LeftCol[0]" in pdf_field
    
    def test_field_uses_c1_4_pattern(self):
        """Test that field uses c1_4[0] pattern (not c1_3[0] which is FATCA)."""
        mapper = FieldMapper("1099-DIV")
        pdf_field = mapper.map_field("secondTinNotification")
        
        # Should use c1_4[0], not c1_3[0] (which is FATCA)
        assert "c1_4[0]" in pdf_field
        assert "c1_3[0]" not in pdf_field
    
    def test_field_is_different_from_fatca(self):
        """Test that secondTinNotification is different from fatcaFilingRequirement."""
        mapper = FieldMapper("1099-DIV")
        
        second_tin_field = mapper.map_field("secondTinNotification")
        fatca_field = mapper.map_field("fatcaFilingRequirement")
        
        # They should be different fields
        assert second_tin_field != fatca_field
        
        # FATCA should be in RghtCol TagCorrectingSubform
        assert "RghtCol" in fatca_field
        assert "TagCorrectingSubform" in fatca_field
        
        # secondTinNotification should be in LeftCol
        assert "LeftCol" in second_tin_field
