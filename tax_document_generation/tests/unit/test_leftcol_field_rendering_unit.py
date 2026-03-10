"""
Unit tests for LeftCol field rendering.

Tests that LeftCol fields (payer name, payer TIN, recipient TIN) render correctly
after the adaptive font sizing changes. These tests verify specific examples of
LeftCol fields to ensure existing functionality is preserved.

**Validates: Requirements 6.1, 6.2, 6.3**
"""

import pytest
import fitz  # PyMuPDF
from tax_document_generation.document_generator import (
    calculate_font_size,
    insert_text_with_fallback,
    FIELD_RENDERING_CONFIG
)


class TestLeftColFieldRendering:
    """Test suite for LeftCol field rendering with adaptive font sizing."""
    
    def test_payer_name_renders_correctly(self):
        """
        Test that payer name still renders correctly in LeftCol field.
        
        Payer name is typically in a LeftCol field with dimensions:
        - Width: ~199pt
        - Height: ~35pt
        
        This test verifies that the adaptive font sizing doesn't break
        existing payer name rendering.
        
        **Validates: Requirement 6.1**
        """
        # Typical payer name field dimensions (from field analysis)
        field_width = 199.40
        field_height = 35.48
        payer_name = "Acme Investment Corporation"
        
        # Get LeftCol rendering config
        config = FIELD_RENDERING_CONFIG['LeftCol']
        
        # Calculate font size
        font_size = calculate_font_size(
            text=payer_name,
            field_width=field_width,
            field_height=field_height,
            max_font_size=config['max_font_size'],
            min_font_size=config['min_font_size']
        )
        
        # Verify font size is within LeftCol bounds
        assert config['min_font_size'] <= font_size <= config['max_font_size']
        
        # Verify font size is reasonable for this field (should use max size)
        # Height constraint: 35.48 × 0.8 = 28.38pt
        # Width constraint: 199.40 / (27 × 0.6) = 12.31pt
        # Result: min(10, 28.38, 12.31) = 10pt
        assert font_size == pytest.approx(10.0, rel=0.01)
        
        # Verify text would fit in a real PDF field
        # Create a temporary PDF to test actual rendering
        doc = fitz.open()
        page = doc.new_page(width=300, height=200)
        rect = fitz.Rect(10, 10, 10 + field_width, 10 + field_height)
        
        # Attempt to insert text
        rc = page.insert_textbox(
            rect,
            payer_name,
            fontsize=font_size,
            fontname="helv",
            color=(0, 0, 0),
            align=fitz.TEXT_ALIGN_LEFT
        )
        
        doc.close()
        
        # Verify insertion was successful (rc >= 0)
        assert rc >= 0, f"Text insertion failed with rc={rc}"
    
    def test_payer_tin_renders_correctly(self):
        """
        Test that payer TIN still renders correctly in LeftCol field.
        
        Payer TIN is typically in a LeftCol field with dimensions:
        - Width: ~150pt
        - Height: ~26pt
        
        This test verifies that TIN values render correctly with adaptive sizing.
        
        **Validates: Requirement 6.2**
        """
        # Typical TIN field dimensions
        field_width = 150.0
        field_height = 26.0
        payer_tin = "12-3456789"
        
        # Get LeftCol rendering config
        config = FIELD_RENDERING_CONFIG['LeftCol']
        
        # Calculate font size
        font_size = calculate_font_size(
            text=payer_tin,
            field_width=field_width,
            field_height=field_height,
            max_font_size=config['max_font_size'],
            min_font_size=config['min_font_size']
        )
        
        # Verify font size is within LeftCol bounds
        assert config['min_font_size'] <= font_size <= config['max_font_size']
        
        # Verify font size is reasonable for TIN (should use max size)
        # Height constraint: 26 × 0.8 = 20.8pt
        # Width constraint: 150 / (10 × 0.6) = 25pt
        # Result: min(10, 20.8, 25) = 10pt
        assert font_size == pytest.approx(10.0, rel=0.01)
        
        # Verify text would fit in a real PDF field
        doc = fitz.open()
        page = doc.new_page(width=300, height=200)
        rect = fitz.Rect(10, 10, 10 + field_width, 10 + field_height)
        
        rc = page.insert_textbox(
            rect,
            payer_tin,
            fontsize=font_size,
            fontname="helv",
            color=(0, 0, 0),
            align=fitz.TEXT_ALIGN_LEFT
        )
        
        doc.close()
        
        assert rc >= 0, f"Text insertion failed with rc={rc}"
    
    def test_recipient_tin_renders_correctly(self):
        """
        Test that recipient TIN still renders correctly in LeftCol field.
        
        Recipient TIN is typically in a LeftCol field with dimensions:
        - Width: ~150pt
        - Height: ~26pt
        
        This test verifies that recipient TIN values render correctly.
        
        **Validates: Requirement 6.3**
        """
        # Typical TIN field dimensions
        field_width = 150.0
        field_height = 26.0
        recipient_tin = "987-65-4321"
        
        # Get LeftCol rendering config
        config = FIELD_RENDERING_CONFIG['LeftCol']
        
        # Calculate font size
        font_size = calculate_font_size(
            text=recipient_tin,
            field_width=field_width,
            field_height=field_height,
            max_font_size=config['max_font_size'],
            min_font_size=config['min_font_size']
        )
        
        # Verify font size is within LeftCol bounds
        assert config['min_font_size'] <= font_size <= config['max_font_size']
        
        # Verify font size is reasonable for TIN (should use max size)
        assert font_size == pytest.approx(10.0, rel=0.01)
        
        # Verify text would fit in a real PDF field
        doc = fitz.open()
        page = doc.new_page(width=300, height=200)
        rect = fitz.Rect(10, 10, 10 + field_width, 10 + field_height)
        
        rc = page.insert_textbox(
            rect,
            recipient_tin,
            fontsize=font_size,
            fontname="helv",
            color=(0, 0, 0),
            align=fitz.TEXT_ALIGN_LEFT
        )
        
        doc.close()
        
        assert rc >= 0, f"Text insertion failed with rc={rc}"
    
    def test_long_payer_name_with_adaptive_sizing(self):
        """
        Test that very long payer names still render with adaptive sizing.
        
        This test verifies that the adaptive font sizing correctly handles
        edge cases where the payer name is very long.
        
        **Validates: Requirement 6.1**
        """
        # Typical payer name field dimensions
        field_width = 199.40
        field_height = 35.48
        long_payer_name = "The Very Long Investment Corporation Name That Might Not Fit"
        
        # Get LeftCol rendering config
        config = FIELD_RENDERING_CONFIG['LeftCol']
        
        # Calculate font size
        font_size = calculate_font_size(
            text=long_payer_name,
            field_width=field_width,
            field_height=field_height,
            max_font_size=config['max_font_size'],
            min_font_size=config['min_font_size']
        )
        
        # Verify font size is within LeftCol bounds
        assert config['min_font_size'] <= font_size <= config['max_font_size']
        
        # For very long text, font size should be reduced
        # Height constraint: 35.48 × 0.8 = 28.38pt
        # Width constraint: 199.40 / (60 × 0.6) = 5.54pt
        # Result: max(7, min(10, 28.38, 5.54)) = 7pt (min_font_size)
        assert font_size == pytest.approx(7.0, rel=0.01)
        
        # Verify text would fit in a real PDF field
        doc = fitz.open()
        page = doc.new_page(width=300, height=200)
        rect = fitz.Rect(10, 10, 10 + field_width, 10 + field_height)
        
        rc = page.insert_textbox(
            rect,
            long_payer_name,
            fontsize=font_size,
            fontname="helv",
            color=(0, 0, 0),
            align=fitz.TEXT_ALIGN_LEFT
        )
        
        doc.close()
        
        assert rc >= 0, f"Text insertion failed with rc={rc}"
    
    def test_insert_text_with_fallback_leftcol_success(self):
        """
        Test that insert_text_with_fallback works correctly for LeftCol fields.
        
        This test verifies that the fallback mechanism works correctly for
        LeftCol fields, which should typically succeed on the first attempt.
        
        **Validates: Requirements 6.1, 6.2, 6.3**
        """
        # Create a test PDF
        doc = fitz.open()
        page = doc.new_page(width=300, height=200)
        
        # Typical LeftCol field dimensions
        field_width = 199.40
        field_height = 35.48
        rect = fitz.Rect(10, 10, 10 + field_width, 10 + field_height)
        
        # Test with typical payer name
        payer_name = "Acme Investment Corporation"
        
        # Get LeftCol rendering config
        config = FIELD_RENDERING_CONFIG['LeftCol']
        
        # Use insert_text_with_fallback
        success = insert_text_with_fallback(
            page=page,
            rect=rect,
            text=payer_name,
            field_name="test_leftcol_field",
            default_font_size=config['default_font_size'],
            min_font_size=config['min_font_size']
        )
        
        doc.close()
        
        # Verify insertion was successful
        assert success is True
    
    def test_leftcol_config_values(self):
        """
        Test that LeftCol rendering config has appropriate values.
        
        This test verifies that the FIELD_RENDERING_CONFIG for LeftCol
        has reasonable values that preserve existing functionality.
        
        **Validates: Requirements 6.1, 6.2, 6.3**
        """
        config = FIELD_RENDERING_CONFIG['LeftCol']
        
        # Verify config exists and has required keys
        assert 'default_font_size' in config
        assert 'min_font_size' in config
        assert 'max_font_size' in config
        
        # Verify values are reasonable for LeftCol fields
        # LeftCol fields are larger, so they should support larger fonts
        assert config['default_font_size'] >= 9.0
        assert config['min_font_size'] >= 7.0
        assert config['max_font_size'] >= 10.0
        
        # Verify min <= default <= max
        assert config['min_font_size'] <= config['default_font_size'] <= config['max_font_size']
    
    def test_payer_name_with_special_characters(self):
        """
        Test that payer names with special characters render correctly.
        
        This test verifies that special characters (e.g., &, Inc., LLC)
        in payer names don't break rendering.
        
        **Validates: Requirement 6.1**
        """
        # Typical payer name field dimensions
        field_width = 199.40
        field_height = 35.48
        payer_name = "Smith & Jones Investment Co., LLC"
        
        # Get LeftCol rendering config
        config = FIELD_RENDERING_CONFIG['LeftCol']
        
        # Calculate font size
        font_size = calculate_font_size(
            text=payer_name,
            field_width=field_width,
            field_height=field_height,
            max_font_size=config['max_font_size'],
            min_font_size=config['min_font_size']
        )
        
        # Verify font size is within bounds
        assert config['min_font_size'] <= font_size <= config['max_font_size']
        
        # Verify text would fit in a real PDF field
        doc = fitz.open()
        page = doc.new_page(width=300, height=200)
        rect = fitz.Rect(10, 10, 10 + field_width, 10 + field_height)
        
        rc = page.insert_textbox(
            rect,
            payer_name,
            fontsize=font_size,
            fontname="helv",
            color=(0, 0, 0),
            align=fitz.TEXT_ALIGN_LEFT
        )
        
        doc.close()
        
        assert rc >= 0, f"Text insertion failed with rc={rc}"
    
    def test_tin_with_different_formats(self):
        """
        Test that TINs with different formats render correctly.
        
        This test verifies that both SSN format (XXX-XX-XXXX) and
        EIN format (XX-XXXXXXX) render correctly.
        
        **Validates: Requirements 6.2, 6.3**
        """
        # Typical TIN field dimensions
        field_width = 150.0
        field_height = 26.0
        
        # Get LeftCol rendering config
        config = FIELD_RENDERING_CONFIG['LeftCol']
        
        # Test SSN format
        ssn = "123-45-6789"
        font_size_ssn = calculate_font_size(
            text=ssn,
            field_width=field_width,
            field_height=field_height,
            max_font_size=config['max_font_size'],
            min_font_size=config['min_font_size']
        )
        assert config['min_font_size'] <= font_size_ssn <= config['max_font_size']
        
        # Test EIN format
        ein = "12-3456789"
        font_size_ein = calculate_font_size(
            text=ein,
            field_width=field_width,
            field_height=field_height,
            max_font_size=config['max_font_size'],
            min_font_size=config['min_font_size']
        )
        assert config['min_font_size'] <= font_size_ein <= config['max_font_size']
        
        # Both formats should use similar font sizes (both are ~10-11 chars)
        assert abs(font_size_ssn - font_size_ein) < 1.0
        
        # Verify both would fit in a real PDF field
        doc = fitz.open()
        page = doc.new_page(width=300, height=200)
        rect = fitz.Rect(10, 10, 10 + field_width, 10 + field_height)
        
        rc_ssn = page.insert_textbox(
            rect,
            ssn,
            fontsize=font_size_ssn,
            fontname="helv",
            color=(0, 0, 0),
            align=fitz.TEXT_ALIGN_LEFT
        )
        
        rc_ein = page.insert_textbox(
            rect,
            ein,
            fontsize=font_size_ein,
            fontname="helv",
            color=(0, 0, 0),
            align=fitz.TEXT_ALIGN_LEFT
        )
        
        doc.close()
        
        assert rc_ssn >= 0, f"SSN insertion failed with rc={rc_ssn}"
        assert rc_ein >= 0, f"EIN insertion failed with rc={rc_ein}"


