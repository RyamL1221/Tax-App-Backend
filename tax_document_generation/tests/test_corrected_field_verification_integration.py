"""
Integration tests for corrected 1099-DIV field mappings.

**Validates: Requirements 3.1, 3.2, 3.3, 4.1, 4.2, 4.3, 5.1, 5.2**

This test suite verifies that the corrected TIN field mappings work correctly
in the complete document generation workflow. It ensures that:
- Payer TIN appears in correct location (f2_7), NOT in city field (f2_4)
- Recipient TIN appears in correct location (f2_8), NOT in account number field (f2_39)
- City field remains empty when no city data provided
- Account number field remains empty when no account data provided
- All three copies (Copy1, Copy2, CopyB) are correctly populated
"""

import pytest
import os
import fitz
from typing import Dict


# Import the document generator
from tax_document_generation.document_generator import generate_document


def extract_field_values_by_copy(pdf_bytes: bytes) -> Dict[str, Dict[str, str]]:
    """
    Extract field values grouped by copy (Copy1, Copy2, CopyB).
    
    Args:
        pdf_bytes: PDF document as bytes
        
    Returns:
        Dictionary mapping copy name to field values
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    
    copy_values = {
        "Copy1": {},
        "Copy2": {},
        "CopyB": {}
    }
    
    try:
        for page_num in range(len(doc)):
            page = doc[page_num]
            widgets = page.widgets()
            
            if widgets:
                for widget in widgets:
                    if widget.field_name:
                        field_name = widget.field_name
                        field_value = widget.field_value or ""
                        
                        # Determine which copy this field belongs to
                        if "Copy1[0]" in field_name:
                            copy_values["Copy1"][field_name] = field_value
                        elif "Copy2[0]" in field_name:
                            copy_values["Copy2"][field_name] = field_value
                        elif "CopyB[0]" in field_name:
                            copy_values["CopyB"][field_name] = field_value
    finally:
        doc.close()
    
    return copy_values


def get_template_path() -> str:
    """
    Find the 1099-DIV template file.
    
    Returns:
        Path to template file
        
    Raises:
        FileNotFoundError: If template not found
    """
    possible_paths = [
        "1099-DIV.pdf",
        "../1099-DIV.pdf",
        "../../1099-DIV.pdf",
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "1099-DIV.pdf"),
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    raise FileNotFoundError("1099-DIV.pdf template not found")


class TestCorrectedTINMappings:
    """Test suite for corrected TIN field mappings."""
    
    def test_payer_tin_in_correct_location_not_city(self):
        """
        Test that payer TIN appears in correct location (f2_7), NOT city field (f2_4).
        
        Requirements: 3.1, 3.2, 3.3
        """
        try:
            template_path = get_template_path()
        except FileNotFoundError:
            pytest.skip("1099-DIV.pdf template not found")
        
        # Read template
        with open(template_path, 'rb') as f:
            template_bytes = f.read()
        
        # Create form data with payer TIN but no city
        form_data = {
            "payerName": "Test Corporation",
            "payerTIN": "12-3456789",
            "totalOrdinaryDividends": "1000.00"
        }
        
        # Generate PDF
        output_bytes = generate_document(template_bytes, form_data, "1099-DIV")
        
        # Extract field values by copy
        copy_values = extract_field_values_by_copy(output_bytes)
        
        # Verify payer TIN is in correct field (f2_7) in all copies
        for copy_name in ["Copy1", "Copy2", "CopyB"]:
            payer_tin_fields = {
                k: v for k, v in copy_values[copy_name].items() 
                if "f2_7[0]" in k
            }
            
            assert len(payer_tin_fields) > 0, \
                f"Payer TIN should be in f2_7 field in {copy_name}"
            
            for field, value in payer_tin_fields.items():
                assert value == "12-3456789", \
                    f"Payer TIN should have correct value in {copy_name}"
        
        # Verify payer TIN is NOT in city field (f2_4) in any copy
        for copy_name in ["Copy1", "Copy2", "CopyB"]:
            city_fields = {
                k: v for k, v in copy_values[copy_name].items() 
                if "f2_4[0]" in k
            }
            
            for field, value in city_fields.items():
                assert value != "12-3456789", \
                    f"Payer TIN should NOT be in city field in {copy_name}"
                assert value == "" or value is None, \
                    f"City field should be empty when no city data provided in {copy_name}"
    
    def test_recipient_tin_in_correct_location_not_account_number(self):
        """
        Test that recipient TIN appears in correct location (f2_8), NOT account number field (f2_39).
        
        Requirements: 4.1, 4.2, 4.3
        """
        try:
            template_path = get_template_path()
        except FileNotFoundError:
            pytest.skip("1099-DIV.pdf template not found")
        
        # Read template
        with open(template_path, 'rb') as f:
            template_bytes = f.read()
        
        # Create form data with recipient TIN but no account number
        form_data = {
            "payerName": "Test Corporation",
            "recipientTIN": "987-65-4321",
            "totalOrdinaryDividends": "1000.00"
        }
        
        # Generate PDF
        output_bytes = generate_document(template_bytes, form_data, "1099-DIV")
        
        # Extract field values by copy
        copy_values = extract_field_values_by_copy(output_bytes)
        
        # Verify recipient TIN is in correct field (f2_8) in all copies
        for copy_name in ["Copy1", "Copy2", "CopyB"]:
            recipient_tin_fields = {
                k: v for k, v in copy_values[copy_name].items() 
                if "f2_8[0]" in k
            }
            
            assert len(recipient_tin_fields) > 0, \
                f"Recipient TIN should be in f2_8 field in {copy_name}"
            
            for field, value in recipient_tin_fields.items():
                assert value == "987-65-4321", \
                    f"Recipient TIN should have correct value in {copy_name}"
        
        # Verify recipient TIN is NOT in account number field (f2_39) in any copy
        for copy_name in ["Copy1", "Copy2", "CopyB"]:
            account_fields = {
                k: v for k, v in copy_values[copy_name].items() 
                if "f2_39[0]" in k
            }
            
            for field, value in account_fields.items():
                assert value != "987-65-4321", \
                    f"Recipient TIN should NOT be in account number field in {copy_name}"
                assert value == "" or value is None, \
                    f"Account number field should be empty when no account data provided in {copy_name}"
    
    def test_both_tins_in_correct_locations(self):
        """
        Test that both TINs appear in correct locations simultaneously.
        
        Requirements: 3.1, 3.2, 4.1, 4.2
        """
        try:
            template_path = get_template_path()
        except FileNotFoundError:
            pytest.skip("1099-DIV.pdf template not found")
        
        # Read template
        with open(template_path, 'rb') as f:
            template_bytes = f.read()
        
        # Create form data with both TINs
        form_data = {
            "payerName": "Test Corporation",
            "payerTIN": "12-3456789",
            "recipientTIN": "987-65-4321",
            "totalOrdinaryDividends": "1000.00"
        }
        
        # Generate PDF
        output_bytes = generate_document(template_bytes, form_data, "1099-DIV")
        
        # Extract field values by copy
        copy_values = extract_field_values_by_copy(output_bytes)
        
        # Verify both TINs are in correct fields in all copies
        for copy_name in ["Copy1", "Copy2", "CopyB"]:
            # Check payer TIN
            payer_tin_fields = {
                k: v for k, v in copy_values[copy_name].items() 
                if "f2_7[0]" in k
            }
            assert len(payer_tin_fields) > 0, \
                f"Payer TIN should be in f2_7 field in {copy_name}"
            for field, value in payer_tin_fields.items():
                assert value == "12-3456789", \
                    f"Payer TIN should have correct value in {copy_name}"
            
            # Check recipient TIN
            recipient_tin_fields = {
                k: v for k, v in copy_values[copy_name].items() 
                if "f2_8[0]" in k
            }
            assert len(recipient_tin_fields) > 0, \
                f"Recipient TIN should be in f2_8 field in {copy_name}"
            for field, value in recipient_tin_fields.items():
                assert value == "987-65-4321", \
                    f"Recipient TIN should have correct value in {copy_name}"
    
    def test_city_and_account_number_fields_remain_empty(self):
        """
        Test that city and account number fields remain empty when not provided.
        
        Requirements: 3.3, 4.3
        """
        try:
            template_path = get_template_path()
        except FileNotFoundError:
            pytest.skip("1099-DIV.pdf template not found")
        
        # Read template
        with open(template_path, 'rb') as f:
            template_bytes = f.read()
        
        # Create form data with TINs but no city or account number
        form_data = {
            "payerName": "Test Corporation",
            "payerTIN": "12-3456789",
            "recipientTIN": "987-65-4321",
            "totalOrdinaryDividends": "1000.00"
        }
        
        # Generate PDF
        output_bytes = generate_document(template_bytes, form_data, "1099-DIV")
        
        # Extract field values by copy
        copy_values = extract_field_values_by_copy(output_bytes)
        
        # Verify city and account number fields are empty in all copies
        for copy_name in ["Copy1", "Copy2", "CopyB"]:
            # Check city field (f2_4)
            city_fields = {
                k: v for k, v in copy_values[copy_name].items() 
                if "f2_4[0]" in k
            }
            for field, value in city_fields.items():
                assert value == "" or value is None, \
                    f"City field should be empty in {copy_name}"
            
            # Check account number field (f2_39)
            account_fields = {
                k: v for k, v in copy_values[copy_name].items() 
                if "f2_39[0]" in k
            }
            for field, value in account_fields.items():
                assert value == "" or value is None, \
                    f"Account number field should be empty in {copy_name}"
    
    def test_city_and_account_number_can_be_provided(self):
        """
        Test that city and account number fields work when explicitly provided.
        
        Requirements: 3.3, 4.3
        """
        try:
            template_path = get_template_path()
        except FileNotFoundError:
            pytest.skip("1099-DIV.pdf template not found")
        
        # Read template
        with open(template_path, 'rb') as f:
            template_bytes = f.read()
        
        # Create form data with city and account number
        form_data = {
            "payerName": "Test Corporation",
            "payerCity": "New York",
            "payerTIN": "12-3456789",
            "recipientTIN": "987-65-4321",
            "accountNumber": "123456789",
            "totalOrdinaryDividends": "1000.00"
        }
        
        # Generate PDF
        output_bytes = generate_document(template_bytes, form_data, "1099-DIV")
        
        # Extract field values by copy
        copy_values = extract_field_values_by_copy(output_bytes)
        
        # Verify city and account number fields are populated in all copies
        for copy_name in ["Copy1", "Copy2", "CopyB"]:
            # Check city field (f2_4)
            city_fields = {
                k: v for k, v in copy_values[copy_name].items() 
                if "f2_4[0]" in k
            }
            assert len(city_fields) > 0, \
                f"City field should exist in {copy_name}"
            for field, value in city_fields.items():
                assert value == "New York", \
                    f"City field should have correct value in {copy_name}"
            
            # Check account number field (f2_39)
            account_fields = {
                k: v for k, v in copy_values[copy_name].items() 
                if "f2_39[0]" in k
            }
            assert len(account_fields) > 0, \
                f"Account number field should exist in {copy_name}"
            for field, value in account_fields.items():
                assert value == "123456789", \
                    f"Account number field should have correct value in {copy_name}"
    
    def test_all_three_copies_have_consistent_values(self):
        """
        Test that all three copies have consistent field values.
        
        Requirements: 3.2, 4.2, 5.2, 8.3
        """
        try:
            template_path = get_template_path()
        except FileNotFoundError:
            pytest.skip("1099-DIV.pdf template not found")
        
        # Read template
        with open(template_path, 'rb') as f:
            template_bytes = f.read()
        
        # Create comprehensive form data
        form_data = {
            "payerName": "Test Corporation",
            "payerTIN": "12-3456789",
            "recipientTIN": "987-65-4321",
            "totalOrdinaryDividends": "1000.00",
            "qualifiedDividends": "500.00"
        }
        
        # Generate PDF
        output_bytes = generate_document(template_bytes, form_data, "1099-DIV")
        
        # Extract field values by copy
        copy_values = extract_field_values_by_copy(output_bytes)
        
        # For each field type, verify consistency across copies
        field_patterns = [
            ("f2_7[0]", "12-3456789", "Payer TIN"),
            ("f2_8[0]", "987-65-4321", "Recipient TIN"),
        ]
        
        for field_pattern, expected_value, field_description in field_patterns:
            copy1_values = [
                v for k, v in copy_values["Copy1"].items() 
                if field_pattern in k
            ]
            copy2_values = [
                v for k, v in copy_values["Copy2"].items() 
                if field_pattern in k
            ]
            copyb_values = [
                v for k, v in copy_values["CopyB"].items() 
                if field_pattern in k
            ]
            
            # Verify all copies have the field
            assert len(copy1_values) > 0, \
                f"{field_description} should exist in Copy1"
            assert len(copy2_values) > 0, \
                f"{field_description} should exist in Copy2"
            assert len(copyb_values) > 0, \
                f"{field_description} should exist in CopyB"
            
            # Verify all copies have the same value
            assert copy1_values[0] == copy2_values[0] == copyb_values[0], \
                f"{field_description} should have consistent value across all copies"
            
            # Verify the value is correct
            assert copy1_values[0] == expected_value, \
                f"{field_description} should have correct value"
    
    def test_regression_no_tin_in_wrong_fields(self):
        """
        Regression test: Verify TINs are NOT in wrong fields.
        
        This test specifically checks that the original bug is fixed:
        - Payer TIN is NOT in city field (f2_4)
        - Recipient TIN is NOT in account number field (f2_39)
        
        Requirements: 3.1, 4.1
        """
        try:
            template_path = get_template_path()
        except FileNotFoundError:
            pytest.skip("1099-DIV.pdf template not found")
        
        # Read template
        with open(template_path, 'rb') as f:
            template_bytes = f.read()
        
        # Create form data with TINs
        form_data = {
            "payerTIN": "12-3456789",
            "recipientTIN": "987-65-4321"
        }
        
        # Generate PDF
        output_bytes = generate_document(template_bytes, form_data, "1099-DIV")
        
        # Extract field values by copy
        copy_values = extract_field_values_by_copy(output_bytes)
        
        # Verify TINs are NOT in wrong fields in any copy
        for copy_name in ["Copy1", "Copy2", "CopyB"]:
            # Check that payer TIN is NOT in city field
            city_fields = {
                k: v for k, v in copy_values[copy_name].items() 
                if "f2_4[0]" in k
            }
            for field, value in city_fields.items():
                assert value != "12-3456789", \
                    f"Payer TIN should NOT be in city field (f2_4) in {copy_name} - this was the original bug!"
            
            # Check that recipient TIN is NOT in account number field
            account_fields = {
                k: v for k, v in copy_values[copy_name].items() 
                if "f2_39[0]" in k
            }
            for field, value in account_fields.items():
                assert value != "987-65-4321", \
                    f"Recipient TIN should NOT be in account number field (f2_39) in {copy_name} - this was the original bug!"
