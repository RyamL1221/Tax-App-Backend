"""
Unit tests for field-specific rendering configuration.

Tests verify that FIELD_RENDERING_CONFIG is properly defined with
appropriate font size settings for different field types.

Requirements: 1.1, 2.1, 3.1
"""

import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from document_generator import FIELD_RENDERING_CONFIG


class TestFieldRenderingConfig:
    """Test suite for FIELD_RENDERING_CONFIG dictionary."""
    
    def test_config_exists(self):
        """Test that FIELD_RENDERING_CONFIG is defined."""
        assert FIELD_RENDERING_CONFIG is not None
        assert isinstance(FIELD_RENDERING_CONFIG, dict)
    
    def test_config_has_required_columns(self):
        """Test that config includes all required column types."""
        required_columns = ['LeftCol', 'RghtCol', 'CopyHeader']
        for column in required_columns:
            assert column in FIELD_RENDERING_CONFIG, f"Missing config for {column}"
    
    def test_leftcol_config(self):
        """Test LeftCol configuration has correct font sizes."""
        config = FIELD_RENDERING_CONFIG['LeftCol']
        
        # Verify all required keys exist
        assert 'default_font_size' in config
        assert 'min_font_size' in config
        assert 'max_font_size' in config
        
        # Verify font sizes are in expected range (9-10pt for LeftCol)
        assert config['default_font_size'] == 9.0
        assert config['min_font_size'] == 7.0
        assert config['max_font_size'] == 10.0
        
        # Verify logical ordering: min <= default <= max
        assert config['min_font_size'] <= config['default_font_size'] <= config['max_font_size']
    
    def test_rghtcol_config(self):
        """Test RghtCol configuration has smaller font sizes for tight boxes."""
        config = FIELD_RENDERING_CONFIG['RghtCol']
        
        # Verify all required keys exist
        assert 'default_font_size' in config
        assert 'min_font_size' in config
        assert 'max_font_size' in config
        
        # Verify font sizes are smaller (7-8pt for RghtCol)
        assert config['default_font_size'] == 7.0
        assert config['min_font_size'] == 6.0
        assert config['max_font_size'] == 8.0
        
        # Verify logical ordering: min <= default <= max
        assert config['min_font_size'] <= config['default_font_size'] <= config['max_font_size']
    
    def test_copyheader_config(self):
        """Test CopyHeader configuration has standard font sizes."""
        config = FIELD_RENDERING_CONFIG['CopyHeader']
        
        # Verify all required keys exist
        assert 'default_font_size' in config
        assert 'min_font_size' in config
        assert 'max_font_size' in config
        
        # Verify font sizes are standard (10-12pt for headers)
        assert config['default_font_size'] == 10.0
        assert config['min_font_size'] == 8.0
        assert config['max_font_size'] == 12.0
        
        # Verify logical ordering: min <= default <= max
        assert config['min_font_size'] <= config['default_font_size'] <= config['max_font_size']
    
    def test_rghtcol_smaller_than_leftcol(self):
        """Test that RghtCol has smaller font sizes than LeftCol."""
        leftcol = FIELD_RENDERING_CONFIG['LeftCol']
        rghtcol = FIELD_RENDERING_CONFIG['RghtCol']
        
        # RghtCol should have smaller default font size
        assert rghtcol['default_font_size'] < leftcol['default_font_size']
        
        # RghtCol should have smaller max font size
        assert rghtcol['max_font_size'] < leftcol['max_font_size']
    
    def test_all_font_sizes_positive(self):
        """Test that all font sizes are positive numbers."""
        for column, config in FIELD_RENDERING_CONFIG.items():
            assert config['default_font_size'] > 0, f"{column} default_font_size must be positive"
            assert config['min_font_size'] > 0, f"{column} min_font_size must be positive"
            assert config['max_font_size'] > 0, f"{column} max_font_size must be positive"
    
    def test_all_font_sizes_reasonable(self):
        """Test that all font sizes are in reasonable range (4-14pt)."""
        for column, config in FIELD_RENDERING_CONFIG.items():
            # Font sizes should be between 4pt and 14pt (reasonable for forms)
            assert 4.0 <= config['min_font_size'] <= 14.0, f"{column} min_font_size out of range"
            assert 4.0 <= config['default_font_size'] <= 14.0, f"{column} default_font_size out of range"
            assert 4.0 <= config['max_font_size'] <= 14.0, f"{column} max_font_size out of range"


class TestFieldRenderingConfigUsage:
    """Test suite for using FIELD_RENDERING_CONFIG in practice."""
    
    def test_get_config_for_leftcol_field(self):
        """Test retrieving config for a LeftCol field."""
        field_name = "topmostSubform[0].Copy1[0].LeftCol[0].f2_7[0]"
        
        # Determine column from field name
        if 'LeftCol' in field_name:
            config = FIELD_RENDERING_CONFIG['LeftCol']
            assert config['default_font_size'] == 9.0
    
    def test_get_config_for_rghtcol_field(self):
        """Test retrieving config for a RghtCol field."""
        field_name = "topmostSubform[0].Copy1[0].RghtCol[0].f2_1[0]"
        
        # Determine column from field name
        if 'RghtCol' in field_name:
            config = FIELD_RENDERING_CONFIG['RghtCol']
            assert config['default_font_size'] == 7.0
    
    def test_get_config_for_copyheader_field(self):
        """Test retrieving config for a CopyHeader field."""
        field_name = "topmostSubform[0].Copy1[0].CopyHeader[0].f1_1[0]"
        
        # Determine column from field name
        if 'CopyHeader' in field_name:
            config = FIELD_RENDERING_CONFIG['CopyHeader']
            assert config['default_font_size'] == 10.0
    
    def test_fallback_for_unknown_column(self):
        """Test fallback behavior for fields without recognized column."""
        field_name = "topmostSubform[0].Copy1[0].UnknownSection[0].f1_1[0]"
        
        # Should use a default config (e.g., LeftCol as fallback)
        # This test documents expected behavior for edge cases
        config = FIELD_RENDERING_CONFIG.get('LeftCol')  # Fallback to LeftCol
        assert config is not None
        assert config['default_font_size'] == 9.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
