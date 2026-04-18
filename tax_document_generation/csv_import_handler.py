"""Lambda handler for CSV import of 1099-DIV records.

Accepts CSV files via either multipart/form-data file upload or a
base64-encoded CSV inside a JSON body. Detects the incoming content type,
extracts the CSV content and file name from either format, then delegates
to the shared parsing/mapping/orchestration pipeline.

Creates and updates Import Job tracking records in DynamoDB throughout
processing. For large imports (row count exceeding SYNC_ROW_THRESHOLD),
delegates processing to AsyncImportProcessorFunction via asynchronous
Lambda invocation and returns HTTP 202 immediately.

Requirements: 1.1, 1.6, 1.7, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8,
              3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 4.1, 4.2, 4.3, 4.4, 4.5,
              6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 7.1, 7.2, 10.1, 10.2, 10.3, 10.4
"""

import os
import sys
import json
import base64
from typing import Dict

import boto3

sys.path.insert(0, os.path.dirname(__file__))

from jwt_validator import validate_jwt
from csv_parser import parse_csv
from row_mapper import map_row_to_form_data
from import_orchestrator import process_import, RowResult, ImportSummary
from import_job_service import (
    create_import_job,
    create_import_job_rows,
    update_import_job_status,
    update_import_job_row,
    increment_row_result,
    determine_terminal_status,
)
from multipart_parser import parse_multipart_body, MultipartResult
from response_formatter import error_response, get_cors_headers
from logger import log_info, log_error
from exceptions import AuthenticationError, ValidationError

MAX_CSV_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB


