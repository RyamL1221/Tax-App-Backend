"""
Integration tests for FATCA checkbox field handling.

This module tests that the FATCA filing requirement checkbox (Box 11)
is correctly set when generating 1099-DIV forms.
"""

import pytest
import pymupdf as fitz
from tax_document_generation.document_generator import generate_document


class TestFATCACheckboxIntegration:
    """Integration tests for FATCA checkbox handling."""
    
    @pytest.fixture
    def template(self):
        """Load the 1099-DIV template."""
        with open('samples/1099-DIV.pdf', 'rb') as f:
            return f.read()
    
    @pytest.fixture
    def minimal_form_data(self):
        """Minimal form data for testing."""
        return {
            "calendarYear": "2024",
            "payerName": "Test Corp",
            "payerTIN": "12-3456789",
            "payerStreetAddress": "123 Main St",
            "payerCity": "New York",
            "payerState": "NY",
            "payerCountry": "USA",
            "payerZip": "10001",
            "recipientName": "John Doe",
            "recipientTIN": "987-65-4321",
            "recipientStreetAddress": "456 Oak Ave",
            "recipientCity": "Los Angeles",
            "recipientState": "CA",
            "recipientCountry": "USA",
            "recipientZip": "90001",
            "totalOrdinaryDividends": "1000.00"
        }
    
    def get_checkbox_value(self, pdf_bytes, field_name):
        """Helper to get checkbox value from generated PDF."""
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            for widget in page.widgets():
                if widget.field_name == field_name and widget.field_type == fitz.PDF_WIDGET_TYPE_CHECKBOX:
                    value = widget.field_value
                    doc.close()
                    return value
        
        doc.close()
        return None
    
    def test_fatca_checkbox_true(self, template, minimal_form_data):
        """Test that FATCA checkbox is checked when set to True."""
        # Add FATCA field set to True
        form_data = {**minimal_form_data, "fatcaFilingRequirement": True}
        
        # Generate document
        output = generate_document(template, form_data, "1099-DIV")
        
        # Verify checkbox is checked in Copy1
        checkbox_value = self.get_checkbox_value(
            output,
            "topmostSubform[0].Copy1[0].RghtCol[0].TagCorrectingSubform[0].c2_3[0]"
        )
        
        # PyMuPDF represents checked checkboxes as "1" or 1
        assert checkbox_value in ['1', 1, 'Yes'], \
            f"Expected checkbox to be checked, but got value: {checkbox_value}"
    
    def test_fatca_checkbox_false(self, template, minimal_form_data):
        """Test that FATCA checkbox is unchecked when set to False."""
        # Add FATCA field set to False
        form_data = {**minimal_form_data, "fatcaFilingRequirement": False}
        
        # Generate document
        output = generate_document(template, form_data, "1099-DIV")
        
        # Verify checkbox is unchecked in Copy1
        checkbox_value = self.get_checkbox_value(
            output,
            "topmostSubform[0].Copy1[0].RghtCol[0].TagCorrectingSubform[0].c2_3[0]"
        )
        
        # PyMuPDF represents unchecked checkboxes as "Off", "0", 0, or False
        assert checkbox_value in ['Off', '0', 0, False, None], \
            f"Expected checkbox to be unchecked, but got value: {checkbox_value}"
    
    def test_fatca_checkbox_omitted(self, template, minimal_form_data):
        """Test that FATCA checkbox is unchecked when field is omitted."""
        # Don't include FATCA field
        form_data = minimal_form_data
        
        # Generate document
        output = generate_document(template, form_data, "1099-DIV")
        
        # Verify checkbox is unchecked in Copy1
        checkbox_value = self.get_checkbox_value(
            output,
            "topmostSubform[0].Copy1[0].RghtCol[0].TagCorrectingSubform[0].c2_3[0]"
        )
        
        # When field is omitted, checkbox should remain in default state (unchecked)
        assert checkbox_value in ['Off', '0', 0, False, None], \
            f"Expected checkbox to be unchecked when omitted, but got value: {checkbox_value}"
    
    def test_fatca_checkbox_string_true(self, template, minimal_form_data):
        """Test that FATCA checkbox is checked when set to string 'true'."""
        # Add FATCA field set to string "true"
        form_data = {**minimal_form_data, "fatcaFilingRequirement": "true"}
        
        # Generate document
        output = generate_document(template, form_data, "1099-DIV")
        
        # Verify checkbox is checked in Copy1
        checkbox_value = self.get_checkbox_value(
            output,
            "topmostSubform[0].Copy1[0].RghtCol[0].TagCorrectingSubform[0].c2_3[0]"
        )
        
        assert checkbox_value in ['1', 1, 'Yes'], \
            f"Expected checkbox to be checked for string 'true', but got value: {checkbox_value}"
    
    def test_fatca_checkbox_all_copies(self, template, minimal_form_data):
        """Test that FATCA checkbox is set correctly in all copies."""
        # Add FATCA field set to True
        form_data = {**minimal_form_data, "fatcaFilingRequirement": True}
        
        # Generate document
        output = generate_document(template, form_data, "1099-DIV")
        
        # Check all three copies
        copies = [
            "topmostSubform[0].Copy1[0].RghtCol[0].TagCorrectingSubform[0].c2_3[0]",
            "topmostSubform[0].CopyB[0].RghtCol[0].TagCorrectingSubform[0].c2_3[0]",
            "topmostSubform[0].Copy2[0].RghtCol[0].TagCorrectingSubform[0].c2_3[0]"
        ]
        
        for copy_field in copies:
            checkbox_value = self.get_checkbox_value(output, copy_field)
            assert checkbox_value in ['1', 1, 'Yes'], \
                f"Expected checkbox in {copy_field} to be checked, but got value: {checkbox_value}"
