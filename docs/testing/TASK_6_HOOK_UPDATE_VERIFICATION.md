# Task 6: Hook Update Verification

## Overview

This document verifies the successful update of the `.kiro/hooks/check-lambda-imports.kiro.hook` to integrate build verification with import pattern checking.

## Changes Made

### Hook Configuration Updates

1. **Name Updated**: "Check Lambda Import Patterns" → "Check Lambda Import Patterns and Build Status"
2. **Description Enhanced**: Now mentions both import checking and SAM build artifact verification
3. **Version Incremented**: v1 → v2
4. **Pattern Added**: Added `document_download/*.py` to the file patterns

### Prompt Enhancement

The hook prompt now includes:

#### 1. Import Pattern Check (Existing)
- Checks for package-prefixed imports
- Checks for relative imports
- Distinguishes between test files and production code

#### 2. Build Verification Check (New)
- Provides code example for using `verify_sam_build` module
- Shows how to extract Lambda directory from file path
- Demonstrates calling `check_build_artifacts()` and `generate_build_feedback()`

#### 3. Consolidated Feedback (New)
- **Both checks pass**: Single brief confirmation message
- **Either check fails**: Consolidated report of all issues
- **Example output**: Shows how to format combined import and build issues

## Requirements Validated

### Requirement 4.1: Integration with Existing Import Check Hook
✅ **VALIDATED**: The hook now performs both import pattern checking and build verification when triggered by Lambda file edits.

### Requirement 4.2: Consolidated Feedback
✅ **VALIDATED**: The prompt instructs the agent to:
- Provide a single confirmation when both checks pass
- Report all problems together when issues are found
- Include actionable guidance for both types of issues

### Requirement 4.3: Maintain Existing Trigger Patterns
✅ **VALIDATED**: The hook still triggers on `fileEdited` events for Lambda `*.py` files in the same directories (plus the new `document_download/` directory).

### Requirement 4.4: Comprehensive Validation
✅ **VALIDATED**: The prompt explicitly states "Always run BOTH checks and consolidate the results. Don't skip the build verification even if imports are correct."

## Hook Behavior

### Trigger Conditions
The hook triggers when any Python file is edited in these directories:
- `user_login/*.py`
- `user_registration/*.py`
- `password_recovery/*.py`
- `tax_document_generation/*.py`
- `document_download/*.py`
- `hello_world/*.py`

### Agent Actions
When triggered, the agent will:

1. **Check Import Patterns**
   - Scan the edited file for package-prefixed imports
   - Scan for relative imports
   - Determine if file is in tests/ directory
   - Identify any incorrect patterns

2. **Verify Build Artifacts**
   - Extract Lambda directory from file path
   - Call `check_build_artifacts(lambda_dir)`
   - Generate feedback using `generate_build_feedback()`
   - Capture build status and issues

3. **Consolidate Results**
   - If both pass: Brief confirmation
   - If either fails: Detailed consolidated report
   - Include fix commands and documentation links

### Example Scenarios

#### Scenario 1: Both Checks Pass
```
✅ Import patterns and build artifacts are valid for UserLoginFunction
```

#### Scenario 2: Import Issues Only
```
⚠️  Issues found in user_login/app.py:

Import Issues:
• Line 5: "from user_login.exceptions import ValidationError" 
  should be "from exceptions import ValidationError"

Build Status:
✅ Build artifacts are valid for UserLoginFunction

Fix import patterns:
Would you like me to fix these imports automatically?

See: .kiro/steering/lambda-import-patterns.md
```

#### Scenario 3: Build Issues Only
```
⚠️  Issues found in user_login/app.py:

Import Patterns:
✅ All imports are correct

Build Issues:
• Build artifacts are older than source files

Fix build:
sam build --parameter-overrides Environment=local

See: .kiro/steering/sam-build-guidelines.md
```

#### Scenario 4: Both Have Issues
```
⚠️  Issues found in user_login/app.py:

Import Issues:
• Line 5: "from user_login.exceptions import ValidationError" 
  should be "from exceptions import ValidationError"
• Line 8: "from user_login.repository import get_user" 
  should be "from repository import get_user"

Build Issues:
• Build artifacts are older than source files
• Cache directories found: __pycache__, .pytest_cache

Fix import patterns:
[offer to fix automatically]

Fix build:
Consider running cache cleanup first:
python debug_tools/apply_fixes.py --remove-cache

Then run SAM build:
sam build --parameter-overrides Environment=local

See: .kiro/steering/lambda-import-patterns.md
See: .kiro/steering/sam-build-guidelines.md
```

## Integration with Existing Modules

The hook leverages the following modules created in previous tasks:

1. **`debug_tools/verify_sam_build.py`** (Task 1)
   - `check_build_artifacts()` - Main verification function
   - Returns `BuildStatus` object with detailed results

2. **`debug_tools/build_feedback_generator.py`** (Task 5)
   - `generate_build_feedback()` - Formats user-facing messages
   - Provides actionable guidance and documentation links

3. **`debug_tools/sam_template_parser.py`** (Task 2)
   - Used internally by `verify_sam_build` to parse template.yaml
   - Extracts Lambda configurations and handler info

4. **`debug_tools/models.py`**
   - `BuildStatus` dataclass for verification results
   - `LambdaConfig` dataclass for template parsing

## Testing Recommendations

To verify the hook works correctly:

### Manual Testing

1. **Test with correct imports and up-to-date build:**
   ```bash
   # Ensure build is up-to-date
   sam build --parameter-overrides Environment=local
   
   # Edit a Lambda file with correct imports
   # Hook should provide brief confirmation
   ```

2. **Test with incorrect imports:**
   ```bash
   # Add package-prefixed import to a Lambda file
   # Hook should detect and offer to fix
   ```

3. **Test with stale build:**
   ```bash
   # Edit a Lambda file
   # Wait a moment, then edit again
   # Hook should detect stale build
   ```

4. **Test with missing build:**
   ```bash
   # Remove .aws-sam/build/ directory
   rm -rf .aws-sam/build/
   
   # Edit a Lambda file
   # Hook should detect missing build and provide setup guidance
   ```

### Automated Testing

The optional integration test (Task 6.1) would verify:
- Hook triggers on file edits
- Both checks are performed
- Feedback is consolidated correctly
- All scenarios produce expected output

## Documentation References

The hook references these documentation files:
- `.kiro/steering/lambda-import-patterns.md` - Import pattern guidelines
- `.kiro/steering/sam-build-guidelines.md` - Build troubleshooting guide
- `.kiro/steering/local-development.md` - First-time setup guide

## Conclusion

✅ **Task 6 Complete**: The check-lambda-imports hook has been successfully updated to integrate build verification with import pattern checking. The hook now provides comprehensive validation that covers both code correctness (import patterns) and deployment readiness (build artifacts), helping developers catch issues early in the development process.

### Key Achievements

1. ✅ Seamless integration of build verification with existing import checking
2. ✅ Consolidated feedback that reports all issues together
3. ✅ Brief confirmations when both checks pass
4. ✅ Actionable guidance with fix commands and documentation links
5. ✅ Maintained existing trigger patterns and behavior
6. ✅ Leverages all modules created in previous tasks

### Next Steps

- Optional: Implement integration tests (Task 6.1) to verify hook behavior
- Optional: Test hook in real development scenarios
- Consider: Add hook to other Lambda directories as they are created
