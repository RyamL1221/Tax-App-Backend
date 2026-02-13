"""
Unit Tests for Response Formatter

Tests response formatting for API Gateway.
"""

import pytest
import json
import os
import base64

from document_download.response_formatter import pdf_response, error_response


def get_expected_cors_origin():
    """Get the expected CORS origin from environment or default."""
    return os.environ.get('CORS_ALLOWED_ORIGIN', '*')


class TestResponseFormatter:
    """Test suite for response formatter."""
    
    def test_pdf_response_has_correct_headers(self):
        """Test that PDF response has correct headers."""
        pdf_bytes = b'%PDF-1.4 fake pdf'
        filename = 'form-1099-DIV.pdf'
        
        response = pdf_response(pdf_bytes, filename)
        
        assert response['headers']['Content-Type'] == 'application/pdf'
        assert 'attachment' in response['headers']['Content-Disposition']
        assert filename in response['headers']['Content-Disposition']
        assert response['headers']['Access-Control-Allow-Origin'] == get_expected_cors_origin()
        assert 'Authorization' in response['headers']['Access-Control-Allow-Headers']
        assert 'GET' in response['headers']['Access-Control-Allow-Methods']
    
    def test_pdf_response_is_base64_encoded(self):
        """Test that PDF response is base64 encoded."""
        pdf_bytes = b'%PDF-1.4 fake pdf content'
        filename = 'test.pdf'
        
        response = pdf_response(pdf_bytes, filename)
        
        assert response['isBase64Encoded'] is True
        assert isinstance(response['body'], str)
        
        # Verify can decode back to original
        decoded = base64.b64decode(response['body'])
        assert decoded == pdf_bytes
    
    def test_pdf_response_status_code(self):
        """Test that PDF response has 200 status code."""
        pdf_bytes = b'test content'
        filename = 'test.pdf'
        
        response = pdf_response(pdf_bytes, filename)
        
        assert response['statusCode'] == 200
    
    def test_error_response_has_correct_structure(self):
        """Test that error response has correct structure."""
        response = error_response(404, 'NotFoundError', 'Document not found')
        
        assert response['statusCode'] == 404
        assert response['headers']['Content-Type'] == 'application/json'
        
        body = json.loads(response['body'])
        assert body['error'] == 'NotFoundError'
        assert body['message'] == 'Document not found'
    
    def test_error_response_cors_headers(self):
        """Test that error response includes CORS headers."""
        response = error_response(500, 'InternalError', 'Server error')
        
        assert response['headers']['Access-Control-Allow-Origin'] == get_expected_cors_origin()
        assert 'Authorization' in response['headers']['Access-Control-Allow-Headers']
        assert 'GET' in response['headers']['Access-Control-Allow-Methods']
    
    def test_cors_headers_present_in_all_responses(self):
        """Test that CORS headers are present in all response types."""
        # PDF response
        pdf_resp = pdf_response(b'test', 'test.pdf')
        assert 'Access-Control-Allow-Origin' in pdf_resp['headers']
        assert 'Access-Control-Allow-Headers' in pdf_resp['headers']
        assert 'Access-Control-Allow-Methods' in pdf_resp['headers']
        
        # Error response
        error_resp = error_response(400, 'BadRequest', 'Bad request')
        assert 'Access-Control-Allow-Origin' in error_resp['headers']
        assert 'Access-Control-Allow-Headers' in error_resp['headers']
        assert 'Access-Control-Allow-Methods' in error_resp['headers']
    
    def test_error_response_various_status_codes(self):
        """Test error responses with various status codes."""
        test_cases = [
            (400, 'BadRequest', 'Bad request'),
            (401, 'AuthenticationError', 'Unauthorized'),
            (403, 'AuthorizationError', 'Forbidden'),
            (404, 'NotFoundError', 'Not found'),
            (500, 'InternalError', 'Internal error')
        ]
        
        for status_code, error_type, message in test_cases:
            response = error_response(status_code, error_type, message)
            
            assert response['statusCode'] == status_code
            body = json.loads(response['body'])
            assert body['error'] == error_type
            assert body['message'] == message
    
    def test_pdf_response_with_special_characters_in_filename(self):
        """Test PDF response with special characters in filename."""
        pdf_bytes = b'test'
        filename = 'form-1099-DIV (Copy A).pdf'
        
        response = pdf_response(pdf_bytes, filename)
        
        assert filename in response['headers']['Content-Disposition']
    
    def test_empty_pdf_response(self):
        """Test PDF response with empty content."""
        pdf_bytes = b''
        filename = 'empty.pdf'
        
        response = pdf_response(pdf_bytes, filename)
        
        assert response['statusCode'] == 200
        assert response['isBase64Encoded'] is True
        decoded = base64.b64decode(response['body'])
        assert decoded == b''
