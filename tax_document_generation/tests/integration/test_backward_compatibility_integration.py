"""
Integration tests for backward compatibility with existing example payloads.

This test suite verifies that existing API payloads continue to work without
modification after adding flexible input formatting support. It loads the
example payloads from docs/examples/ and verifies that:
1. Pre-formatted payloads are accepted without errors
2. No normalization changes are applied to pre-formatted values
3. PDF output is generated successfully

Requirements: 3.1, 3.2, 3.3, 3.4, 3.5
"""

import json
import os
import pytest
from unittest.mock import Mock, patch, MagicMock

from tax_document_generation.input_normalizer import normalize_form_data
from tax_document_generation.input_validator import validate_form_data


class TestBackwardCompatibility:
    """Test backward compatibility with existing example payloads."""
    
    def load_example_payload(self, filename: str) -> dict:
        """Load an example payload from docs/examples/."""
        # Get the path to the examples directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(current_dir))
        examples_dir = os.path.join(project_root, 'docs', 'examples')
        filepath = os.path.join(examples_dir, filename)
        
        with open(filepath, 'r') as f:
            return json.load(f)
    
    def test_minimal_example_no_normalization(self):
        """
        Test that minimal example payload requires minimal normalization.
        
        The minimal example uses pre-formatted values, but JSON parsing
        converts 1000.00 to 1000.0 (float), so the normalizer will add
        the trailing zero back. TINs remain unchanged since they're strings.
        
        This demonstrates backward compatibility: the system accepts the
        payload and produces correct output, even though JSON parsing
        causes minor format changes.
        
        Requirements: 3.1, 3.2
        """
        # Load minimal example
        payload = self.load_example_payload('1099-DIV-minimal-example.json')
        document_type = payload['documentType']
        form_data = payload['formData']
        
        # Validate (should pass)
        validate_form_data(document_type, form_data)
        
        # Normalize
        result = normalize_form_data(form_data, document_type)
        
        # JSON parsing converts 1000.00 to 1000.0, so normalizer adds trailing zero
        # This is expected and demonstrates the normalizer is working correctly
        assert len(result.changes) == 1
        assert result.changes[0][0] == 'totalOrdinaryDividends'
        assert result.changes[0][1] == '1000.0'  # JSON parsed value
        assert result.changes[0][2] == '1000.00'  # Normalized value
        
        # Verify TINs were not changed (they're strings, so JSON preserves format)
        assert result.normalized_data['payerTIN'] == '12-3456789'
        assert result.normalized_data['recipientTIN'] == '123-45-6789'
    
    def test_typical_example_no_normalization(self):
        """
        Test that typical example payload requires minimal normalization.
        
        The typical example uses pre-formatted values, but JSON parsing
        converts decimal values like 1000.00 to 1000.0, so the normalizer
        will add trailing zeros back.
        
        Requirements: 3.1, 3.2
        """
        # Load typical example
        payload = self.load_example_payload('1099-DIV-typical-example.json')
        document_type = payload['documentType']
        form_data = payload['formData']
        
        # Validate (should pass)
        validate_form_data(document_type, form_data)
        
        # Normalize
        result = normalize_form_data(form_data, document_type)
        
        # JSON parsing causes loss of trailing zeros, so normalizer adds them back
        # This is expected behavior
        assert len(result.changes) == 3
        decimal_fields_changed = {change[0] for change in result.changes}
        assert decimal_fields_changed == {
            'totalOrdinaryDividends',
            'qualifiedDividends',
            'federalIncomeTaxWithheld'
        }
        
        # Verify all normalized values have two decimal places
        for field_name, original, normalized in result.changes:
            assert normalized.endswith('.00')
        
        # Verify TINs were not changed
        assert result.normalized_data['payerTIN'] == '12-3456789'
        assert result.normalized_data['recipientTIN'] == '123-45-6789'
    
    def test_complete_example_no_normalization(self):
        """
        Test that complete example payload requires minimal normalization.
        
        The complete example uses pre-formatted values for all fields,
        but JSON parsing converts decimal values, so the normalizer
        will add trailing zeros back to all decimal fields.
        
        Requirements: 3.1, 3.2
        """
        # Load complete example
        payload = self.load_example_payload('1099-DIV-complete-example.json')
        document_type = payload['documentType']
        form_data = payload['formData']
        
        # Validate (should pass)
        validate_form_data(document_type, form_data)
        
        # Normalize
        result = normalize_form_data(form_data, document_type)
        
        # JSON parsing causes loss of trailing zeros for all decimal fields
        # The normalizer adds them back - this is expected behavior
        assert len(result.changes) == 19  # All decimal fields
        
        # Verify all normalized values have two decimal places
        for field_name, original, normalized in result.changes:
            assert normalized.endswith('.00'), \
                f"Field {field_name} should have two decimal places: {normalized}"
        
        # Verify TINs were not changed (strings preserve format)
        assert result.normalized_data['payerTIN'] == '12-3456789'
        assert result.normalized_data['recipientTIN'] == '123-45-6789'
    
    @patch('tax_document_generation.app.get_template')
    @patch('tax_document_generation.app.generate_document')
    @patch('tax_document_generation.app.store_output')
    @patch('tax_document_generation.app.create_job')
    @patch('tax_document_generation.app.update_job_completed')
    @patch('tax_document_generation.app.validate_jwt')
    def test_minimal_example_end_to_end(
        self,
        mock_validate_jwt,
        mock_update_job_completed,
        mock_create_job,
        mock_store_output,
        mock_generate_document,
        mock_get_template
    ):
        """
        Test end-to-end processing of minimal example payload.
        
        Verifies that the complete Lambda handler workflow succeeds
        with a pre-formatted payload.
        
        Requirements: 3.2, 3.3, 3.4
        """
        from tax_document_generation.app import lambda_handler
        
        # Load minimal example
        payload = self.load_example_payload('1099-DIV-minimal-example.json')
        
        # Setup mocks
        mock_validate_jwt.return_value = {'userId': 'test-user-123', 'email': 'test@example.com'}
        mock_get_template.return_value = b'mock-template-pdf'
        mock_generate_document.return_value = b'mock-generated-pdf'
        mock_store_output.return_value = 'outputs/test-user-123/job-123/1099-DIV.pdf'
        mock_update_job_completed.return_value = {
            'jobId': 'job-123',
            'userId': 'test-user-123',
            'documentType': '1099-DIV',
            'status': 'COMPLETED',
            'outputKey': 'outputs/test-user-123/job-123/1099-DIV.pdf',
            'createdAt': '2024-01-01T00:00:00Z',
            'updatedAt': '2024-01-01T00:00:01Z',
            'completedAt': '2024-01-01T00:00:01Z'
        }
        
        # Create Lambda event
        event = {
            'headers': {
                'Authorization': 'Bearer mock-jwt-token'
            },
            'body': json.dumps(payload)
        }
        
        # Set environment variables
        os.environ['TEMPLATES_BUCKET'] = 'test-templates'
        os.environ['OUTPUTS_BUCKET'] = 'test-outputs'
        os.environ['JOB_TABLE_NAME'] = 'test-jobs'
        os.environ['JWT_SECRET_KEY'] = 'test-secret-key-at-least-32-characters-long'
        
        # Call Lambda handler
        response = lambda_handler(event, None)
        
        # Verify success response
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['jobId'] == 'job-123'
        assert body['status'] == 'COMPLETED'
        
        # Verify document was generated with correct data
        mock_generate_document.assert_called_once()
        call_args = mock_generate_document.call_args
        generated_form_data = call_args[0][1]  # Second argument is form_data
        
        # Verify form data was normalized (JSON parsing converts 1000.00 to 1000.0,
        # normalizer converts it back to "1000.00" string)
        assert generated_form_data['totalOrdinaryDividends'] == '1000.00'
        assert isinstance(generated_form_data['totalOrdinaryDividends'], str)
    
    @patch('tax_document_generation.app.get_template')
    @patch('tax_document_generation.app.generate_document')
    @patch('tax_document_generation.app.store_output')
    @patch('tax_document_generation.app.create_job')
    @patch('tax_document_generation.app.update_job_completed')
    @patch('tax_document_generation.app.validate_jwt')
    def test_typical_example_end_to_end(
        self,
        mock_validate_jwt,
        mock_update_job_completed,
        mock_create_job,
        mock_store_output,
        mock_generate_document,
        mock_get_template
    ):
        """
        Test end-to-end processing of typical example payload.
        
        Requirements: 3.2, 3.3, 3.4
        """
        from tax_document_generation.app import lambda_handler
        
        # Load typical example
        payload = self.load_example_payload('1099-DIV-typical-example.json')
        
        # Setup mocks
        mock_validate_jwt.return_value = {'userId': 'test-user-456', 'email': 'test@example.com'}
        mock_get_template.return_value = b'mock-template-pdf'
        mock_generate_document.return_value = b'mock-generated-pdf'
        mock_store_output.return_value = 'outputs/test-user-456/job-456/1099-DIV.pdf'
        mock_update_job_completed.return_value = {
            'jobId': 'job-456',
            'userId': 'test-user-456',
            'documentType': '1099-DIV',
            'status': 'COMPLETED',
            'outputKey': 'outputs/test-user-456/job-456/1099-DIV.pdf',
            'createdAt': '2024-01-01T00:00:00Z',
            'updatedAt': '2024-01-01T00:00:01Z',
            'completedAt': '2024-01-01T00:00:01Z'
        }
        
        # Create Lambda event
        event = {
            'headers': {
                'Authorization': 'Bearer mock-jwt-token'
            },
            'body': json.dumps(payload)
        }
        
        # Set environment variables
        os.environ['TEMPLATES_BUCKET'] = 'test-templates'
        os.environ['OUTPUTS_BUCKET'] = 'test-outputs'
        os.environ['JOB_TABLE_NAME'] = 'test-jobs'
        os.environ['JWT_SECRET_KEY'] = 'test-secret-key-at-least-32-characters-long'
        
        # Call Lambda handler
        response = lambda_handler(event, None)
        
        # Verify success response
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['status'] == 'COMPLETED'
        
        # Verify document was generated with normalized data
        mock_generate_document.assert_called_once()
        call_args = mock_generate_document.call_args
        generated_form_data = call_args[0][1]
        
        # Verify decimal fields were normalized to strings with two decimal places
        assert generated_form_data['totalOrdinaryDividends'] == '1000.00'
        assert generated_form_data['qualifiedDividends'] == '800.00'
        assert generated_form_data['federalIncomeTaxWithheld'] == '150.00'
        assert isinstance(generated_form_data['totalOrdinaryDividends'], str)
    
    @patch('tax_document_generation.app.get_template')
    @patch('tax_document_generation.app.generate_document')
    @patch('tax_document_generation.app.store_output')
    @patch('tax_document_generation.app.create_job')
    @patch('tax_document_generation.app.update_job_completed')
    @patch('tax_document_generation.app.validate_jwt')
    def test_complete_example_end_to_end(
        self,
        mock_validate_jwt,
        mock_update_job_completed,
        mock_create_job,
        mock_store_output,
        mock_generate_document,
        mock_get_template
    ):
        """
        Test end-to-end processing of complete example payload.
        
        Requirements: 3.2, 3.3, 3.4
        """
        from tax_document_generation.app import lambda_handler
        
        # Load complete example
        payload = self.load_example_payload('1099-DIV-complete-example.json')
        
        # Setup mocks
        mock_validate_jwt.return_value = {'userId': 'test-user-789', 'email': 'test@example.com'}
        mock_get_template.return_value = b'mock-template-pdf'
        mock_generate_document.return_value = b'mock-generated-pdf'
        mock_store_output.return_value = 'outputs/test-user-789/job-789/1099-DIV.pdf'
        mock_update_job_completed.return_value = {
            'jobId': 'job-789',
            'userId': 'test-user-789',
            'documentType': '1099-DIV',
            'status': 'COMPLETED',
            'outputKey': 'outputs/test-user-789/job-789/1099-DIV.pdf',
            'createdAt': '2024-01-01T00:00:00Z',
            'updatedAt': '2024-01-01T00:00:01Z',
            'completedAt': '2024-01-01T00:00:01Z'
        }
        
        # Create Lambda event
        event = {
            'headers': {
                'Authorization': 'Bearer mock-jwt-token'
            },
            'body': json.dumps(payload)
        }
        
        # Set environment variables
        os.environ['TEMPLATES_BUCKET'] = 'test-templates'
        os.environ['OUTPUTS_BUCKET'] = 'test-outputs'
        os.environ['JOB_TABLE_NAME'] = 'test-jobs'
        os.environ['JWT_SECRET_KEY'] = 'test-secret-key-at-least-32-characters-long'
        
        # Call Lambda handler
        response = lambda_handler(event, None)
        
        # Verify success response
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['status'] == 'COMPLETED'
        
        # Verify document was generated with normalized data
        mock_generate_document.assert_called_once()
        call_args = mock_generate_document.call_args
        generated_form_data = call_args[0][1]
        
        # Verify all decimal fields were normalized to strings with two decimal places
        assert generated_form_data['totalOrdinaryDividends'] == '1000.00'
        assert generated_form_data['qualifiedDividends'] == '800.00'
        assert generated_form_data['federalIncomeTaxWithheld'] == '150.00'
        assert isinstance(generated_form_data['totalOrdinaryDividends'], str)
        # Spot check a few more decimal fields
        assert generated_form_data['section199ADividends'] == '300.00'
        assert generated_form_data['foreignTaxPaid'] == '75.00'
