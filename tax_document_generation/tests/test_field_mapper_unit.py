"""
Unit tests for FieldMapper class.

These tests verify specific field mappings and FieldMapper functionality.

Feature: fix-pdf-field-mapping
"""

import pytest
from tax_document_generation.field_mapper import FieldMapper
from tax_document_generation.field_mappings.div_1099 import FIELD_MAPPING


class TestFieldMapperUnit:
    """Unit tests for FieldMapper class."""
    
    def test_payer_name_mapping(self):
        """
        **Validates: Requirements 5.1**
        
        Verify that payerName maps to the correct PDF field.
        
        This test verifies that:
        1. payerName is recognized as a valid field
        2. The correct PDF field name is returned
        3. The mapping matches the configuration
        """
        # Initialize the field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Map the payerName field
        pdf_field_name = mapper.map_field("payerName")
        
        # Verify the mapping is correct
        expected_pdf_field = FIELD_MAPPING["payerName"]
        
        assert pdf_field_name == expected_pdf_field, \
            f"payerName should map to '{expected_pdf_field}', got '{pdf_field_name}'"
        
        # Verify it's the expected field (from the left column)
        assert "LeftCol" in pdf_field_name, \
            "payerName should be in the LeftCol section"
        
        assert pdf_field_name.startswith("topmostSubform[0].Copy1[0]."), \
            "payerName should follow the standard PDF field pattern"
    
    def test_total_ordinary_dividends_mapping(self):
        """
        **Validates: Requirements 5.2**
        
        Verify that totalOrdinaryDividends maps to the correct PDF field (box 1a).
        
        This test verifies that:
        1. totalOrdinaryDividends is recognized as a valid field
        2. The correct PDF field name is returned
        3. The mapping points to box 1a
        """
        # Initialize the field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Map the totalOrdinaryDividends field
        pdf_field_name = mapper.map_field("totalOrdinaryDividends")
        
        # Verify the mapping is correct
        expected_pdf_field = FIELD_MAPPING["totalOrdinaryDividends"]
        
        assert pdf_field_name == expected_pdf_field, \
            f"totalOrdinaryDividends should map to '{expected_pdf_field}', got '{pdf_field_name}'"
        
        # Verify it's in the right column (where box values are)
        assert "RghtCol" in pdf_field_name, \
            "totalOrdinaryDividends should be in the RghtCol section"
        
        assert pdf_field_name.startswith("topmostSubform[0].Copy1[0]."), \
            "totalOrdinaryDividends should follow the standard PDF field pattern"
    
    def test_1099_div_initialization(self):
        """
        **Validates: Requirements 2.1**
        
        Verify that "1099-DIV" document type initializes successfully.
        
        This test verifies that:
        1. FieldMapper accepts "1099-DIV" as a valid document type
        2. Initialization completes without errors
        3. Mapping configuration is loaded
        """
        # Initialize the field mapper - should not raise exception
        mapper = FieldMapper("1099-DIV")
        
        # Verify the mapper is initialized
        assert mapper is not None, \
            "FieldMapper should be initialized"
        
        assert mapper.document_type == "1099-DIV", \
            "Document type should be set correctly"
        
        # Verify mapping is loaded
        assert hasattr(mapper, '_mapping'), \
            "Mapper should have _mapping attribute"
        
        assert len(mapper._mapping) > 0, \
            "Mapping should contain field definitions"
    
    def test_backward_compatibility_of_generate_document_signature(self):
        """
        **Validates: Requirements 3.4**
        
        Verify that document_generator.generate_document() signature is unchanged.
        
        This test verifies that:
        1. Function signature remains the same
        2. Parameters are in the same order
        3. Backward compatibility is maintained
        """
        from tax_document_generation.document_generator import generate_document
        import inspect
        
        # Get the function signature
        sig = inspect.signature(generate_document)
        params = list(sig.parameters.keys())
        
        # Verify the expected parameters exist
        assert "template" in params, \
            "generate_document should have 'template' parameter"
        
        assert "form_data" in params, \
            "generate_document should have 'form_data' parameter"
        
        assert "document_type" in params, \
            "generate_document should have 'document_type' parameter"
        
        # Verify parameter order
        assert params.index("template") < params.index("form_data"), \
            "template should come before form_data"
        
        assert params.index("form_data") < params.index("document_type"), \
            "form_data should come before document_type"
    
    def test_unsupported_document_type_raises_error(self):
        """
        Verify that unsupported document types raise a clear error.
        
        This test verifies that:
        1. Invalid document types are rejected
        2. Clear error message is provided
        3. ValueError is raised
        """
        # Try to initialize with unsupported document type
        with pytest.raises(ValueError) as exc_info:
            mapper = FieldMapper("1099-MISC")
        
        # Verify the error message is clear
        error_message = str(exc_info.value)
        
        assert "1099-MISC" in error_message, \
            "Error message should mention the unsupported document type"
        
        assert "not supported" in error_message.lower(), \
            "Error message should indicate the type is not supported"
    
    def test_map_field_returns_none_for_invalid_field(self):
        """
        Verify that invalid field names return None.
        
        This test verifies that:
        1. Invalid field names are handled gracefully
        2. None is returned (not an exception)
        3. System continues to function
        """
        # Initialize the field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Try to map an invalid field
        result = mapper.map_field("invalidFieldName")
        
        # Verify None is returned
        assert result is None, \
            "Invalid field name should return None"
    
    def test_map_all_fields_with_empty_dict(self):
        """
        Verify that empty form data returns empty mapped data.
        
        This test verifies that:
        1. Empty input is handled gracefully
        2. Empty dict is returned
        3. No errors occur
        """
        # Initialize the field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Map empty form data
        result = mapper.map_all_fields({})
        
        # Verify empty dict is returned
        assert result == {}, \
            "Empty form data should return empty mapped data"
    
    def test_map_all_fields_excludes_unmapped_fields(self):
        """
        Verify that unmapped fields are excluded from the result.
        
        This test verifies that:
        1. Only valid fields are in the result
        2. Invalid fields are filtered out
        3. Result contains only mapped fields
        4. Multi-copy mappings are generated (3 copies per field)
        """
        # Initialize the field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Create form data with valid and invalid fields
        form_data = {
            "payerName": "Test Payer",
            "invalidField": "Test Value",
            "totalOrdinaryDividends": "1000.00"
        }
        
        # Map the fields
        result = mapper.map_all_fields(form_data)
        
        # Verify only valid fields are in the result (2 API fields × 3 copies = 6 PDF fields)
        assert len(result) == 6, \
            "Result should contain 6 PDF fields (2 API fields × 3 copies each)"
        
        # Verify the invalid field is not in the result
        for key in result.keys():
            assert key != "invalidField", \
                "Invalid field should not be in the result"
        
        # Verify all three copies are present for each valid field
        payer_name_copies = [k for k in result.keys() if "f2_2[0]" in k]
        assert len(payer_name_copies) == 3, \
            "Should have 3 copies of payerName field"
        
        dividends_copies = [k for k in result.keys() if "f2_9[0]" in k]
        assert len(dividends_copies) == 3, \
            "Should have 3 copies of totalOrdinaryDividends field"
    
    def test_get_unmapped_fields_returns_correct_list(self):
        """
        Verify that get_unmapped_fields returns the correct list of unmapped fields.
        
        This test verifies that:
        1. Unmapped fields are identified correctly
        2. List contains all unmapped fields
        3. List does not contain valid fields
        """
        # Initialize the field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Create form data with valid and invalid fields
        form_data = {
            "payerName": "Test Payer",
            "invalidField1": "Test Value 1",
            "totalOrdinaryDividends": "1000.00",
            "invalidField2": "Test Value 2"
        }
        
        # Get unmapped fields
        unmapped = mapper.get_unmapped_fields(form_data)
        
        # Verify the correct fields are identified as unmapped
        assert "invalidField1" in unmapped, \
            "invalidField1 should be in unmapped list"
        
        assert "invalidField2" in unmapped, \
            "invalidField2 should be in unmapped list"
        
        assert "payerName" not in unmapped, \
            "payerName should not be in unmapped list"
        
        assert "totalOrdinaryDividends" not in unmapped, \
            "totalOrdinaryDividends should not be in unmapped list"
        
        assert len(unmapped) == 2, \
            "Should have exactly 2 unmapped fields"
    
    def test_recipient_tin_mapping(self):
        """
        Verify that recipientTIN maps to the correct PDF field.
        
        This test verifies that:
        1. recipientTIN is recognized as a valid field
        2. The correct PDF field name is returned
        3. The mapping is in the left column
        """
        # Initialize the field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Map the recipientTIN field
        pdf_field_name = mapper.map_field("recipientTIN")
        
        # Verify the mapping is correct
        expected_pdf_field = FIELD_MAPPING["recipientTIN"]
        
        assert pdf_field_name == expected_pdf_field, \
            f"recipientTIN should map to '{expected_pdf_field}', got '{pdf_field_name}'"
        
        # Verify it's in the left column
        assert "LeftCol" in pdf_field_name, \
            "recipientTIN should be in the LeftCol section"
    
    def test_qualified_dividends_mapping(self):
        """
        Verify that qualifiedDividends maps to the correct PDF field (box 1b).
        
        This test verifies that:
        1. qualifiedDividends is recognized as a valid field
        2. The correct PDF field name is returned
        3. The mapping is in the right column
        """
        # Initialize the field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Map the qualifiedDividends field
        pdf_field_name = mapper.map_field("qualifiedDividends")
        
        # Verify the mapping is correct
        expected_pdf_field = FIELD_MAPPING["qualifiedDividends"]
        
        assert pdf_field_name == expected_pdf_field, \
            f"qualifiedDividends should map to '{expected_pdf_field}', got '{pdf_field_name}'"
        
        # Verify it's in the right column
        assert "RghtCol" in pdf_field_name, \
            "qualifiedDividends should be in the RghtCol section"
    
    def test_multiple_mappers_have_same_mappings(self):
        """
        Verify that multiple FieldMapper instances have the same mappings.
        
        This test verifies that:
        1. Mappings are consistent across instances
        2. No instance-specific state affects mappings
        3. Configuration is loaded correctly
        """
        # Initialize multiple field mappers
        mapper1 = FieldMapper("1099-DIV")
        mapper2 = FieldMapper("1099-DIV")
        
        # Map the same field with both mappers
        result1 = mapper1.map_field("payerName")
        result2 = mapper2.map_field("payerName")
        
        # Verify results are identical
        assert result1 == result2, \
            "Multiple mappers should have the same mappings"
    
    def test_map_all_fields_preserves_values(self):
        """
        Verify that map_all_fields preserves field values.
        
        This test verifies that:
        1. Values are not modified during mapping
        2. Only keys are translated
        3. Data integrity is maintained
        """
        # Initialize the field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Create form data
        form_data = {
            "payerName": "Test Payer Inc.",
            "totalOrdinaryDividends": "12345.67"
        }
        
        # Map the fields
        result = mapper.map_all_fields(form_data)
        
        # Verify values are preserved
        result_values = list(result.values())
        
        assert "Test Payer Inc." in result_values, \
            "payerName value should be preserved"
        
        assert "12345.67" in result_values, \
            "totalOrdinaryDividends value should be preserved"
