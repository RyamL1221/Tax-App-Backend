"""Lambda handler for CSV import of 1099-DIV records.

Accepts a base64-encoded CSV file, parses and validates it, maps each row
to canonical formData, and delegates to the import orchestrator for
sequential generation through the shared Generation_Service.

Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 6.1, 6.5, 6.6
"""

import os
import sys
import json
import base64
from typing import Dict

sys.path.insert(0, os.path.dirname(__file__))

from jwt_validator import validate_jwt
from csv_parser import parse_csv
from row_mapper import map_row_to_form_data
from import_orchestrator import process_import, RowResult, ImportSummary
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

        # Parse request body
        body = event.get("body", "{}")
        if isinstance(body, str):
            body = json.loads(body)

        # Extract csvFile
        csv_file_b64 = body.get("csvFile")
        if not csv_file_b64:
            raise ValidationError("Missing required field: csvFile")

        # Decode base64
        try:
            csv_bytes = base64.b64decode(csv_file_b64)
        except Exception:
            raise ValidationError("Invalid base64 encoding in csvFile")

        # Enforce size limit
        if len(csv_bytes) > MAX_CSV_SIZE_BYTES:
            raise ValidationError("CSV file exceeds maximum size of 5 MB")

        csv_content = csv_bytes.decode("utf-8")

        # Parse CSV (validates headers, filters blank rows)
        parsed_rows = parse_csv(csv_content)

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

        summary = {
            "total": total,
            "succeeded": succeeded,
            "failed": failed,
            "results": all_results,
        }

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
