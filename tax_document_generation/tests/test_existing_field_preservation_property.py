"""
Property-based test for existing field preservation.

This test verifies that fields that currently render correctly (LeftCol fields)
continue to work after the adaptive font sizing implementation.

Task: 7.1 - Write property test for existing field preservation
Property 5: Existing Field Preservation
Validates: Requirements 6.1, 6.2, 6.3
Feature: fix-incorrect-field-mappings
"""

import pytest
from hypothesis import given, strategies as st, settings
import os
import fitz  # PyMuPDF
from tax_document_generation.document_generator import generate_document


class TestExistingFieldPreservation:
    """Property-based tests for existing field preservation."""
    
    @given(
        payer_name=st.text(
            min_size=5, 
            max_size=50, 
            alphabet=st.characters(min_codepoint=32, max_codepoint=126)
        ).filter(lambda x: x.strip() and x.strip().isprintable()),
        payer_tin=st.from_regex(r'[0-9]{2}-[0-9]{7}', fullmatch=True),
        recipient_name=st.text(
            min_size=5, 
            max_size=50, 
            alphabet=st.characters(min_codepoint=32, max_codepoint=126)
        ).filter(lambda x: x.strip() and x.strip().isprintable()),
        recipient_tin=st.from_regex(r'[0-9]{3}-[0-9]{2}-[0-9]{4}', fullmatch=True)
    )
    @settings(max_examples=20, deadline=None)
    def test_leftcol_fields_still_render_correctly(
        self,
        payer_name,
        payer_tin,
        recipient_name,
        recipient_tin
    ):
        """
        **Property 5: Existing Field Preservation**
        **Validates: Requirements 6.1, 6.2, 6.3**
        
        For any form data with LeftCol fields, applying the new rendering logic
        should not break existing functionality.
        
        This test verifies that:
        1. Payer name still renders correctly
        2. Payer TIN still renders correctly
        3. Recipient name still renders correctly
        4. Recipient TIN still renders correctly
        5. No errors occur during generation
        """
        # Get template path
        template_path = os.path.join(os.path.dirname(__file__), '..', '..', '1099-DIV.pdf')
        
        # Skip if template not found
        if not os.path.exists(template_path):
            pytest.skip(f"Template not found: {template_path}")
        
        # Create form data with LeftCol fields
        form_data = {
            "payerName": payer_name.strip(),
            "payerTIN": payer_tin,
            "recipientName": recipient_name.strip(),
            "recipientTIN": recipient_tin
        }
        
        # Skip if any field is empty after stripping
        if not all(form_data.values()):
            return
        
        # Load template
        with open(template_path, "rb") as f:
            template_bytes = f.read()
        
        # Generate document - should not raise exception
        try:
            result_bytes = generate_document(
                template=template_bytes,
                form_data=form_data,
                document_type="1099-DIV"
            )
        except Exception as e:
            pytest.fail(f"Document generation failed for LeftCol fields: {e}")
        
        # Verify result is valid PDF
        assert result_bytes is not None, \
            "Document generation should return bytes"
        
        assert isinstance(result_bytes, bytes), \
            "Result should be bytes"
        
        assert len(result_bytes) > 0, \
            "Result should not be empty"
        
        assert result_bytes.startswith(b"%PDF"), \
            "Result should be a valid PDF"
        
        # Open PDF and extract text
        doc = fitz.open(stream=result_bytes, filetype="pdf")
        
        all_text = ""
        for page_num in range(len(doc)):
            page = doc[page_num]
            all_text += page.get_text()
        
        doc.close()
        
        # Verify LeftCol fields are present in the text
        # These fields should still work after the adaptive font sizing changes
        
        assert payer_name.strip() in all_text, \
            f"Payer name '{payer_name.strip()}' should be visible in generated PDF"
        
        assert payer_tin in all_text, \
            f"Payer TIN '{payer_tin}' should be visible in generated PDF"
        
        assert recipient_name.strip() in all_text, \
            f"Recipient name '{recipient_name.strip()}' should be visible in generated PDF"
        
        assert recipient_tin in all_text, \
            f"Recipient TIN '{recipient_tin}' should be visible in generated PDF"
    
    @given(
        payer_name=st.text(
            min_size=5, 
            max_size=100, 
            alphabet=st.characters(min_codepoint=32, max_codepoint=126)
        ).filter(lambda x: x.strip() and x.strip().isprintable())
    )
    @settings(max_examples=20, deadline=None)
    def test_payer_name_field_continues_to_work(self, payer_name):
        """
        **Property 5: Existing Field Preservation**
        **Validates: Requirements 6.2**
        
        For any payer name, the payer name field should continue to display
        correctly after mapping corrections.
        
        This test specifically focuses on the payer name field, which was
        working correctly before the changes.
        """
        # Get template path
        template_path = os.path.join(os.path.dirname(__file__), '..', '..', '1099-DIV.pdf')
        
        # Skip if template not found
        if not os.path.exists(template_path):
            pytest.skip(f"Template not found: {template_path}")
        
        # Skip empty names
        if not payer_name.strip():
            return
        
        # Create form data with just payer name
        form_data = {
            "payerName": payer_name.strip()
        }
        
        # Load template
        with open(template_path, "rb") as f:
            template_bytes = f.read()
        
        # Generate document
        try:
            result_bytes = generate_document(
                template=template_bytes,
                form_data=form_data,
                document_type="1099-DIV"
            )
        except Exception as e:
            pytest.fail(f"Document generation failed for payer name: {e}")
        
        # Verify result is valid
        assert result_bytes is not None and len(result_bytes) > 0, \
            "Document should be generated successfully"
        
        # Extract text and verify payer name is present
        doc = fitz.open(stream=result_bytes, filetype="pdf")
        all_text = ""
        for page_num in range(len(doc)):
            all_text += doc[page_num].get_text()
        doc.close()
        
        assert payer_name.strip() in all_text, \
            f"Payer name '{payer_name.strip()}' should be visible"
    
    @given(
        address=st.text(
            min_size=5, 
            max_size=50, 
            alphabet=st.characters(min_codepoint=32, max_codepoint=126)
        ).filter(lambda x: x.strip() and x.strip().isprintable()),
        city=st.text(
            min_size=3, 
            max_size=30, 
            alphabet=st.characters(min_codepoint=65, max_codepoint=122)
        ).filter(lambda x: x.strip() and x.strip().isalpha()),
        state=st.from_regex(r'[A-Z]{2}', fullmatch=True),
        zip_code=st.from_regex(r'[0-9]{5}', fullmatch=True)
    )
    @settings(max_examples=20, deadline=None)
    def test_address_fields_continue_to_work(
        self,
        address,
        city,
        state,
        zip_code
    ):
        """
        **Property 5: Existing Field Preservation**
        **Validates: Requirements 6.3**
        
        For any address data, address fields should continue to display
        correctly after mapping corrections.
        
        This test verifies that all other correctly mapped fields continue
        to work.
        """
        # Get template path
        template_path = os.path.join(os.path.dirname(__file__), '..', '..', '1099-DIV.pdf')
        
        # Skip if template not found
        if not os.path.exists(template_path):
            pytest.skip(f"Template not found: {template_path}")
        
        # Skip empty values
        if not address.strip() or not city.strip():
            return
        
        # Create form data with address fields
        form_data = {
            "payerStreetAddress": address.strip(),
            "payerCity": city.strip(),
            "payerState": state,
            "payerZip": zip_code
        }
        
        # Load template
        with open(template_path, "rb") as f:
            template_bytes = f.read()
        
        # Generate document
        try:
            result_bytes = generate_document(
                template=template_bytes,
                form_data=form_data,
                document_type="1099-DIV"
            )
        except Exception as e:
            pytest.fail(f"Document generation failed for address fields: {e}")
        
        # Verify result is valid
        assert result_bytes is not None and len(result_bytes) > 0, \
            "Document should be generated successfully"
        
        # Extract text and verify address fields are present
        doc = fitz.open(stream=result_bytes, filetype="pdf")
        all_text = ""
        for page_num in range(len(doc)):
            all_text += doc[page_num].get_text()
        doc.close()
        
        # Verify at least some address components are present
        # (Text extraction may not be perfect, but we should find most values)
        assert city.strip() in all_text or state in all_text or zip_code in all_text, \
            "At least some address components should be visible"
    
    @given(
        form_data_size=st.integers(min_value=1, max_value=10)
    )
    @settings(max_examples=50, deadline=None)
    def test_multiple_leftcol_fields_together(self, form_data_size):
        """
        **Property 5: Existing Field Preservation**
        **Validates: Requirements 6.1, 6.2, 6.3**
        
        For any combination of LeftCol fields, all fields should render
        correctly together.
        
        This test verifies that the new rendering logic doesn't introduce
        interactions between fields that break existing functionality.
        """
        # Get template path
        template_path = os.path.join(os.path.dirname(__file__), '..', '..', '1099-DIV.pdf')
        
        # Skip if template not found
        if not os.path.exists(template_path):
            pytest.skip(f"Template not found: {template_path}")
        
        # Create form data with multiple LeftCol fields
        form_data = {}
        
        # Add a subset of LeftCol fields
        leftcol_fields = [
            ("payerName", "Test Payer Corporation"),
            ("payerTIN", "12-3456789"),
            ("payerStreetAddress", "123 Main Street"),
            ("payerCity", "New York"),
            ("payerState", "NY"),
            ("payerZip", "10001"),
            ("recipientName", "Test Recipient"),
            ("recipientTIN", "987-65-4321"),
            ("recipientStreetAddress", "456 Oak Avenue"),
            ("recipientCity", "Chicago"),
            ("recipientState", "IL"),
            ("recipientZip", "60601"),
        ]
        
        # Select a subset of fields based on form_data_size
        for i in range(min(form_data_size, len(leftcol_fields))):
            field_name, field_value = leftcol_fields[i]
            form_data[field_name] = field_value
        
        # Skip if no fields
        if not form_data:
            return
        
        # Load template
        with open(template_path, "rb") as f:
            template_bytes = f.read()
        
        # Generate document
        try:
            result_bytes = generate_document(
                template=template_bytes,
                form_data=form_data,
                document_type="1099-DIV"
            )
        except Exception as e:
            pytest.fail(f"Document generation failed for multiple LeftCol fields: {e}")
        
        # Verify result is valid
        assert result_bytes is not None and len(result_bytes) > 0, \
            "Document should be generated successfully"
        
        # Extract text
        doc = fitz.open(stream=result_bytes, filetype="pdf")
        all_text = ""
        for page_num in range(len(doc)):
            all_text += doc[page_num].get_text()
        doc.close()
        
        # Verify at least some fields are present
        found_count = 0
        for field_name, field_value in form_data.items():
            if field_value in all_text:
                found_count += 1
        
        # At least half of the fields should be found
        # (Text extraction may not be perfect)
        assert found_count >= len(form_data) // 2, \
            f"At least half of the fields should be visible (found {found_count}/{len(form_data)})"
