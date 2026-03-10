"""
Unit tests for text insertion with fallback logic.

Tests the insert_text_with_fallback() function to verify:
- Successful insertion at default font size
- Fallback to smaller font sizes when text doesn't fit
- Failure after all attempts exhausted
- Proper logging of success/failure

Requirements: 1.2, 2.2, 3.2
"""

import unittest
from unittest.mock import Mock, patch, call
import fitz  # PyMuPDF

from tax_document_generation.document_generator import insert_text_with_fallback


class TestTextInsertionFallback(unittest.TestCase):
    """Unit tests for insert_text_with_fallback function."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a mock page object
        self.mock_page = Mock(spec=fitz.Page)
        
        # Create a mock rect
        self.mock_rect = Mock(spec=fitz.Rect)
        self.mock_rect.width = 100.0
        self.mock_rect.height = 12.0
    
    def test_successful_insertion_at_default_font_size(self):
        """Test successful text insertion at default font size."""
        # Arrange
        self.mock_page.insert_textbox.return_value = 1.0  # Success (rc >= 0)
        
        # Act
        result = insert_text_with_fallback(
            page=self.mock_page,
            rect=self.mock_rect,
            text="Test Value",
            field_name="test_field",
            default_font_size=10.0
        )
        
        # Assert
        self.assertTrue(result)
        self.mock_page.insert_textbox.assert_called_once()
        
        # Verify the call arguments
        call_args = self.mock_page.insert_textbox.call_args
        self.assertEqual(call_args[0][0], self.mock_rect)  # rect
        self.assertEqual(call_args[0][1], "Test Value")  # text
        self.assertEqual(call_args[1]['fontsize'], 10.0)  # font size
        self.assertEqual(call_args[1]['fontname'], "helv")  # font name
    
    def test_fallback_to_smaller_font_size_on_first_failure(self):
        """Test fallback to smaller font size when first attempt fails."""
        # Arrange
        # First attempt fails (rc < 0), second attempt succeeds
        self.mock_page.insert_textbox.side_effect = [-1.0, 1.0]
        
        # Act
        with patch('tax_document_generation.document_generator.logger') as mock_logger:
            result = insert_text_with_fallback(
                page=self.mock_page,
                rect=self.mock_rect,
                text="Long Text Value",
                field_name="test_field",
                default_font_size=10.0
            )
        
        # Assert
        self.assertTrue(result)
        self.assertEqual(self.mock_page.insert_textbox.call_count, 2)
        
        # Verify font sizes used
        first_call = self.mock_page.insert_textbox.call_args_list[0]
        second_call = self.mock_page.insert_textbox.call_args_list[1]
        
        self.assertEqual(first_call[1]['fontsize'], 10.0)  # First attempt
        self.assertEqual(second_call[1]['fontsize'], 9.0)  # Second attempt (reduced by 1)
        
        # Verify success logging
        mock_logger.info.assert_called()
        log_message = mock_logger.info.call_args[0][0]
        self.assertIn("Successfully rendered", log_message)
        self.assertIn("9.0pt", log_message)
    
    def test_multiple_fallback_attempts(self):
        """Test multiple fallback attempts before success."""
        # Arrange
        # First two attempts fail, third succeeds
        self.mock_page.insert_textbox.side_effect = [-1.0, -1.5, 1.0]
        
        # Act
        with patch('tax_document_generation.document_generator.logger') as mock_logger:
            result = insert_text_with_fallback(
                page=self.mock_page,
                rect=self.mock_rect,
                text="Very Long Text Value That Needs Small Font",
                field_name="test_field",
                default_font_size=10.0
            )
        
        # Assert
        self.assertTrue(result)
        self.assertEqual(self.mock_page.insert_textbox.call_count, 3)
        
        # Verify font sizes used: 10.0, 9.0, 8.0
        calls = self.mock_page.insert_textbox.call_args_list
        self.assertEqual(calls[0][1]['fontsize'], 10.0)
        self.assertEqual(calls[1][1]['fontsize'], 9.0)
        self.assertEqual(calls[2][1]['fontsize'], 8.0)
    
    def test_failure_after_all_attempts_exhausted(self):
        """Test failure when all retry attempts are exhausted."""
        # Arrange
        # All attempts fail
        self.mock_page.insert_textbox.return_value = -2.0  # Always fails
        
        # Act
        with patch('tax_document_generation.document_generator.logger') as mock_logger:
            result = insert_text_with_fallback(
                page=self.mock_page,
                rect=self.mock_rect,
                text="Extremely Long Text That Cannot Fit",
                field_name="test_field",
                default_font_size=10.0,
                min_font_size=6.0
            )
        
        # Assert
        self.assertFalse(result)
        self.assertEqual(self.mock_page.insert_textbox.call_count, 3)  # Max 3 attempts
        
        # Verify error logging
        mock_logger.error.assert_called()
        error_message = mock_logger.error.call_args[0][0]
        self.assertIn("Failed to render", error_message)
        self.assertIn("after 3 attempts", error_message)
    
    def test_respects_minimum_font_size(self):
        """Test that function respects minimum font size constraint."""
        # Arrange
        # All attempts fail
        self.mock_page.insert_textbox.return_value = -1.0
        
        # Act
        with patch('tax_document_generation.document_generator.logger') as mock_logger:
            result = insert_text_with_fallback(
                page=self.mock_page,
                rect=self.mock_rect,
                text="Text",
                field_name="test_field",
                default_font_size=7.0,
                min_font_size=6.0
            )
        
        # Assert
        self.assertFalse(result)
        
        # Should try: 7.0, 6.0, then stop (5.0 would be below minimum)
        # But we allow 3 attempts, so it tries 7.0, 6.0, 5.0 (which triggers warning)
        calls = self.mock_page.insert_textbox.call_args_list
        
        # Verify warning about minimum font size
        mock_logger.warning.assert_called()
        warning_message = mock_logger.warning.call_args[0][0]
        self.assertIn("minimum font size", warning_message)
    
    def test_custom_text_color(self):
        """Test that custom text color is passed through correctly."""
        # Arrange
        self.mock_page.insert_textbox.return_value = 1.0
        custom_color = (1, 0, 0)  # Red
        
        # Act
        result = insert_text_with_fallback(
            page=self.mock_page,
            rect=self.mock_rect,
            text="Red Text",
            field_name="test_field",
            text_color=custom_color
        )
        
        # Assert
        self.assertTrue(result)
        call_args = self.mock_page.insert_textbox.call_args
        self.assertEqual(call_args[1]['color'], custom_color)
    
    def test_empty_text_handling(self):
        """Test handling of empty text."""
        # Arrange
        self.mock_page.insert_textbox.return_value = 1.0
        
        # Act
        result = insert_text_with_fallback(
            page=self.mock_page,
            rect=self.mock_rect,
            text="",
            field_name="test_field"
        )
        
        # Assert
        self.assertTrue(result)
        self.mock_page.insert_textbox.assert_called_once()
    
    def test_logging_includes_field_dimensions(self):
        """Test that logging includes field dimensions for debugging."""
        # Arrange
        self.mock_page.insert_textbox.return_value = -1.0  # Always fails
        
        # Act
        with patch('tax_document_generation.document_generator.logger') as mock_logger:
            result = insert_text_with_fallback(
                page=self.mock_page,
                rect=self.mock_rect,
                text="Test",
                field_name="test_field"
            )
        
        # Assert
        self.assertFalse(result)
        
        # Check that debug logs include dimensions
        debug_calls = [call[0][0] for call in mock_logger.debug.call_args_list]
        self.assertTrue(any("100.0x12.0" in msg for msg in debug_calls))


if __name__ == '__main__':
    unittest.main()
