"""
Integration tests for CopyA checkbox rendering.

Tests that VOIDED and CORRECTED checkboxes render correctly on CopyA
after fixing the field name generation bug.

Requirements: 3.1, 3.2, 3.3
"""

import pytest
import pymupdf as fitz
from tax_document_generation.document_generator import generate_document
from tax_document_generation.field_mapper import FieldMapper


class TestVoidedCheckboxRendersOnCopyA:
    """Test VOIDED checkbox renders on CopyA."""
    
    def test_voided_checkbox_renders_on_copya(self):
        """Test VOIDED checkbox renders at correct field on CopyA."""
        # Form data with voided=True
        form_data = {
            "calendarYear": "2024",
            "voided": True,
            "payerName": "Test Payer",
            "payerTIN": "12-3456789",
            "recipientName": "Test Recipient",
            "recipientTIN": "987-65-4321",
            "totalOrdinaryDividends": "1000.00"
        }
        
        # Load template
        with open("samples/1099-DIV.pdf", "rb") as f:
            template_bytes = f.read()
        
        # Generate PDF
        pdf_bytes = generate_document(template_bytes, form_data, "1099-DIV")
        
        # Open generated PDF
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        
        # CopyA is on page 2 (index 1)
        page = doc[1]
        
        # Check for drawings (checkbox rendering creates line drawings)
        drawings = page.get_drawings()
        
        # Should have drawings on CopyA (checkboxes render as graphics)
        assert len(drawings) > 0, "CopyA should have drawings (checkbox graphics)"
        
        # Verify the VOIDED checkbox field was mapped correctly
        mapper = FieldMapper("1099-DIV")
        mapped_data = mapper.map_all_fields(form_data)
        
        # CopyA VOIDED field should be in mapped data
        copya_voided_field = "topmostSubform[0].CopyA[0].CopyHeader[0].c1_1[0]"
        assert copya_voided_field in mapped_data, f"CopyA VOIDED field {copya_voided_field} should be mapped"
        assert mapped_data[copya_voided_field] is True, "CopyA VOIDED field should be True"
        
        doc.close()


class TestCorrectedCheckboxRendersOnCopyA:
    """Test CORRECTED checkbox renders on CopyA."""
    
    def test_corrected_checkbox_renders_on_copya(self):
        """Test CORRECTED checkbox renders at correct field on CopyA."""
        # Form data with corrected=True
        form_data = {
            "calendarYear": "2024",
            "corrected": True,
            "payerName": "Test Payer",
            "payerTIN": "12-3456789",
            "recipientName": "Test Recipient",
            "recipientTIN": "987-65-4321",
            "totalOrdinaryDividends": "1000.00"
        }
        
        # Load template
        with open("samples/1099-DIV.pdf", "rb") as f:
            template_bytes = f.read()
        
        # Generate PDF
        pdf_bytes = generate_document(template_bytes, form_data, "1099-DIV")
        
        # Open generated PDF
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        
        # CopyA is on page 2 (index 1)
        page = doc[1]
        
        # Check for drawings
        drawings = page.get_drawings()
        
        # Should have drawings on CopyA
        assert len(drawings) > 0, "CopyA should have drawings (checkbox graphics)"
        
        # Verify the CORRECTED checkbox field was mapped correctly
        mapper = FieldMapper("1099-DIV")
        mapped_data = mapper.map_all_fields(form_data)
        
        # CopyA CORRECTED field should be in mapped data
        copya_corrected_field = "topmostSubform[0].CopyA[0].CopyHeader[0].c1_1[1]"
        assert copya_corrected_field in mapped_data, f"CopyA CORRECTED field {copya_corrected_field} should be mapped"
        assert mapped_data[copya_corrected_field] is True, "CopyA CORRECTED field should be True"
        
        doc.close()


