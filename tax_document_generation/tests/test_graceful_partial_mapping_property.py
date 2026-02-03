"""
Property Test: Graceful Partial Mapping

Feature: pymupdf-migration
Property 13: Graceful Partial Mapping

Tests that for any form data where some fields lack mappings,
the document generation completes successfully and returns valid PDF bytes.

**Validates: Requirements 4.5**
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


# Strategy for generating form data with varying amounts of unmapped fields
def partial_mapping_strategy():
    """Generate form data with some unmapped fields."""
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
    
    # Generate dictionaries with varying ratios of mapped/unmapped
    mapped_data = st.dictionaries(
        keys=mapped_fields,
        values=st.text(min_size=1, max_size=50),
        min_size=0,  # Allow zero mapped fields
        max_size=3
    )
    
    unmapped_data = st.dictionaries(
        keys=unmapped_fields,
        values=st.text(min_size=1, max_size=50),
        min_size=1,  # Always have at least one unmapped field
        max_size=5
    )
    
    return st.builds(
        lambda m, u: {**m, **u},
        mapped_data,
        unmapped_data
    )


class TestGracefulPartialMappingProperty:
    """Property-based tests for graceful partial mapping."""
    
    @settings(max_examples=20, deadline=None)
    @given(form_data=partial_mapping_strategy())
    def test_partial_mapping_completes_successfully(self, form_data):
        """
        **Validates: Requirements 4.5**
        Feature: pymupdf-migration, Property 13: Graceful Partial Mapping
        
        For any form data where some fields lack mappings,
        the document generation SHALL complete successfully.
        
        This test verifies that:
        1. No exceptions are raised
        2. Document generation completes
        3. A result is returned
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
            
            # Setup mock widgets for mapped fields
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
                pytest.fail(f"Document generation should complete successfully with unmapped fields: {e}")
            
            # Verify result exists
            assert result is not None, "Document generation should return a result"
    
    @settings(max_examples=20, deadline=None)
    @given(form_data=partial_mapping_strategy())
    def test_partial_mapping_returns_valid_pdf_bytes(self, form_data):
        """
        **Validates: Requirements 4.5**
        Feature: pymupdf-migration, Property 13: Graceful Partial Mapping
        
        For any form data where some fields lack mappings,
        the document generation SHALL return valid PDF bytes.
        
        This test verifies that:
        1. Result is bytes type
        2. Result is non-empty
        3. Result has PDF structure
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
            
            # Setup mock widgets
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
            
            # Generate the document
            result = generate_document(mock_template, form_data, "1099-DIV")
            
            # Verify result is valid PDF bytes
            assert isinstance(result, bytes), \
                f"Result should be bytes, got {type(result)}"
            
            assert len(result) > 0, \
                "Result should be non-empty"
            
            assert result.startswith(b"%PDF"), \
                "Result should be a valid PDF (start with %PDF header)"
    
    @settings(max_examples=20, deadline=None)
    @given(form_data=partial_mapping_strategy())
    def test_partial_mapping_logs_unmapped_fields(self, form_data):
        """
        **Validates: Requirements 4.5**
        Feature: pymupdf-migration, Property 13: Graceful Partial Mapping
        
        For any form data where some fields lack mappings,
        the document generation SHALL log warnings for unmapped fields.
        
        This test verifies that:
        1. Unmapped fields are logged
        2. Logging doesn't prevent completion
        3. System continues gracefully
        """
        # Create a mock PDF template
        mock_template = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n%%EOF"
        
        # Mock PyMuPDF (fitz) components
        with patch('tax_document_generation.document_generator.fitz') as mock_fitz, \
             patch('tax_document_generation.document_generator.FieldMapper') as mock_mapper_class, \
             patch('tax_document_generation.document_generator.logger') as mock_logger:
            
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
            
            # Setup mock widgets
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
            
            # Generate the document
            result = generate_document(mock_template, form_data, "1099-DIV")
            
            # Verify warnings were logged for unmapped fields
            if unmapped_fields:
                # Check that warning was called
                warning_calls = [call for call in mock_logger.warning.call_args_list]
                assert len(warning_calls) > 0, \
                    "Warnings should be logged for unmapped fields"
    
    @settings(max_examples=20, deadline=None)
    @given(form_data=partial_mapping_strategy())
    def test_zero_mapped_fields_still_succeeds(self, form_data):
        """
        **Validates: Requirements 4.5**
        Feature: pymupdf-migration, Property 13: Graceful Partial Mapping
        
        For form data where NO fields have mappings,
        the document generation SHALL still complete successfully.
        
        This test verifies that:
        1. Complete mapping failure doesn't crash
        2. Valid PDF is still returned
        3. Graceful degradation occurs
        """
        # Force all fields to be unmapped
        unmapped_only_data = {f"unmapped_{k}": v for k, v in form_data.items()}
        
        # Create a mock PDF template
        mock_template = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n%%EOF"
        
        # Mock PyMuPDF (fitz) components
        with patch('tax_document_generation.document_generator.fitz') as mock_fitz, \
             patch('tax_document_generation.document_generator.FieldMapper') as mock_mapper_class:
            
            # Setup mock field mapper - no mapped fields
            mock_mapper = Mock()
            mock_mapper.map_all_fields.return_value = {}  # Empty mapped data
            mock_mapper.get_unmapped_fields.return_value = list(unmapped_only_data.keys())
            mock_mapper_class.return_value = mock_mapper
            
            # Setup mock page with no widgets (or empty widgets)
            mock_page = Mock()
            mock_page.widgets.return_value = []
            
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
                result = generate_document(mock_template, unmapped_only_data, "1099-DIV")
            except Exception as e:
                pytest.fail(f"Document generation should succeed even with zero mapped fields: {e}")
            
            # Verify result is valid
            assert result is not None
            assert isinstance(result, bytes)
            assert len(result) > 0
            assert result.startswith(b"%PDF")


def test_graceful_partial_mapping_with_real_template():
    """
    Unit test: Verify graceful partial mapping with real 1099-DIV template.
    
    This test uses the actual template to verify that document generation
    completes successfully even when many fields are unmapped.
    """
    try:
        import fitz
    except ImportError:
        pytest.skip("PyMuPDF not installed")
    
    template = get_1099_div_template()
    
    # Mostly unmapped fields with a few mapped ones
    form_data = {
        "payerName": "Test Payer Company",  # Mapped
        "unknownField1": "Should not appear",  # Unmapped
        "unknownField2": "Also should not appear",  # Unmapped
        "unknownField3": "Still should not appear",  # Unmapped
        "recipientName": "John Doe",  # Mapped
        "unknownField4": "Nope",  # Unmapped
    }
    
    # Should complete successfully
    result = generate_document(template, form_data, "1099-DIV")
    
    # Verify output is valid
    assert isinstance(result, bytes)
    assert len(result) > 0
    
    # Open the generated PDF
    doc = fitz.open(stream=result, filetype="pdf")
    assert len(doc) > 0
    doc.close()


def test_graceful_partial_mapping_all_unmapped():
    """
    Unit test: Verify graceful handling when ALL fields are unmapped.
    
    This test verifies that document generation completes successfully
    even when no fields can be mapped.
    """
    try:
        import fitz
    except ImportError:
        pytest.skip("PyMuPDF not installed")
    
    template = get_1099_div_template()
    
    # All unmapped fields
    form_data = {
        "unknownField1": "Should not appear",
        "unknownField2": "Also should not appear",
        "unknownField3": "Still should not appear",
    }
    
    # Should complete successfully
    result = generate_document(template, form_data, "1099-DIV")
    
    # Verify output is valid
    assert isinstance(result, bytes)
    assert len(result) > 0
    
    # Open the generated PDF
    doc = fitz.open(stream=result, filetype="pdf")
    assert len(doc) > 0
    doc.close()
