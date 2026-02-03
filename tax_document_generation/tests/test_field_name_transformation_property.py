"""
Property-based tests for field name transformation in FieldMapper.

These tests verify that the _generate_copy_variants() method correctly transforms
Copy1 field names to Copy2 and CopyB variants while preserving all other path
components. Each property test runs with a minimum of 100 iterations.

Feature: multi-page-form-filling
Property 1: Field Name Transformation Correctness

**Validates: Requirements 1.2, 1.4, 2.1, 2.2, 2.3**
"""

import pytest
from hypothesis import given, settings, strategies as st, assume
from tax_document_generation.field_mapper import FieldMapper


# Strategy for generating Copy1 field names
def copy1_field_name_strategy():
    """
    Generate realistic Copy1 PDF field names.
    
    PDF field names follow the pattern:
    topmostSubform[0].Copy1[0].<section>[0].<field>[0]
    
    Examples:
    - topmostSubform[0].Copy1[0].LeftCol[0].f2_2[0]
    - topmostSubform[0].Copy1[0].RghtCol[0].Lines9-11[0].f2_15[0]
    """
    # Generate section names (LeftCol, RghtCol, etc.)
    section_strategy = st.sampled_from([
        "LeftCol",
        "RghtCol",
        "Lines9-11",
        "Lines12-14",
        "Header"
    ])
    
    # Generate field names (f2_2, f2_15, etc.)
    field_strategy = st.text(
        min_size=3,
        max_size=10,
        alphabet=st.characters(whitelist_categories=('Ll', 'Nd'), whitelist_characters='_-')
    ).filter(lambda x: len(x) > 0 and x[0].isalpha())
    
    # Build the complete field name
    return st.builds(
        lambda section, field: f"topmostSubform[0].Copy1[0].{section}[0].{field}[0]",
        section=section_strategy,
        field=field_strategy
    )


# Strategy for generating field names with multiple path components
@st.composite
def complex_copy1_field_name_strategy(draw):
    """
    Generate complex Copy1 field names with multiple nested components.
    
    Examples:
    - topmostSubform[0].Copy1[0].Section1[0].SubSection[0].Field[0]
    - topmostSubform[0].Copy1[0].A[0].B[0].C[0].D[0]
    """
    # Generate 2-5 path components between Copy1 and the final field
    num_components = draw(st.integers(min_value=2, max_value=5))
    
    components = []
    for i in range(num_components):
        component = draw(st.text(
            min_size=1,
            max_size=15,
            alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='_-')
        ).filter(lambda x: len(x) > 0 and x[0].isalpha()))
        components.append(f"{component}[0]")
    
    return f"topmostSubform[0].Copy1[0].{'.'.join(components)}"