class TestBothCheckboxesRenderOnCopyA:
    """Test both VOIDED and CORRECTED checkboxes render on CopyA."""
    
    def test_both_checkboxes_render_on_copya(self):
        """Test both checkboxes render when both flags are set."""
        # Form data with both voided=True and corrected=True
        form_data = {
            "calendarYear": "2024",
            "voided": True,
            "corrected": True,
            "payerName": "Test Payer",
            "payerTIN": "12-3456789",
            "recipientName": "Test Recipient",
            "recipientTIN": "987-65-4321",
            "totalOrdinaryDividends": "1000.00"
        }
        
        # Load template
        with open("samples/1099-DIV.pdf", "rb") as f:
            template_bytes = f.read()
        
        # Generate PDF
        pdf_bytes = generate_document(template_bytes, form_data, "1099-DIV")
        
        # Open generated PDF
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        
        # CopyA is on page 2 (index 1)
        page = doc[1]
        
        # Check for drawings
        drawings = page.get_drawings()
        
        # Should have drawings on CopyA (both checkboxes)
        assert len(drawings) > 0, "CopyA should have drawings (both checkbox graphics)"
        
        # Verify both checkbox fields were mapped correctly
        mapper = FieldMapper("1099-DIV")
        mapped_data = mapper.map_all_fields(form_data)
        
        # Both CopyA checkbox fields should be in mapped data
        copya_voided_field = "topmostSubform[0].CopyA[0].CopyHeader[0].c1_1[0]"
        copya_corrected_field = "topmostSubform[0].CopyA[0].CopyHeader[0].c1_1[1]"
        
        assert copya_voided_field in mapped_data, "CopyA VOIDED field should be mapped"
        assert copya_corrected_field in mapped_data, "CopyA CORRECTED field should be mapped"
        assert mapped_data[copya_voided_field] is True, "CopyA VOIDED should be True"
        assert mapped_data[copya_corrected_field] is True, "CopyA CORRECTED should be True"
        
        doc.close()


class TestCopy1Copy2CopyBStillWork:
    """Regression test: Verify Copy1, Copy2, CopyB checkboxes still work."""
    
    def test_voided_checkbox_renders_on_copy1(self):
        """Test VOIDED checkbox still renders on Copy1 (regression test)."""
        form_data = {
            "calendarYear": "2024",
            "voided": True,
            "payerName": "Test Payer",
            "payerTIN": "12-3456789",
            "recipientName": "Test Recipient",
            "recipientTIN": "987-65-4321",
            "totalOrdinaryDividends": "1000.00"
        }
        
        # Load template
        with open("samples/1099-DIV.pdf", "rb") as f:
            template_bytes = f.read()
        
        # Generate PDF
        pdf_bytes = generate_document(template_bytes, form_data, "1099-DIV")
        
        # Open generated PDF
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        
        # Copy1 is on page 3 (index 2)
        page = doc[2]
        
        # Check for drawings
        drawings = page.get_drawings()
        
        # Should have drawings on Copy1
        assert len(drawings) > 0, "Copy1 should have drawings (checkbox graphics)"
        
        # Verify Copy1 field mapping
        mapper = FieldMapper("1099-DIV")
        mapped_data = mapper.map_all_fields(form_data)
        
        copy1_voided_field = "topmostSubform[0].Copy1[0].CopyHeader[0].c2_1[0]"
        assert copy1_voided_field in mapped_data, "Copy1 VOIDED field should be mapped"
        
        doc.close()
    
    def test_corrected_checkbox_renders_on_copy2(self):
        """Test CORRECTED checkbox still renders on Copy2 (regression test)."""
        form_data = {
            "calendarYear": "2024",
            "corrected": True,
            "payerName": "Test Payer",
            "payerTIN": "12-3456789",
            "recipientName": "Test Recipient",
            "recipientTIN": "987-65-4321",
            "totalOrdinaryDividends": "1000.00"
        }
        
        # Load template
        with open("samples/1099-DIV.pdf", "rb") as f:
            template_bytes = f.read()
        
        # Generate PDF
        pdf_bytes = generate_document(template_bytes, form_data, "1099-DIV")
        
        # Open generated PDF
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        
        # Copy2 is on page 6 (index 5)
        page = doc[5]
        
        # Check for drawings
        drawings = page.get_drawings()
        
        # Should have drawings on Copy2
        assert len(drawings) > 0, "Copy2 should have drawings (checkbox graphics)"
        
        # Verify Copy2 field mapping
        mapper = FieldMapper("1099-DIV")
        mapped_data = mapper.map_all_fields(form_data)
        
        copy2_corrected_field = "topmostSubform[0].Copy2[0].CopyHeader[0].c2_1[1]"
        assert copy2_corrected_field in mapped_data, "Copy2 CORRECTED field should be mapped"
        
        doc.close()
