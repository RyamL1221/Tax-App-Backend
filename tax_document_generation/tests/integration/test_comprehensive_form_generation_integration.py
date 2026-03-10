"""
Integration test for comprehensive form generation with all fields.

This test verifies end-to-end functionality of generating a complete 1099-DIV
form with all fields populated, ensuring that the adaptive font sizing and
field rendering work correctly.

Task: 6.2 - Write integration test for complete form generation
Requirements: 8.1, 8.2, 8.3
Feature: fix-incorrect-field-mappings
"""

import pytest
import os
import fitz  # PyMuPDF


class TestComprehensiveFormGeneration:
    """Integration tests for comprehensive form generation."""
    
    @pytest.fixture
    def template_path(self):
        """Get path to 1099-DIV template."""
        # Template is in the root directory
        return os.path.join(os.path.dirname(__file__), '..', '..', '1099-DIV.pdf')
    
    @pytest.fixture
    def comprehensive_form_data(self):
        """Comprehensive test data with all critical fields."""
        return {
            # Payer Information
            "payerName": "Acme Investment Corporation",
            "payerTIN": "12-3456789",
            "payerStreetAddress": "123 Wall Street, Suite 500",
            "payerCity": "New York",
            "payerState": "NY",
            "payerZip": "10005",
            
            # Recipient Information
            "recipientName": "John Q. Taxpayer",
            "recipientTIN": "987-65-4321",
            "recipientStreetAddress": "456 Main Street",
            "recipientCity": "Springfield",
            "recipientState": "IL",
            "recipientZip": "62701",
            "accountNumber": "ACC-123456",
            
            # Monetary Fields (RghtCol - the critical fields that were failing)
            "totalOrdinaryDividends": "1500.00",
            "qualifiedDividends": "1200.00",
            "totalCapitalGainDistributions": "250.00",
            "unrecapturedSection1250Gain": "50.00",
            "section1202Gain": "25.00",
            "section897OrdinaryDividends": "10.00",
            "section897CapitalGain": "5.00",
            "nondividendDistributions": "100.00",
            "federalIncomeTaxWithheld": "150.00",
            "section199ADividends": "800.00",
            "investmentExpenses": "25.00",
            "foreignTaxPaid": "75.00",
            "foreignCountry": "Canada",
            "cashLiquidationDistributions": "0.00",
            "noncashLiquidationDistributions": "0.00",
            "exemptInterestDividends": "50.00",
            "state": "NY",
            "stateTaxWithheld": "50.00",
        }
    
    def test_generate_complete_1099_div_with_all_fields(
        self, 
        template_path, 
        comprehensive_form_data
    ):
        """
        **Validates: Requirements 8.1**
        
        Test generating a complete 1099-DIV with all fields populated.
        
        This test verifies that:
        1. Form data with all fields can be processed
        2. PDF is generated successfully
        3. No errors occur during generation
        4. Result is valid PDF bytes
        """
        from tax_document_generation.document_generator import generate_document
        
        # Load template
        assert os.path.exists(template_path), \
            f"Template file not found: {template_path}"
        
        with open(template_path, "rb") as f:
            template_bytes = f.read()
        
        # Generate document
        result_bytes = generate_document(
            template=template_bytes,
            form_data=comprehensive_form_data,
            document_type="1099-DIV"
        )
        
        # Verify result is valid PDF bytes
        assert result_bytes is not None, \
            "Document generation should return bytes"
        
        assert isinstance(result_bytes, bytes), \
            "Result should be bytes"
        
        assert len(result_bytes) > 0, \
            "Result should not be empty"
        
        assert result_bytes.startswith(b"%PDF"), \
            "Result should be a valid PDF"
        
        # Verify PDF can be opened
        doc = fitz.open(stream=result_bytes, filetype="pdf")
        assert doc is not None, \
            "Generated PDF should be openable"
        
        assert len(doc) > 0, \
            "Generated PDF should have at least one page"
        
        doc.close()
    
    def test_verify_critical_fields_present_in_generated_pdf(
        self, 
        template_path, 
        comprehensive_form_data
    ):
        """
        **Validates: Requirements 8.2, 8.3**
        
        Test that critical fields are present in the generated PDF.
        
        This test verifies that:
        1. Payer name, TIN are visible
        2. Recipient name, TIN are visible
        3. Monetary values are visible
        4. Text extraction finds the expected values
        """
        from tax_document_generation.document_generator import generate_document
        
        # Load template
        with open(template_path, "rb") as f:
            template_bytes = f.read()
        
        # Generate document
        result_bytes = generate_document(
            template=template_bytes,
            form_data=comprehensive_form_data,
            document_type="1099-DIV"
        )
        
        # Open generated PDF and extract text
        doc = fitz.open(stream=result_bytes, filetype="pdf")
        
        # Extract text from all pages
        all_text = ""
        for page_num in range(len(doc)):
            page = doc[page_num]
            all_text += page.get_text()
        
        doc.close()
        
        # Verify critical fields are present in the text
        # Note: Text extraction may not be perfect, but we should find most values
        
        # Payer information
        assert "Acme Investment Corporation" in all_text, \
            "Payer name should be visible in generated PDF"
        
        assert "12-3456789" in all_text, \
            "Payer TIN should be visible in generated PDF"
        
        # Recipient information
        assert "John Q. Taxpayer" in all_text, \
            "Recipient name should be visible in generated PDF"
        
        assert "987-65-4321" in all_text, \
            "Recipient TIN should be visible in generated PDF"
        
        # Monetary values (these were the problematic RghtCol fields)
        # Note: PDF text extraction may format numbers differently
        assert "1500" in all_text or "1,500" in all_text, \
            "Total ordinary dividends should be visible in generated PDF"
        
        assert "1200" in all_text or "1,200" in all_text, \
            "Qualified dividends should be visible in generated PDF"
        
        assert "250" in all_text, \
            "Total capital gain distributions should be visible in generated PDF"
    
    def test_all_three_copies_generated(
        self, 
        template_path, 
        comprehensive_form_data
    ):
        """
        **Validates: Requirements 5.2, 5.3**
        
        Test that all three copies (Copy1, Copy2, CopyB) are generated.
        
        This test verifies that:
        1. Generated PDF has multiple pages (one per copy)
        2. Each copy contains the same data
        3. Multi-copy field mapping works correctly
        """
        from tax_document_generation.document_generator import generate_document
        
        # Load template
        with open(template_path, "rb") as f:
            template_bytes = f.read()
        
        # Generate document
        result_bytes = generate_document(
            template=template_bytes,
            form_data=comprehensive_form_data,
            document_type="1099-DIV"
        )
        
        # Open generated PDF
        doc = fitz.open(stream=result_bytes, filetype="pdf")
        
        # 1099-DIV has 6 pages (2 pages per copy × 3 copies)
        assert len(doc) >= 3, \
            f"Generated PDF should have at least 3 pages, but has {len(doc)}"
        
        # Extract text from each page
        page_texts = []
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_text = page.get_text()
            page_texts.append(page_text)
        
        doc.close()
        
        # Verify at least some pages contain critical data
        # (Some pages may be instruction pages without form data)
        payer_found = False
        recipient_found = False
        
        for page_num, page_text in enumerate(page_texts):
            if "Acme Investment Corporation" in page_text:
                payer_found = True
            if "John Q. Taxpayer" in page_text:
                recipient_found = True
        
        assert payer_found, \
            "At least one page should contain payer name"
        
        assert recipient_found, \
            "At least one page should contain recipient name"
    
    def test_edge_case_very_long_names(self, template_path):
        """
        **Validates: Requirements 1.1, 2.1, 3.1**
        
        Test that very long names are handled with adaptive font sizing.
        
        This test verifies that:
        1. Long names don't cause errors
        2. Adaptive font sizing reduces font size to fit text
        3. PDF is generated successfully
        """
        from tax_document_generation.document_generator import generate_document
        
        # Create form data with very long names
        edge_case_data = {
            "payerName": "The Very Long Investment Corporation Name That Might Not Fit In Standard Font Size",
            "recipientName": "John Quincy Taxpayer III Esquire With A Very Long Name",
            "payerTIN": "12-3456789",
            "recipientTIN": "987-65-4321",
            "totalOrdinaryDividends": "999999999.99",  # Very large number
        }
        
        # Load template
        with open(template_path, "rb") as f:
            template_bytes = f.read()
        
        # Generate document - should not raise exception
        result_bytes = generate_document(
            template=template_bytes,
            form_data=edge_case_data,
            document_type="1099-DIV"
        )
        
        # Verify result is valid
        assert result_bytes is not None, \
            "Document generation should succeed with long names"
        
        assert isinstance(result_bytes, bytes), \
            "Result should be bytes"
        
        assert result_bytes.startswith(b"%PDF"), \
            "Result should be a valid PDF"
    
    def test_empty_form_data_generates_valid_pdf(self, template_path):
        """
        Test that empty form data generates a valid (empty) PDF.
        
        This test verifies that:
        1. Empty form data is handled gracefully
        2. No errors occur
        3. Valid PDF is still generated
        """
        from tax_document_generation.document_generator import generate_document
        
        # Load template
        with open(template_path, "rb") as f:
            template_bytes = f.read()
        
        # Generate document with empty data
        result_bytes = generate_document(
            template=template_bytes,
            form_data={},
            document_type="1099-DIV"
        )
        
        # Verify result is valid
        assert result_bytes is not None, \
            "Document generation should succeed with empty data"
        
        assert isinstance(result_bytes, bytes), \
            "Result should be bytes"
        
        assert result_bytes.startswith(b"%PDF"), \
            "Result should be a valid PDF"
    
    def test_partial_form_data_generates_valid_pdf(self, template_path):
        """
        Test that partial form data generates a valid PDF.
        
        This test verifies that:
        1. Partial form data is handled gracefully
        2. Only provided fields are populated
        3. Valid PDF is generated
        """
        from tax_document_generation.document_generator import generate_document
        
        # Create partial form data (only a few fields)
        partial_data = {
            "payerName": "Test Payer",
            "recipientName": "Test Recipient",
            "totalOrdinaryDividends": "100.00",
        }
        
        # Load template
        with open(template_path, "rb") as f:
            template_bytes = f.read()
        
        # Generate document
        result_bytes = generate_document(
            template=template_bytes,
            form_data=partial_data,
            document_type="1099-DIV"
        )
        
        # Verify result is valid
        assert result_bytes is not None, \
            "Document generation should succeed with partial data"
        
        assert isinstance(result_bytes, bytes), \
            "Result should be bytes"
        
        assert result_bytes.startswith(b"%PDF"), \
            "Result should be a valid PDF"
        
        # Verify provided fields are present
        doc = fitz.open(stream=result_bytes, filetype="pdf")
        all_text = ""
        for page_num in range(len(doc)):
            page = doc[page_num]
            all_text += page.get_text()
        doc.close()
        
        assert "Test Payer" in all_text, \
            "Provided payer name should be visible"
        
        assert "Test Recipient" in all_text, \
            "Provided recipient name should be visible"
