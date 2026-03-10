"""
Unit Test: Graceful Field Error Handling

Tests that individual field population failures don't stop the entire
document generation process.

**Validates: Requirements 4.3, 4.5, 9.1, 9.2**
"""

import pytest
from unittest.mock import Mock, patch

from tax_document_generation.document_generator import generate_document


def test_field_population_error_continues_processing():
    """
    Test that if one field fails to populate, other fields are still processed.
    
    This verifies graceful error handling where individual field failures
    don't stop the entire document generation.
    """
    mock_template = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n%%EOF"
    
    form_data = {
        "field1": "value1",
        "field2": "value2",
        "field3": "value3",
    }
    
    with patch('tax_document_generation.document_generator.fitz') as mock_fitz, \
         patch('tax_document_generation.document_generator.FieldMapper') as mock_mapper_class:
        
        # Setup mock field mapper
        mock_mapper = Mock()
        mapped_data = {
            "pdf_field1": "value1",
            "pdf_field2": "value2",
            "pdf_field3": "value3",
        }
        mock_mapper.map_all_fields.return_value = mapped_data
        mock_mapper.get_unmapped_fields.return_value = []
        mock_mapper_class.return_value = mock_mapper
        
        # Setup mock widgets - make field2 fail
        mock_widget1 = Mock()
        mock_widget1.field_name = "pdf_field1"
        mock_widget1.field_value = None
        mock_widget1.field_flags = 0
        mock_widget1.update = Mock()
        
        mock_widget2 = Mock()
        mock_widget2.field_name = "pdf_field2"
        mock_widget2.field_flags = 0
        # Make setting field_value raise an exception
        type(mock_widget2).field_value = property(
            lambda self: None,
            lambda self, value: (_ for _ in ()).throw(ValueError("Field type mismatch"))
        )
        mock_widget2.update = Mock()
        
        mock_widget3 = Mock()
        mock_widget3.field_name = "pdf_field3"
        mock_widget3.field_value = None
        mock_widget3.field_flags = 0
        mock_widget3.update = Mock()
        
        mock_widgets = [mock_widget1, mock_widget2, mock_widget3]
        
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
        result = generate_document(mock_template, form_data, "1099-DIV")
        
        # Verify result is valid
        assert result is not None
        assert isinstance(result, bytes)
        assert len(result) > 0
        
        # Verify field1 and field3 were populated (field2 failed)
        assert mock_widget1.field_value == "value1"
        assert mock_widget3.field_value == "value3"
        
        # Verify update was called for successful fields
        assert mock_widget1.update.called
        assert mock_widget3.update.called


def test_field_population_error_logs_warning():
    """
    Test that field population errors are logged as warnings.
    
    This verifies that failures are logged but don't stop processing.
    """
    mock_template = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n%%EOF"
    
    form_data = {
        "field1": "value1",
        "field2": "value2",
    }
    
    with patch('tax_document_generation.document_generator.fitz') as mock_fitz, \
         patch('tax_document_generation.document_generator.FieldMapper') as mock_mapper_class, \
         patch('tax_document_generation.document_generator.logger') as mock_logger:
        
        # Setup mock field mapper
        mock_mapper = Mock()
        mapped_data = {
            "pdf_field1": "value1",
            "pdf_field2": "value2",
        }
        mock_mapper.map_all_fields.return_value = mapped_data
        mock_mapper.get_unmapped_fields.return_value = []
        mock_mapper_class.return_value = mock_mapper
        
        # Setup mock widgets - make field2 fail
        mock_widget1 = Mock()
        mock_widget1.field_name = "pdf_field1"
        mock_widget1.field_value = None
        mock_widget1.field_flags = 0
        mock_widget1.update = Mock()
        
        mock_widget2 = Mock()
        mock_widget2.field_name = "pdf_field2"
        mock_widget2.field_flags = 0
        # Make setting field_value raise an exception
        type(mock_widget2).field_value = property(
            lambda self: None,
            lambda self, value: (_ for _ in ()).throw(ValueError("Field type mismatch"))
        )
        mock_widget2.update = Mock()
        
        mock_widgets = [mock_widget1, mock_widget2]
        
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
        
        # Verify warnings were logged
        warning_calls = [call for call in mock_logger.warning.call_args_list]
        
        # Should have at least one warning for the failed field
        failed_field_warnings = [
            call for call in warning_calls
            if "Failed to populate field" in str(call) and "pdf_field2" in str(call)
        ]
        assert len(failed_field_warnings) > 0, "Should log warning for failed field"


