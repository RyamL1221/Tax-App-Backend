"""Lambda handler for retrieving import job row results.

Returns the per-row processing results for a single import job, scoped to
the authenticated user.

Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9, 6.2, 6.3
"""

import os
import sys
import json
from typing import Dict

sys.path.insert(0, os.path.dirname(__file__))

from jwt_validator import validate_jwt
from import_job_service import get_import_job, get_import_job_rows
from response_formatter import error_response, get_cors_headers
from logger import log_info, log_error
from exceptions import AuthenticationError


def lambda_handler(event: Dict, context) -> Dict:
    """
    Handle import job row results retrieval requests.

    Flow:
      1. Handle OPTIONS preflight.
      2. Validate JWT from Authorization header.
      3. Extract importJobId from path parameters.
      4. Retrieve parent import job and verify userId.
      5. Query all row records ordered by rowNumber.
      6. Return row results as JSON array.

    Returns HTTP 404 for non-existent jobs or unauthorized access.

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
                "Access-Control-Allow-Methods": "GET,OPTIONS",
            },
            "body": "",
        }

    try:
        # Environment variables
        import_jobs_table = os.environ.get("IMPORT_JOBS_TABLE_NAME")
        import_job_rows_table = os.environ.get("IMPORT_JOB_ROWS_TABLE_NAME")
        jwt_secret = os.environ.get("JWT_SECRET_KEY")

        if not all([import_jobs_table, import_job_rows_table, jwt_secret]):
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

        # Extract importJobId from path parameters
        path_params = event.get("pathParameters") or {}
        import_job_id = path_params.get("importJobId")

        if not import_job_id:
            return error_response(400, "ValidationError", "Missing importJobId parameter")

        log_info(f"Import job rows request for {import_job_id} from user {user_id}")

        # Retrieve parent import job
        import_job = get_import_job(import_jobs_table, import_job_id)

        if not import_job:
            return error_response(404, "NotFoundError", "Import job not found")

        # Verify userId matches authenticated user (return 404 to prevent enumeration)
        if import_job.get("userId") != user_id:
            return error_response(404, "NotFoundError", "Import job not found")

        # Query all row records ordered by rowNumber
        rows = get_import_job_rows(import_job_rows_table, import_job_id)

        # Build row results with conditional fields
        row_results = []
        for row in rows:
            row_entry = {
                "rowNumber": row.get("rowNumber", 0),
                "status": row.get("status", ""),
            }

            row_status = row.get("status", "")
            if row_status == "SUCCEEDED":
                row_entry["outputKey"] = row.get("outputKey", "")
            elif row_status == "FAILED":
                row_entry["errors"] = row.get("errors", "")

            row_results.append(row_entry)

        response_body = {
            "importJobId": import_job_id,
            "rows": row_results,
        }

        return {
            "statusCode": 200,
            "headers": get_cors_headers(),
            "body": json.dumps(response_body),
        }

    except AuthenticationError as e:
        return error_response(401, "AuthenticationError", str(e))

    except Exception as e:
        log_error("import_job_rows", e)
        return error_response(500, "InternalError", "An unexpected error occurred")
