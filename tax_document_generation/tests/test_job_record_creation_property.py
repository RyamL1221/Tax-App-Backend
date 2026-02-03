"""
Property Tests: Job Record Creation and Management

Feature: tax-document-generation
Property 11: Initial Job Record Creation
Property 12: Completed Job Record Completeness
Property 13: Failed Job Record State
Property 14: Job Record Required Fields

Tests job repository operations and state transitions.
**Validates: Requirements 5.1, 5.3, 5.4, 5.5**
"""

import pytest
from hypothesis import given, strategies as st, settings
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from tax_document_generation.job_repository import (
    create_job,
    update_job_completed,
    update_job_failed,
    get_job
)


@st.composite
def job_parameters(draw):
    """Generate random job parameters."""
    job_id = draw(st.uuids()).hex
    user_id = draw(st.uuids()).hex
    document_type = draw(st.sampled_from(["1040", "1099", "W2", "1040-EZ"]))
    template_key = f"templates/irs/{document_type}.pdf"
    return job_id, user_id, document_type, template_key


@settings(max_examples=20)
@given(params=job_parameters())
@patch('tax_document_generation.job_repository.boto3')
def test_initial_job_record_creation(mock_boto3, params):
    """
    Property 11: For any generation request, a job record should be created
    with status PENDING before processing begins.
    
    This ensures all jobs are tracked from the start.
    """
    job_id, user_id, document_type, template_key = params
    table_name = "test-table"
    
    # Mock DynamoDB
    mock_table = Mock()
    mock_resource = Mock()
    mock_resource.Table.return_value = mock_table
    mock_boto3.resource.return_value = mock_resource
    
    # Create job
    result = create_job(table_name, job_id, user_id, document_type, template_key)
    
    # Verify job was created with PENDING status
    assert result['jobId'] == job_id
    assert result['userId'] == user_id
    assert result['documentType'] == document_type
    assert result['status'] == 'PENDING'
    assert result['templateKey'] == template_key
    assert 'createdAt' in result
    assert 'updatedAt' in result
    
    # Verify DynamoDB was called
    mock_table.put_item.assert_called_once()
    call_args = mock_table.put_item.call_args[1]
    assert call_args['Item']['status'] == 'PENDING'


@settings(max_examples=20)
@given(params=job_parameters())
@patch('tax_document_generation.job_repository.boto3')
def test_completed_job_record_completeness(mock_boto3, params):
    """
    Property 12: For any successfully completed generation, the job record
    should have status COMPLETED and include outputKey and completedAt timestamp.
    
    This ensures completed jobs have all required information.
    """
    job_id, user_id, document_type, template_key = params
    table_name = "test-table"
    output_key = f"outputs/{user_id}/{job_id}/form-{document_type}.pdf"
    
    # Mock DynamoDB
    mock_table = Mock()
    mock_resource = Mock()
    mock_resource.Table.return_value = mock_table
    mock_boto3.resource.return_value = mock_resource
    
    # Mock the update response
    mock_table.update_item.return_value = {
        'Attributes': {
            'jobId': job_id,
            'userId': user_id,
            'status': 'COMPLETED',
            'outputKey': output_key,
            'completedAt': datetime.utcnow().isoformat() + 'Z',
            'updatedAt': datetime.utcnow().isoformat() + 'Z'
        }
    }
    
    # Update job to completed
    result = update_job_completed(table_name, job_id, output_key)
    
    # Verify completed job has required fields
    assert result['status'] == 'COMPLETED'
    assert result['outputKey'] == output_key
    assert 'completedAt' in result
    assert 'updatedAt' in result
    
    # Verify DynamoDB was called correctly
    mock_table.update_item.assert_called_once()
    call_args = mock_table.update_item.call_args[1]
    assert call_args['Key']['jobId'] == job_id
    assert ':status' in call_args['ExpressionAttributeValues']
    assert call_args['ExpressionAttributeValues'][':status'] == 'COMPLETED'


