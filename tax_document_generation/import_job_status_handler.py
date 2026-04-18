"""Lambda handler for retrieving import job status.

Returns the status and metadata of a single import job, scoped to the
authenticated user.

Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 6.1, 6.3
"""

import os
import sys
import json
from typing import Dict

sys.path.insert(0, os.path.dirname(__file__))

from jwt_validator import validate_jwt
from import_job_service import get_import_job
from response_formatter import error_response, get_cors_headers
from logger import log_info, log_error
from exceptions import AuthenticationError


def lambda_handler(event: Dict, context) -> Dict:
    """
    Handle import job status retrieval requests.

    Flow:
      1. Handle OPTIONS preflight.
      2. Validate JWT from Authorization header.
      3. Extract importJobId from path parameters.
      4. Retrieve import job record.
      5. Verify userId matches authenticated user.
      6. Return import job data as JSON.

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
        jwt_secret = os.environ.get("JWT_SECRET_KEY")

        if not all([import_jobs_table, jwt_secret]):
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

        log_info(f"Import job status request for {import_job_id} from user {user_id}")

        # Retrieve import job
        import_job = get_import_job(import_jobs_table, import_job_id)

        if not import_job:
            return error_response(404, "NotFoundError", "Import job not found")

        # Verify userId matches authenticated user (return 404 to prevent enumeration)
        if import_job.get("userId") != user_id:
            return error_response(404, "NotFoundError", "Import job not found")

        # Return import job data
        response_body = {
            "importJobId": import_job.get("importJobId", ""),
            "status": import_job.get("status", ""),
            "totalRows": import_job.get("totalRows", 0),
            "processedRows": import_job.get("processedRows", 0),
            "successCount": import_job.get("successCount", 0),
            "failureCount": import_job.get("failureCount", 0),
            "fileName": import_job.get("fileName", ""),
            "documentType": import_job.get("documentType", ""),
            "createdAt": import_job.get("createdAt", ""),
            "updatedAt": import_job.get("updatedAt", ""),
            "completedAt": import_job.get("completedAt", ""),
        }

        return {
            "statusCode": 200,
            "headers": get_cors_headers(),
            "body": json.dumps(response_body),
        }

    except AuthenticationError as e:
        return error_response(401, "AuthenticationError", str(e))

    except Exception as e:
        log_error("import_job_status", e)
        return error_response(500, "InternalError", "An unexpected error occurred")
