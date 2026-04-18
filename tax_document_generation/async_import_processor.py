"""Asynchronous import processor for large CSV imports.

Invoked asynchronously by csv_import_handler when the row count exceeds
SYNC_ROW_THRESHOLD. Processes rows sequentially, updating import job
records as it goes.

Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7
"""

import os
import sys
from datetime import datetime, timezone
from typing import Dict

sys.path.insert(0, os.path.dirname(__file__))

from csv_parser import parse_csv
from row_mapper import map_row_to_form_data
from import_job_service import (
    update_import_job_status,
    update_import_job_row,
    increment_row_result,
    determine_terminal_status,
)
from generation_service import generate_single_document
from logger import log_info, log_error


def lambda_handler(event: Dict, context) -> None:
    """
    Process CSV import rows asynchronously.

    Receives the importJobId and CSV content via the event payload.
    Processes rows sequentially, updating the import job and row records
    in DynamoDB as each row completes.

    On system-level failure, marks the import job as FAILED with
    a descriptive error message.

    Args:
        event: Dict with importJobId, csvContent, userId, fileName.
        context: Lambda context (unused).
    """
    import_jobs_table = os.environ.get("IMPORT_JOBS_TABLE_NAME")
    import_job_rows_table = os.environ.get("IMPORT_JOB_ROWS_TABLE_NAME")
    templates_bucket = os.environ.get("TEMPLATES_BUCKET")
    outputs_bucket = os.environ.get("OUTPUTS_BUCKET")
    job_table_name = os.environ.get("JOB_TABLE_NAME")

    import_job_id = event.get("importJobId", "")
    csv_content = event.get("csvContent", "")
    user_id = event.get("userId", "")
    file_name = event.get("fileName", "")

    log_info(f"Async processor started for job {import_job_id}", {
        "fileName": file_name,
        "userId": user_id,
    })

    try:
        # Transition PENDING → PROCESSING
        update_import_job_status(import_jobs_table, import_job_id, "PROCESSING")
        log_info(f"Import job {import_job_id} transitioned to PROCESSING")

        # Parse CSV and map rows
        parsed_rows = parse_csv(csv_content)
        total_rows = len(parsed_rows)

        success_count = 0
        failure_count = 0

        for index, row in enumerate(parsed_rows):
            row_number = index + 1

            try:
                form_data = map_row_to_form_data(row)

                result = generate_single_document(
                    user_id=user_id,
                    document_type="1099-DIV",
                    form_data=form_data,
                    templates_bucket=templates_bucket,
                    outputs_bucket=outputs_bucket,
                    job_table_name=job_table_name,
                )

                if result.status == "COMPLETED":
                    update_import_job_row(
                        import_job_rows_table,
                        import_job_id,
                        row_number,
                        "SUCCEEDED",
                        output_key=result.output_key,
                    )
                    increment_row_result(import_jobs_table, import_job_id, succeeded=True)
                    success_count += 1
                else:
                    update_import_job_row(
                        import_job_rows_table,
                        import_job_id,
                        row_number,
                        "FAILED",
                        errors=result.error_message,
                    )
                    increment_row_result(import_jobs_table, import_job_id, succeeded=False)
                    failure_count += 1

            except ValueError as e:
                # Row mapping failure — record and continue
                update_import_job_row(
                    import_job_rows_table,
                    import_job_id,
                    row_number,
                    "FAILED",
                    errors=str(e),
                )
                increment_row_result(import_jobs_table, import_job_id, succeeded=False)
                failure_count += 1
                log_error(import_job_id, e, {"row": row_number})

            except Exception as e:
                # Unexpected per-row error — record and continue
                update_import_job_row(
                    import_job_rows_table,
                    import_job_id,
                    row_number,
                    "FAILED",
                    errors=str(e),
                )
                increment_row_result(import_jobs_table, import_job_id, succeeded=False)
                failure_count += 1
                log_error(import_job_id, e, {"row": row_number})

        # Determine and set terminal status
        terminal_status = determine_terminal_status(success_count, failure_count, total_rows)
        update_import_job_status(import_jobs_table, import_job_id, terminal_status)

        log_info(f"Async processing complete for job {import_job_id}", {
            "status": terminal_status,
            "total": total_rows,
            "succeeded": success_count,
            "failed": failure_count,
        })

    except Exception as e:
        # System-level error — mark the entire job FAILED
        error_msg = f"System error during async processing: {str(e)}"
        log_error(import_job_id, e)
        try:
            update_import_job_status(
                import_jobs_table, import_job_id, "FAILED", error_message=error_msg
            )
        except Exception:
            log_error(import_job_id, Exception("Failed to update job status to FAILED"))
