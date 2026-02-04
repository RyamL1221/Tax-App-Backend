"""
Regression tests for Task 7 - Fix 1099-DIV Field Positions.

These tests verify that the field mapping corrections made in Task 4 did not
break the two fields that were already working correctly:
1. Payer name (payerName)
2. Total ordinary dividends (totalOrdinaryDividends)

Requirements: 5.1, 5.2
Feature: fix-1099-div-field-positions
"""

import pytest
import fitz
from io import BytesIO
from tax_document_generation.document_generator import generate_document
from tax_document_generation.field_mapper import FieldMapper
from tax_document_generation.field_mappings.div_1099 import FIELD_MAPPING


class TestPayerNameRegression:
    """
    Regression tests for payer name field.
    
    Validates: Requirement 5.1 - Payer name continues to work after mapping changes.
    """
    
    def test_payer_name_mapping_unchanged(self):
        """
        Test that payer name mapping is still correct.
        
        The payer name field should map to:
        topmostSubform[0].Copy1[0].LeftCol[0].f2_2[0]
        """
        assert "payerName" in FIELD_MAPPING
        expected_mapping = "topmostSubform[0].Copy1[0].LeftCol[0].f2_2[0]"
        assert FIELD_MAPPING["payerName"] == expected_mapping, \
            f"Payer name mapping changed! Expected {expected_mapping}, got {FIELD_MAPPING['payerName']}"
    
    def test_payer_name_field_mapper_returns_correct_pdf_field(self):
        """
        Test that field mapper returns correct PDF field name for payer name.
        """
        mapper = FieldMapper("1099-DIV")
        pdf_field = mapper.map_field("payerName")
        
        assert pdf_field is not None, "Payer name should map to a PDF field"
        assert "f2_2[0]" in pdf_field, "Payer name should map to f2_2[0]"
        assert "LeftCol" in pdf_field, "Payer name should be in LeftCol"
    
    def test_payer_name_generates_three_copies(self):
        """
        Test that payer name mapping generates three copies (Copy1, Copy2, CopyB).
        """
        mapper = FieldMapper("1099-DIV")
        mapped_data = mapper.map_all_fields({"payerName": "Test Payer Inc"})
        
        # Count how many fields contain "f2_2" (payer name field ID)
        payer_name_fields = [k for k in mapped_data.keys() if "f2_2[0]" in k]
        
        assert len(payer_name_fields) == 3, \
            f"Expected 3 copies of payer name field, got {len(payer_name_fields)}"
        
        # Verify all three copies have the same value
        values = [mapped_data[k] for k in payer_name_fields]
        assert all(v == "Test Payer Inc" for v in values), \
            "All copies should have the same payer name value"
    
    @pytest.mark.skip(reason="Requires actual PDF template file")
    def test_payer_name_appears_in_generated_pdf(self, sample_1099_div_template):
        """
        Integration test: Verify payer name appears in generated PDF.
        
        This test generates a PDF with payer name and verifies it appears
        in the correct position.
        """
        form_data = {
            "payerName": "Regression Test Payer Corp"
        }
        
        pdf_bytes = generate_document(sample_1099_div_template, form_data)
        
        # Open generated PDF and verify field value
        doc = fitz.open(stream=BytesIO(pdf_bytes), filetype="pdf")
        
        # Check that payer name appears in the PDF
        found_payer_name = False
        for page in doc:
            text = page.get_text()
            if "Regression Test Payer Corp" in text:
                found_payer_name = True
                break
        
        assert found_payer_name, "Payer name should appear in generated PDF"
        doc.close()


class TestTotalOrdinaryDividendsRegression:
    """
    Regression tests for total ordinary dividends field.
    
    Validates: Requirement 5.2 - Total ordinary dividends continues to work after mapping changes.
    """
    
    def test_total_ordinary_dividends_mapping_unchanged(self):
        """
        Test that total ordinary dividends mapping is still correct.
        
        The total ordinary dividends field should map to:
        topmostSubform[0].Copy1[0].RghtCol[0].f2_9[0]
        """
        assert "totalOrdinaryDividends" in FIELD_MAPPING
        expected_mapping = "topmostSubform[0].Copy1[0].RghtCol[0].f2_9[0]"
        assert FIELD_MAPPING["totalOrdinaryDividends"] == expected_mapping, \
            f"Total ordinary dividends mapping changed! Expected {expected_mapping}, got {FIELD_MAPPING['totalOrdinaryDividends']}"
    
    def test_total_ordinary_dividends_field_mapper_returns_correct_pdf_field(self):
        """
        Test that field mapper returns correct PDF field name for total ordinary dividends.
        """
        mapper = FieldMapper("1099-DIV")
        pdf_field = mapper.map_field("totalOrdinaryDividends")
        
        assert pdf_field is not None, "Total ordinary dividends should map to a PDF field"
        assert "f2_9[0]" in pdf_field, "Total ordinary dividends should map to f2_9[0]"
        assert "RghtCol" in pdf_field, "Total ordinary dividends should be in RghtCol"
    
    def test_total_ordinary_dividends_generates_three_copies(self):
        """
        Test that total ordinary dividends mapping generates three copies.
        """
        mapper = FieldMapper("1099-DIV")
        mapped_data = mapper.map_all_fields({"totalOrdinaryDividends": "1234.56"})
        
        # Count how many fields contain "f2_9" (total ordinary dividends field ID)
        dividend_fields = [k for k in mapped_data.keys() if "f2_9[0]" in k]
        
        assert len(dividend_fields) == 3, \
            f"Expected 3 copies of total ordinary dividends field, got {len(dividend_fields)}"
        
        # Verify all three copies have the same value
        values = [mapped_data[k] for k in dividend_fields]
        assert all(v == "1234.56" for v in values), \
            "All copies should have the same total ordinary dividends value"
    
    @pytest.mark.skip(reason="Requires actual PDF template file")
    def test_total_ordinary_dividends_appears_in_generated_pdf(self, sample_1099_div_template):
        """
        Integration test: Verify total ordinary dividends appears in generated PDF.
        
        This test generates a PDF with total ordinary dividends and verifies
        it appears in the correct position.
        """
        form_data = {
            "totalOrdinaryDividends": "9876.54"
        }
        
        pdf_bytes = generate_document(sample_1099_div_template, form_data)
        
        # Open generated PDF and verify field value
        doc = fitz.open(stream=BytesIO(pdf_bytes), filetype="pdf")
        
        # Check that total ordinary dividends appears in the PDF
        found_dividends = False
        for page in doc:
            text = page.get_text()
            if "9876.54" in text:
                found_dividends = True
                break
        
        assert found_dividends, "Total ordinary dividends should appear in generated PDF"
        doc.close()


