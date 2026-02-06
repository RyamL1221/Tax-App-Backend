"""
Unit tests for secondTinNotification copy variant generation.

Tests verify that the secondTinNotification field only appears on CopyA
(not on Copy1, Copy2, or CopyB) since it's a CopyA-only field.

Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2
"""

import pytest
from tax_document_generation.field_mapper import FieldMapper


class TestSecondTinNotificationCopyVariants:
    """Test secondTinNotification copy variant generation."""
    
    def test_field_only_on_copya(self):
        """Test that secondTinNotification only appears on CopyA."""
        mapper = FieldMapper("1099-DIV")
        form_data = {"secondTinNotification": True}
        mapped_data = mapper.map_all_fields(form_data)
        
        # Should only have CopyA field (no Copy1, Copy2, CopyB variants)
        copya_field = "topmostSubform[0].CopyA[0].LeftCol[0].c1_4[0]"
        assert copya_field in mapped_data, f"CopyA field not found: {copya_field}"
        assert mapped_data[copya_field] == True
        
        # Verify only one field was generated (CopyA only)
        assert len(mapped_data) == 1, f"Expected 1 field, got {len(mapped_data)}"
    
    def test_no_copy1_variant(self):
        """Test that secondTinNotification does not generate Copy1 variant."""
        mapper = FieldMapper("1099-DIV")
        form_data = {"secondTinNotification": True}
        mapped_data = mapper.map_all_fields(form_data)
        
        # Copy1 variant should NOT exist
        copy1_field = "topmostSubform[0].Copy1[0].LeftCol[0].c2_4[0]"
        assert copy1_field not in mapped_data, f"Copy1 variant should not exist: {copy1_field}"
    
    def test_no_copy2_variant(self):
        """Test that secondTinNotification does not generate Copy2 variant."""
        mapper = FieldMapper("1099-DIV")
        form_data = {"secondTinNotification": True}
        mapped_data = mapper.map_all_fields(form_data)
        
        # Copy2 variant should NOT exist
        copy2_field = "topmostSubform[0].Copy2[0].LeftCol[0].c2_4[0]"
        assert copy2_field not in mapped_data, f"Copy2 variant should not exist: {copy2_field}"
    
    def test_no_copyb_variant(self):
        """Test that secondTinNotification does not generate CopyB variant."""
        mapper = FieldMapper("1099-DIV")
        form_data = {"secondTinNotification": True}
        mapped_data = mapper.map_all_fields(form_data)
        
        # CopyB variant should NOT exist
        copyb_field = "topmostSubform[0].CopyB[0].LeftCol[0].c2_4[0]"
        assert copyb_field not in mapped_data, f"CopyB variant should not exist: {copyb_field}"
    
    def test_false_value_only_on_copya(self):
        """Test that false value is also only on CopyA."""
        mapper = FieldMapper("1099-DIV")
        form_data = {"secondTinNotification": False}
        mapped_data = mapper.map_all_fields(form_data)
        
        # Should only have CopyA field with false value
        copya_field = "topmostSubform[0].CopyA[0].LeftCol[0].c1_4[0]"
        assert copya_field in mapped_data
        assert mapped_data[copya_field] == False
        assert len(mapped_data) == 1
    
    def test_copya_uses_c1_4_pattern(self):
        """Test that CopyA field uses c1_4[0] pattern."""
        mapper = FieldMapper("1099-DIV")
        form_data = {"secondTinNotification": True}
        mapped_data = mapper.map_all_fields(form_data)
        
        # Verify CopyA uses c1_4[0] pattern (not c2_4[0])
        copya_field = "topmostSubform[0].CopyA[0].LeftCol[0].c1_4[0]"
        assert copya_field in mapped_data
        
        # Verify no c2_4[0] pattern exists
        for field_name in mapped_data.keys():
            assert "c2_4[0]" not in field_name, f"Should not have c2_4[0] pattern: {field_name}"