def test_all_fields_fail_still_returns_pdf():
    """
    Test that even if all fields fail to populate, a valid PDF is still returned.
    
    This verifies extreme graceful degradation.
    """
    mock_template = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n%%EOF"
    
    form_data = {
        "field1": "value1",
        "field2": "value2",
    }
    
    with patch('tax_document_generation.document_generator.fitz') as mock_fitz, \
         patch('tax_document_generation.document_generator.FieldMapper') as mock_mapper_class:
        
        # Setup mock field mapper
        mock_mapper = Mock()
        mapped_data = {
            "pdf_field1": "value1",
            "pdf_field2": "value2",
        }
        mock_mapper.map_all_fields.return_value = mapped_data
        mock_mapper.get_unmapped_fields.return_value = []
        mock_mapper_class.return_value = mock_mapper
        
        # Setup mock widgets - make both fail
        mock_widget1 = Mock()
        mock_widget1.field_name = "pdf_field1"
        mock_widget1.field_flags = 0
        type(mock_widget1).field_value = property(
            lambda self: None,
            lambda self, value: (_ for _ in ()).throw(ValueError("Error 1"))
        )
        mock_widget1.update = Mock()
        
        mock_widget2 = Mock()
        mock_widget2.field_name = "pdf_field2"
        mock_widget2.field_flags = 0
        type(mock_widget2).field_value = property(
            lambda self: None,
            lambda self, value: (_ for _ in ()).throw(ValueError("Error 2"))
        )
        mock_widget2.update = Mock()
        
        mock_widgets = [mock_widget1, mock_widget2]
        
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
        result = generate_document(mock_template, form_data, "1099-DIV")
        
        # Verify result is valid
        assert result is not None
        assert isinstance(result, bytes)
        assert len(result) > 0
        assert result.startswith(b"%PDF")


def test_widget_update_error_continues_processing():
    """
    Test that if widget.update() fails, processing continues.
    
    This verifies graceful handling of update failures.
    """
    mock_template = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n%%EOF"
    
    form_data = {
        "field1": "value1",
        "field2": "value2",
    }
    
    with patch('tax_document_generation.document_generator.fitz') as mock_fitz, \
         patch('tax_document_generation.document_generator.FieldMapper') as mock_mapper_class:
        
        # Setup mock field mapper
        mock_mapper = Mock()
        mapped_data = {
            "pdf_field1": "value1",
            "pdf_field2": "value2",
        }
        mock_mapper.map_all_fields.return_value = mapped_data
        mock_mapper.get_unmapped_fields.return_value = []
        mock_mapper_class.return_value = mock_mapper
        
        # Setup mock widgets - make field1's update fail
        mock_widget1 = Mock()
        mock_widget1.field_name = "pdf_field1"
        mock_widget1.field_value = None
        mock_widget1.field_flags = 0
        mock_widget1.update = Mock(side_effect=RuntimeError("Update failed"))
        
        mock_widget2 = Mock()
        mock_widget2.field_name = "pdf_field2"
        mock_widget2.field_value = None
        mock_widget2.field_flags = 0
        mock_widget2.update = Mock()
        
        mock_widgets = [mock_widget1, mock_widget2]
        
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
        result = generate_document(mock_template, form_data, "1099-DIV")
        
        # Verify result is valid
        assert result is not None
        assert isinstance(result, bytes)
        assert len(result) > 0
        
        # Verify field2 was still processed
        assert mock_widget2.field_value == "value2"
        assert mock_widget2.update.called
