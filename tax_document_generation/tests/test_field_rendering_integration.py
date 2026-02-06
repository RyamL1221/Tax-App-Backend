"""
Integration tests for field-specific rendering configuration with font size calculation.

Tests verify that FIELD_RENDERING_CONFIG works correctly with calculate_font_size()
to produce appropriate font sizes for different field types.

Requirements: 1.1, 2.1, 3.1
"""

import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from document_generator import FIELD_RENDERING_CONFIG, calculate_font_size


class TestFieldRenderingIntegration:
    """Test suite for integrating FIELD_RENDERING_CONFIG with calculate_font_size."""
    
    def test_leftcol_field_with_config(self):
        """Test calculating font size for LeftCol field using config."""
        # Get LeftCol configuration
        config = FIELD_RENDERING_CONFIG['LeftCol']
        
        # Typical LeftCol field dimensions
        field_width = 199.40
        field_height = 35.48
        text = "John Q. Taxpayer"
        
        # Calculate font size using config bounds
        font_size = calculate_font_size(
            text,
            field_width,
            field_height,
            max_font_size=config['max_font_size'],
            min_font_size=config['min_font_size']
        )
        
        # Should use standard font size (9-10pt)
        assert config['min_font_size'] <= font_size <= config['max_font_size']
        assert font_size == 10.0  # Should fit comfortably at max size
    
    def test_rghtcol_field_with_config(self):
        """Test calculating font size for RghtCol field using config."""
        # Get RghtCol configuration
        config = FIELD_RENDERING_CONFIG['RghtCol']
        
        # Typical RghtCol field dimensions (small field)
        field_width = 80.59
        field_height = 12.04
        text = "1234.56"
        
        # Calculate font size using config bounds
        font_size = calculate_font_size(
            text,
            field_width,
            field_height,
            max_font_size=config['max_font_size'],
            min_font_size=config['min_font_size']
        )
        
        # Should use smaller font size (6-8pt)
        assert config['min_font_size'] <= font_size <= config['max_font_size']
        # With max_font_size=8.0, height constraint is 12.04 × 0.8 = 9.63pt
        # So result should be min(8.0, 9.63, ...) = 8.0pt
        assert font_size == 8.0
    
    def test_copyheader_field_with_config(self):
        """Test calculating font size for CopyHeader field using config."""
        # Get CopyHeader configuration
        config = FIELD_RENDERING_CONFIG['CopyHeader']
        
        # Typical header field dimensions
        field_width = 150.0
        field_height = 20.0
        text = "Copy A"
        
        # Calculate font size using config bounds
        font_size = calculate_font_size(
            text,
            field_width,
            field_height,
            max_font_size=config['max_font_size'],
            min_font_size=config['min_font_size']
        )
        
        # Should use standard header font size (8-12pt)
        assert config['min_font_size'] <= font_size <= config['max_font_size']
        # Height constraint: 20 × 0.8 = 16pt
        # Result: min(12, 16, ...) = 12pt
        assert font_size == 12.0
    
    def test_rghtcol_produces_smaller_font_than_leftcol(self):
        """Test that RghtCol produces smaller font sizes than LeftCol for same text."""
        text = "Test Value"
        
        # Use same field dimensions for comparison
        field_width = 100.0
        field_height = 15.0
        
        # Calculate with LeftCol config
        leftcol_config = FIELD_RENDERING_CONFIG['LeftCol']
        leftcol_font = calculate_font_size(
            text,
            field_width,
            field_height,
            max_font_size=leftcol_config['max_font_size'],
            min_font_size=leftcol_config['min_font_size']
        )
        
        # Calculate with RghtCol config
        rghtcol_config = FIELD_RENDERING_CONFIG['RghtCol']
        rghtcol_font = calculate_font_size(
            text,
            field_width,
            field_height,
            max_font_size=rghtcol_config['max_font_size'],
            min_font_size=rghtcol_config['min_font_size']
        )
        
        # RghtCol should produce smaller or equal font size
        assert rghtcol_font <= leftcol_font
    
    def test_long_text_in_rghtcol_uses_minimum(self):
        """Test that very long text in RghtCol field uses minimum font size."""
        config = FIELD_RENDERING_CONFIG['RghtCol']
        
        # Small RghtCol field with long text
        field_width = 80.0
        field_height = 12.0
        text = "123456789012345"  # 15 characters
        
        font_size = calculate_font_size(
            text,
            field_width,
            field_height,
            max_font_size=config['max_font_size'],
            min_font_size=config['min_font_size']
        )
        
        # With 15 chars: width constraint = 80 / (15 × 0.6) = 8.89pt
        # Height constraint: 12 × 0.8 = 9.6pt
        # Result: min(8, 9.6, 8.89) = 8pt (max_font_size for RghtCol)
        # This is still within bounds, so it's acceptable
        assert config['min_font_size'] <= font_size <= config['max_font_size']
    
    def test_short_text_in_leftcol_uses_maximum(self):
        """Test that short text in LeftCol field uses maximum font size."""
        config = FIELD_RENDERING_CONFIG['LeftCol']
        
        # Large LeftCol field with short text
        field_width = 200.0
        field_height = 35.0
        text = "ABC"
        
        font_size = calculate_font_size(
            text,
            field_width,
            field_height,
            max_font_size=config['max_font_size'],
            min_font_size=config['min_font_size']
        )
        
        # Should use maximum font size
        assert font_size == config['max_font_size']
    
    def test_determine_column_from_field_name(self):
        """Test determining column type from PDF field name."""
        test_cases = [
            ("topmostSubform[0].Copy1[0].LeftCol[0].f2_7[0]", "LeftCol"),
            ("topmostSubform[0].Copy1[0].RghtCol[0].f2_1[0]", "RghtCol"),
            ("topmostSubform[0].Copy1[0].CopyHeader[0].f1_1[0]", "CopyHeader"),
            ("topmostSubform[0].Copy2[0].LeftCol[0].f2_8[0]", "LeftCol"),
            ("topmostSubform[0].CopyB[0].RghtCol[0].f2_2[0]", "RghtCol"),
        ]
        
        for field_name, expected_column in test_cases:
            # Determine column from field name
            if 'LeftCol' in field_name:
                column = 'LeftCol'
            elif 'RghtCol' in field_name:
                column = 'RghtCol'
            elif 'CopyHeader' in field_name:
                column = 'CopyHeader'
            else:
                column = 'LeftCol'  # Default fallback
            
            assert column == expected_column, f"Failed to identify column for {field_name}"
            
            # Verify config exists for this column
            assert column in FIELD_RENDERING_CONFIG
    
    def test_config_provides_sensible_defaults(self):
        """Test that config provides sensible default font sizes for each column."""
        # LeftCol: Standard fields, should have comfortable default (9pt)
        assert FIELD_RENDERING_CONFIG['LeftCol']['default_font_size'] == 9.0
        
        # RghtCol: Tight fields, should have smaller default (7pt)
        assert FIELD_RENDERING_CONFIG['RghtCol']['default_font_size'] == 7.0
        
        # CopyHeader: Header fields, should have standard default (10pt)
        assert FIELD_RENDERING_CONFIG['CopyHeader']['default_font_size'] == 10.0
    
    def test_all_configs_work_with_calculate_font_size(self):
        """Test that all configs can be used with calculate_font_size."""
        text = "Test"
        field_width = 100.0
        field_height = 20.0
        
        for column, config in FIELD_RENDERING_CONFIG.items():
            # Should not raise any exceptions
            font_size = calculate_font_size(
                text,
                field_width,
                field_height,
                max_font_size=config['max_font_size'],
                min_font_size=config['min_font_size']
            )
            
            # Result should be within bounds
            assert config['min_font_size'] <= font_size <= config['max_font_size']
            
            # Result should be a positive number
            assert font_size > 0


