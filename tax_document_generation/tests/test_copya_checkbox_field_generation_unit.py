"""
Unit tests for CopyA checkbox field name generation.

Tests the fix for the bug where checkbox field prefixes (c2_) were not
being replaced with (c1_) for CopyA, causing VOIDED and CORRECTED
checkboxes to fail rendering on CopyA.

Requirements: 1.1, 1.3, 4.2
"""

import pytest
from tax_document_generation.field_mapper import FieldMapper


class TestCheckboxPrefixReplacementForCopyA:
    """Test checkbox prefix replacement for CopyA variants."""
    
    def test_voided_checkbox_generates_correct_copya_field(self):
        """Test VOIDED checkbox field generates correct CopyA variant with c1_ prefix."""
        mapper = FieldMapper("1099-DIV")
        
        # Base field from canonical mapping
        base_field = "topmostSubform[0].Copy1[0].CopyHeader[0].c2_1[0]"
        
        # Generate variants
        variants = mapper._generate_copy_variants(base_field)
        
        # CopyA should have c1_ prefix (not c2_)
        expected_copya = "topmostSubform[0].CopyA[0].CopyHeader[0].c1_1[0]"
        assert variants[0] == expected_copya, f"Expected {expected_copya}, got {variants[0]}"
    
    def test_corrected_checkbox_generates_correct_copya_field(self):
        """Test CORRECTED checkbox field generates correct CopyA variant with c1_ prefix."""
        mapper = FieldMapper("1099-DIV")
        
        # Base field from canonical mapping
        base_field = "topmostSubform[0].Copy1[0].CopyHeader[0].c2_1[1]"
        
        # Generate variants
        variants = mapper._generate_copy_variants(base_field)
        
        # CopyA should have c1_ prefix (not c2_)
        expected_copya = "topmostSubform[0].CopyA[0].CopyHeader[0].c1_1[1]"
        assert variants[0] == expected_copya, f"Expected {expected_copya}, got {variants[0]}"
    
    def test_fatca_checkbox_generates_correct_copya_field(self):
        """Test FATCA checkbox field generates correct CopyA variant with c1_ prefix."""
        mapper = FieldMapper("1099-DIV")
        
        # FATCA checkbox field
        base_field = "topmostSubform[0].Copy1[0].RghtCol[0].TagCorrectingSubform[0].c2_3[0]"
        
        # Generate variants
        variants = mapper._generate_copy_variants(base_field)
        
        # CopyA should have c1_ prefix
        expected_copya = "topmostSubform[0].CopyA[0].RghtCol[0].TagCorrectingSubform[0].c1_3[0]"
        assert variants[0] == expected_copya


class TestTextFieldPrefixReplacementForCopyA:
    """Test text field prefix replacement for CopyA variants (existing behavior)."""
    
    def test_text_field_generates_correct_copya_field(self):
        """Test text field generates correct CopyA variant with f1_ prefix."""
        mapper = FieldMapper("1099-DIV")
        
        # Text field from canonical mapping
        base_field = "topmostSubform[0].Copy1[0].LeftCol[0].f2_2[0]"
        
        # Generate variants
        variants = mapper._generate_copy_variants(base_field)
        
        # CopyA should have f1_ prefix (not f2_)
        expected_copya = "topmostSubform[0].CopyA[0].LeftCol[0].f1_2[0]"
        assert variants[0] == expected_copya
    
    def test_calendar_year_field_generates_correct_copya_field(self):
        """Test calendar year field generates correct CopyA variant with f1_ prefix."""
        mapper = FieldMapper("1099-DIV")
        
        # Calendar year field
        base_field = "topmostSubform[0].Copy1[0].CopyHeader[0].CalendarYear[0].f2_1[0]"
        
        # Generate variants
        variants = mapper._generate_copy_variants(base_field)
        
        # CopyA should have f1_ prefix
        expected_copya = "topmostSubform[0].CopyA[0].CopyHeader[0].CalendarYear[0].f1_1[0]"
        assert variants[0] == expected_copya


class TestCopy1Copy2CopyBPreserveOriginalPrefixes:
    """Test that Copy1, Copy2, CopyB preserve original field prefixes."""
    
    def test_checkbox_fields_preserve_c2_prefix_for_copy1_copy2_copyb(self):
        """Test checkbox fields maintain c2_ prefix for Copy1, Copy2, CopyB."""
        mapper = FieldMapper("1099-DIV")
        
        # Checkbox field
        base_field = "topmostSubform[0].Copy1[0].CopyHeader[0].c2_1[0]"
        
        # Generate variants
        variants = mapper._generate_copy_variants(base_field)
        
        # Copy1, Copy2, CopyB should all have c2_ prefix
        assert "c2_1[0]" in variants[1], "Copy1 should preserve c2_ prefix"
        assert "c2_1[0]" in variants[2], "Copy2 should preserve c2_ prefix"
        assert "c2_1[0]" in variants[3], "CopyB should preserve c2_ prefix"
    
    def test_text_fields_preserve_f2_prefix_for_copy1_copy2_copyb(self):
        """Test text fields maintain f2_ prefix for Copy1, Copy2, CopyB."""
        mapper = FieldMapper("1099-DIV")
        
        # Text field
        base_field = "topmostSubform[0].Copy1[0].LeftCol[0].f2_2[0]"
        
        # Generate variants
        variants = mapper._generate_copy_variants(base_field)
        
        # Copy1, Copy2, CopyB should all have f2_ prefix
        assert "f2_2[0]" in variants[1], "Copy1 should preserve f2_ prefix"
        assert "f2_2[0]" in variants[2], "Copy2 should preserve f2_ prefix"
        assert "f2_2[0]" in variants[3], "CopyB should preserve f2_ prefix"


class TestMixedFieldTypes:
    """Test field names containing both text and checkbox patterns."""
    
    def test_field_with_both_f2_and_c2_patterns(self):
        """Test field name with both f2_ and c2_ patterns (edge case)."""
        mapper = FieldMapper("1099-DIV")
        
        # Hypothetical field with both patterns (unlikely but test edge case)
        base_field = "topmostSubform[0].Copy1[0].f2_1[0].c2_1[0]"
        
        # Generate variants
        variants = mapper._generate_copy_variants(base_field)
        
        # CopyA should replace both prefixes
        expected_copya = "topmostSubform[0].CopyA[0].f1_1[0].c1_1[0]"
        assert variants[0] == expected_copya
    
    def test_multiple_checkbox_prefixes_in_path(self):
        """Test field with multiple c2_ occurrences in path."""
        mapper = FieldMapper("1099-DIV")
        
        # Field with multiple c2_ patterns
        base_field = "topmostSubform[0].Copy1[0].c2_section[0].c2_1[0]"
        
        # Generate variants
        variants = mapper._generate_copy_variants(base_field)
        
        # CopyA should replace all c2_ occurrences
        expected_copya = "topmostSubform[0].CopyA[0].c1_section[0].c1_1[0]"
        assert variants[0] == expected_copya


class TestVariantOrder:
    """Test that variants are returned in correct order."""
    
    def test_variant_order_is_copya_copy1_copy2_copyb(self):
        """Test variants are returned in order: CopyA, Copy1, Copy2, CopyB."""
        mapper = FieldMapper("1099-DIV")
        
        base_field = "topmostSubform[0].Copy1[0].CopyHeader[0].c2_1[0]"
        
        variants = mapper._generate_copy_variants(base_field)
        
        assert len(variants) == 4
        assert "CopyA[0]" in variants[0]
        assert "Copy1[0]" in variants[1]
        assert "Copy2[0]" in variants[2]
        assert "CopyB[0]" in variants[3]
