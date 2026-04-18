"""Multipart form-data parser for CSV file uploads.

Extracts the uploaded file content and optional fileName field from
multipart/form-data request bodies using the python-multipart library.

Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 5.1, 5.2, 5.3, 5.4, 5.5
"""

import io
from dataclasses import dataclass

from python_multipart.multipart import parse_options_header
from python_multipart.exceptions import FormParserError, MultipartParseError
from python_multipart import parse_form
from exceptions import ValidationError


@dataclass
class MultipartResult:
    """Result of parsing a multipart/form-data request."""

    file_content: bytes
    file_name: str
    original_filename: str


def parse_multipart_body(
    body: bytes,
    content_type: str,
) -> MultipartResult:
    """Parse a multipart/form-data body and extract the CSV file.

    Extracts:
      - The 'file' field content as bytes
      - The 'fileName' form field value if present
      - The original filename from the file part's Content-Disposition header

    File name resolution order:
      1. Explicit 'fileName' form field value
      2. Original filename from the file upload part
      3. Default: "import.csv"

    Args:
        body: Raw multipart body bytes (already base64-decoded if needed).
        content_type: Full Content-Type header value including boundary.

    Returns:
        MultipartResult with file content and resolved file name.

    Raises:
        ValidationError: If boundary is missing, body is malformed,
                        'file' field is absent, or file is empty.
    """
    # Extract boundary from Content-Type header
    _, options = parse_options_header(content_type)
    boundary = options.get(b"boundary")
    if not boundary:
        raise ValidationError("Invalid multipart request: missing boundary")

    # Parse the multipart body
    fields = {}
    files = {}

    def on_field(field):
        fields[field.field_name.decode("utf-8")] = field.value.decode("utf-8")

    def on_file(file):
        file.file_object.seek(0)
        content = file.file_object.read()
        files[file.field_name.decode("utf-8")] = {
            "filename": file.file_name.decode("utf-8") if file.file_name else "",
            "content": content,
        }

    headers = {"Content-Type": content_type.encode("utf-8") if isinstance(content_type, str) else content_type}

    try:
        parse_form(headers, io.BytesIO(body), on_field=on_field, on_file=on_file)
    except (MultipartParseError, FormParserError):
        raise ValidationError("Invalid multipart request: could not parse body")

    # Extract file content - parse_form routes parts with a filename attribute
    # to on_file, and parts without one to on_field. Handle both cases.
    if "file" in files:
        file_info = files["file"]
        file_content = file_info["content"]
        original_filename = file_info["filename"]
    elif "file" in fields:
        # Part had no filename attribute, so parse_form treated it as a field
        file_content = fields["file"].encode("utf-8") if isinstance(fields["file"], str) else fields["file"]
        original_filename = ""
    else:
        raise ValidationError("Missing required file field in multipart request")

    # Validate file is not empty
    if len(file_content) == 0:
        raise ValidationError("Uploaded file is empty")

    # File name resolution: explicit fileName field > original filename > default
    explicit_file_name = fields.get("fileName", "").strip()
    if explicit_file_name:
        resolved_name = explicit_file_name
    elif original_filename:
        resolved_name = original_filename
    else:
        resolved_name = "import.csv"

    return MultipartResult(
        file_content=file_content,
        file_name=resolved_name,
        original_filename=original_filename,
    )
