"""
Integration Tests for Lambda Handler

Tests the complete document download workflow end-to-end.
"""

import pytest
import json
import base64
import jwt
import os
from datetime import datetime, timedelta
from moto import mock_dynamodb, mock_s3
import boto3

from document_download.app import lambda_handler


@mock_dynamodb
@mock_s3
class TestLambdaHandlerIntegration:
    """Integration tests for Lambda handler."""
    
    def setup_method(self):
        """Set up test environment."""
        # Set environment variables
        os.environ['JWT_SECRET_KEY'] = 'test-secret-key-at-least-32-characters-long'
        os.environ['JOB_TABLE_NAME'] = 'TestJobsTable'
        os.environ['OUTPUTS_BUCKET'] = 'test-outputs-bucket'
        
        # Create DynamoDB table
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        self.table = dynamodb.create_table(
            TableName='TestJobsTable',
            KeySchema=[{'AttributeName': 'jobId', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'jobId', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Create S3 bucket
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='test-outputs-bucket')
        self.s3 = s3
    
    def create_jwt_token(self, user_id: str, email: str) -> str:
        """Create a valid JWT token."""
        secret = os.environ['JWT_SECRET_KEY']
        payload = {
            'userId': user_id,
            'email': email,
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(hours=1)
        }
        return jwt.encode(payload, secret, algorithm='HS256')
    
    def test_successful_download_with_valid_token_and_authorization(self):
        """Test successful download with valid token and authorization."""
        # Create job
        job_id = 'job123'
        user_id = 'user456'
        output_key = f'outputs/{user_id}/{job_id}/form-1099-DIV.pdf'
        
        self.table.put_item(Item={
            'jobId': job_id,
            'userId': user_id,
            'documentType': '1099-DIV',
            'status': 'COMPLETED',
            'outputKey': output_key,
            'createdAt': '2024-01-01T00:00:00Z',
            'updatedAt': '2024-01-01T00:05:00Z',
            'completedAt': '2024-01-01T00:05:00Z'
        })
        
        # Upload PDF to S3
        pdf_content = b'%PDF-1.4 fake pdf content'
        self.s3.put_object(Bucket='test-outputs-bucket', Key=output_key, Body=pdf_content)
        
        # Create event
        token = self.create_jwt_token(user_id, 'test@example.com')
        event = {
            'pathParameters': {'jobId': job_id},
            'headers': {'Authorization': f'Bearer {token}'}
        }
        
        # Call handler
        response = lambda_handler(event, None)
        
        # Verify response
        assert response['statusCode'] == 200
        assert response['headers']['Content-Type'] == 'application/pdf'
        assert 'form-1099-DIV.pdf' in response['headers']['Content-Disposition']
        assert response['isBase64Encoded'] is True
        
        # Verify content
        decoded = base64.b64decode(response['body'])
        assert decoded == pdf_content
    
    def test_401_for_missing_authorization_header(self):
        """Test 401 for missing Authorization header."""
        event = {
            'pathParameters': {'jobId': 'job123'},
            'headers': {}
        }
        
        response = lambda_handler(event, None)
        
        assert response['statusCode'] == 401
        body = json.loads(response['body'])
        assert body['error'] == 'AuthenticationError'
    
    def test_401_for_invalid_jwt_token(self):
        """Test 401 for invalid JWT token."""
        event = {
            'pathParameters': {'jobId': 'job123'},
            'headers': {'Authorization': 'Bearer invalid.token.here'}
        }
        
        response = lambda_handler(event, None)
        
        assert response['statusCode'] == 401
        body = json.loads(response['body'])
        assert body['error'] == 'AuthenticationError'
    
    def test_403_for_mismatched_user_id(self):
        """Test 403 for mismatched userId."""
        # Create job for user1
        job_id = 'job789'
        user1_id = 'user1'
        user2_id = 'user2'
        
        self.table.put_item(Item={
            'jobId': job_id,
            'userId': user1_id,
            'documentType': '1099-DIV',
            'status': 'COMPLETED',
            'outputKey': f'outputs/{user1_id}/{job_id}/form-1099-DIV.pdf',
            'createdAt': '2024-01-01T00:00:00Z'
        })
        
        # Try to access with user2's token
        token = self.create_jwt_token(user2_id, 'user2@example.com')
        event = {
            'pathParameters': {'jobId': job_id},
            'headers': {'Authorization': f'Bearer {token}'}
        }
        
        response = lambda_handler(event, None)
        
        assert response['statusCode'] == 403
        body = json.loads(response['body'])
        assert body['error'] == 'AuthorizationError'
    
    def test_404_for_non_existent_job(self):
        """Test 404 for non-existent job."""
        token = self.create_jwt_token('user123', 'test@example.com')
        event = {
            'pathParameters': {'jobId': 'nonexistent-job'},
            'headers': {'Authorization': f'Bearer {token}'}
        }
        
        response = lambda_handler(event, None)
        
        assert response['statusCode'] == 404
        body = json.loads(response['body'])
        assert body['error'] == 'NotFoundError'
    
    def test_404_for_non_existent_document(self):
        """Test 404 for non-existent document."""
        # Create job but don't upload document
        job_id = 'job-no-doc'
        user_id = 'user999'
        output_key = f'outputs/{user_id}/{job_id}/form-1099-DIV.pdf'
        
        self.table.put_item(Item={
            'jobId': job_id,
            'userId': user_id,
            'documentType': '1099-DIV',
            'status': 'COMPLETED',
            'outputKey': output_key,
            'createdAt': '2024-01-01T00:00:00Z'
        })
        
        token = self.create_jwt_token(user_id, 'test@example.com')
        event = {
            'pathParameters': {'jobId': job_id},
            'headers': {'Authorization': f'Bearer {token}'}
        }
        
        response = lambda_handler(event, None)
        
        assert response['statusCode'] == 404
        body = json.loads(response['body'])
        assert body['error'] == 'NotFoundError'
    
    def test_400_for_failed_job_status(self):
        """Test 400 for FAILED job status."""
        job_id = 'job-failed'
        user_id = 'user888'
        
        self.table.put_item(Item={
            'jobId': job_id,
            'userId': user_id,
            'documentType': '1099-DIV',
            'status': 'FAILED',
            'errorMessage': 'Template not found',
            'createdAt': '2024-01-01T00:00:00Z'
        })
        
        token = self.create_jwt_token(user_id, 'test@example.com')
        event = {
            'pathParameters': {'jobId': job_id},
            'headers': {'Authorization': f'Bearer {token}'}
        }
        
        response = lambda_handler(event, None)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['error'] == 'DocumentGenerationFailed'
    
    def test_correct_filename_in_content_disposition_header(self):
        """Test correct filename in Content-Disposition header."""
        job_id = 'job-filename'
        user_id = 'user-filename'
        document_type = '1099-INT'
        output_key = f'outputs/{user_id}/{job_id}/form-{document_type}.pdf'
        
        self.table.put_item(Item={
            'jobId': job_id,
            'userId': user_id,
            'documentType': document_type,
            'status': 'COMPLETED',
            'outputKey': output_key,
            'createdAt': '2024-01-01T00:00:00Z'
        })
        
        self.s3.put_object(Bucket='test-outputs-bucket', Key=output_key, Body=b'test pdf')
        
        token = self.create_jwt_token(user_id, 'test@example.com')
        event = {
            'pathParameters': {'jobId': job_id},
            'headers': {'Authorization': f'Bearer {token}'}
        }
        
        response = lambda_handler(event, None)
        
        assert response['statusCode'] == 200
        disposition = response['headers']['Content-Disposition']
        assert f'form-{document_type}.pdf' in disposition
    
    def test_404_for_pending_job(self):
        """Test 404 for PENDING job (document not ready)."""
        job_id = 'job-pending'
        user_id = 'user-pending'
        
        self.table.put_item(Item={
            'jobId': job_id,
            'userId': user_id,
            'documentType': '1099-DIV',
            'status': 'PENDING',
            'createdAt': '2024-01-01T00:00:00Z'
        })
        
        token = self.create_jwt_token(user_id, 'test@example.com')
        event = {
            'pathParameters': {'jobId': job_id},
            'headers': {'Authorization': f'Bearer {token}'}
        }
        
        response = lambda_handler(event, None)
        
        assert response['statusCode'] == 404
        body = json.loads(response['body'])
        assert body['error'] == 'NotFoundError'
