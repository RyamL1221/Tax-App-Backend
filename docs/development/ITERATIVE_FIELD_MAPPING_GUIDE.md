# Iterative Field Mapping Fixes Guide

## Overview

The Iterative Field Mapping Fixes tool provides a systematic, stage-based approach to correcting PDF field mappings for tax document generation. The tool guides you through multiple iterations of analysis, recommendation, testing, and approval, ensuring each mapping change is verified before proceeding.

## Key Features

- **Automated Analysis**: Identifies invalid mappings and field issues
- **Intelligent Recommendations**: Suggests corrections based on field name matching
- **Test PDF Generation**: Creates test PDFs for manual verification
- **Approval Checkpoints**: Requires explicit approval before applying changes
- **Version Control**: Maintains history of all configuration changes with rollback capability
- **Comprehensive Reporting**: Documents all iterations and decisions

## Workflow Stages

The tool follows a four-stage workflow for each iteration:

### 1. Analysis Stage
- Extracts all fields from the PDF template
- Identifies mappings that reference non-existent PDF fields
- Compares current mappings against expected field locations
- Generates a comprehensive analysis report

### 2. Recommendation Stage
- Analyzes PDF field names to suggest logical field mappings
- Scores candidate fields based on name similarity and properties
- Provides rationale for each recommended change
- Prioritizes fixes by impact (critical fields first)

### 3. Testing Stage
- Applies recommended changes to create a new configuration
- Generates a test PDF with sample data
- Runs automated validation checks
- Saves test PDF for manual inspection

### 4. Approval Stage
- Presents test PDF for manual review
- Waits for explicit user approval
- Applies changes if approved, or rolls back if rejected
- Prepares next iteration if more issues remain

## Installation

The tool is part of the `tax_document_generation` module. No additional installation is required.

## Usage

### Basic Usage

```bash
python -m tax_document_generation.iterative_fixer.cli \
  --form-type 1099-DIV \
  --template samples/1099-DIV.pdf
```

### With Custom Configuration Directory

```bash
python -m tax_document_generation.iterative_fixer.cli \
  --form-type 1099-DIV \
  --template samples/1099-DIV.pdf \
  --config-dir custom/config/path
```

### With Verbose Logging

```bash
python -m tax_document_generation.iterative_fixer.cli \
  --form-type 1099-DIV \
  --template samples/1099-DIV.pdf \
  --verbose
```

## Command-Line Options

- `--form-type`: Form type (e.g., 1099-DIV, 1099-INT) - **Required**
- `--template`: Path to PDF template file - **Required**
- `--config-dir`: Configuration directory (default: `tax_document_generation/field_mappings/{form-type}`)
- `--verbose`: Enable verbose logging

## Approval Decisions

At each approval checkpoint, you have three options:

### Approve
- Accepts the recommended changes
- Saves the new configuration
- Continues to the next iteration if more issues remain
- Command: Type `yes` or `y`

### Reject
- Rejects the recommended changes
- Keeps the current configuration
- Continues to the next iteration with different recommendations
- Command: Type `no` or `n`

### Rollback
- Reverts to the previous configuration
- Exits the workflow
- Use when you want to undo recent changes
- Command: Type `rollback`

## Example Session

```
============================================================
Iterative Field Mapping Fixes - 1099-DIV
============================================================

--- Iteration 1 ---

Stage 1: Analysis
----------------------------------------
Extracting PDF fields...
Found 156 fields in PDF
Analyzing mappings...

Analysis complete: 5 issues found. 5 invalid mappings, 0 metadata mismatches.

Invalid mappings found:
  - payer_name: PDF field 'old_payer_field' does not exist in template
  - recipient_name: PDF field 'old_recipient_field' does not exist in template
  ... and 3 more

Stage 2: Recommendations
----------------------------------------

Stage 1: critical priority fixes
Impact: 5 fields affected

  payer_name:
    Current: old_payer_field
    Recommended: topmostSubform[0].Page1[0].f1_1[0]
    Confidence: 0.85 | Priority: critical
    Rationale: Recommended 'topmostSubform[0].Page1[0].f1_1[0]' for 'payer_name' (confidence: 0.85). High confidence match based on field name similarity. Field is on page 1, type: text.

Stage 3: Testing
----------------------------------------
Generating test PDF...
Test PDF saved to: tax_document_generation/iterative_fixer/test_outputs/test_iteration_1.pdf

Running validation...
Validation passed: 0 existence errors, 0 positioning errors, 0 regression failures

Stage 4: Approval
----------------------------------------

Please review the test PDF: tax_document_generation/iterative_fixer/test_outputs/test_iteration_1.pdf

Verify that:
  1. All fields are correctly positioned
  2. Data is visible and readable
  3. No fields are missing or misaligned

Approve these changes? (yes/no/rollback): yes
Comments (optional): Looks good

✓ Changes approved: Looks good
Configuration saved as version v1

--- Iteration 2 ---
...
```

