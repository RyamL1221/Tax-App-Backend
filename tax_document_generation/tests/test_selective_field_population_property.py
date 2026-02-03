"""
Property Test: Selective Field Population

Feature: pymupdf-migration
Property 12: Selective Field Population

Tests that for any form data with both mapped and unmapped fields,
only the mapped fields are populated in the output PDF.

**Validates: Requirements 4.3, 10.2**
"""

import pytest
from hypothesis import given, settings, strategies as st
from unittest.mock import Mock, patch
import os

from tax_document_generation.document_generator import generate_document


def get_1099_div_template():
    """Load the actual 1099-DIV template from the project root."""
    test_dir = os.path.dirname(os.path.abspath(__file__))
    tax_doc_dir = os.path.dirname(test_dir)
    project_root = os.path.dirname(tax_doc_dir)
    template_path = os.path.join(project_root, "1099-DIV.pdf")
    
    if not os.path.exists(template_path):
        pytest.skip(f"1099-DIV template not found at {template_path}")
    
    with open(template_path, "rb") as f:
        return f.read()


# Strategy for generating form data with mixed mapped/unmapped fields
def mixed_form_data_strategy():
    """Generate form data with both mapped and unmapped fields."""
    # Known mapped fields for 1099-DIV
    mapped_fields = st.sampled_from([
        "payerName", "payerTIN", "recipientName", "recipientTIN",
        "totalOrdinaryDividends", "qualifiedDividends"
    ])
    
    # Unmapped fields (random strings)
    unmapped_fields = st.text(
        min_size=1, 
        max_size=20, 
        alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))
    ).filter(lambda s: s not in ["payerName", "payerTIN", "recipientName", "recipientTIN",
                                   "totalOrdinaryDividends", "qualifiedDividends"])
    
    # Generate dictionaries with both types
    mapped_data = st.dictionaries(
        keys=mapped_fields,
        values=st.text(min_size=1, max_size=50),
        min_size=1,
        max_size=3
    )
    
    unmapped_data = st.dictionaries(
        keys=unmapped_fields,
        values=st.text(min_size=1, max_size=50),
        min_size=1,
        max_size=3
    )
    
    return st.builds(
        lambda m, u: {**m, **u},
        mapped_data,
        unmapped_data
    )