def lambda_handler(event: Dict, context) -> Dict:
    """
    Handle CSV import requests for 1099-DIV batch generation.

    Flow:
      1. Handle OPTIONS preflight.
      2. Validate JWT from Authorization header.
      3. Extract and decode base64 csvFile from request body.
      4. Enforce 5 MB size limit on decoded content.
      5. Parse CSV (header validation, blank row filtering).
      6. Map each row to formData via row_mapper.
      7. Delegate mapped rows to import_orchestrator.
      8. Return ImportSummary as HTTP 200 JSON response.

    Args:
        event: API Gateway proxy event.
        context: Lambda context.

    Returns:
        API Gateway proxy response.
    """
    # Handle OPTIONS preflight
    http_method = event.get("httpMethod", "")
    if http_method == "OPTIONS":
        cors_origin = os.environ.get("CORS_ALLOWED_ORIGIN", "*")
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": cors_origin,
                "Access-Control-Allow-Headers": "Content-Type,Authorization",
                "Access-Control-Allow-Methods": "POST,OPTIONS",
            },
            "body": "",
        }

    try:
        # Environment variables
        templates_bucket = os.environ.get("TEMPLATES_BUCKET")
        outputs_bucket = os.environ.get("OUTPUTS_BUCKET")
        job_table_name = os.environ.get("JOB_TABLE_NAME")
        jwt_secret = os.environ.get("JWT_SECRET_KEY")
        import_jobs_table = os.environ.get("IMPORT_JOBS_TABLE_NAME")
        import_job_rows_table = os.environ.get("IMPORT_JOB_ROWS_TABLE_NAME")
        sync_row_threshold = int(os.environ.get("SYNC_ROW_THRESHOLD", "10"))

        if not all([templates_bucket, outputs_bucket, job_table_name, jwt_secret]):
            raise Exception("Missing required environment variables")

        # Validate JWT
        auth_header = event.get("headers", {}).get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            raise AuthenticationError("Missing or invalid Authorization header")

        token = auth_header.replace("Bearer ", "")
        jwt_payload = validate_jwt(token, jwt_secret)
        user_id = jwt_payload.get("userId")

        if not user_id:
            raise AuthenticationError("JWT token missing userId claim")

        log_info(f"CSV import request from user {user_id}")

        # --- Base64 body decoding (API Gateway binary media types) ---
        raw_body = event.get("body", "")
        is_base64 = event.get("isBase64Encoded", False)

        if is_base64:
            try:
                raw_body = base64.b64decode(raw_body)
            except Exception:
                raise ValidationError("Invalid request encoding")
        elif isinstance(raw_body, str):
            raw_body = raw_body.encode("utf-8")

        # --- Content-Type detection (case-insensitive header lookup) ---
        headers = event.get("headers", {}) or {}
        content_type = ""
        for key, value in headers.items():
            if key.lower() == "content-type":
                content_type = value
                break

        # --- Route based on content type ---
        if content_type.lower().startswith("multipart/form-data"):
            # Multipart path
            result = parse_multipart_body(raw_body, content_type)
            try:
                csv_content = result.file_content.decode("utf-8")
            except UnicodeDecodeError:
                raise ValidationError("Invalid file encoding: file must be UTF-8")
            file_name = result.file_name
        else:
            # Existing JSON/base64 path (unchanged)
            if isinstance(raw_body, bytes):
                body = json.loads(raw_body.decode("utf-8"))
            else:
                body = json.loads(raw_body)

            csv_file_b64 = body.get("csvFile")
            if not csv_file_b64:
                raise ValidationError("Missing required field: csvFile")

            file_name = body.get("fileName", "import.csv")

            try:
                csv_bytes = base64.b64decode(csv_file_b64)
            except Exception:
                raise ValidationError("Invalid base64 encoding in csvFile")

            csv_content = csv_bytes.decode("utf-8")

        # Enforce size limit (same for both paths)
        if len(csv_content.encode("utf-8")) > MAX_CSV_SIZE_BYTES:
            raise ValidationError("CSV file exceeds maximum size of 5 MB")

        # Parse CSV (validates headers, filters blank rows)
        parsed_rows = parse_csv(csv_content)
        total_rows = len(parsed_rows)

        # Create ImportJob and ImportJobRow records before processing
        import_job = None
        if import_jobs_table and import_job_rows_table:
            import_job = create_import_job(
                import_jobs_table, user_id, file_name, "1099-DIV", total_rows
            )
            create_import_job_rows(
                import_job_rows_table, import_job.import_job_id, total_rows
            )
            log_info(f"Import job {import_job.import_job_id} created with PENDING status")

        # Async path: delegate to AsyncImportProcessorFunction for large imports
        async_processor_function = os.environ.get("ASYNC_PROCESSOR_FUNCTION_NAME")
        if import_job and total_rows > sync_row_threshold and async_processor_function:
            log_info(
                f"Row count {total_rows} exceeds threshold {sync_row_threshold}, "
                f"invoking async processor for job {import_job.import_job_id}"
            )
            endpoint_url = os.environ.get("AWS_ENDPOINT_URL")
            lambda_client_kwargs = {"service_name": "lambda"}
            if endpoint_url:
                lambda_client_kwargs["endpoint_url"] = endpoint_url
            lambda_client = boto3.client(**lambda_client_kwargs)

            payload = json.dumps({
                "importJobId": import_job.import_job_id,
                "csvContent": csv_content,
                "userId": user_id,
                "fileName": file_name,
            })

            lambda_client.invoke(
                FunctionName=async_processor_function,
                InvocationType="Event",
                Payload=payload.encode("utf-8"),
            )

            log_info(f"Async processor invoked for job {import_job.import_job_id}")

            return {
                "statusCode": 202,
                "headers": get_cors_headers(),
                "body": json.dumps({
                    "importJobId": import_job.import_job_id,
                    "status": "PENDING",
                    "message": f"Import job created. Poll GET /documents/import/jobs/{import_job.import_job_id} for status.",
                }),
            }

        # Sync path: transition to PROCESSING and process rows inline
        if import_job and import_jobs_table:
            update_import_job_status(
                import_jobs_table, import_job.import_job_id, "PROCESSING"
            )
            log_info(f"Import job {import_job.import_job_id} transitioned to PROCESSING")

        # Map each row to formData, catching ValueError per-row
        mapped_rows = []
        pre_mapping_failures = []

        for index, row in enumerate(parsed_rows):
            row_number = index + 1
            try:
                form_data = map_row_to_form_data(row)
                mapped_rows.append((row_number, form_data))
            except ValueError as e:
                pre_mapping_failures.append(
                    RowResult(
                        row=row_number,
                        status="failed",
                        error=str(e),
                    )
                )
                # Update import job row for pre-mapping failures
                if import_job and import_job_rows_table and import_jobs_table:
                    update_import_job_row(
                        import_job_rows_table,
                        import_job.import_job_id,
                        row_number,
                        "FAILED",
                        errors=str(e),
                    )
                    increment_row_result(
                        import_jobs_table, import_job.import_job_id, succeeded=False
                    )

        # Process mapped rows through the orchestrator
        if mapped_rows:
            # Re-index rows for the orchestrator (it uses 0-based enumerate internally)
            form_data_list = [fd for _, fd in mapped_rows]
            orchestrator_result = process_import(
                rows=form_data_list,
                user_id=user_id,
                document_type="1099-DIV",
                templates_bucket=templates_bucket,
                outputs_bucket=outputs_bucket,
                job_table_name=job_table_name,
            )

            # Fix row numbers: orchestrator uses 1-based from its own list,
            # but we need the original CSV row numbers
            original_row_numbers = [rn for rn, _ in mapped_rows]
            for i, result_dict in enumerate(orchestrator_result.results):
                result_dict["row"] = original_row_numbers[i]

                # Update import job row tracking for each orchestrator result
                if import_job and import_job_rows_table and import_jobs_table:
                    csv_row_num = original_row_numbers[i]
                    if result_dict.get("status") == "succeeded":
                        update_import_job_row(
                            import_job_rows_table,
                            import_job.import_job_id,
                            csv_row_num,
                            "SUCCEEDED",
                            output_key=result_dict.get("outputKey", ""),
                        )
                        increment_row_result(
                            import_jobs_table, import_job.import_job_id, succeeded=True
                        )
                    else:
                        update_import_job_row(
                            import_job_rows_table,
                            import_job.import_job_id,
                            csv_row_num,
                            "FAILED",
                            errors=result_dict.get("error", ""),
                        )
                        increment_row_result(
                            import_jobs_table, import_job.import_job_id, succeeded=False
                        )

            # Merge pre-mapping failures with orchestrator results
            all_results = []
            orch_idx = 0
            fail_idx = 0
            orch_results = orchestrator_result.results
            fail_results = [f.to_dict() for f in pre_mapping_failures]

            # Merge by row number to maintain order
            while orch_idx < len(orch_results) or fail_idx < len(fail_results):
                if orch_idx < len(orch_results) and fail_idx < len(fail_results):
                    if orch_results[orch_idx]["row"] < fail_results[fail_idx]["row"]:
                        all_results.append(orch_results[orch_idx])
                        orch_idx += 1
                    else:
                        all_results.append(fail_results[fail_idx])
                        fail_idx += 1
                elif orch_idx < len(orch_results):
                    all_results.append(orch_results[orch_idx])
                    orch_idx += 1
                else:
                    all_results.append(fail_results[fail_idx])
                    fail_idx += 1

            total = len(parsed_rows)
            succeeded = orchestrator_result.succeeded
            failed = orchestrator_result.failed + len(pre_mapping_failures)
        else:
            # All rows failed mapping
            all_results = [f.to_dict() for f in pre_mapping_failures]
            total = len(parsed_rows)
            succeeded = 0
            failed = len(pre_mapping_failures)

        # Determine and set terminal status on the import job
        if import_job and import_jobs_table:
            terminal_status = determine_terminal_status(succeeded, failed, total)
            update_import_job_status(
                import_jobs_table, import_job.import_job_id, terminal_status
            )
            log_info(f"Import job {import_job.import_job_id} completed with status {terminal_status}")

        summary = {
            "total": total,
            "succeeded": succeeded,
            "failed": failed,
            "results": all_results,
        }

        # Add importJobId to response for backward-compatible enhancement
        if import_job:
            summary["importJobId"] = import_job.import_job_id

        return {
            "statusCode": 200,
            "headers": get_cors_headers(),
            "body": json.dumps(summary),
        }

    except AuthenticationError as e:
        return error_response(401, "AuthenticationError", str(e))

    except ValidationError as e:
        return error_response(400, "ValidationError", str(e))

    except Exception as e:
        log_error("csv_import", e)
        return error_response(500, "InternalError", "An unexpected error occurred")