@settings(max_examples=20)
@given(params=job_parameters())
@patch('tax_document_generation.job_repository.boto3')
def test_failed_job_record_state(mock_boto3, params):
    """
    Property 13: For any failed generation, the job record should have
    status FAILED and include an errorMessage field.
    
    This ensures failures are properly tracked with diagnostic information.
    """
    job_id, user_id, document_type, template_key = params
    table_name = "test-table"
    error_message = "Template not found"
    
    # Mock DynamoDB
    mock_table = Mock()
    mock_resource = Mock()
    mock_resource.Table.return_value = mock_table
    mock_boto3.resource.return_value = mock_resource
    
    # Mock the update response
    mock_table.update_item.return_value = {
        'Attributes': {
            'jobId': job_id,
            'userId': user_id,
            'status': 'FAILED',
            'errorMessage': error_message,
            'updatedAt': datetime.utcnow().isoformat() + 'Z'
        }
    }
    
    # Update job to failed
    result = update_job_failed(table_name, job_id, error_message)
    
    # Verify failed job has required fields
    assert result['status'] == 'FAILED'
    assert result['errorMessage'] == error_message
    assert 'updatedAt' in result
    
    # Verify DynamoDB was called correctly
    mock_table.update_item.assert_called_once()
    call_args = mock_table.update_item.call_args[1]
    assert call_args['Key']['jobId'] == job_id
    assert call_args['ExpressionAttributeValues'][':status'] == 'FAILED'
    assert call_args['ExpressionAttributeValues'][':error'] == error_message


@settings(max_examples=20)
@given(params=job_parameters())
@patch('tax_document_generation.job_repository.boto3')
def test_job_record_required_fields(mock_boto3, params):
    """
    Property 14: For any job record, it should contain at minimum:
    jobId, userId, documentType, status, createdAt, updatedAt, and templateKey.
    
    This ensures all jobs have complete metadata for tracking and auditing.
    """
    job_id, user_id, document_type, template_key = params
    table_name = "test-table"
    
    # Mock DynamoDB
    mock_table = Mock()
    mock_resource = Mock()
    mock_resource.Table.return_value = mock_table
    mock_boto3.resource.return_value = mock_resource
    
    # Create job
    result = create_job(table_name, job_id, user_id, document_type, template_key)
    
    # Verify all required fields are present
    required_fields = ['jobId', 'userId', 'documentType', 'status', 'createdAt', 'updatedAt', 'templateKey']
    for field in required_fields:
        assert field in result, f"Required field '{field}' missing from job record"
    
    # Verify field values are not empty
    for field in required_fields:
        assert result[field], f"Required field '{field}' is empty"


def test_job_creation_unit():
    """
    Unit test: Verify job creation with specific values.
    """
    with patch('tax_document_generation.job_repository.boto3') as mock_boto3:
        mock_table = Mock()
        mock_resource = Mock()
        mock_resource.Table.return_value = mock_table
        mock_boto3.resource.return_value = mock_resource
        
        job_id = "job-123"
        user_id = "user-456"
        document_type = "1040"
        template_key = "templates/irs/1040.pdf"
        
        result = create_job("table", job_id, user_id, document_type, template_key)
        
        assert result['jobId'] == job_id
        assert result['userId'] == user_id
        assert result['status'] == 'PENDING'


def test_job_state_transitions():
    """
    Unit test: Verify job can transition through states.
    """
    with patch('tax_document_generation.job_repository.boto3') as mock_boto3:
        mock_table = Mock()
        mock_resource = Mock()
        mock_resource.Table.return_value = mock_table
        mock_boto3.resource.return_value = mock_resource
        
        job_id = "job-123"
        table_name = "table"
        
        # Mock update responses
        mock_table.update_item.return_value = {
            'Attributes': {
                'jobId': job_id,
                'status': 'COMPLETED',
                'outputKey': 'outputs/user/job/form.pdf',
                'completedAt': datetime.utcnow().isoformat() + 'Z'
            }
        }
        
        # Update to completed
        result = update_job_completed(table_name, job_id, "outputs/user/job/form.pdf")
        assert result['status'] == 'COMPLETED'
        assert 'outputKey' in result