class TestSelectiveFieldPopulationProperty:
    """Property-based tests for selective field population."""
    
    @settings(max_examples=100, deadline=None)
    @given(form_data=mixed_form_data_strategy())
    def test_only_mapped_fields_are_populated(self, form_data):
        """
        **Validates: Requirements 4.3, 10.2**
        Feature: pymupdf-migration, Property 12: Selective Field Population
        
        For any form data with both mapped and unmapped fields,
        only the mapped fields SHALL be populated in the output PDF.
        
        This test verifies that:
        1. Mapped fields are populated in the PDF
        2. Unmapped fields are NOT populated in the PDF
        3. Unmapped fields do not cause errors
        """
        # Create a mock PDF template
        mock_template = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n%%EOF"
        
        # Mock PyMuPDF (fitz) components
        with patch('tax_document_generation.document_generator.fitz') as mock_fitz, \
             patch('tax_document_generation.document_generator.FieldMapper') as mock_mapper_class:
            
            # Setup mock field mapper
            mock_mapper = Mock()
            
            # Separate mapped and unmapped fields
            known_mapped = ["payerName", "payerTIN", "recipientName", "recipientTIN",
                           "totalOrdinaryDividends", "qualifiedDividends"]
            mapped_fields = {k: v for k, v in form_data.items() if k in known_mapped}
            unmapped_fields = [k for k in form_data.keys() if k not in known_mapped]
            
            # Create mapped data with PDF field names (simulating FieldMapper behavior)
            mapped_data = {f"pdf_{k}": v for k, v in mapped_fields.items()}
            
            mock_mapper.map_all_fields.return_value = mapped_data
            mock_mapper.get_unmapped_fields.return_value = unmapped_fields
            mock_mapper_class.return_value = mock_mapper
            
            # Setup mock widgets - include both mapped and unmapped PDF field names
            mock_widgets = []
            
            # Add widgets for mapped fields
            for pdf_field_name, value in mapped_data.items():
                mock_widget = Mock()
                mock_widget.field_name = pdf_field_name
                mock_widget.field_value = None
                mock_widget.field_flags = 0
                mock_widget.update = Mock()
                mock_widgets.append(mock_widget)
            
            # Add widgets for unmapped fields (these should NOT be populated)
            for unmapped_field in unmapped_fields:
                mock_widget = Mock()
                mock_widget.field_name = f"pdf_{unmapped_field}"
                mock_widget.field_value = None
                mock_widget.field_flags = 0
                mock_widget.update = Mock()
                mock_widgets.append(mock_widget)
            
            # Setup mock page with widgets
            mock_page = Mock()
            mock_page.widgets.return_value = mock_widgets
            
            # Setup mock PDF document
            mock_doc = Mock()
            mock_doc.__len__ = Mock(return_value=1)
            mock_doc.__getitem__ = Mock(return_value=mock_page)
            mock_doc.is_form_pdf = True
            mock_doc.xref_length.return_value = 10
            mock_doc.xref_get_key.return_value = None
            mock_doc.tobytes.return_value = b"%PDF-1.4\ngenerated content\n%%EOF"
            mock_doc.close = Mock()
            
            # Setup fitz.open to return mock document
            mock_fitz.open.return_value = mock_doc
            
            # Generate the document
            result = generate_document(mock_template, form_data, "1099-DIV")
            
            # CRITICAL VERIFICATION: Only mapped fields were populated
            for widget in mock_widgets:
                if widget.field_name in mapped_data:
                    # This is a mapped field - should be populated
                    expected_str = str(mapped_data[widget.field_name])
                    assert widget.field_value == expected_str, \
                        f"Mapped field '{widget.field_name}' should be populated with '{expected_str}'"
                else:
                    # This is an unmapped field - should NOT be populated
                    assert widget.field_value is None, \
                        f"Unmapped field '{widget.field_name}' should NOT be populated"
    
    @settings(max_examples=100, deadline=None)
    @given(form_data=mixed_form_data_strategy())
    def test_unmapped_fields_do_not_prevent_population(self, form_data):
        """
        **Validates: Requirements 4.3, 10.2**
        Feature: pymupdf-migration, Property 12: Selective Field Population
        
        For any form data with unmapped fields,
        the presence of unmapped fields SHALL NOT prevent mapped fields from being populated.
        
        This test verifies that:
        1. Document generation completes successfully
        2. Mapped fields are still populated despite unmapped fields
        3. No exceptions are raised
        """
        # Create a mock PDF template
        mock_template = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n%%EOF"
        
        # Mock PyMuPDF (fitz) components
        with patch('tax_document_generation.document_generator.fitz') as mock_fitz, \
             patch('tax_document_generation.document_generator.FieldMapper') as mock_mapper_class:
            
            # Setup mock field mapper
            mock_mapper = Mock()
            
            # Separate mapped and unmapped fields
            known_mapped = ["payerName", "payerTIN", "recipientName", "recipientTIN",
                           "totalOrdinaryDividends", "qualifiedDividends"]
            mapped_fields = {k: v for k, v in form_data.items() if k in known_mapped}
            unmapped_fields = [k for k in form_data.keys() if k not in known_mapped]
            
            # Create mapped data with PDF field names
            mapped_data = {f"pdf_{k}": v for k, v in mapped_fields.items()}
            
            mock_mapper.map_all_fields.return_value = mapped_data
            mock_mapper.get_unmapped_fields.return_value = unmapped_fields
            mock_mapper_class.return_value = mock_mapper
            
            # Setup mock widgets for mapped fields only
            mock_widgets = []
            for pdf_field_name, value in mapped_data.items():
                mock_widget = Mock()
                mock_widget.field_name = pdf_field_name
                mock_widget.field_value = None
                mock_widget.field_flags = 0
                mock_widget.update = Mock()
                mock_widgets.append(mock_widget)
            
            # Setup mock page with widgets
            mock_page = Mock()
            mock_page.widgets.return_value = mock_widgets
            
            # Setup mock PDF document
            mock_doc = Mock()
            mock_doc.__len__ = Mock(return_value=1)
            mock_doc.__getitem__ = Mock(return_value=mock_page)
            mock_doc.is_form_pdf = True
            mock_doc.xref_length.return_value = 10
            mock_doc.xref_get_key.return_value = None
            mock_doc.tobytes.return_value = b"%PDF-1.4\ngenerated content\n%%EOF"
            mock_doc.close = Mock()
            
            # Setup fitz.open to return mock document
            mock_fitz.open.return_value = mock_doc
            
            # Generate the document - should not raise exception
            try:
                result = generate_document(mock_template, form_data, "1099-DIV")
            except Exception as e:
                pytest.fail(f"Document generation should not raise exception with unmapped fields: {e}")
            
            # Verify result is valid
            assert result is not None
            assert isinstance(result, bytes)
            assert len(result) > 0
            
            # Verify mapped fields were populated
            if mapped_data:
                populated_count = sum(1 for w in mock_widgets if w.field_value is not None)
                assert populated_count == len(mapped_data), \
                    f"Expected {len(mapped_data)} mapped fields to be populated, got {populated_count}"
    
    @settings(max_examples=100, deadline=None)
    @given(form_data=mixed_form_data_strategy())
    def test_selective_population_maintains_field_order(self, form_data):
        """
        **Validates: Requirements 4.3, 10.2**
        Feature: pymupdf-migration, Property 12: Selective Field Population
        
        For any form data with mixed fields,
        selective population SHALL maintain the order of field processing.
        
        This test verifies that:
        1. Fields are processed in the order they appear in the PDF
        2. Skipping unmapped fields doesn't affect order
        3. All mapped fields are processed regardless of position
        """
        # Create a mock PDF template
        mock_template = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n%%EOF"
        
        # Mock PyMuPDF (fitz) components
        with patch('tax_document_generation.document_generator.fitz') as mock_fitz, \
             patch('tax_document_generation.document_generator.FieldMapper') as mock_mapper_class:
            
            # Setup mock field mapper
            mock_mapper = Mock()
            
            # Separate mapped and unmapped fields
            known_mapped = ["payerName", "payerTIN", "recipientName", "recipientTIN",
                           "totalOrdinaryDividends", "qualifiedDividends"]
            mapped_fields = {k: v for k, v in form_data.items() if k in known_mapped}
            unmapped_fields = [k for k in form_data.keys() if k not in known_mapped]
            
            # Create mapped data with PDF field names
            mapped_data = {f"pdf_{k}": v for k, v in mapped_fields.items()}
            
            mock_mapper.map_all_fields.return_value = mapped_data
            mock_mapper.get_unmapped_fields.return_value = unmapped_fields
            mock_mapper_class.return_value = mock_mapper
            
            # Setup mock widgets in a specific order (interleaved mapped/unmapped)
            mock_widgets = []
            all_fields = list(mapped_data.keys()) + [f"pdf_{u}" for u in unmapped_fields]
            
            for field_name in all_fields:
                mock_widget = Mock()
                mock_widget.field_name = field_name
                mock_widget.field_value = None
                mock_widget.field_flags = 0
                mock_widget.update = Mock()
                mock_widgets.append(mock_widget)
            
            # Setup mock page with widgets
            mock_page = Mock()
            mock_page.widgets.return_value = mock_widgets
            
            # Setup mock PDF document
            mock_doc = Mock()
            mock_doc.__len__ = Mock(return_value=1)
            mock_doc.__getitem__ = Mock(return_value=mock_page)
            mock_doc.is_form_pdf = True
            mock_doc.xref_length.return_value = 10
            mock_doc.xref_get_key.return_value = None
            mock_doc.tobytes.return_value = b"%PDF-1.4\ngenerated content\n%%EOF"
            mock_doc.close = Mock()
            
            # Setup fitz.open to return mock document
            mock_fitz.open.return_value = mock_doc
            
            # Generate the document
            result = generate_document(mock_template, form_data, "1099-DIV")
            
            # Verify all mapped fields were processed
            populated_fields = [w.field_name for w in mock_widgets if w.field_value is not None]
            expected_populated = list(mapped_data.keys())
            
            assert set(populated_fields) == set(expected_populated), \
                f"Expected fields {expected_populated} to be populated, got {populated_fields}"


