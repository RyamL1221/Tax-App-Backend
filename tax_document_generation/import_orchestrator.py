"""
Orchestrates CSV import by processing rows through Generation_Service.

This module iterates over mapped rows, invokes the Generation_Service for each
row synchronously, collects per-row results (success or error), and assembles
the final summary response.

Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 6.1, 6.2, 6.3, 6.4, 6.5, 6.6
"""

from typing import List, Dict, Any
from dataclasses import dataclass

from generation_service import generate_single_document, GenerationResult
from logger import log_info, log_error


@dataclass
class RowResult:
    """Per-row processing outcome."""
    row: int              # 1-based row index
    status: str           # "succeeded" or "failed"
    job_id: str = ""
    output_key: str = ""
    error: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to camelCase dict for JSON response."""
        result: Dict[str, Any] = {
            "row": self.row,
            "status": self.status,
        }
        if self.status == "succeeded":
            result["jobId"] = self.job_id
            result["outputKey"] = self.output_key
        else:
            result["error"] = self.error
        return result


@dataclass
class ImportSummary:
    """Aggregate result of a CSV import."""
    total: int
    succeeded: int
    failed: int
    results: List[Dict[str, Any]]


def process_import(
    rows: List[Dict[str, Any]],
    user_id: str,
    document_type: str,
    templates_bucket: str,
    outputs_bucket: str,
    job_table_name: str,
) -> ImportSummary:
    """
    Process all mapped rows sequentially through Generation_Service.

    For each row:
      - Invoke generate_single_document.
      - On success: record row index, job_id, output_key.
      - On failure: record row index and error message.
      - Continue to next row regardless of outcome.

    Args:
        rows: List of formData dicts (one per CSV data row).
        user_id: Authenticated user ID.
        document_type: Always "1099-DIV".
        templates_bucket: S3 bucket for templates.
        outputs_bucket: S3 bucket for outputs.
        job_table_name: DynamoDB table for jobs.

    Returns:
        ImportSummary with totals and per-row results.
    """
    results: List[Dict[str, Any]] = []
    succeeded_count = 0
    failed_count = 0

    log_info(f"Starting CSV import: {len(rows)} rows to process", {
        "documentType": document_type,
        "userId": user_id,
    })

    for index, form_data in enumerate(rows):
        row_number = index + 1  # 1-based

        try:
            gen_result: GenerationResult = generate_single_document(
                user_id=user_id,
                document_type=document_type,
                form_data=form_data,
                templates_bucket=templates_bucket,
                outputs_bucket=outputs_bucket,
                job_table_name=job_table_name,
            )

            if gen_result.status == "COMPLETED":
                row_result = RowResult(
                    row=row_number,
                    status="succeeded",
                    job_id=gen_result.job_id,
                    output_key=gen_result.output_key,
                )
                succeeded_count += 1
            else:
                row_result = RowResult(
                    row=row_number,
                    status="failed",
                    error=gen_result.error_message,
                )
                failed_count += 1

        except Exception as e:
            row_result = RowResult(
                row=row_number,
                status="failed",
                error=str(e),
            )
            failed_count += 1
            log_error("import", e, {"row": row_number})

        results.append(row_result.to_dict())

    log_info(f"CSV import complete: {succeeded_count} succeeded, {failed_count} failed", {
        "total": len(rows),
        "succeeded": succeeded_count,
        "failed": failed_count,
    })

    return ImportSummary(
        total=len(rows),
        succeeded=succeeded_count,
        failed=failed_count,
        results=results,
    )
