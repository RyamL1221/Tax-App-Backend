"""
Unit tests for font size calculation function.

Tests the calculate_font_size() function with various text lengths,
field dimensions, and boundary conditions.
"""

import pytest
from tax_document_generation.document_generator import calculate_font_size


class TestFontSizeCalculation:
    """Test suite for calculate_font_size() function."""
    
    def test_empty_text_returns_max_font_size(self):
        """Empty text should return the maximum font size."""
        result = calculate_font_size("", 100.0, 20.0, max_font_size=10.0, min_font_size=6.0)
        assert result == 10.0
    
    def test_short_text_in_large_field(self):
        """Short text in a large field should use maximum font size."""
        # Field: 200pt wide × 30pt high, Text: "ABC" (3 chars)
        # Height constraint: 30 × 0.8 = 24pt
        # Width constraint: 200 / (3 × 0.6) = 111pt
        # Result: min(10, 24, 111) = 10pt (max_font_size)
        result = calculate_font_size("ABC", 200.0, 30.0, max_font_size=10.0, min_font_size=6.0)
        assert result == 10.0
    
    def test_long_text_in_small_field_width_constrained(self):
        """Long text in a narrow field should reduce font size based on width."""
        # Field: 50pt wide × 20pt high, Text: "ABCDEFGHIJ" (10 chars)
        # Height constraint: 20 × 0.8 = 16pt
        # Width constraint: 50 / (10 × 0.6) = 8.33pt
        # Result: min(10, 16, 8.33) = 8.33pt
        result = calculate_font_size("ABCDEFGHIJ", 50.0, 20.0, max_font_size=10.0, min_font_size=6.0)
        assert result == pytest.approx(8.33, rel=0.01)
    
    def test_text_in_short_field_height_constrained(self):
        """Text in a short field should reduce font size based on height."""
        # Field: 100pt wide × 10pt high, Text: "ABC" (3 chars)
        # Height constraint: 10 × 0.8 = 8pt
        # Width constraint: 100 / (3 × 0.6) = 55.56pt
        # Result: min(10, 8, 55.56) = 8pt
        result = calculate_font_size("ABC", 100.0, 10.0, max_font_size=10.0, min_font_size=6.0)
        assert result == 8.0
    
    def test_respects_minimum_font_size(self):
        """Font size should never go below the minimum."""
        # Field: 10pt wide × 10pt high, Text: "ABCDEFGHIJKLMNOP" (16 chars)
        # Height constraint: 10 × 0.8 = 8pt
        # Width constraint: 10 / (16 × 0.6) = 1.04pt
        # Result: max(6, min(10, 8, 1.04)) = 6pt (min_font_size)
        result = calculate_font_size("ABCDEFGHIJKLMNOP", 10.0, 10.0, max_font_size=10.0, min_font_size=6.0)
        assert result == 6.0
    
    def test_respects_maximum_font_size(self):
        """Font size should never exceed the maximum."""
        # Field: 500pt wide × 100pt high, Text: "A" (1 char)
        # Height constraint: 100 × 0.8 = 80pt
        # Width constraint: 500 / (1 × 0.6) = 833pt
        # Result: min(10, 80, 833) = 10pt (max_font_size)
        result = calculate_font_size("A", 500.0, 100.0, max_font_size=10.0, min_font_size=6.0)
        assert result == 10.0
    
    def test_typical_rghtcol_field(self):
        """Test with typical RghtCol field dimensions (small field)."""
        # RghtCol: avg 80.59pt wide × 12.04pt high
        # Text: "1234.56" (7 chars)
        # Height constraint: 12.04 × 0.8 = 9.63pt
        # Width constraint: 80.59 / (7 × 0.6) = 19.19pt
        # Result: min(10, 9.63, 19.19) = 9.63pt
        result = calculate_font_size("1234.56", 80.59, 12.04, max_font_size=10.0, min_font_size=6.0)
        assert result == pytest.approx(9.63, rel=0.01)
    
    def test_typical_leftcol_field(self):
        """Test with typical LeftCol field dimensions (large field)."""
        # LeftCol: avg 199.40pt wide × 35.48pt high
        # Text: "John Q. Taxpayer" (16 chars)
        # Height constraint: 35.48 × 0.8 = 28.38pt
        # Width constraint: 199.40 / (16 × 0.6) = 20.77pt
        # Result: min(10, 28.38, 20.77) = 10pt (max_font_size)
        result = calculate_font_size("John Q. Taxpayer", 199.40, 35.48, max_font_size=10.0, min_font_size=6.0)
        assert result == 10.0
    
    def test_very_small_field(self):
        """Test with very small field (9pt height - minimum found in analysis)."""
        # Field: 50pt wide × 9pt high, Text: "ABC" (3 chars)
        # Height constraint: 9 × 0.8 = 7.2pt
        # Width constraint: 50 / (3 × 0.6) = 27.78pt
        # Result: min(10, 7.2, 27.78) = 7.2pt
        result = calculate_font_size("ABC", 50.0, 9.0, max_font_size=10.0, min_font_size=6.0)
        assert result == pytest.approx(7.2, rel=0.01)
    
    def test_custom_bounds(self):
        """Test with custom min/max font size bounds."""
        # Field: 100pt wide × 20pt high, Text: "TEST" (4 chars)
        # Height constraint: 20 × 0.8 = 16pt
        # Width constraint: 100 / (4 × 0.6) = 41.67pt
        # Result: min(8, 16, 41.67) = 8pt (max_font_size)
        result = calculate_font_size("TEST", 100.0, 20.0, max_font_size=8.0, min_font_size=5.0)
        assert result == 8.0
    
    def test_single_character(self):
        """Test with single character text."""
        # Field: 50pt wide × 15pt high, Text: "X" (1 char)
        # Height constraint: 15 × 0.8 = 12pt
        # Width constraint: 50 / (1 × 0.6) = 83.33pt
        # Result: min(10, 12, 83.33) = 10pt (max_font_size)
        result = calculate_font_size("X", 50.0, 15.0, max_font_size=10.0, min_font_size=6.0)
        assert result == 10.0
    
    def test_very_long_text(self):
        """Test with very long text that requires minimum font size."""
        long_text = "A" * 100  # 100 characters
        # Field: 100pt wide × 20pt high
        # Height constraint: 20 × 0.8 = 16pt
        # Width constraint: 100 / (100 × 0.6) = 1.67pt
        # Result: max(6, min(10, 16, 1.67)) = 6pt (min_font_size)
        result = calculate_font_size(long_text, 100.0, 20.0, max_font_size=10.0, min_font_size=6.0)
        assert result == 6.0
    
    def test_monetary_value_in_rghtcol(self):
        """Test with typical monetary value in RghtCol field."""
        # Field: 80pt wide × 12pt high, Text: "12345.67" (8 chars)
        # Height constraint: 12 × 0.8 = 9.6pt
        # Width constraint: 80 / (8 × 0.6) = 16.67pt
        # Result: min(10, 9.6, 16.67) = 9.6pt
        result = calculate_font_size("12345.67", 80.0, 12.0, max_font_size=10.0, min_font_size=6.0)
        assert result == pytest.approx(9.6, rel=0.01)
    
    def test_tin_in_leftcol(self):
        """Test with TIN (Tax Identification Number) in LeftCol field."""
        # Field: 150pt wide × 26pt high, Text: "12-3456789" (10 chars)
        # Height constraint: 26 × 0.8 = 20.8pt
        # Width constraint: 150 / (10 × 0.6) = 25pt
        # Result: min(10, 20.8, 25) = 10pt (max_font_size)
        result = calculate_font_size("12-3456789", 150.0, 26.0, max_font_size=10.0, min_font_size=6.0)
        assert result == 10.0
    
    def test_zero_width_field(self):
        """Test with zero width field (edge case)."""
        # Field: 0pt wide × 20pt high, Text: "ABC" (3 chars)
        # Height constraint: 20 × 0.8 = 16pt
        # Width constraint: 0 / (3 × 0.6) = 0pt
        # Result: max(6, min(10, 16, 0)) = 6pt (min_font_size)
        result = calculate_font_size("ABC", 0.0, 20.0, max_font_size=10.0, min_font_size=6.0)
        assert result == 6.0
    
    def test_zero_height_field(self):
        """Test with zero height field (edge case)."""
        # Field: 100pt wide × 0pt high, Text: "ABC" (3 chars)
        # Height constraint: 0 × 0.8 = 0pt
        # Width constraint: 100 / (3 × 0.6) = 55.56pt
        # Result: max(6, min(10, 0, 55.56)) = 6pt (min_font_size)
        result = calculate_font_size("ABC", 100.0, 0.0, max_font_size=10.0, min_font_size=6.0)
        assert result == 6.0
    
    def test_negative_dimensions(self):
        """Test with negative dimensions (edge case)."""
        # Field: -100pt wide × -20pt high, Text: "ABC" (3 chars)
        # Should handle gracefully and return min_font_size
        result = calculate_font_size("ABC", -100.0, -20.0, max_font_size=10.0, min_font_size=6.0)
        assert result == 6.0
    
    def test_whitespace_text(self):
        """Test with whitespace-only text."""
        # Field: 100pt wide × 20pt high, Text: "   " (3 spaces)
        # Should treat spaces as characters
        # Height constraint: 20 × 0.8 = 16pt
        # Width constraint: 100 / (3 × 0.6) = 55.56pt
        # Result: min(10, 16, 55.56) = 10pt (max_font_size)
        result = calculate_font_size("   ", 100.0, 20.0, max_font_size=10.0, min_font_size=6.0)
        assert result == 10.0
    
    def test_special_characters(self):
        """Test with special characters."""
        # Field: 100pt wide × 20pt high, Text: "$1,234.56" (9 chars)
        # Height constraint: 20 × 0.8 = 16pt
        # Width constraint: 100 / (9 × 0.6) = 18.52pt
        # Result: min(10, 16, 18.52) = 10pt (max_font_size)
        result = calculate_font_size("$1,234.56", 100.0, 20.0, max_font_size=10.0, min_font_size=6.0)
        assert result == 10.0
    
    def test_unicode_characters(self):
        """Test with unicode characters."""
        # Field: 100pt wide × 20pt high, Text: "Café" (4 chars)
        # Height constraint: 20 × 0.8 = 16pt
        # Width constraint: 100 / (4 × 0.6) = 41.67pt
        # Result: min(10, 16, 41.67) = 10pt (max_font_size)
        result = calculate_font_size("Café", 100.0, 20.0, max_font_size=10.0, min_font_size=6.0)
        assert result == 10.0
    
    def test_newline_characters(self):
        """Test with text containing newlines."""
        # Field: 100pt wide × 20pt high, Text: "Line1\nLine2" (11 chars including newline)
        # Height constraint: 20 × 0.8 = 16pt
        # Width constraint: 100 / (11 × 0.6) = 15.15pt
        # Result: min(10, 16, 15.15) = 10pt (max_font_size)
        result = calculate_font_size("Line1\nLine2", 100.0, 20.0, max_font_size=10.0, min_font_size=6.0)
        assert result == 10.0


