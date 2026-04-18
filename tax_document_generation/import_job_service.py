"""Import Job Service for managing batch import job records in DynamoDB.

Provides create, update, and query operations for ImportJobs and ImportJobRows
tables with atomic counter updates and status transition validation.
"""

import os
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

import boto3
from botocore.exceptions import ClientError

from logger import log_info, log_error
from exceptions import ValidationError


# Valid status transitions per the state machine
VALID_TRANSITIONS = {
    "PENDING": {"PROCESSING", "FAILED"},
    "PROCESSING": {"COMPLETED", "COMPLETED_WITH_ERRORS", "FAILED"},
}

TERMINAL_STATUSES = {"COMPLETED", "COMPLETED_WITH_ERRORS", "FAILED"}


@dataclass
class ImportJob:
    """Represents a batch import job record."""
    import_job_id: str
    user_id: str
    file_name: str
    document_type: str
    status: str
    total_rows: int
    processed_rows: int = 0
    success_count: int = 0
    failure_count: int = 0
    error_message: str = ""
    created_at: str = ""
    updated_at: str = ""
    completed_at: str = ""


@dataclass
class ImportJobRow:
    """Represents a single row result within an import job."""
    import_job_id: str
    row_number: int
    status: str
    errors: str = ""
    output_key: str = ""


def _get_dynamodb_resource():
    """Get DynamoDB resource, using endpoint URL if available (for LocalStack)."""
    endpoint_url = os.environ.get('AWS_ENDPOINT_URL')
    if endpoint_url:
        return boto3.resource('dynamodb', endpoint_url=endpoint_url)
    return boto3.resource('dynamodb')


def create_import_job(
    table_name: str,
    user_id: str,
    file_name: str,
    document_type: str,
    total_rows: int,
) -> ImportJob:
    """
    Create a new import job record with PENDING status.

    Args:
        table_name: DynamoDB table name for ImportJobs.
        user_id: Authenticated user ID from JWT.
        file_name: Name of the uploaded CSV file.
        document_type: IRS form type (e.g. "1099-DIV").
        total_rows: Number of data rows in the CSV.

    Returns:
        ImportJob with generated importJobId and initial counters.
    """
    dynamodb = _get_dynamodb_resource()
    table = dynamodb.Table(table_name)

    import_job_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    item = {
        'importJobId': import_job_id,
        'userId': user_id,
        'fileName': file_name,
        'documentType': document_type,
        'status': 'PENDING',
        'totalRows': total_rows,
        'processedRows': 0,
        'successCount': 0,
        'failureCount': 0,
        'errorMessage': '',
        'createdAt': now,
        'updatedAt': now,
        'completedAt': '',
    }

    table.put_item(Item=item)

    log_info("Import job created", {
        'importJobId': import_job_id,
        'userId': user_id,
        'totalRows': total_rows,
    })

    return ImportJob(
        import_job_id=import_job_id,
        user_id=user_id,
        file_name=file_name,
        document_type=document_type,
        status='PENDING',
        total_rows=total_rows,
        processed_rows=0,
        success_count=0,
        failure_count=0,
        error_message='',
        created_at=now,
        updated_at=now,
        completed_at='',
    )


def create_import_job_rows(
    table_name: str,
    import_job_id: str,
    total_rows: int,
) -> None:
    """
    Batch-create PENDING row records for all rows in the import job.

    Uses DynamoDB batch_write_item with 25-item batches.

    Args:
        table_name: DynamoDB table name for ImportJobRows.
        import_job_id: Parent import job ID.
        total_rows: Number of rows to create.
    """
    dynamodb = _get_dynamodb_resource()
    table = dynamodb.Table(table_name)

    # DynamoDB batch_write_item supports max 25 items per batch
    batch_size = 25
    for start in range(0, total_rows, batch_size):
        end = min(start + batch_size, total_rows)
        with table.batch_writer() as batch:
            for row_num in range(start, end):
                batch.put_item(Item={
                    'importJobId': import_job_id,
                    'rowNumber': row_num + 1,  # 1-based row numbers
                    'status': 'PENDING',
                    'errors': '',
                    'outputKey': '',
                })

    log_info("Import job rows created", {
        'importJobId': import_job_id,
        'totalRows': total_rows,
    })


