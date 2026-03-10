"""
Integration tests for input normalizer with Lambda handler.

Tests the complete flow: validation → normalization → field mapping → PDF generation.

Requirements: 7.1, 7.2, 7.3, 7.4
"""

import json
import os
import pytest
from unittest.mock import patch, MagicMock
from tax_document_generation.app import lambda_handler


class TestNormalizerIntegration:
    """Test normalizer integration with Lambda handler."""
    
    @patch('tax_document_generation.app.validate_jwt')
    @patch('tax_document_generation.app.create_job')
    @patch('tax_document_generation.app.update_job_completed')
    @patch('tax_document_generation.app.get_template')
    @patch('tax_document_generation.app.generate_document')
    @patch('tax_document_generation.app.store_output')
    def test_normalizes_decimal_fields_in_complete_flow(
        self,
        mock_store,
        mock_generate,
        mock_template,
        mock_update_job,
        mock_create_job,
        mock_validate_jwt
    ):
        """Test that decimal fields are normalized in complete Lambda flow."""
        # Setup mocks
        mock_validate_jwt.return_value = {'userId': 'user123', 'email': 'test@example.com'}
        mock_create_job.return_value = None
        mock_template.return_value = b"mock_template"
        mock_generate.return_value = b"mock_pdf"
        mock_store.return_value = "outputs/user123/job456/1099-DIV.pdf"
        # Mock complete DynamoDB response with all fields
        mock_update_job.return_value = {
            'jobId': 'job456',
            'userId': 'user123',
            'documentType': '1099-DIV',
            'status': 'COMPLETED',
            'outputKey': 'outputs/user123/job456/1099-DIV.pdf',
            'createdAt': '2024-01-01T00:00:00Z',
            'updatedAt': '2024-01-01T00:00:01Z',
            'completedAt': '2024-01-01T00:00:01Z'
        }
        
        # Setup environment
        os.environ['TEMPLATES_BUCKET'] = 'test-templates'
        os.environ['OUTPUTS_BUCKET'] = 'test-outputs'
        os.environ['JOB_TABLE_NAME'] = 'test-jobs'
        os.environ['JWT_SECRET_KEY'] = 'test-secret-key-at-least-32-characters-long'
        
        # Create event with unnormalized decimal values
        event = {
            'headers': {
                'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiJ1c2VyMTIzIiwiZW1haWwiOiJ0ZXN0QGV4YW1wbGUuY29tIiwiaWF0IjoxNzAwMDAwMDAwLCJleHAiOjk5OTk5OTk5OTl9.Xqj8VZ8qZ8qZ8qZ8qZ8qZ8qZ8qZ8qZ8qZ8qZ8qZ8qZ8'
            },
            'body': json.dumps({
                'documentType': '1099-DIV',
                'formData': {
                    'calendarYear': '2024',
                    'payerName': 'Example Corp',
                    'payerTIN': '12-3456789',
                    'recipientName': 'John Doe',
                    'recipientTIN': '987-65-4321',
                    'totalOrdinaryDividends': '1000',  # Should be normalized to 1000.00
                    'qualifiedDividends': 500  # Should be normalized to 500.00
                }
            })
        }
        
        # Call Lambda handler
        response = lambda_handler(event, None)
        
        # Verify response
        assert response['statusCode'] == 200
        
        # Verify generate_document was called with normalized data
        mock_generate.assert_called_once()
        call_args = mock_generate.call_args
        normalized_data = call_args[0][1]  # Second argument is form_data
        
        # Check that decimal fields were normalized
        assert normalized_data['totalOrdinaryDividends'] == '1000.00'
        assert normalized_data['qualifiedDividends'] == '500.00'
        
        # Check that other fields remain unchanged
        assert normalized_data['payerName'] == 'Example Corp'
        assert normalized_data['recipientName'] == 'John Doe'
    
    @patch('tax_document_generation.app.validate_jwt')
    @patch('tax_document_generation.app.create_job')
    @patch('tax_document_generation.app.update_job_completed')
    @patch('tax_document_generation.app.get_template')
    @patch('tax_document_generation.app.generate_document')
    @patch('tax_document_generation.app.store_output')
    def test_normalizes_tin_fields_in_complete_flow(
        self,
        mock_store,
        mock_generate,
        mock_template,
        mock_update_job,
        mock_create_job,
        mock_validate_jwt
    ):
        """Test that TIN fields are normalized in complete Lambda flow."""
        # Setup mocks
        mock_validate_jwt.return_value = {'userId': 'user123', 'email': 'test@example.com'}
        mock_create_job.return_value = None
        mock_template.return_value = b"mock_template"
        mock_generate.return_value = b"mock_pdf"
        mock_store.return_value = "outputs/user123/job456/1099-DIV.pdf"
        # Mock complete DynamoDB response with all fields
        mock_update_job.return_value = {
            'jobId': 'job456',
            'userId': 'user123',
            'documentType': '1099-DIV',
            'status': 'COMPLETED',
            'outputKey': 'outputs/user123/job456/1099-DIV.pdf',
            'createdAt': '2024-01-01T00:00:00Z',
            'updatedAt': '2024-01-01T00:00:01Z',
            'completedAt': '2024-01-01T00:00:01Z'
        }
        
        # Setup environment
        os.environ['TEMPLATES_BUCKET'] = 'test-templates'
        os.environ['OUTPUTS_BUCKET'] = 'test-outputs'
        os.environ['JOB_TABLE_NAME'] = 'test-jobs'
        os.environ['JWT_SECRET_KEY'] = 'test-secret-key-at-least-32-characters-long'
        
        # Create event with unnormalized TIN values
        event = {
            'headers': {
                'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiJ1c2VyMTIzIiwiZW1haWwiOiJ0ZXN0QGV4YW1wbGUuY29tIiwiaWF0IjoxNzAwMDAwMDAwLCJleHAiOjk5OTk5OTk5OTl9.Xqj8VZ8qZ8qZ8qZ8qZ8qZ8qZ8qZ8qZ8qZ8qZ8qZ8qZ8'
            },
            'body': json.dumps({
                'documentType': '1099-DIV',
                'formData': {
                    'calendarYear': '2024',
                    'payerName': 'Example Corp',
                    'payerTIN': '123456789',  # Should be normalized to 12-3456789
                    'recipientName': 'John Doe',
                    'recipientTIN': '987654321',  # Should be normalized to 987-65-4321
                    'totalOrdinaryDividends': '1000.00'
                }
            })
        }
        
        # Call Lambda handler
        response = lambda_handler(event, None)
        
        # Verify response
        assert response['statusCode'] == 200
        
        # Verify generate_document was called with normalized data
        mock_generate.assert_called_once()
        call_args = mock_generate.call_args
        normalized_data = call_args[0][1]  # Second argument is form_data
        
        # Check that TIN fields were normalized
        assert normalized_data['payerTIN'] == '12-3456789'
        assert normalized_data['recipientTIN'] == '987-65-4321'
        
        # Check that other fields remain unchanged
        assert normalized_data['totalOrdinaryDividends'] == '1000.00'
    
    @patch('tax_document_generation.app.validate_jwt')
    @patch('tax_document_generation.app.create_job')
    @patch('tax_document_generation.app.update_job_completed')
    @patch('tax_document_generation.app.get_template')
    @patch('tax_document_generation.app.generate_document')
    @patch('tax_document_generation.app.store_output')
    def test_preformatted_payload_requires_no_normalization(
        self,
        mock_store,
        mock_generate,
        mock_template,
        mock_update_job,
        mock_create_job,
        mock_validate_jwt
    ):
        """Test that pre-formatted payloads pass through unchanged."""
        # Setup mocks
        mock_validate_jwt.return_value = {'userId': 'user123', 'email': 'test@example.com'}
        mock_create_job.return_value = None
        mock_template.return_value = b"mock_template"
        mock_generate.return_value = b"mock_pdf"
        mock_store.return_value = "outputs/user123/job456/1099-DIV.pdf"
        # Mock complete DynamoDB response with all fields
        mock_update_job.return_value = {
            'jobId': 'job456',
            'userId': 'user123',
            'documentType': '1099-DIV',
            'status': 'COMPLETED',
            'outputKey': 'outputs/user123/job456/1099-DIV.pdf',
            'createdAt': '2024-01-01T00:00:00Z',
            'updatedAt': '2024-01-01T00:00:01Z',
            'completedAt': '2024-01-01T00:00:01Z'
        }
        
        # Setup environment
        os.environ['TEMPLATES_BUCKET'] = 'test-templates'
        os.environ['OUTPUTS_BUCKET'] = 'test-outputs'
        os.environ['JOB_TABLE_NAME'] = 'test-jobs'
        os.environ['JWT_SECRET_KEY'] = 'test-secret-key-at-least-32-characters-long'
        
        # Create event with pre-formatted values
        original_form_data = {
            'calendarYear': '2024',
            'payerName': 'Example Corp',
            'payerTIN': '12-3456789',  # Already formatted
            'recipientName': 'John Doe',
            'recipientTIN': '987-65-4321',  # Already formatted
            'totalOrdinaryDividends': '1000.00',  # Already formatted
            'qualifiedDividends': '500.00'  # Already formatted
        }
        
        event = {
            'headers': {
                'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiJ1c2VyMTIzIiwiZW1haWwiOiJ0ZXN0QGV4YW1wbGUuY29tIiwiaWF0IjoxNzAwMDAwMDAwLCJleHAiOjk5OTk5OTk5OTl9.Xqj8VZ8qZ8qZ8qZ8qZ8qZ8qZ8qZ8qZ8qZ8qZ8qZ8qZ8'
            },
            'body': json.dumps({
                'documentType': '1099-DIV',
                'formData': original_form_data
            })
        }
        
        # Call Lambda handler
        response = lambda_handler(event, None)
        
        # Verify response
        assert response['statusCode'] == 200
        
        # Verify generate_document was called with unchanged data
        mock_generate.assert_called_once()
        call_args = mock_generate.call_args
        normalized_data = call_args[0][1]  # Second argument is form_data
        
        # All fields should be unchanged
        assert normalized_data == original_form_data
    
    @patch('tax_document_generation.app.validate_jwt')
    @patch('tax_document_generation.app.create_job')
    @patch('tax_document_generation.app.update_job_completed')
    @patch('tax_document_generation.app.get_template')
    @patch('tax_document_generation.app.generate_document')
    @patch('tax_document_generation.app.store_output')
    @patch('tax_document_generation.app.log_info')
    def test_normalization_changes_are_logged(
        self,
        mock_log_info,
        mock_store,
        mock_generate,
        mock_template,
        mock_update_job,
        mock_create_job,
        mock_validate_jwt
    ):
        """Test that normalization changes are logged."""
        # Setup mocks
        mock_validate_jwt.return_value = {'userId': 'user123', 'email': 'test@example.com'}
        mock_create_job.return_value = None
        mock_template.return_value = b"mock_template"
        mock_generate.return_value = b"mock_pdf"
        mock_store.return_value = "outputs/user123/job456/1099-DIV.pdf"
        # Mock complete DynamoDB response with all fields
        mock_update_job.return_value = {
            'jobId': 'job456',
            'userId': 'user123',
            'documentType': '1099-DIV',
            'status': 'COMPLETED',
            'outputKey': 'outputs/user123/job456/1099-DIV.pdf',
            'createdAt': '2024-01-01T00:00:00Z',
            'updatedAt': '2024-01-01T00:00:01Z',
            'completedAt': '2024-01-01T00:00:01Z'
        }
        
        # Setup environment
        os.environ['TEMPLATES_BUCKET'] = 'test-templates'
        os.environ['OUTPUTS_BUCKET'] = 'test-outputs'
        os.environ['JOB_TABLE_NAME'] = 'test-jobs'
        os.environ['JWT_SECRET_KEY'] = 'test-secret-key-at-least-32-characters-long'
        
        # Create event with unnormalized values
        event = {
            'headers': {
                'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiJ1c2VyMTIzIiwiZW1haWwiOiJ0ZXN0QGV4YW1wbGUuY29tIiwiaWF0IjoxNzAwMDAwMDAwLCJleHAiOjk5OTk5OTk5OTl9.Xqj8VZ8qZ8qZ8qZ8qZ8qZ8qZ8qZ8qZ8qZ8qZ8qZ8qZ8'
            },
            'body': json.dumps({
                'documentType': '1099-DIV',
                'formData': {
                    'calendarYear': '2024',
                    'payerName': 'Example Corp',
                    'payerTIN': '123456789',
                    'recipientName': 'John Doe',
                    'recipientTIN': '987654321',
                    'totalOrdinaryDividends': '1000'
                }
            })
        }
        
        # Call Lambda handler
        response = lambda_handler(event, None)
        
        # Verify response
        assert response['statusCode'] == 200
        
        # Verify normalization was logged
        log_calls = [str(call) for call in mock_log_info.call_args_list]
        log_messages = ' '.join(log_calls)
        
        # Should log count of normalized fields
        assert 'Normalized 3 fields' in log_messages
        
        # Should log individual field changes (with TIN masking)
        assert 'payerTIN' in log_messages
        assert 'recipientTIN' in log_messages
        assert 'totalOrdinaryDividends' in log_messages
    
    @patch('tax_document_generation.app.validate_jwt')
    @patch('tax_document_generation.app.create_job')
    @patch('tax_document_generation.app.update_job_completed')
    @patch('tax_document_generation.app.get_template')
    @patch('tax_document_generation.app.generate_document')
    @patch('tax_document_generation.app.store_output')
    @patch('tax_document_generation.app.log_info')
    def test_no_normalization_logged_for_preformatted_data(
        self,
        mock_log_info,
        mock_store,
        mock_generate,
        mock_template,
        mock_update_job,
        mock_create_job,
        mock_validate_jwt
    ):
        """Test that 'no normalization needed' is logged for pre-formatted data."""
        # Setup mocks
        mock_validate_jwt.return_value = {'userId': 'user123', 'email': 'test@example.com'}
        mock_create_job.return_value = None
        mock_template.return_value = b"mock_template"
        mock_generate.return_value = b"mock_pdf"
        mock_store.return_value = "outputs/user123/job456/1099-DIV.pdf"
        # Mock complete DynamoDB response with all fields
        mock_update_job.return_value = {
            'jobId': 'job456',
            'userId': 'user123',
            'documentType': '1099-DIV',
            'status': 'COMPLETED',
            'outputKey': 'outputs/user123/job456/1099-DIV.pdf',
            'createdAt': '2024-01-01T00:00:00Z',
            'updatedAt': '2024-01-01T00:00:01Z',
            'completedAt': '2024-01-01T00:00:01Z'
        }
        
        # Setup environment
        os.environ['TEMPLATES_BUCKET'] = 'test-templates'
        os.environ['OUTPUTS_BUCKET'] = 'test-outputs'
        os.environ['JOB_TABLE_NAME'] = 'test-jobs'
        os.environ['JWT_SECRET_KEY'] = 'test-secret-key-at-least-32-characters-long'
        
        # Create event with pre-formatted values
        event = {
            'headers': {
                'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiJ1c2VyMTIzIiwiZW1haWwiOiJ0ZXN0QGV4YW1wbGUuY29tIiwiaWF0IjoxNzAwMDAwMDAwLCJleHAiOjk5OTk5OTk5OTl9.Xqj8VZ8qZ8qZ8qZ8qZ8qZ8qZ8qZ8qZ8qZ8qZ8qZ8qZ8'
            },
            'body': json.dumps({
                'documentType': '1099-DIV',
                'formData': {
                    'calendarYear': '2024',
                    'payerName': 'Example Corp',
                    'payerTIN': '12-3456789',
                    'recipientName': 'John Doe',
                    'recipientTIN': '987-65-4321',
                    'totalOrdinaryDividends': '1000.00'
                }
            })
        }
        
        # Call Lambda handler
        response = lambda_handler(event, None)
        
        # Verify response
        assert response['statusCode'] == 200
        
        # Verify "no normalization needed" was logged
        log_calls = [str(call) for call in mock_log_info.call_args_list]
        log_messages = ' '.join(log_calls)
        
        assert 'No normalization needed' in log_messages or 'using payload as-is' in log_messages