class TestFontSizeBounds:
    """Test suite for font size boundary conditions."""
    
    def test_min_equals_max(self):
        """Test when min_font_size equals max_font_size."""
        result = calculate_font_size("ABC", 100.0, 20.0, max_font_size=8.0, min_font_size=8.0)
        assert result == 8.0
    
    def test_min_greater_than_max(self):
        """Test when min_font_size is greater than max_font_size (invalid config)."""
        # Should still respect the bounds, returning min_font_size
        result = calculate_font_size("ABC", 100.0, 20.0, max_font_size=6.0, min_font_size=10.0)
        # Result will be max(10, min(6, ...)) which gives 10
        assert result == 10.0
    
    def test_very_small_bounds(self):
        """Test with very small font size bounds."""
        result = calculate_font_size("ABC", 100.0, 20.0, max_font_size=2.0, min_font_size=1.0)
        assert result == 2.0
    
    def test_very_large_bounds(self):
        """Test with very large font size bounds."""
        # Field: 1000pt wide × 200pt high, Text: "A" (1 char)
        # Height constraint: 200 × 0.8 = 160pt
        # Width constraint: 1000 / (1 × 0.6) = 1666.67pt
        # Result: min(100, 160, 1666.67) = 100pt (max_font_size)
        result = calculate_font_size("A", 1000.0, 200.0, max_font_size=100.0, min_font_size=50.0)
        assert result == 100.0