def update_import_job_status(
    table_name: str,
    import_job_id: str,
    new_status: str,
    error_message: str = "",
) -> None:
    """
    Transition the import job to a new status.

    Validates the transition against the state machine. Sets completedAt
    for terminal statuses.

    Args:
        table_name: DynamoDB table name.
        import_job_id: Import job ID.
        new_status: Target status.
        error_message: Error message (for FAILED status).

    Raises:
        ValidationError: If transition is invalid.
    """
    dynamodb = _get_dynamodb_resource()
    table = dynamodb.Table(table_name)

    # Get current status
    response = table.get_item(Key={'importJobId': import_job_id})
    item = response.get('Item')
    if not item:
        raise ValidationError(f"Import job {import_job_id} not found")

    current_status = item.get('status', '')
    allowed = VALID_TRANSITIONS.get(current_status, set())
    if new_status not in allowed:
        raise ValidationError(
            f"Invalid status transition from {current_status} to {new_status}"
        )

    now = datetime.now(timezone.utc).isoformat()

    update_expr = 'SET #status = :status, updatedAt = :updated'
    expr_names = {'#status': 'status'}
    expr_values = {
        ':status': new_status,
        ':updated': now,
    }

    if error_message:
        update_expr += ', errorMessage = :error'
        expr_values[':error'] = error_message

    if new_status in TERMINAL_STATUSES:
        update_expr += ', completedAt = :completed'
        expr_values[':completed'] = now

    table.update_item(
        Key={'importJobId': import_job_id},
        UpdateExpression=update_expr,
        ExpressionAttributeNames=expr_names,
        ExpressionAttributeValues=expr_values,
    )

    log_info("Import job status updated", {
        'importJobId': import_job_id,
        'from': current_status,
        'to': new_status,
    })


def increment_row_result(
    job_table_name: str,
    import_job_id: str,
    succeeded: bool,
) -> None:
    """
    Atomically increment processedRows and successCount or failureCount.

    Uses DynamoDB ADD expression for atomic updates.

    Args:
        job_table_name: DynamoDB table name for ImportJobs.
        import_job_id: Import job ID.
        succeeded: True to increment successCount, False for failureCount.
    """
    dynamodb = _get_dynamodb_resource()
    table = dynamodb.Table(job_table_name)

    now = datetime.now(timezone.utc).isoformat()
    counter_field = 'successCount' if succeeded else 'failureCount'

    table.update_item(
        Key={'importJobId': import_job_id},
        UpdateExpression=(
            'SET updatedAt = :updated '
            'ADD processedRows :inc, #counter :inc'
        ),
        ExpressionAttributeNames={'#counter': counter_field},
        ExpressionAttributeValues={
            ':updated': now,
            ':inc': 1,
        },
    )


def update_import_job_row(
    table_name: str,
    import_job_id: str,
    row_number: int,
    status: str,
    output_key: str = "",
    errors: str = "",
) -> None:
    """
    Update a single row record with its processing outcome.

    Args:
        table_name: DynamoDB table name for ImportJobRows.
        import_job_id: Parent import job ID.
        row_number: Row number (sort key).
        status: SUCCEEDED or FAILED.
        output_key: S3 key of generated PDF (for SUCCEEDED).
        errors: Error details (for FAILED).
    """
    dynamodb = _get_dynamodb_resource()
    table = dynamodb.Table(table_name)

    table.update_item(
        Key={
            'importJobId': import_job_id,
            'rowNumber': row_number,
        },
        UpdateExpression='SET #status = :status, outputKey = :output, errors = :errors',
        ExpressionAttributeNames={'#status': 'status'},
        ExpressionAttributeValues={
            ':status': status,
            ':output': output_key,
            ':errors': errors,
        },
    )


def get_import_job(
    table_name: str,
    import_job_id: str,
) -> Optional[Dict[str, Any]]:
    """
    Retrieve a single import job by ID.

    Args:
        table_name: DynamoDB table name.
        import_job_id: Import job ID.

    Returns:
        Import job dict or None if not found.
    """
    dynamodb = _get_dynamodb_resource()
    table = dynamodb.Table(table_name)

    response = table.get_item(Key={'importJobId': import_job_id})
    return response.get('Item')


def get_import_job_rows(
    table_name: str,
    import_job_id: str,
) -> List[Dict[str, Any]]:
    """
    Retrieve all row records for an import job, ordered by rowNumber.

    Uses DynamoDB Query on the partition key with ScanIndexForward=True.

    Args:
        table_name: DynamoDB table name for ImportJobRows.
        import_job_id: Import job ID.

    Returns:
        List of row dicts ordered by rowNumber.
    """
    dynamodb = _get_dynamodb_resource()
    table = dynamodb.Table(table_name)

    response = table.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key('importJobId').eq(import_job_id),
        ScanIndexForward=True,
    )
    return response.get('Items', [])


def determine_terminal_status(
    success_count: int,
    failure_count: int,
    total_rows: int,
) -> str:
    """
    Determine the appropriate terminal status based on row outcomes.

    Args:
        success_count: Number of rows that succeeded.
        failure_count: Number of rows that failed.
        total_rows: Total number of rows.

    Returns:
        "COMPLETED" if all succeeded,
        "FAILED" if all failed,
        "COMPLETED_WITH_ERRORS" otherwise.
    """
    if failure_count == 0:
        return "COMPLETED"
    if success_count == 0:
        return "FAILED"
    return "COMPLETED_WITH_ERRORS"
