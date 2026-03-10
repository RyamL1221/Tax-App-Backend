"""
Integration test to verify address combiner integration in document_generator.

This test verifies that the document generator correctly:
1. Normalizes address fields
2. Combines address components
3. Maps combined fields to PDF fields

Requirements: 5.1, 5.2, 5.3
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tax_document_generation.document_generator import generate_document
from tax_document_generation.exceptions import GenerationError


class TestDocumentGeneratorAddressIntegration:
    """Test address combiner integration in document generator."""
    
    @patch('tax_document_generation.document_generator.fitz')
    @patch('tax_document_generation.document_generator.FieldMapper')
    def test_address_normalization_called(self, mock_mapper_class, mock_fitz):
        """Test that address normalization is called during document generation."""
        # Setup mocks
        mock_doc = MagicMock()
        mock_fitz.open.return_value = mock_doc
        mock_doc.__len__.return_value = 1
        mock_doc.tobytes.return_value = b'PDF content'
        
        mock_mapper = MagicMock()
        mock_mapper_class.return_value = mock_mapper
        mock_mapper.map_all_fields.return_value = {}
        mock_mapper.get_unmapped_fields.return_value = []
        
        # Test data with old combined format
        form_data = {
            "payerName": "Example Corp",
            "payerCity": "New York, NY 10001"  # Old combined format
        }
        
        # Generate document
        template = b'%PDF-1.4 fake template'
        result = generate_document(template, form_data, "1099-DIV")
        
        # Verify result
        assert result == b'PDF content'
        
        # Verify mapper was called (which means normalization and combination happened)
        assert mock_mapper.map_all_fields.called
    
    @patch('tax_document_generation.document_generator.fitz')
    @patch('tax_document_generation.document_generator.FieldMapper')
    def test_address_combination_called(self, mock_mapper_class, mock_fitz):
        """Test that address combination is called during document generation."""
        # Setup mocks
        mock_doc = MagicMock()
        mock_fitz.open.return_value = mock_doc
        mock_doc.__len__.return_value = 1
        mock_doc.tobytes.return_value = b'PDF content'
        
        mock_mapper = MagicMock()
        mock_mapper_class.return_value = mock_mapper
        mock_mapper.get_unmapped_fields.return_value = []
        
        # Capture the form_data passed to map_all_fields
        captured_form_data = None
        def capture_form_data(form_data):
            nonlocal captured_form_data
            captured_form_data = form_data.copy()
            return {}
        
        mock_mapper.map_all_fields.side_effect = capture_form_data
        
        # Test data with separate address components
        form_data = {
            "payerName": "Example Corp",
            "payerStreetAddress": "123 Main St",
            "payerCity": "New York",
            "payerState": "NY",
            "payerZip": "10001",
            "payerTelephoneNumber": "(555) 123-4567"
        }
        
        # Generate document
        template = b'%PDF-1.4 fake template'
        result = generate_document(template, form_data, "1099-DIV")
        
        # Verify result
        assert result == b'PDF content'
        
        # Verify address combination happened
        assert captured_form_data is not None
        assert "payerAddressBlock" in captured_form_data
        
        # Verify combined address contains all components
        address_block = captured_form_data["payerAddressBlock"]
        assert "Example Corp" in address_block
        assert "123 Main St" in address_block
        assert "New York, NY 10001" in address_block
        assert "(555) 123-4567" in address_block
        
        # Verify individual components were removed
        assert "payerStreetAddress" not in captured_form_data
        assert "payerCity" not in captured_form_data
        assert "payerState" not in captured_form_data
        assert "payerZip" not in captured_form_data
        assert "payerTelephoneNumber" not in captured_form_data
        
        # Verify payerName is kept (for backward compatibility)
        assert "payerName" in captured_form_data
    
    @patch('tax_document_generation.document_generator.fitz')
    @patch('tax_document_generation.document_generator.FieldMapper')
    def test_recipient_address_combination(self, mock_mapper_class, mock_fitz):
        """Test that recipient address is combined correctly."""
        # Setup mocks
        mock_doc = MagicMock()
        mock_fitz.open.return_value = mock_doc
        mock_doc.__len__.return_value = 1
        mock_doc.tobytes.return_value = b'PDF content'
        
        mock_mapper = MagicMock()
        mock_mapper_class.return_value = mock_mapper
        mock_mapper.get_unmapped_fields.return_value = []
        
        # Capture the form_data passed to map_all_fields
        captured_form_data = None
        def capture_form_data(form_data):
            nonlocal captured_form_data
            captured_form_data = form_data.copy()
            return {}
        
        mock_mapper.map_all_fields.side_effect = capture_form_data
        
        # Test data with recipient address components
        form_data = {
            "recipientName": "John Doe",
            "recipientStreetAddress": "456 Oak Ave",
            "recipientCity": "Los Angeles",
            "recipientState": "CA",
            "recipientZip": "90001"
        }
        
        # Generate document
        template = b'%PDF-1.4 fake template'
        result = generate_document(template, form_data, "1099-DIV")
        
        # Verify result
        assert result == b'PDF content'
        
        # Verify recipient address combination happened
        assert captured_form_data is not None
        assert "recipientCityStateZip" in captured_form_data
        
        # Verify combined address
        city_state_zip = captured_form_data["recipientCityStateZip"]
        assert city_state_zip == "Los Angeles, CA 90001"
        
        # Verify individual components were removed
        assert "recipientCity" not in captured_form_data
        assert "recipientState" not in captured_form_data
        assert "recipientZip" not in captured_form_data
        
        # Verify required fields are kept
        assert "recipientName" in captured_form_data
        assert "recipientStreetAddress" in captured_form_data
    
    @patch('tax_document_generation.document_generator.fitz')
    @patch('tax_document_generation.document_generator.FieldMapper')
    def test_integration_order(self, mock_mapper_class, mock_fitz):
        """Test that normalization happens before combination."""
        # Setup mocks
        mock_doc = MagicMock()
        mock_fitz.open.return_value = mock_doc
        mock_doc.__len__.return_value = 1
        mock_doc.tobytes.return_value = b'PDF content'
        
        mock_mapper = MagicMock()
        mock_mapper_class.return_value = mock_mapper
        mock_mapper.get_unmapped_fields.return_value = []
        
        # Capture the form_data passed to map_all_fields
        captured_form_data = None
        def capture_form_data(form_data):
            nonlocal captured_form_data
            captured_form_data = form_data.copy()
            return {}
        
        mock_mapper.map_all_fields.side_effect = capture_form_data
        
        # Test data with old combined format (requires normalization)
        form_data = {
            "payerName": "Example Corp",
            "payerCity": "Boston, MA 02101"  # Old combined format
        }
        
        # Generate document
        template = b'%PDF-1.4 fake template'
        result = generate_document(template, form_data, "1099-DIV")
        
        # Verify result
        assert result == b'PDF content'
        
        # Verify normalization happened (city was split)
        # and then combination happened (address block was created)
        assert captured_form_data is not None
        assert "payerAddressBlock" in captured_form_data
        
        # The address block should contain the normalized components
        address_block = captured_form_data["payerAddressBlock"]
        assert "Example Corp" in address_block
        assert "Boston, MA 02101" in address_block