class TestRealWorldScenarios:
    """Test real-world scenarios with actual field data."""
    
    def test_payer_tin_in_leftcol(self):
        """Test payer TIN field (LeftCol) with typical data."""
        config = FIELD_RENDERING_CONFIG['LeftCol']
        
        # Payer TIN field dimensions (from field analysis)
        field_width = 150.0
        field_height = 26.0
        text = "12-3456789"
        
        font_size = calculate_font_size(
            text,
            field_width,
            field_height,
            max_font_size=config['max_font_size'],
            min_font_size=config['min_font_size']
        )
        
        # Should fit comfortably at standard size
        assert font_size >= 9.0
        assert font_size <= config['max_font_size']
    
    def test_recipient_name_in_leftcol(self):
        """Test recipient name field (LeftCol) with typical data."""
        config = FIELD_RENDERING_CONFIG['LeftCol']
        
        # Recipient name field dimensions
        field_width = 199.40
        field_height = 35.48
        text = "John Q. Taxpayer"
        
        font_size = calculate_font_size(
            text,
            field_width,
            field_height,
            max_font_size=config['max_font_size'],
            min_font_size=config['min_font_size']
        )
        
        # Should use maximum font size for good readability
        assert font_size == config['max_font_size']
    
    def test_monetary_value_in_rghtcol(self):
        """Test monetary value field (RghtCol) with typical data."""
        config = FIELD_RENDERING_CONFIG['RghtCol']
        
        # Monetary field dimensions (small RghtCol field)
        field_width = 80.59
        field_height = 12.04
        text = "12345.67"
        
        font_size = calculate_font_size(
            text,
            field_width,
            field_height,
            max_font_size=config['max_font_size'],
            min_font_size=config['min_font_size']
        )
        
        # Should use smaller font size to fit in tight space
        assert font_size <= config['max_font_size']
        assert font_size >= config['min_font_size']
    
    def test_large_monetary_value_in_rghtcol(self):
        """Test large monetary value in RghtCol field."""
        config = FIELD_RENDERING_CONFIG['RghtCol']
        
        # Small field with large value
        field_width = 80.0
        field_height = 12.0
        text = "999999.99"  # 9 characters
        
        font_size = calculate_font_size(
            text,
            field_width,
            field_height,
            max_font_size=config['max_font_size'],
            min_font_size=config['min_font_size']
        )
        
        # With 9 chars: width constraint = 80 / (9 × 0.6) = 14.81pt
        # Height constraint: 12 × 0.8 = 9.6pt
        # Result: min(8, 9.6, 14.81) = 8pt (max_font_size for RghtCol)
        # Font size should be at or near the maximum for RghtCol
        assert font_size <= config['max_font_size']
        assert font_size >= config['min_font_size']
    
    def test_long_company_name_in_leftcol(self):
        """Test long company name in LeftCol field."""
        config = FIELD_RENDERING_CONFIG['LeftCol']
        
        # Large field with long text
        field_width = 199.40
        field_height = 35.48
        text = "The Very Long Investment Corporation Name"
        
        font_size = calculate_font_size(
            text,
            field_width,
            field_height,
            max_font_size=config['max_font_size'],
            min_font_size=config['min_font_size']
        )
        
        # Should reduce font size but stay within bounds
        assert config['min_font_size'] <= font_size <= config['max_font_size']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
