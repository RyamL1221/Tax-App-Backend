"""
Reusable single-record 1099-DIV generation service.

This module encapsulates the core single-record generation pipeline extracted
from the Lambda handler (app.py). Both the manual endpoint and the CSV import
handler delegate to this shared service, guaranteeing identical behavior.

Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7
"""

import uuid
import time
from typing import Dict, Any
from dataclasses import dataclass

from input_validator import validate_form_data
from input_normalizer import normalize_form_data
from template_retriever import get_template
from document_generator import generate_document
from output_persister import store_output
from job_repository import create_job, update_job_completed, update_job_failed
from logger import log_error, log_success, log_info
from exceptions import (
    ValidationError,
    TemplateNotFoundError,
    GenerationError,
    S3Error,
)


@dataclass
class GenerationResult:
    """Result of a single document generation."""
    job_id: str
    status: str            # "COMPLETED" or "FAILED"
    output_key: str = ""   # S3 key, empty on failure
    error_message: str = ""
    error_type: str = ""   # e.g. "ValidationError", "GenerationError"


def generate_single_document(
    user_id: str,
    document_type: str,
    form_data: Dict[str, Any],
    templates_bucket: str,
    outputs_bucket: str,
    job_table_name: str,
) -> GenerationResult:
    """
    Execute the full single-record generation pipeline.

    Steps:
      1. Create PENDING job record
      2. Validate form data
      3. Normalize form data
      4. Retrieve PDF template from S3
      5. Generate PDF document
      6. Store output to S3
      7. Update job record to COMPLETED

    On failure at any step, the job record is updated to FAILED and
    a GenerationResult with error details is returned.

    Args:
        user_id: Authenticated user ID from JWT.
        document_type: IRS form type (e.g. "1099-DIV").
        form_data: Canonical formData dictionary.
        templates_bucket: S3 bucket for PDF templates.
        outputs_bucket: S3 bucket for generated outputs.
        job_table_name: DynamoDB table for job records.

    Returns:
        GenerationResult with job_id, status, output_key or error info.
    """
    start_time = time.time()
    job_id = str(uuid.uuid4())
    template_key = f"templates/irs/{document_type}.pdf"

    try:
        # Step 1: Create PENDING job record
        create_job(job_table_name, job_id, user_id, document_type, template_key)
        log_info(f"Created job {job_id} with PENDING status")

        # Step 2: Validate form data
        validate_form_data(document_type, form_data)
        log_info(f"Validated form data for job {job_id}")

        # Step 3: Normalize form data (flexible input formatting)
        try:
            normalization_result = normalize_form_data(form_data, document_type)
            normalized_form_data = normalization_result.normalized_data

            # Log normalization changes
            if normalization_result.changes:
                log_info(f"Normalized {len(normalization_result.changes)} fields for job {job_id}")
                for field_name, original, normalized in normalization_result.changes:
                    # Mask sensitive data (TINs) in logs
                    if 'tin' in field_name.lower() or 'TIN' in field_name:
                        log_info(f"  {field_name}: ***-**-{original[-4:]} -> ***-**-{normalized[-4:]}")
                    else:
                        log_info(f"  {field_name}: {original} -> {normalized}")
            else:
                log_info(f"No normalization needed for job {job_id}, using payload as-is")
        except ValueError as e:
            # Normalization failed - treat as validation error
            error_msg = f"Input normalization failed: {str(e)}"
            log_error(job_id, e)
            raise ValidationError(error_msg)

        # Step 4: Retrieve template from S3
        template = get_template(templates_bucket, document_type)
        log_info(f"Retrieved template for document type {document_type}")

        # Step 5: Generate document with normalized data
        generated_document = generate_document(template, normalized_form_data, document_type)
        log_info(f"Generated document for job {job_id}")

        # Step 6: Store output to S3
        output_key = store_output(outputs_bucket, user_id, job_id, generated_document, document_type)
        log_info(f"Stored output to {output_key}")

        # Step 7: Update job to COMPLETED
        update_job_completed(job_table_name, job_id, output_key)

        # Log success with duration
        duration_ms = (time.time() - start_time) * 1000
        log_success(job_id, duration_ms, {
            'documentType': document_type,
            'userId': user_id,
        })

        return GenerationResult(
            job_id=job_id,
            status="COMPLETED",
            output_key=output_key,
        )

    except ValidationError as e:
        error_msg = str(e)
        update_job_failed(job_table_name, job_id, error_msg)
        log_error(job_id, e)
        return GenerationResult(
            job_id=job_id,
            status="FAILED",
            error_message=error_msg,
            error_type="ValidationError",
        )

    except TemplateNotFoundError as e:
        error_msg = str(e)
        update_job_failed(job_table_name, job_id, error_msg)
        log_error(job_id, e)
        return GenerationResult(
            job_id=job_id,
            status="FAILED",
            error_message=error_msg,
            error_type="TemplateNotFoundError",
        )

    except GenerationError as e:
        error_msg = "An error occurred during document generation"
        update_job_failed(job_table_name, job_id, str(e))
        log_error(job_id, e)
        return GenerationResult(
            job_id=job_id,
            status="FAILED",
            error_message=error_msg,
            error_type="GenerationError",
        )

    except S3Error as e:
        error_msg = "An error occurred while storing the document"
        update_job_failed(job_table_name, job_id, str(e))
        log_error(job_id, e)
        return GenerationResult(
            job_id=job_id,
            status="FAILED",
            error_message=error_msg,
            error_type="S3Error",
        )

    except Exception as e:
        error_msg = "An unexpected error occurred"
        try:
            update_job_failed(job_table_name, job_id, str(e))
        except Exception:
            pass  # Don't fail if we can't update the job
        log_error(job_id, e)
        return GenerationResult(
            job_id=job_id,
            status="FAILED",
            error_message=error_msg,
            error_type="InternalError",
        )