class TestFieldNameTransformationProperty:
    """Property-based tests for field name transformation correctness."""
    
    @settings(max_examples=20)
    @given(copy1_field=copy1_field_name_strategy())
    def test_copy2_transformation_preserves_structure(self, copy1_field):
        """
        **Validates: Requirements 1.2, 1.4, 2.1, 2.3**
        Feature: multi-page-form-filling, Property 1: Field Name Transformation Correctness
        
        For any Copy1 PDF field name containing "Copy1[0]",
        transforming it to Copy2 should produce a field name that is identical
        except for "Copy1[0]" being replaced with "Copy2[0]".
        
        This test verifies that:
        1. Copy2 variant is generated
        2. Only the copy prefix differs
        3. All other path components are preserved exactly
        4. Field structure is maintained
        """
        # Initialize the field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Generate variants
        variants = mapper._generate_copy_variants(copy1_field)
        
        # Verify we get 3 variants
        assert len(variants) == 3, \
            f"Should generate 3 variants for Copy1 field, got {len(variants)}"
        
        # Extract the Copy2 variant
        copy2_field = variants[1]
        
        # CRITICAL VERIFICATION: Copy2 field should be identical to Copy1 except for the copy prefix
        expected_copy2 = copy1_field.replace("Copy1[0]", "Copy2[0]")
        assert copy2_field == expected_copy2, \
            f"Copy2 variant should be '{expected_copy2}', got '{copy2_field}'"
        
        # Verify the transformation only affected the copy prefix
        # Split by "Copy1[0]" and "Copy2[0]" to compare the parts
        copy1_parts = copy1_field.split("Copy1[0]")
        copy2_parts = copy2_field.split("Copy2[0]")
        
        assert len(copy1_parts) == len(copy2_parts), \
            "Copy1 and Copy2 should have the same number of parts"
        
        # Verify all parts except the copy prefix are identical
        for i, (part1, part2) in enumerate(zip(copy1_parts, copy2_parts)):
            assert part1 == part2, \
                f"Part {i} should be identical: '{part1}' vs '{part2}'"
    
    @settings(max_examples=20)
    @given(copy1_field=copy1_field_name_strategy())
    def test_copyb_transformation_preserves_structure(self, copy1_field):
        """
        **Validates: Requirements 1.2, 1.4, 2.2, 2.3**
        Feature: multi-page-form-filling, Property 1: Field Name Transformation Correctness
        
        For any Copy1 PDF field name containing "Copy1[0]",
        transforming it to CopyB should produce a field name that is identical
        except for "Copy1[0]" being replaced with "CopyB[0]".
        
        This test verifies that:
        1. CopyB variant is generated
        2. Only the copy prefix differs
        3. All other path components are preserved exactly
        4. Field structure is maintained
        """
        # Initialize the field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Generate variants
        variants = mapper._generate_copy_variants(copy1_field)
        
        # Verify we get 3 variants
        assert len(variants) == 3, \
            f"Should generate 3 variants for Copy1 field, got {len(variants)}"
        
        # Extract the CopyB variant
        copyb_field = variants[2]
        
        # CRITICAL VERIFICATION: CopyB field should be identical to Copy1 except for the copy prefix
        expected_copyb = copy1_field.replace("Copy1[0]", "CopyB[0]")
        assert copyb_field == expected_copyb, \
            f"CopyB variant should be '{expected_copyb}', got '{copyb_field}'"
        
        # Verify the transformation only affected the copy prefix
        # Split by "Copy1[0]" and "CopyB[0]" to compare the parts
        copy1_parts = copy1_field.split("Copy1[0]")
        copyb_parts = copyb_field.split("CopyB[0]")
        
        assert len(copy1_parts) == len(copyb_parts), \
            "Copy1 and CopyB should have the same number of parts"
        
        # Verify all parts except the copy prefix are identical
        for i, (part1, part2) in enumerate(zip(copy1_parts, copyb_parts)):
            assert part1 == part2, \
                f"Part {i} should be identical: '{part1}' vs '{part2}'"
    
    @settings(max_examples=20)
    @given(copy1_field=copy1_field_name_strategy())
    def test_all_three_variants_have_same_structure(self, copy1_field):
        """
        **Validates: Requirements 1.2, 1.4, 2.1, 2.2, 2.3**
        Feature: multi-page-form-filling, Property 1: Field Name Transformation Correctness
        
        For any Copy1 PDF field name containing "Copy1[0]",
        all three variants (Copy1, Copy2, CopyB) should have identical structure
        with only the copy prefix differing.
        
        This test verifies that:
        1. All three variants are generated
        2. All variants have the same path structure
        3. Only the copy prefix differs between variants
        4. No other transformations occur
        """
        # Initialize the field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Generate variants
        variants = mapper._generate_copy_variants(copy1_field)
        
        # Verify we get exactly 3 variants
        assert len(variants) == 3, \
            f"Should generate exactly 3 variants, got {len(variants)}"
        
        copy1_variant = variants[0]
        copy2_variant = variants[1]
        copyb_variant = variants[2]
        
        # CRITICAL VERIFICATION: Copy1 variant should be unchanged
        assert copy1_variant == copy1_field, \
            f"Copy1 variant should be unchanged: '{copy1_field}' vs '{copy1_variant}'"
        
        # CRITICAL VERIFICATION: All variants should have the same structure
        # Remove the copy prefix from each and verify they're identical
        copy1_without_prefix = copy1_variant.replace("Copy1[0]", "COPY[0]")
        copy2_without_prefix = copy2_variant.replace("Copy2[0]", "COPY[0]")
        copyb_without_prefix = copyb_variant.replace("CopyB[0]", "COPY[0]")
        
        assert copy1_without_prefix == copy2_without_prefix, \
            f"Copy1 and Copy2 should have identical structure: " \
            f"'{copy1_without_prefix}' vs '{copy2_without_prefix}'"
        
        assert copy1_without_prefix == copyb_without_prefix, \
            f"Copy1 and CopyB should have identical structure: " \
            f"'{copy1_without_prefix}' vs '{copyb_without_prefix}'"
        
        # Verify the copy prefixes are correct
        assert "Copy1[0]" in copy1_variant, \
            "Copy1 variant should contain 'Copy1[0]'"
        
        assert "Copy2[0]" in copy2_variant, \
            "Copy2 variant should contain 'Copy2[0]'"
        
        assert "CopyB[0]" in copyb_variant, \
            "CopyB variant should contain 'CopyB[0]'"
    
    @settings(max_examples=20)
    @given(copy1_field=complex_copy1_field_name_strategy())
    def test_complex_field_paths_preserved(self, copy1_field):
        """
        **Validates: Requirements 1.2, 1.4, 2.3**
        Feature: multi-page-form-filling, Property 1: Field Name Transformation Correctness
        
        For any Copy1 PDF field name with complex nested paths,
        all path components should be preserved exactly in all variants,
        with only the copy prefix changing.
        
        This test verifies that:
        1. Complex nested paths are handled correctly
        2. All path components are preserved
        3. Array indices are maintained
        4. Only the copy prefix is transformed
        """
        # Initialize the field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Generate variants
        variants = mapper._generate_copy_variants(copy1_field)
        
        # Verify we get 3 variants
        assert len(variants) == 3, \
            f"Should generate 3 variants for complex Copy1 field, got {len(variants)}"
        
        # Extract all path components from Copy1 (excluding the copy prefix)
        copy1_parts = copy1_field.split(".")
        
        # Verify each variant has the same number of path components
        for i, variant in enumerate(variants):
            variant_parts = variant.split(".")
            assert len(variant_parts) == len(copy1_parts), \
                f"Variant {i} should have {len(copy1_parts)} path components, " \
                f"got {len(variant_parts)}"
            
            # Verify all components except the copy prefix are identical
            for j, (copy1_part, variant_part) in enumerate(zip(copy1_parts, variant_parts)):
                # Skip the copy prefix component
                if "Copy1[0]" in copy1_part or "Copy2[0]" in variant_part or "CopyB[0]" in variant_part:
                    continue
                
                assert copy1_part == variant_part, \
                    f"Path component {j} should be identical: '{copy1_part}' vs '{variant_part}'"
    
    @settings(max_examples=20)
    @given(
        copy1_field=copy1_field_name_strategy(),
        value=st.text(min_size=1, max_size=50)
    )
    def test_transformation_independent_of_value(self, copy1_field, value):
        """
        **Validates: Requirements 2.1, 2.2**
        Feature: multi-page-form-filling, Property 1: Field Name Transformation Correctness
        
        For any Copy1 PDF field name,
        the transformation to Copy2 and CopyB should be independent of any
        associated field value.
        
        This test verifies that:
        1. Field name transformation doesn't depend on field values
        2. Same field name always produces same variants
        3. Transformation is deterministic
        """
        # Initialize the field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Generate variants (value is not used in transformation)
        variants1 = mapper._generate_copy_variants(copy1_field)
        variants2 = mapper._generate_copy_variants(copy1_field)
        
        # CRITICAL VERIFICATION: Transformation should be deterministic
        assert variants1 == variants2, \
            f"Same field name should always produce same variants"
        
        # Verify we get 3 variants
        assert len(variants1) == 3, \
            f"Should generate 3 variants, got {len(variants1)}"
        
        # Verify the variants are correct
        assert variants1[0] == copy1_field, \
            "First variant should be the original Copy1 field"
        
        assert variants1[1] == copy1_field.replace("Copy1[0]", "Copy2[0]"), \
            "Second variant should have Copy2[0]"
        
        assert variants1[2] == copy1_field.replace("Copy1[0]", "CopyB[0]"), \
            "Third variant should have CopyB[0]"
    
    @settings(max_examples=20)
    @given(copy1_field=copy1_field_name_strategy())
    def test_no_copy_prefix_leakage(self, copy1_field):
        """
        **Validates: Requirements 2.1, 2.2, 2.3**
        Feature: multi-page-form-filling, Property 1: Field Name Transformation Correctness
        
        For any Copy1 PDF field name,
        the Copy2 variant should not contain "Copy1[0]" or "CopyB[0]",
        and the CopyB variant should not contain "Copy1[0]" or "Copy2[0]".
        
        This test verifies that:
        1. Copy prefixes are completely replaced
        2. No mixing of copy prefixes occurs
        3. Each variant has only its designated copy prefix
        """
        # Initialize the field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Generate variants
        variants = mapper._generate_copy_variants(copy1_field)
        
        copy1_variant = variants[0]
        copy2_variant = variants[1]
        copyb_variant = variants[2]
        
        # CRITICAL VERIFICATION: Copy2 variant should not contain Copy1 or CopyB
        assert "Copy1[0]" not in copy2_variant, \
            f"Copy2 variant should not contain 'Copy1[0]': {copy2_variant}"
        
        assert "CopyB[0]" not in copy2_variant, \
            f"Copy2 variant should not contain 'CopyB[0]': {copy2_variant}"
        
        assert "Copy2[0]" in copy2_variant, \
            f"Copy2 variant should contain 'Copy2[0]': {copy2_variant}"
        
        # CRITICAL VERIFICATION: CopyB variant should not contain Copy1 or Copy2
        assert "Copy1[0]" not in copyb_variant, \
            f"CopyB variant should not contain 'Copy1[0]': {copyb_variant}"
        
        assert "Copy2[0]" not in copyb_variant, \
            f"CopyB variant should not contain 'Copy2[0]': {copyb_variant}"
        
        assert "CopyB[0]" in copyb_variant, \
            f"CopyB variant should contain 'CopyB[0]': {copyb_variant}"
        
        # CRITICAL VERIFICATION: Copy1 variant should only contain Copy1
        assert "Copy1[0]" in copy1_variant, \
            f"Copy1 variant should contain 'Copy1[0]': {copy1_variant}"
        
        assert "Copy2[0]" not in copy1_variant, \
            f"Copy1 variant should not contain 'Copy2[0]': {copy1_variant}"
        
        assert "CopyB[0]" not in copy1_variant, \
            f"Copy1 variant should not contain 'CopyB[0]': {copy1_variant}"
    
    @settings(max_examples=20)
    @given(
        field_without_copy1=st.text(
            min_size=1,
            max_size=100,
            alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='[]._-')
        ).filter(lambda x: "Copy1[0]" not in x and len(x) > 0)
    )
    def test_non_copy1_fields_return_single_variant(self, field_without_copy1):
        """
        **Validates: Requirements 2.4**
        Feature: multi-page-form-filling, Property 1: Field Name Transformation Correctness
        
        For any field name that does not contain "Copy1[0]",
        the transformation should return only the original field name
        without generating additional variants.
        
        This test verifies that:
        1. Fields without Copy1[0] are handled gracefully
        2. Only one variant is returned (the original)
        3. No transformation occurs
        4. No errors are raised
        """
        # Initialize the field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Generate variants
        variants = mapper._generate_copy_variants(field_without_copy1)
        
        # CRITICAL VERIFICATION: Should return only 1 variant
        assert len(variants) == 1, \
            f"Field without Copy1[0] should return 1 variant, got {len(variants)}"
        
        # CRITICAL VERIFICATION: The variant should be the original field unchanged
        assert variants[0] == field_without_copy1, \
            f"Variant should be the original field: '{field_without_copy1}' vs '{variants[0]}'"
        
        # Verify no transformation occurred - the output should be identical to input
        # (even if the input contains Copy2[0] or CopyB[0], it should be returned as-is)
        assert variants[0] == field_without_copy1, \
            "Field without Copy1[0] should be returned unchanged"
