"""
Unit tests for field name transformation in FieldMapper.

These tests verify the _generate_copy_variants() method handles various
edge cases correctly.

Feature: multi-page-form-filling
"""

import pytest
from tax_document_generation.field_mapper import FieldMapper


class TestFieldNameTransformationUnit:
    """Unit tests for field name transformation edge cases."""
    
    def test_generate_copy_variants_with_valid_copy1_field(self):
        """
        **Validates: Requirements 2.1, 2.2, 2.3**
        
        Verify that a valid Copy1 field name generates three variants.
        
        This test verifies that:
        1. Copy1 field name is preserved
        2. Copy2 variant is generated correctly
        3. CopyB variant is generated correctly
        4. All three variants are returned
        """
        # Initialize the field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Test with a typical Copy1 field name
        copy1_field = "topmostSubform[0].Copy1[0].LeftCol[0].f2_2[0]"
        
        # Generate variants
        variants = mapper._generate_copy_variants(copy1_field)
        
        # Verify we get exactly 3 variants
        assert len(variants) == 3, \
            "Should generate exactly 3 variants (Copy1, Copy2, CopyB)"
        
        # Verify Copy1 is preserved
        assert variants[0] == "topmostSubform[0].Copy1[0].LeftCol[0].f2_2[0]", \
            "First variant should be the original Copy1 field"
        
        # Verify Copy2 is generated correctly
        assert variants[1] == "topmostSubform[0].Copy2[0].LeftCol[0].f2_2[0]", \
            "Second variant should have Copy2[0] instead of Copy1[0]"
        
        # Verify CopyB is generated correctly
        assert variants[2] == "topmostSubform[0].CopyB[0].LeftCol[0].f2_2[0]", \
            "Third variant should have CopyB[0] instead of Copy1[0]"
    
    def test_generate_copy_variants_without_copy1_pattern(self):
        """
        **Validates: Requirements 2.4**
        
        Verify that field names without Copy1[0] pattern return only the original.
        
        This test verifies that:
        1. Field names without Copy1[0] are handled gracefully
        2. Only the original field name is returned
        3. No error is raised
        """
        # Initialize the field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Test with a field name that doesn't contain Copy1[0]
        field_without_copy1 = "topmostSubform[0].SomeOtherField[0].f1_1[0]"
        
        # Generate variants
        variants = mapper._generate_copy_variants(field_without_copy1)
        
        # Verify we get only 1 variant (the original)
        assert len(variants) == 1, \
            "Should return only the original field when Copy1[0] is not present"
        
        # Verify the original field is returned unchanged
        assert variants[0] == field_without_copy1, \
            "Should return the original field name unchanged"
    
    def test_generate_copy_variants_with_empty_string(self):
        """
        **Validates: Requirements 2.4**
        
        Verify that empty string is handled gracefully.
        
        This test verifies that:
        1. Empty string doesn't cause an error
        2. Empty string is returned as-is
        3. System continues to function
        """
        # Initialize the field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Test with empty string
        empty_field = ""
        
        # Generate variants
        variants = mapper._generate_copy_variants(empty_field)
        
        # Verify we get only 1 variant (the empty string)
        assert len(variants) == 1, \
            "Should return a list with one element for empty string"
        
        # Verify the empty string is returned
        assert variants[0] == "", \
            "Should return the empty string unchanged"
    
    def test_generate_copy_variants_with_malformed_field_name(self):
        """
        **Validates: Requirements 2.4**
        
        Verify that malformed field names are handled gracefully.
        
        This test verifies that:
        1. Malformed field names don't cause errors
        2. Original field name is returned
        3. System continues to function
        """
        # Initialize the field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Test with various malformed field names
        malformed_fields = [
            "Copy1",  # Missing [0]
            "Copy1[0]",  # Only the pattern, no context
            "topmostSubform.Copy1.LeftCol",  # Missing brackets
            "random_text_Copy1[0]_more_text",  # Unusual structure
        ]
        
        for malformed_field in malformed_fields:
            # Generate variants
            variants = mapper._generate_copy_variants(malformed_field)
            
            # For fields with Copy1[0], should generate 3 variants
            if "Copy1[0]" in malformed_field:
                assert len(variants) == 3, \
                    f"Field '{malformed_field}' contains Copy1[0], should generate 3 variants"
                
                # Verify transformations occurred
                assert "Copy2[0]" in variants[1], \
                    f"Second variant should contain Copy2[0]"
                
                assert "CopyB[0]" in variants[2], \
                    f"Third variant should contain CopyB[0]"
            else:
                # For fields without Copy1[0], should return only original
                assert len(variants) == 1, \
                    f"Field '{malformed_field}' without Copy1[0] should return only original"
                
                assert variants[0] == malformed_field, \
                    f"Should return original field '{malformed_field}' unchanged"
    
    def test_generate_copy_variants_preserves_field_structure(self):
        """
        **Validates: Requirements 1.2, 1.4, 2.3**
        
        Verify that field structure is preserved except for copy prefix.
        
        This test verifies that:
        1. All path components except Copy prefix are preserved
        2. Array indices are maintained
        3. Field hierarchy is unchanged
        """
        # Initialize the field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Test with a complex field name
        complex_field = "topmostSubform[0].Copy1[0].RghtCol[0].Lines9-11[0].f2_15[0]"
        
        # Generate variants
        variants = mapper._generate_copy_variants(complex_field)
        
        # Verify all variants have the same structure except for copy prefix
        for variant in variants:
            # All should start with topmostSubform[0]
            assert variant.startswith("topmostSubform[0]."), \
                "All variants should start with topmostSubform[0]"
            
            # All should contain RghtCol[0]
            assert ".RghtCol[0]." in variant, \
                "All variants should contain RghtCol[0]"
            
            # All should contain Lines9-11[0]
            assert ".Lines9-11[0]." in variant, \
                "All variants should contain Lines9-11[0]"
            
            # All should end with f2_15[0]
            assert variant.endswith(".f2_15[0]"), \
                "All variants should end with f2_15[0]"
        
        # Verify only the copy prefix differs
        assert variants[0].replace("Copy1[0]", "Copy2[0]") == variants[1], \
            "Copy2 variant should differ only in copy prefix"
        
        assert variants[0].replace("Copy1[0]", "CopyB[0]") == variants[2], \
            "CopyB variant should differ only in copy prefix"
    
    def test_generate_copy_variants_with_multiple_copy1_occurrences(self):
        """
        **Validates: Requirements 2.1, 2.2**
        
        Verify that all occurrences of Copy1[0] are replaced.
        
        This test verifies that:
        1. Multiple Copy1[0] patterns are all replaced
        2. Replacement is consistent across all occurrences
        3. No partial replacements occur
        """
        # Initialize the field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Test with a field name that has Copy1[0] multiple times
        # (This is unlikely in real PDFs but tests the replacement logic)
        field_with_multiple = "Copy1[0].topmostSubform[0].Copy1[0].LeftCol[0]"
        
        # Generate variants
        variants = mapper._generate_copy_variants(field_with_multiple)
        
        # Verify we get 3 variants
        assert len(variants) == 3, \
            "Should generate 3 variants even with multiple Copy1[0] occurrences"
        
        # Verify all Copy1[0] occurrences are replaced in Copy2 variant
        assert "Copy1[0]" not in variants[1], \
            "Copy2 variant should not contain any Copy1[0]"
        
        assert variants[1].count("Copy2[0]") == 2, \
            "Copy2 variant should have Copy2[0] in all positions"
        
        # Verify all Copy1[0] occurrences are replaced in CopyB variant
        assert "Copy1[0]" not in variants[2], \
            "CopyB variant should not contain any Copy1[0]"
        
        assert variants[2].count("CopyB[0]") == 2, \
            "CopyB variant should have CopyB[0] in all positions"
    
    def test_generate_copy_variants_with_special_characters(self):
        """
        **Validates: Requirements 2.3**
        
        Verify that special characters in field names are preserved.
        
        This test verifies that:
        1. Special characters are not affected by transformation
        2. Only Copy1[0] pattern is replaced
        3. Field name integrity is maintained
        """
        # Initialize the field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Test with field names containing special characters
        field_with_special = "topmostSubform[0].Copy1[0].Lines9-11[0].f2_15[0]"
        
        # Generate variants
        variants = mapper._generate_copy_variants(field_with_special)
        
        # Verify special characters are preserved in all variants
        for variant in variants:
            assert "Lines9-11[0]" in variant, \
                "Hyphen in Lines9-11 should be preserved"
            
            assert "f2_15[0]" in variant, \
                "Underscore in f2_15 should be preserved"
            
            assert "[0]" in variant, \
                "Array indices should be preserved"
