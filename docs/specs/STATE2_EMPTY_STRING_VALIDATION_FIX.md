# 1099-DIV Optional-Field Empty-String Validation Fix

**Branch:** `bugfix/state2-empty-fix`
**Status:** Fixed + regression-tested
**Component:** `tax_document_generation/input_validator.py`

## TL;DR

A 1099-DIV submission failed with HTTP 400 `"State code must be exactly 2
uppercase letters (e.g., 'NY', 'CA')"`. The original bug report framed this as
"second-state fields are wrongly treated as required." That framing was wrong.
The real cause: optional fields sent as an **empty string** `""` were run
through format validators intended for present values. The fix is a single
early-`continue` that treats empty/whitespace-only **optional** fields as
absent before format validation.

## Original report's premise vs. what was actually true

| | |
|---|---|
| **Reported premise** | Absent second-state fields (`state2`, `stateIdentificationNumber2`, `stateTaxWithheld2`) were being rejected as if required. |
| **What was actually true** | Absence was **never** rejected. The trigger was optional fields submitted as `""` (a *present* empty value) reaching `_validate_state_code` / `_validate_amount`, which are written for non-empty values. `""` fails the "2 uppercase letters" state-code check. |

The frontend console confirmed it:

```
[Form1099Div] API Error: {status: 400, message: "State code must be exactly 2 uppercase letters (e.g., 'NY', 'CA')"}
```

That is a **format** error, not a missing-required-field error. The form was
sending a blank state field (most likely the unused second state) as `""`
instead of omitting it.

## Root cause (code-level)

In `_validate_field_types_and_formats`, the loop skips optional fields only
when they are **absent** from `form_data`. When an optional field is *present*
with value `""`, it fell through to type + format validation. For state codes
that means `_validate_state_code("")`, which requires exactly two uppercase
letters and therefore rejects `""`.

## The fix

`tax_document_generation/input_validator.py` — one guard added inside the
validation loop, before the type/format checks:

```python
# Treat empty/whitespace-only OPTIONAL fields as absent.
if field_name in optional_fields and isinstance(field_value, str) and not field_value.strip():
    continue
```

- Applies to **optional** fields only. Required fields intentionally fall
  through so their own checks still fire (e.g. an empty required `payerName`
  still errors with "must be a non-empty string").
- Empty-string and whitespace-only values are both treated as absent.

## Scope note — positive expansion, not scope creep

The fix resolves this for **every optional string field** (all state codes:
`state`, `state2`, `payerState`, `recipientState`; ZIPs; phone; amount fields
sent as strings) — not just the three second-state fields named in the report.
This is intentional: it is the same bug class, addressed with the same single
check, and requires no per-field logic. Fixing only `state2` would have left
identical latent failures on every other optional field.

## Ruled out (do not re-investigate)

1. **No "all-or-nothing" cross-field rule exists.** A payload with
   `stateTaxWithheld2` present but `state2`/`stateIdentificationNumber2` absent
   returned **HTTP 200 COMPLETED**. There is no enforced coupling between
   second-state fields, so the "all-or-nothing fires incorrectly" hypothesis is
   moot — there is no such rule to fire.
2. **The CSV / bulk-import path was never a factor.** `csv_import_handler.py`
   and `async_import_processor.py` map rows via `row_mapper.map_row_to_form_data`
   (which *omits* empty cells) and then call the same `generate_single_document`
   → `validate_form_data`. Both the manual endpoint and the import path converge
   on the identical validator; there is no separate stricter validation.
3. **No gateway/OpenAPI/DTO schema layer.** `/documents/generate` uses the
   implicit `ServerlessRestApi` with no `DefinitionBody`, `RequestValidator`, or
   `AWS::ApiGateway::Model`. A repo-wide search found no OpenAPI/Swagger spec and
   no JSON-schema DTO. Nothing between API Gateway and the Lambda enforces field
   requirements.

## Known separate follow-up (NOT fixed here — low priority)

There are two independent definitions of "required" that disagree on
`calendarYear`:

- `input_validator.py` (used by the live endpoint **and** the CSV path) treats
  `calendarYear` as **optional**.
- `FIELD_METADATA` / `FieldMapper.validate_required_fields` treats it as
  **required**.

This discrepancy is **dormant**: `FieldMapper.validate_required_fields` is
called only by tests, never by production code. It does not affect any
second-state field and did not contribute to this bug. Left as a separate,
low-priority cleanup (reconcile the two "required" sources, or delete the unused
metadata-driven check). If reconciled later, update the relevant steering/docs.

## Verification

- Fix confirmed against the real `lambda_handler` code path (moto-mocked S3 +
  DynamoDB, valid JWT) during investigation.
- Permanent regression tests added in
  `tax_document_generation/tests/unit/test_input_validator_unit.py`
  (`TestOptionalEmptyStringFields`, 12 tests): empty/whitespace optional fields
  accepted; complete second-state block accepted with pass-through; malformed
  non-empty values still rejected with their specific messages; required-field
  integrity preserved.
- Validator-related unit scope, all green:

  | File | Tests |
  |---|---|
  | `test_input_validator_unit.py` | 31 (19 pre-existing + 12 new) |
  | `test_new_field_validation_unit.py` | 21 |
  | `test_second_tin_notification_validation_unit.py` | 9 |
  | `test_voided_corrected_validation_unit.py` | 15 |
  | **Total** | **76 passed** |

## Changes in this session (relative to `dev`)

Exactly two files:

- `tax_document_generation/input_validator.py` — +9 lines (the fix).
- `tax_document_generation/tests/unit/test_input_validator_unit.py` — +152
  lines (the regression test class).

## Frontend spec-doc question (decision for Ryan)

The original prompt asked whether the frontend spec doc (`form1099DivSchema.ts`
and its spec) should note that the true root cause was backend-side. That file
lives in a **separate frontend repo**, not this backend repo. Recommendation:
optionally harden the frontend to omit empty optional fields (send `undefined`
rather than `""`) as belt-and-suspenders — but that is **not required**; the
backend fix fully resolves the error. Flagging as a decision rather than editing
another repo unprompted.
```
