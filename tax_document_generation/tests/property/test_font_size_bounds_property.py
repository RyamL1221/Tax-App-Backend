"""
Property-based tests for font size bounds in calculate_font_size().

These tests verify that the calculate_font_size() function always returns
a font size within the configured minimum and maximum bounds, regardless of
the input text content or field dimensions.

Feature: fix-incorrect-field-mappings
Property 2: Font Size Bounds

**Validates: Requirements 1.1, 2.1, 3.1**
"""

import pytest
from hypothesis import given, settings, strategies as st, assume
from tax_document_generation.document_generator import calculate_font_size


# Strategy for generating realistic field dimensions
@st.composite
def field_dimensions_strategy(draw):
    """Generate realistic PDF field dimensions."""
    width = draw(st.floats(min_value=10.0, max_value=500.0))
    height = draw(st.floats(min_value=5.0, max_value=100.0))
    return width, height


# Strategy for generating text content
def text_content_strategy():
    """Generate realistic text content for PDF fields."""
    return st.one_of(
        st.text(min_size=0, max_size=100, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd', 'Pd', 'Ps', 'Pe', 'Po'),
            whitelist_characters=' .,()-'
        )),
        st.just(""),  # Empty text
        st.text(min_size=1, max_size=20),  # Short text
        st.text(min_size=50, max_size=100),  # Long text
    )


# Strategy for generating font size bounds
@st.composite
def font_size_bounds_strategy(draw):
    """Generate realistic font size bounds."""
    min_font = draw(st.floats(min_value=1.0, max_value=10.0))
    max_font = draw(st.floats(min_value=min_font, max_value=20.0))
    return min_font, max_font


class TestFontSizeBoundsProperty:
    """Property-based tests for font size bounds correctness."""
    
    @settings(max_examples=30)
    @given(
        dimensions=field_dimensions_strategy(),
        text=text_content_strategy(),
        bounds=font_size_bounds_strategy()
    )
    def test_font_size_within_bounds(self, dimensions, text, bounds):
        """
        **Validates: Requirements 1.1, 2.1, 3.1**
        Feature: fix-incorrect-field-mappings, Property 2: Font Size Bounds
        
        For any field dimensions, text content, and configured bounds,
        the calculated font size must be within the minimum and maximum bounds.
        """
        width, height = dimensions
        min_font_size, max_font_size = bounds
        
        result = calculate_font_size(
            text=text,
            field_width=width,
            field_height=height,
            max_font_size=max_font_size,
            min_font_size=min_font_size
        )
        
        assert result >= min_font_size, \
            f"Font size {result} is below minimum {min_font_size}"
        assert result <= max_font_size, \
            f"Font size {result} exceeds maximum {max_font_size}"
    
    @settings(max_examples=30)
    @given(
        dimensions=field_dimensions_strategy(),
        text=text_content_strategy()
    )
    def test_font_size_within_default_bounds(self, dimensions, text):
        """
        **Validates: Requirements 1.1, 2.1, 3.1**
        Feature: fix-incorrect-field-mappings, Property 2: Font Size Bounds
        
        For any field dimensions and text content using default bounds,
        the calculated font size must be within 6.0pt and 10.0pt.
        """
        width, height = dimensions
        
        result = calculate_font_size(
            text=text,
            field_width=width,
            field_height=height
        )
        
        assert result >= 6.0, f"Font size {result} is below default minimum 6.0pt"
        assert result <= 10.0, f"Font size {result} exceeds default maximum 10.0pt"
    
    @settings(max_examples=20)
    @given(
        width=st.floats(min_value=0.0, max_value=10.0),
        height=st.floats(min_value=0.0, max_value=10.0),
        text=st.text(min_size=1, max_size=100)
    )
    def test_bounds_respected_for_edge_cases(self, width, height, text):
        """
        **Validates: Requirements 1.1, 2.1, 3.1**
        Feature: fix-incorrect-field-mappings, Property 2: Font Size Bounds
        
        For edge case field dimensions (very small or zero),
        the calculated font size must still respect bounds.
        """
        result = calculate_font_size(
            text=text,
            field_width=width,
            field_height=height,
            max_font_size=10.0,
            min_font_size=6.0
        )
        
        assert result >= 6.0, f"Font size {result} is below minimum 6.0pt"
        assert result <= 10.0, f"Font size {result} exceeds maximum 10.0pt"