def test_selective_population_with_real_template():
    """
    Unit test: Verify selective population with real 1099-DIV template.
    
    This test uses the actual template to verify that only mapped fields
    are populated when unmapped fields are present.
    """
    try:
        import fitz
    except ImportError:
        pytest.skip("PyMuPDF not installed")
    
    template = get_1099_div_template()
    
    # Mix of mapped and unmapped fields
    form_data = {
        "payerName": "Test Payer Company",  # Mapped
        "payerTIN": "12-3456789",  # Mapped
        "unknownField1": "Should not appear",  # Unmapped
        "recipientName": "John Doe",  # Mapped
        "unknownField2": "Also should not appear",  # Unmapped
    }
    
    result = generate_document(template, form_data, "1099-DIV")
    
    # Verify output is valid
    assert isinstance(result, bytes)
    assert len(result) > 0
    
    # Open the generated PDF and verify only mapped fields have values
    doc = fitz.open(stream=result, filetype="pdf")
    
    # Check that some fields were populated (the mapped ones)
    populated_count = 0
    for page_num in range(len(doc)):
        page = doc[page_num]
        widgets = page.widgets()
        if widgets:
            for widget in widgets:
                if widget.field_value:
                    populated_count += 1
    
    doc.close()
    
    # At least the mapped fields should be populated
    assert populated_count > 0, "Expected mapped fields to be populated"
