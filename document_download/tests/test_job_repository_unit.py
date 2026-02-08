"""
Unit Tests for Job Repository

Tests job retrieval from DynamoDB.
"""

import pytest
from moto import mock_dynamodb
import boto3
from botocore.exceptions import ClientError

from document_download.job_repository import get_job
from document_download.exceptions import JobNotFoundError, DatabaseError


@mock_dynamodb
class TestJobRepository:
    """Test suite for job repository."""
    
    def setup_method(self):
        """Set up test DynamoDB table."""
        self.dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        self.table_name = 'TestJobsTable'
        
        # Create table
        self.table = self.dynamodb.create_table(
            TableName=self.table_name,
            KeySchema=[
                {'AttributeName': 'jobId', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'jobId', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
    
    def test_successful_job_retrieval(self):
        """Test successful job retrieval."""
        # Insert test job
        job_data = {
            'jobId': 'job123',
            'userId': 'user456',
            'documentType': '1099-DIV',
            'status': 'COMPLETED',
            'outputKey': 'outputs/user456/job123/form-1099-DIV.pdf',
            'createdAt': '2024-01-01T00:00:00Z',
            'updatedAt': '2024-01-01T00:05:00Z',
            'completedAt': '2024-01-01T00:05:00Z'
        }
        self.table.put_item(Item=job_data)
        
        # Retrieve job
        result = get_job(self.table_name, 'job123')
        
        assert result['jobId'] == 'job123'
        assert result['userId'] == 'user456'
        assert result['status'] == 'COMPLETED'
        assert result['outputKey'] == 'outputs/user456/job123/form-1099-DIV.pdf'
    
    def test_non_existent_job_raises_job_not_found_error(self):
        """Test that non-existent job raises JobNotFoundError."""
        with pytest.raises(JobNotFoundError) as exc_info:
            get_job(self.table_name, 'nonexistent-job')
        
        assert "not found" in str(exc_info.value).lower()
    
    def test_job_record_structure_validation(self):
        """Test that job record has expected structure."""
        # Insert test job
        job_data = {
            'jobId': 'job789',
            'userId': 'user101',
            'documentType': '1099-INT',
            'status': 'PENDING',
            'createdAt': '2024-01-01T00:00:00Z',
            'updatedAt': '2024-01-01T00:00:00Z'
        }
        self.table.put_item(Item=job_data)
        
        # Retrieve job
        result = get_job(self.table_name, 'job789')
        
        # Verify required fields
        assert 'jobId' in result
        assert 'userId' in result
        assert 'documentType' in result
        assert 'status' in result
        assert 'createdAt' in result
        assert 'updatedAt' in result
    
    def test_completed_job_has_output_key(self):
        """Test that COMPLETED job has outputKey."""
        # Insert completed job
        job_data = {
            'jobId': 'job-completed',
            'userId': 'user202',
            'documentType': '1099-DIV',
            'status': 'COMPLETED',
            'outputKey': 'outputs/user202/job-completed/form-1099-DIV.pdf',
            'createdAt': '2024-01-01T00:00:00Z',
            'updatedAt': '2024-01-01T00:05:00Z',
            'completedAt': '2024-01-01T00:05:00Z'
        }
        self.table.put_item(Item=job_data)
        
        # Retrieve job
        result = get_job(self.table_name, 'job-completed')
        
        assert result['status'] == 'COMPLETED'
        assert 'outputKey' in result
        assert result['outputKey'].endswith('.pdf')
    
    def test_failed_job_has_error_message(self):
        """Test that FAILED job has errorMessage."""
        # Insert failed job
        job_data = {
            'jobId': 'job-failed',
            'userId': 'user303',
            'documentType': '1099-DIV',
            'status': 'FAILED',
            'errorMessage': 'Template not found',
            'createdAt': '2024-01-01T00:00:00Z',
            'updatedAt': '2024-01-01T00:01:00Z'
        }
        self.table.put_item(Item=job_data)
        
        # Retrieve job
        result = get_job(self.table_name, 'job-failed')
        
        assert result['status'] == 'FAILED'
        assert 'errorMessage' in result
        assert result['errorMessage'] == 'Template not found'
