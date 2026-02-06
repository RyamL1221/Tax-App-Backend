"""
Unit tests for checkbox flattening function.

Tests the flatten_checkbox() function to verify:
- Checkmark drawing for checked state
- Empty box drawing for unchecked state
- Proportional sizing for different checkbox dimensions
- Error handling and graceful degradation

**Validates: Requirements 1.1, 2.1**
"""

import unittest
from unittest.mock import Mock, patch, call
import fitz  # PyMuPDF

from tax_document_generation.document_generator import flatten_checkbox


class TestFlattenCheckbox(unittest.TestCase):
    """Unit tests for flatten_checkbox function."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a mock page object
        self.mock_page = Mock(spec=fitz.Page)
        
        # Create a mock widget with a standard 9×9 checkbox rect
        self.mock_widget = Mock(spec=fitz.Widget)
        self.mock_rect = fitz.Rect(100.0, 200.0, 109.0, 209.0)  # 9×9 checkbox
        self.mock_widget.rect = self.mock_rect
    
    def test_draws_empty_box_for_unchecked_state(self):
        """Test that unchecked checkbox draws only the border."""
        # Act
        with patch('tax_document_generation.document_generator.logger') as mock_logger:
            flatten_checkbox(
                page=self.mock_page,
                widget=self.mock_widget,
                value="Off"
            )
        
        # Assert - should draw rectangle border only
        self.mock_page.draw_rect.assert_called_once()
        
        # Verify rectangle parameters
        call_args = self.mock_page.draw_rect.call_args
        self.assertEqual(call_args[0][0], self.mock_rect)  # rect
        self.assertEqual(call_args[1]['color'], (0, 0, 0))  # black
        self.assertEqual(call_args[1]['width'], 0.5)  # 0.5pt line width
        
        # Should NOT draw any lines (no checkmark)
        self.mock_page.draw_line.assert_not_called()
        
        # Verify logging
        debug_calls = [call[0][0] for call in mock_logger.debug.call_args_list]
        self.assertTrue(any("empty checkbox" in msg for msg in debug_calls))
    
    def test_draws_checkmark_for_checked_state_with_on_state_1(self):
        """Test that checked checkbox (on_state='1') draws border and checkmark."""
        # Act
        with patch('tax_document_generation.document_generator.logger') as mock_logger:
            flatten_checkbox(
                page=self.mock_page,
                widget=self.mock_widget,
                value="1"  # on_state value
            )
        
        # Assert - should draw rectangle border
        self.mock_page.draw_rect.assert_called_once()
        
        # Should draw two lines for checkmark
        self.assertEqual(self.mock_page.draw_line.call_count, 2)
        
        # Verify checkmark lines are drawn with correct parameters
        line_calls = self.mock_page.draw_line.call_args_list
        
        # Both lines should be black with 1.5pt width
        for line_call in line_calls:
            self.assertEqual(line_call[1]['color'], (0, 0, 0))
            self.assertEqual(line_call[1]['width'], 1.5)
        
        # Verify logging
        debug_calls = [call[0][0] for call in mock_logger.debug.call_args_list]
        self.assertTrue(any("Drew checkmark" in msg for msg in debug_calls))
    
    def test_draws_checkmark_for_checked_state_with_on_state_2(self):
        """Test that checked checkbox (on_state='2') draws border and checkmark."""
        # Act
        flatten_checkbox(
            page=self.mock_page,
            widget=self.mock_widget,
            value="2"  # alternative on_state value
        )
        
        # Assert - should draw rectangle border
        self.mock_page.draw_rect.assert_called_once()
        
        # Should draw two lines for checkmark
        self.assertEqual(self.mock_page.draw_line.call_count, 2)
    
    def test_proportional_checkmark_coordinates_standard_9x9(self):
        """Test that checkmark coordinates are proportional for standard 9×9 checkbox."""
        # Act
        flatten_checkbox(
            page=self.mock_page,
            widget=self.mock_widget,
            value="1"
        )
        
        # Assert - verify checkmark coordinates are proportional
        line_calls = self.mock_page.draw_line.call_args_list
        
        # Extract the two line segments
        line1_p1 = line_calls[0][0][0]  # First line, first point
        line1_p2 = line_calls[0][0][1]  # First line, second point
        line2_p1 = line_calls[1][0][0]  # Second line, first point
        line2_p2 = line_calls[1][0][1]  # Second line, second point
        
        # Verify proportional coordinates based on implementation
        # Left stroke: from (x0 + width*0.2, y0 + height*0.5) to (x0 + width*0.4, y0 + height*0.7)
        x0, y0, x1, y1 = self.mock_rect
        width = x1 - x0  # 9.0
        height = y1 - y0  # 9.0
        
        # First line (left stroke)
        expected_p1_x = x0 + width * 0.2  # 100 + 1.8 = 101.8
        expected_p1_y = y0 + height * 0.5  # 200 + 4.5 = 204.5
        expected_p2_x = x0 + width * 0.4  # 100 + 3.6 = 103.6
        expected_p2_y = y0 + height * 0.7  # 200 + 6.3 = 206.3
        
        self.assertAlmostEqual(line1_p1.x, expected_p1_x, places=1)
        self.assertAlmostEqual(line1_p1.y, expected_p1_y, places=1)
        self.assertAlmostEqual(line1_p2.x, expected_p2_x, places=1)
        self.assertAlmostEqual(line1_p2.y, expected_p2_y, places=1)
        
        # Second line (right stroke) - should start where first line ends
        expected_p3_x = x0 + width * 0.4  # 103.6
        expected_p3_y = y0 + height * 0.7  # 206.3
        expected_p4_x = x0 + width * 0.8  # 100 + 7.2 = 107.2
        expected_p4_y = y0 + height * 0.3  # 200 + 2.7 = 202.7
        
        self.assertAlmostEqual(line2_p1.x, expected_p3_x, places=1)
        self.assertAlmostEqual(line2_p1.y, expected_p3_y, places=1)
        self.assertAlmostEqual(line2_p2.x, expected_p4_x, places=1)
        self.assertAlmostEqual(line2_p2.y, expected_p4_y, places=1)
    
    def test_proportional_checkmark_coordinates_larger_checkbox(self):
        """Test that checkmark scales proportionally for larger checkbox."""
        # Create a larger checkbox (18×18)
        large_rect = fitz.Rect(100.0, 200.0, 118.0, 218.0)
        self.mock_widget.rect = large_rect
        
        # Act
        flatten_checkbox(
            page=self.mock_page,
            widget=self.mock_widget,
            value="1"
        )
        
        # Assert - verify checkmark coordinates scale proportionally
        line_calls = self.mock_page.draw_line.call_args_list
        
        x0, y0, x1, y1 = large_rect
        width = x1 - x0  # 18.0
        height = y1 - y0  # 18.0
        
        # First line
        line1_p1 = line_calls[0][0][0]
        expected_p1_x = x0 + width * 0.2  # 100 + 3.6 = 103.6
        expected_p1_y = y0 + height * 0.5  # 200 + 9.0 = 209.0
        
        self.assertAlmostEqual(line1_p1.x, expected_p1_x, places=1)
        self.assertAlmostEqual(line1_p1.y, expected_p1_y, places=1)
    
    def test_proportional_checkmark_coordinates_smaller_checkbox(self):
        """Test that checkmark scales proportionally for smaller checkbox."""
        # Create a smaller checkbox (6×6)
        small_rect = fitz.Rect(100.0, 200.0, 106.0, 206.0)
        self.mock_widget.rect = small_rect
        
        # Act
        flatten_checkbox(
            page=self.mock_page,
            widget=self.mock_widget,
            value="1"
        )
        
        # Assert - verify checkmark coordinates scale proportionally
        line_calls = self.mock_page.draw_line.call_args_list
        
        x0, y0, x1, y1 = small_rect
        width = x1 - x0  # 6.0
        height = y1 - y0  # 6.0
        
        # First line
        line1_p1 = line_calls[0][0][0]
        expected_p1_x = x0 + width * 0.2  # 100 + 1.2 = 101.2
        expected_p1_y = y0 + height * 0.5  # 200 + 3.0 = 203.0
        
        self.assertAlmostEqual(line1_p1.x, expected_p1_x, places=1)
        self.assertAlmostEqual(line1_p1.y, expected_p1_y, places=1)
    
    def test_proportional_checkmark_coordinates_rectangular_checkbox(self):
        """Test that checkmark scales proportionally for non-square checkbox."""
        # Create a rectangular checkbox (12×8)
        rect_checkbox = fitz.Rect(100.0, 200.0, 112.0, 208.0)
        self.mock_widget.rect = rect_checkbox
        
        # Act
        flatten_checkbox(
            page=self.mock_page,
            widget=self.mock_widget,
            value="1"
        )
        
        # Assert - verify checkmark coordinates scale proportionally
        line_calls = self.mock_page.draw_line.call_args_list
        
        x0, y0, x1, y1 = rect_checkbox
        width = x1 - x0  # 12.0
        height = y1 - y0  # 8.0
        
        # First line - should use width for x, height for y
        line1_p1 = line_calls[0][0][0]
        expected_p1_x = x0 + width * 0.2  # 100 + 2.4 = 102.4
        expected_p1_y = y0 + height * 0.5  # 200 + 4.0 = 204.0
        
        self.assertAlmostEqual(line1_p1.x, expected_p1_x, places=1)
        self.assertAlmostEqual(line1_p1.y, expected_p1_y, places=1)
    
    def test_handles_none_rect_gracefully(self):
        """Test that function handles None rect gracefully."""
        # Arrange
        self.mock_widget.rect = None
        
        # Act
        with patch('tax_document_generation.document_generator.logger') as mock_logger:
            flatten_checkbox(
                page=self.mock_page,
                widget=self.mock_widget,
                value="1"
            )
        
        # Assert - should not crash, should log error
        mock_logger.error.assert_called()
        error_message = mock_logger.error.call_args[0][0]
        self.assertIn("widget.rect is None", error_message)
        
        # Should not attempt to draw anything
        self.mock_page.draw_rect.assert_not_called()
        self.mock_page.draw_line.assert_not_called()
    
    def test_handles_draw_rect_exception_gracefully(self):
        """Test that function handles draw_rect exception gracefully."""
        # Arrange
        self.mock_page.draw_rect.side_effect = Exception("Drawing error")
        
        # Act
        with patch('tax_document_generation.document_generator.logger') as mock_logger:
            flatten_checkbox(
                page=self.mock_page,
                widget=self.mock_widget,
                value="Off"
            )
        
        # Assert - should log error but not raise
        mock_logger.error.assert_called()
        error_message = mock_logger.error.call_args[0][0]
        self.assertIn("Failed to flatten checkbox", error_message)
    
    def test_handles_draw_line_exception_gracefully(self):
        """Test that function handles draw_line exception gracefully."""
        # Arrange
        self.mock_page.draw_line.side_effect = Exception("Line drawing error")
        
        # Act
        with patch('tax_document_generation.document_generator.logger') as mock_logger:
            flatten_checkbox(
                page=self.mock_page,
                widget=self.mock_widget,
                value="1"
            )
        
        # Assert - should log error but not raise
        mock_logger.error.assert_called()
        error_message = mock_logger.error.call_args[0][0]
        self.assertIn("Failed to flatten checkbox", error_message)
    
    def test_logs_checkbox_dimensions(self):
        """Test that function logs checkbox dimensions for debugging."""
        # Act
        with patch('tax_document_generation.document_generator.logger') as mock_logger:
            flatten_checkbox(
                page=self.mock_page,
                widget=self.mock_widget,
                value="1"
            )
        
        # Assert - should log dimensions
        debug_calls = [call[0][0] for call in mock_logger.debug.call_args_list]
        
        # Should log dimensions in the format "9.0×9.0pt"
        self.assertTrue(any("9.0×9.0" in msg for msg in debug_calls))
    
    def test_checkmark_continuity(self):
        """Test that checkmark lines connect properly (second line starts where first ends)."""
        # Act
        flatten_checkbox(
            page=self.mock_page,
            widget=self.mock_widget,
            value="1"
        )
        
        # Assert - verify lines connect
        line_calls = self.mock_page.draw_line.call_args_list
        
        # End point of first line
        line1_end = line_calls[0][0][1]
        
        # Start point of second line
        line2_start = line_calls[1][0][0]
        
        # They should be the same point (checkmark is continuous)
        self.assertAlmostEqual(line1_end.x, line2_start.x, places=1)
        self.assertAlmostEqual(line1_end.y, line2_start.y, places=1)
    
    def test_empty_string_value_treated_as_checked(self):
        """Test that empty string value is treated as checked (not 'Off')."""
        # Act
        flatten_checkbox(
            page=self.mock_page,
            widget=self.mock_widget,
            value=""
        )
        
        # Assert - should draw border and checkmark (empty string != "Off")
        self.mock_page.draw_rect.assert_called_once()
        self.assertEqual(self.mock_page.draw_line.call_count, 2)
    
    def test_arbitrary_string_value_treated_as_checked(self):
        """Test that any non-'Off' string value is treated as checked."""
        # Act
        flatten_checkbox(
            page=self.mock_page,
            widget=self.mock_widget,
            value="Yes"
        )
        
        # Assert - should draw border and checkmark
        self.mock_page.draw_rect.assert_called_once()
        self.assertEqual(self.mock_page.draw_line.call_count, 2)
    
    def test_case_sensitive_off_value(self):
        """Test that 'Off' is case-sensitive."""
        # Act - test with different cases
        test_cases = [
            ("Off", False),  # Should be unchecked
            ("off", True),   # Should be checked (not exact match)
            ("OFF", True),   # Should be checked (not exact match)
        ]
        
        for value, should_draw_checkmark in test_cases:
            # Reset mocks
            self.mock_page.reset_mock()
            
            # Act
            flatten_checkbox(
                page=self.mock_page,
                widget=self.mock_widget,
                value=value
            )
            
            # Assert
            if should_draw_checkmark:
                self.assertEqual(
                    self.mock_page.draw_line.call_count, 2,
                    f"Value '{value}' should draw checkmark"
                )
            else:
                self.mock_page.draw_line.assert_not_called()
    
    def test_very_small_checkbox_still_draws(self):
        """Test that very small checkboxes still draw (edge case)."""
        # Create a very small checkbox (1×1)
        tiny_rect = fitz.Rect(100.0, 200.0, 101.0, 201.0)
        self.mock_widget.rect = tiny_rect
        
        # Act
        flatten_checkbox(
            page=self.mock_page,
            widget=self.mock_widget,
            value="1"
        )
        
        # Assert - should still draw border and checkmark
        self.mock_page.draw_rect.assert_called_once()
        self.assertEqual(self.mock_page.draw_line.call_count, 2)
    
    def test_zero_width_checkbox_edge_case(self):
        """Test handling of zero-width checkbox (edge case)."""
        # Create a zero-width checkbox
        zero_width_rect = fitz.Rect(100.0, 200.0, 100.0, 209.0)
        self.mock_widget.rect = zero_width_rect
        
        # Act
        flatten_checkbox(
            page=self.mock_page,
            widget=self.mock_widget,
            value="1"
        )
        
        # Assert - should still attempt to draw (may not be visible but shouldn't crash)
        self.mock_page.draw_rect.assert_called_once()
        # Checkmark lines will have same x coordinates but should still be drawn
        self.assertEqual(self.mock_page.draw_line.call_count, 2)
    
    def test_zero_height_checkbox_edge_case(self):
        """Test handling of zero-height checkbox (edge case)."""
        # Create a zero-height checkbox
        zero_height_rect = fitz.Rect(100.0, 200.0, 109.0, 200.0)
        self.mock_widget.rect = zero_height_rect
        
        # Act
        flatten_checkbox(
            page=self.mock_page,
            widget=self.mock_widget,
            value="1"
        )
        
        # Assert - should still attempt to draw
        self.mock_page.draw_rect.assert_called_once()
        self.assertEqual(self.mock_page.draw_line.call_count, 2)


class TestCheckmarkProportions:
    """Test suite specifically for checkmark proportional sizing."""
    
    def test_checkmark_proportions_are_consistent(self):
        """Test that checkmark proportions are consistent across different sizes."""
        # Test with multiple checkbox sizes
        test_sizes = [
            (6, 6),    # Small
            (9, 9),    # Standard
            (12, 12),  # Medium
            (18, 18),  # Large
        ]
        
        for width, height in test_sizes:
            # Arrange
            mock_page = Mock(spec=fitz.Page)
            mock_widget = Mock(spec=fitz.Widget)
            rect = fitz.Rect(100.0, 200.0, 100.0 + width, 200.0 + height)
            mock_widget.rect = rect
            
            # Act
            flatten_checkbox(
                page=mock_page,
                widget=mock_widget,
                value="1"
            )
            
            # Assert - verify proportions are maintained
            line_calls = mock_page.draw_line.call_args_list
            
            # Extract coordinates
            line1_p1 = line_calls[0][0][0]
            line1_p2 = line_calls[0][0][1]
            line2_p2 = line_calls[1][0][1]
            
            # Calculate relative positions (should be same proportions)
            rel_p1_x = (line1_p1.x - 100.0) / width
            rel_p1_y = (line1_p1.y - 200.0) / height
            rel_p2_x = (line1_p2.x - 100.0) / width
            rel_p2_y = (line1_p2.y - 200.0) / height
            rel_p4_x = (line2_p2.x - 100.0) / width
            rel_p4_y = (line2_p2.y - 200.0) / height
            
            # Verify proportions match expected values
            assert abs(rel_p1_x - 0.2) < 0.01, f"Size {width}×{height}: p1.x proportion incorrect"
            assert abs(rel_p1_y - 0.5) < 0.01, f"Size {width}×{height}: p1.y proportion incorrect"
            assert abs(rel_p2_x - 0.4) < 0.01, f"Size {width}×{height}: p2.x proportion incorrect"
            assert abs(rel_p2_y - 0.7) < 0.01, f"Size {width}×{height}: p2.y proportion incorrect"
            assert abs(rel_p4_x - 0.8) < 0.01, f"Size {width}×{height}: p4.x proportion incorrect"
            assert abs(rel_p4_y - 0.3) < 0.01, f"Size {width}×{height}: p4.y proportion incorrect"


if __name__ == '__main__':
    unittest.main()
