"""
Test script to verify enhanced logging for rendering failures (Task 4.3).

This script tests that the logging enhancements include:
1. Field name, text length, field dimensions, and font size used
2. Success with reduced font size
3. Final failure with details

Requirements: 1.3, 2.3, 3.3
"""

import unittest
from unittest.mock import Mock, patch
import fitz  # PyMuPDF

from tax_document_generation.document_generator import insert_text_with_fallback


class TestTask43Logging(unittest.TestCase):
    """Test enhanced logging for rendering failures."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_page = Mock(spec=fitz.Page)
        self.mock_rect = Mock(spec=fitz.Rect)
        self.mock_rect.width = 100.0
        self.mock_rect.height = 12.0
    
    def test_success_logging_includes_all_required_details(self):
        """Test that success logging includes field name, text length, dimensions, and font size."""
        # Arrange
        self.mock_page.insert_textbox.return_value = 1.0  # Success
        
        # Act
        with patch('tax_document_generation.document_generator.logger') as mock_logger:
            result = insert_text_with_fallback(
                page=self.mock_page,
                rect=self.mock_rect,
                text="Test Value",
                field_name="test_field",
                default_font_size=10.0
            )
        
        # Assert
        self.assertTrue(result)
        mock_logger.info.assert_called_once()
        
        log_message = mock_logger.info.call_args[0][0]
        
        # Verify all required details are in the log message
        self.assertIn("test_field", log_message, "Field name should be logged")
        self.assertIn("10", log_message, "Text length should be logged")
        self.assertIn("100.0x12.0", log_message, "Field dimensions should be logged")
        self.assertIn("10.0pt", log_message, "Font size used should be logged")
        self.assertIn("Successfully rendered", log_message, "Success message should be logged")
    
    def test_success_with_reduced_font_logging(self):
        """Test that success with reduced font size is logged with all details."""
        # Arrange
        # First attempt fails, second succeeds
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
        mock_logger.info.assert_called_once()
        
        log_message = mock_logger.info.call_args[0][0]
        
        # Verify all required details are in the log message
        self.assertIn("test_field", log_message, "Field name should be logged")
        self.assertIn("reduced font size", log_message, "Reduced font size message should be logged")
        self.assertIn("9.0pt", log_message, "Reduced font size should be logged")
        self.assertIn("10.0pt", log_message, "Default font size should be logged")
        self.assertIn("15", log_message, "Text length should be logged")
        self.assertIn("100.0x12.0", log_message, "Field dimensions should be logged")
        self.assertIn("2 attempt", log_message, "Number of attempts should be logged")
    
    def test_final_failure_logging_includes_all_details(self):
        """Test that final failure logging includes all required details."""
        # Arrange
        # All attempts fail
        self.mock_page.insert_textbox.return_value = -2.0
        
        # Act
        with patch('tax_document_generation.document_generator.logger') as mock_logger:
            result = insert_text_with_fallback(
                page=self.mock_page,
                rect=self.mock_rect,
                text="Text That Cannot Fit",
                field_name="test_field",
                default_font_size=10.0,
                min_font_size=6.0
            )
        
        # Assert
        self.assertFalse(result)
        mock_logger.error.assert_called_once()
        
        error_message = mock_logger.error.call_args[0][0]
        
        # Verify all required details are in the error message
        self.assertIn("test_field", error_message, "Field name should be logged")
        self.assertIn("Failed to render", error_message, "Failure message should be logged")
        self.assertIn("3 attempts", error_message, "Number of attempts should be logged")
        self.assertIn("Text length: 20", error_message, "Text length should be logged")
        self.assertIn("100.0x12.0", error_message, "Field dimensions should be logged")
        self.assertIn("8.0pt", error_message, "Final font size attempted should be logged")
        self.assertIn("6.0pt", error_message, "Minimum font size should be logged")
    
    def test_debug_logging_during_attempts(self):
        """Test that debug logging includes details during retry attempts."""
        # Arrange
        # First two attempts fail, third succeeds
        self.mock_page.insert_textbox.side_effect = [-1.0, -1.5, 1.0]
        
        # Act
        with patch('tax_document_generation.document_generator.logger') as mock_logger:
            result = insert_text_with_fallback(
                page=self.mock_page,
                rect=self.mock_rect,
                text="Test",
                field_name="test_field",
                default_font_size=10.0
            )
        
        # Assert
        self.assertTrue(result)
        
        # Verify debug logs were called for failed attempts
        self.assertGreaterEqual(mock_logger.debug.call_count, 2)
        
        # Check first debug log (first failed attempt)
        first_debug = mock_logger.debug.call_args_list[0][0][0]
        self.assertIn("test_field", first_debug, "Field name should be in debug log")
        self.assertIn("100.0x12.0", first_debug, "Dimensions should be in debug log")
        self.assertIn("10.0pt", first_debug, "Font size should be in debug log")
        self.assertIn("Attempt 1/3", first_debug, "Attempt number should be in debug log")


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