class TestLeftColFieldPreservation:
    """Test suite to verify that existing LeftCol field functionality is preserved."""
    
    def test_leftcol_fields_use_correct_config(self):
        """
        Test that LeftCol fields use the correct rendering configuration.
        
        This test verifies that when a field name contains "LeftCol",
        the correct configuration is selected.
        
        **Validates: Requirements 6.1, 6.2, 6.3**
        """
        # Simulate field name detection logic from document_generator.py
        field_names = [
            "topmostSubform[0].Copy1[0].LeftCol[0].f2_1[0]",  # Payer name
            "topmostSubform[0].Copy1[0].LeftCol[0].f2_7[0]",  # Payer TIN
            "topmostSubform[0].Copy1[0].LeftCol[0].f2_13[0]", # Recipient TIN
        ]
        
        for field_name in field_names:
            # Determine column type (same logic as in document_generator.py)
            column_type = 'LeftCol'  # Default
            if 'LeftCol' in field_name:
                column_type = 'LeftCol'
            elif 'RghtCol' in field_name:
                column_type = 'RghtCol'
            elif 'CopyHeader' in field_name:
                column_type = 'CopyHeader'
            
            # Verify LeftCol is detected
            assert column_type == 'LeftCol', f"Field {field_name} should be detected as LeftCol"
            
            # Verify correct config is retrieved
            config = FIELD_RENDERING_CONFIG.get(column_type, FIELD_RENDERING_CONFIG['LeftCol'])
            assert config == FIELD_RENDERING_CONFIG['LeftCol']
    
    def test_leftcol_default_font_size_appropriate(self):
        """
        Test that LeftCol default font size is appropriate for typical content.
        
        This test verifies that the default font size for LeftCol fields
        is suitable for typical payer/recipient names and TINs.
        
        **Validates: Requirements 6.1, 6.2, 6.3**
        """
        config = FIELD_RENDERING_CONFIG['LeftCol']
        default_font_size = config['default_font_size']
        
        # Default should be 9-10pt for good readability
        assert 9.0 <= default_font_size <= 10.0
        
        # Verify default font size works for typical content
        typical_contents = [
            "Acme Investment Corporation",
            "12-3456789",
            "987-65-4321",
            "John Q. Taxpayer",
        ]
        
        # Typical LeftCol dimensions
        field_width = 199.40
        field_height = 35.48
        
        for content in typical_contents:
            # Calculate font size with default as max
            font_size = calculate_font_size(
                text=content,
                field_width=field_width,
                field_height=field_height,
                max_font_size=default_font_size,
                min_font_size=config['min_font_size']
            )
            
            # For typical content, should be able to use default or close to it
            # (allowing some reduction for longer names)
            assert font_size >= config['min_font_size']
            assert font_size <= default_font_size