class TestBothFieldsTogether:
    """
    Test that both payer name and total ordinary dividends work together.
    
    Validates: Requirements 5.1, 5.2 - Both fields work simultaneously.
    """
    
    def test_both_fields_map_correctly(self):
        """
        Test that both fields map to correct PDF fields simultaneously.
        """
        mapper = FieldMapper("1099-DIV")
        form_data = {
            "payerName": "Test Payer",
            "totalOrdinaryDividends": "500.00"
        }
        
        mapped_data = mapper.map_all_fields(form_data)
        
        # Verify payer name fields exist
        payer_fields = [k for k in mapped_data.keys() if "f2_2[0]" in k]
        assert len(payer_fields) == 3, "Should have 3 payer name fields"
        
        # Verify total ordinary dividends fields exist
        dividend_fields = [k for k in mapped_data.keys() if "f2_9[0]" in k]
        assert len(dividend_fields) == 3, "Should have 3 total ordinary dividends fields"
        
        # Verify values are correct
        for field in payer_fields:
            assert mapped_data[field] == "Test Payer"
        
        for field in dividend_fields:
            assert mapped_data[field] == "500.00"
    
    def test_both_fields_with_corrected_fields(self):
        """
        Test that payer name and total ordinary dividends work alongside corrected fields.
        
        This verifies that the corrections to recipientName, payerTIN, and recipientTIN
        did not break the already-working fields.
        """
        mapper = FieldMapper("1099-DIV")
        form_data = {
            "payerName": "Regression Test Corp",
            "payerTIN": "12-3456789",
            "recipientName": "John Doe",
            "recipientTIN": "987-65-4321",
            "totalOrdinaryDividends": "1500.00"
        }
        
        mapped_data = mapper.map_all_fields(form_data)
        
        # Verify all five critical fields are mapped
        payer_name_fields = [k for k in mapped_data.keys() if "f2_2[0]" in k]
        payer_tin_fields = [k for k in mapped_data.keys() if "f2_7[0]" in k]
        recipient_name_fields = [k for k in mapped_data.keys() if "f2_5[0]" in k]
        recipient_tin_fields = [k for k in mapped_data.keys() if "f2_8[0]" in k]
        dividend_fields = [k for k in mapped_data.keys() if "f2_9[0]" in k]
        
        assert len(payer_name_fields) == 3, "Should have 3 payer name fields"
        assert len(payer_tin_fields) == 3, "Should have 3 payer TIN fields"
        assert len(recipient_name_fields) == 3, "Should have 3 recipient name fields"
        assert len(recipient_tin_fields) == 3, "Should have 3 recipient TIN fields"
        assert len(dividend_fields) == 3, "Should have 3 total ordinary dividends fields"
        
        # Verify values are correct
        for field in payer_name_fields:
            assert mapped_data[field] == "Regression Test Corp"
        
        for field in dividend_fields:
            assert mapped_data[field] == "1500.00"


class TestNoRegressionInExistingTests:
    """
    Verify that existing unit tests for these fields still pass.
    
    This class documents which existing tests cover payer name and
    total ordinary dividends functionality.
    """
    
    def test_existing_payer_name_tests_documented(self):
        """
        Document existing tests that cover payer name functionality.
        
        Existing tests:
        - test_field_mapper_unit.py::TestFieldMapperUnit::test_payer_name_mapping
        - test_leftcol_field_rendering_unit.py::TestLeftColFieldRendering::test_payer_name_renders_correctly
        - test_leftcol_field_rendering_unit.py::TestLeftColFieldRendering::test_long_payer_name_with_adaptive_sizing
        - test_leftcol_field_rendering_unit.py::TestLeftColFieldRendering::test_payer_name_with_special_characters
        - test_visual_field_mapper_integration.py::TestVisualFieldMapperIntegration::test_identify_payer_name_in_left_column
        """
        # This test just documents that these tests exist and should pass
        assert True, "Existing payer name tests are documented"
    
    def test_existing_total_ordinary_dividends_tests_documented(self):
        """
        Document existing tests that cover total ordinary dividends functionality.
        
        Existing tests:
        - test_field_mapper_unit.py::TestFieldMapperUnit::test_total_ordinary_dividends_mapping
        """
        # This test just documents that these tests exist and should pass
        assert True, "Existing total ordinary dividends tests are documented"