## Manual Verification Steps

When reviewing test PDFs, check the following:

1. **Field Positioning**: Verify data appears in the correct boxes
2. **Data Visibility**: Ensure all text is visible and readable
3. **Field Alignment**: Check that text is properly aligned within fields
4. **No Overlaps**: Verify fields don't overlap or obscure each other
5. **Complete Coverage**: Ensure all expected fields are filled

## Output Files

The tool generates several output files:

### Test PDFs
- Location: `tax_document_generation/iterative_fixer/test_outputs/`
- Naming: `test_iteration_{N}.pdf`
- Purpose: Manual verification of field mappings

### Configuration Versions
- Location: `{config_dir}/versions/`
- Naming: `config_{timestamp}.json`
- Purpose: Version history with rollback capability

### Reports
- Location: `tax_document_generation/iterative_fixer/reports/`
- Files:
  - `final_summary.md`: Overall workflow summary
  - `changelog.md`: Detailed change history
  - `iteration_{N}_report.md`: Individual iteration reports

### Logs
- Location: `iterative_fixer.log`
- Purpose: Detailed execution logs for troubleshooting

## Configuration Files

### Current Configuration
- Location: `{config_dir}/current_config.json`
- Format:
```json
{
  "form_type": "1099-DIV",
  "mappings": {
    "payer_name": "topmostSubform[0].Page1[0].f1_1[0]",
    "recipient_name": "topmostSubform[0].Page1[0].f1_2[0]",
    ...
  },
  "version": "v1",
  "timestamp": "2024-01-15T10:30:00",
  "metadata": {
    "approval_status": "approved",
    "iteration_number": 1
  }
}
```

## Troubleshooting

### No Fields Found in PDF
**Problem**: "No form fields found in PDF"

**Solution**: Verify the PDF template contains form fields. Use Adobe Acrobat to check if the PDF has interactive form fields.

### Configuration File Not Found
**Problem**: "Configuration file not found"

**Solution**: Create an initial configuration file or specify a different config directory with `--config-dir`.

### Import Errors
**Problem**: Module import errors

**Solution**: Ensure you're running from the project root directory and the virtual environment is activated.

### Test PDF Generation Fails
**Problem**: "Test PDF generation failed"

**Solution**: Check that the template PDF is not corrupted and has write permissions in the output directory.

## Best Practices

1. **Start with Critical Fields**: The tool prioritizes critical fields first. Review these carefully.

2. **Verify Each Iteration**: Don't rush through approvals. Take time to review each test PDF thoroughly.

3. **Use Descriptive Comments**: When approving or rejecting, add comments explaining your decision.

4. **Keep Backups**: The tool maintains version history, but keep external backups of working configurations.

5. **Test Incrementally**: Approve small batches of changes rather than large sets to isolate issues.

6. **Document Issues**: If you find problems, note them in the approval comments for future reference.

## Integration with Existing Tools

The iterative fixer integrates with existing field mapping infrastructure:

- **Field Metadata**: Reads from `field_mappings/field_metadata.py`
- **Visual Field Mapper**: Compatible with `visual_field_mapper.py` output
- **Validation Scripts**: Uses `validate_field_mappings.py` for validation
- **Document Generator**: Test PDFs use `document_generator.py`

## Advanced Usage

### Programmatic Usage

You can use the tool programmatically in Python:

```python
from tax_document_generation.iterative_fixer.workflow_controller import IterativeWorkflowController

controller = IterativeWorkflowController(
    form_type="1099-DIV",
    template_path="samples/1099-DIV.pdf",
    config_dir="custom/config/path"
)

controller.start_workflow()
```

### Custom Approval Logic

For automated testing, you can subclass `IterativeWorkflowController` and override `await_user_approval()`:

```python
class AutomatedController(IterativeWorkflowController):
    def await_user_approval(self, test_results):
        # Implement custom approval logic
        if test_results.validation_report.passed:
            return ApprovalDecision(
                approved=True,
                comments="Auto-approved",
                timestamp=datetime.now()
            )
        return super().await_user_approval(test_results)
```

## Support

For issues or questions:
1. Check the logs in `iterative_fixer.log`
2. Review the troubleshooting section above
3. Consult the design document in `.kiro/specs/iterative-field-mapping-fixes/design.md`
4. Check existing field mapping documentation in `docs/architecture/`

## Related Documentation

- [Field Mapping Reference](../architecture/1099-DIV_FIELD_REFERENCE.md)
- [Field Metadata](../../tax_document_generation/field_mappings/field_metadata.py)
- [Visual Field Mapper](../../tax_document_generation/visual_field_mapper.py)
- [Validation Scripts](../../tax_document_generation/validate_field_mappings.py)
