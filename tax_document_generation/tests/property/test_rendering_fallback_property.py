"""
Property-based tests for rendering fallback behavior in insert_text_with_fallback().

These tests verify that the insert_text_with_fallback() function attempts
progressively smaller font sizes when text doesn't fit at the default size.

Feature: fix-incorrect-field-mappings
Property 7: Rendering Fallback Behavior

**Validates: Requirements 1.3, 2.3, 3.3**
"""

import pytest
from hypothesis import given, settings, strategies as st, assume
from unittest.mock import Mock
import fitz  # PyMuPDF

from tax_document_generation.document_generator import insert_text_with_fallback


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


class TestRenderingFallbackProperty:
    """Property-based tests for rendering fallback behavior."""
    
    @settings(max_examples=30)
    @given(
        dimensions=field_dimensions_strategy(),
        text=text_content_strategy(),
        default_font_size=st.floats(min_value=8.0, max_value=15.0),
        min_font_size=st.floats(min_value=4.0, max_value=6.0)
    )
    def test_fallback_attempts_progressively_smaller_font_sizes(
        self, dimensions, text, default_font_size, min_font_size
    ):
        """
        **Validates: Requirements 1.3, 2.3, 3.3**
        Feature: fix-incorrect-field-mappings, Property 7: Rendering Fallback Behavior
        
        For any text that doesn't fit at the default font size,
        the system should attempt progressively smaller font sizes before failing.
        """
        assume(default_font_size >= min_font_size + 2.0)
        
        width, height = dimensions
        
        mock_page = Mock(spec=fitz.Page)
        mock_rect = Mock(spec=fitz.Rect)
        mock_rect.width = width
        mock_rect.height = height
        
        # Simulate text doesn't fit: first 2 attempts fail, 3rd succeeds
        mock_page.insert_textbox.side_effect = [-1.0, -1.5, 0.5]
        
        result = insert_text_with_fallback(
            page=mock_page,
            rect=mock_rect,
            text=text,
            field_name="test_field",
            default_font_size=default_font_size,
            min_font_size=min_font_size
        )
        
        call_count = mock_page.insert_textbox.call_count
        assert call_count == 3, f"Expected 3 attempts, got {call_count}"
        
        # Verify font sizes decreased on each attempt
        calls = mock_page.insert_textbox.call_args_list
        first_call_fontsize = calls[0][1]['fontsize']
        assert abs(first_call_fontsize - default_font_size) < 0.01
        
        if call_count >= 2:
            second_call_fontsize = calls[1][1]['fontsize']
            expected_second = default_font_size - 1.0
            assert abs(second_call_fontsize - expected_second) < 0.01
        
        assert result is True
    
    @settings(max_examples=30)
    @given(
        dimensions=field_dimensions_strategy(),
        text=text_content_strategy(),
        default_font_size=st.floats(min_value=7.0, max_value=15.0)
    )
    def test_fallback_succeeds_immediately_when_text_fits(
        self, dimensions, text, default_font_size
    ):
        """
        **Validates: Requirements 1.3, 2.3, 3.3**
        Feature: fix-incorrect-field-mappings, Property 7: Rendering Fallback Behavior
        
        For any text that fits at the default font size,
        the system should succeed on the first attempt without fallback.
        """
        width, height = dimensions
        min_font_size = 6.0
        
        assume(default_font_size >= min_font_size)
        
        mock_page = Mock(spec=fitz.Page)
        mock_rect = Mock(spec=fitz.Rect)
        mock_rect.width = width
        mock_rect.height = height
        
        # Simulate text fits immediately
        mock_page.insert_textbox.return_value = 0.5
        
        result = insert_text_with_fallback(
            page=mock_page,
            rect=mock_rect,
            text=text,
            field_name="test_field",
            default_font_size=default_font_size,
            min_font_size=min_font_size
        )
        
        call_count = mock_page.insert_textbox.call_count
        assert call_count == 1, f"Function should make only 1 attempt when text fits, got {call_count}"
        assert result is True
    
    @settings(max_examples=20)
    @given(
        dimensions=field_dimensions_strategy(),
        text=text_content_strategy(),
        default_font_size=st.floats(min_value=7.0, max_value=15.0)
    )
    def test_fallback_respects_max_attempts_limit(
        self, dimensions, text, default_font_size
    ):
        """
        **Validates: Requirements 1.3, 2.3, 3.3**
        Feature: fix-incorrect-field-mappings, Property 7: Rendering Fallback Behavior
        
        For any text that never fits,
        the system should make at most 3 attempts before giving up.
        """
        width, height = dimensions
        min_font_size = 4.0
        
        assume(default_font_size > min_font_size)
        
        mock_page = Mock(spec=fitz.Page)
        mock_rect = Mock(spec=fitz.Rect)
        mock_rect.width = width
        mock_rect.height = height
        
        # Simulate text never fits
        mock_page.insert_textbox.return_value = -1.0
        
        result = insert_text_with_fallback(
            page=mock_page,
            rect=mock_rect,
            text=text,
            field_name="test_field",
            default_font_size=default_font_size,
            min_font_size=min_font_size
        )
        
        call_count = mock_page.insert_textbox.call_count
        assert call_count <= 3, f"Function should make at most 3 attempts, got {call_count}"
        assert result is False
