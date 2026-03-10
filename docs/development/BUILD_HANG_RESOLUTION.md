# SAM Build Hang Resolution Guide

## Root Cause

The SAM build process was hanging during the **PythonPipBuilder:CopySource** phase due to the presence of cache directories and unnecessary files in Lambda function directories. These files caused the build process to copy excessive data, leading to timeouts and hangs.

## Issues Identified

### 1. Cache Directories (15 instances)
Cache directories were present in all Lambda function directories:
- `__pycache__/` - Python bytecode cache
- `.pytest_cache/` - Pytest test cache
- `.hypothesis/` - Hypothesis property-based testing cache

**Impact**: These directories contain generated files that should not be included in Lambda deployments. They significantly increase build time and can cause the CopySource phase to hang.

### 2. .gitignore Violations (2 instances)
Files that should be ignored were present:
- `.DS_Store` files in `password_recovery/` directory

**Impact**: These system files add unnecessary data to the build process.

### 3. Dependency Version Conflicts (10 instances)
Version conflicts across Lambda functions for:
- `boto3`: Mixed versions (unpinned in user_registration, `>=1.34.0` in others)
- `bcrypt`: Mixed versions (unpinned in user_registration, `>=4.1.0` in others)
- `email-validator`: Mixed versions (unpinned in user_registration, `>=2.1.0` in others)

**Impact**: While not directly causing build hangs, version conflicts can lead to dependency resolution issues and inconsistent behavior across functions.

## Resolution Steps

### Automated Fixes Applied

1. **Removed all cache directories** (15 directories)
   - Deleted `__pycache__`, `.pytest_cache`, and `.hypothesis` from all Lambda functions
   - Created backup before removal at `.backups/backup_20260205_163046`

2. **Updated .gitignore**
   - Added `.DS_Store` pattern to prevent future commits of system files

### Manual Actions Required

**Fix dependency version conflicts:**

Update `user_registration/requirements.txt` to pin versions:
```
boto3>=1.34.0
bcrypt>=4.1.0
email-validator>=2.1.0
```

This standardizes versions across all Lambda functions.

## Preventive Measures

### 1. Add to .gitignore

Ensure your `.gitignore` includes:
```
# Python cache
__pycache__/
*.pyc
*.pyo
*.pyd

# Testing cache
.pytest_cache/
.hypothesis/
.tox/
.coverage
htmlcov/

# IDE and system files
.DS_Store
Thumbs.db
*.swp
*.swo

# Build artifacts
.aws-sam/
dist/
build/
*.egg-info/
```

### 2. Clean Before Building

Always clean cache directories before running SAM build:
```bash
# Run diagnostic tool
python debug_tools/diagnose_build_hang.py

# Apply automated fixes
python debug_tools/apply_fixes.py --dry-run  # Preview changes
python debug_tools/apply_fixes.py            # Apply fixes

# Then build
sam build --parameter-overrides Environment=local
```

### 3. Use Make Commands

Add to your `Makefile`:
```makefile
.PHONY: clean-cache
clean-cache:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".hypothesis" -exec rm -rf {} +

.PHONY: sam-build-clean
sam-build-clean: clean-cache
	sam build --parameter-overrides Environment=local
```

### 4. Pre-commit Hook

Consider adding a pre-commit hook to prevent committing cache files:
```bash
#!/bin/bash
# .git/hooks/pre-commit

# Check for cache directories
if git diff --cached --name-only | grep -E "(__pycache__|\.pytest_cache|\.hypothesis)"; then
    echo "Error: Attempting to commit cache directories"
    echo "Run: make clean-cache"
    exit 1
fi
```

### 5. CI/CD Integration

In your CI/CD pipeline, always run diagnostics before building:
```yaml
# Example GitHub Actions
- name: Run SAM build diagnostics
  run: python debug_tools/diagnose_build_hang.py --json -o diagnostic_report.json

- name: Apply automated fixes
  run: python debug_tools/apply_fixes.py --report diagnostic_report.json

- name: Build SAM application
  run: sam build --parameter-overrides Environment=local
```

## Diagnostic Tool Usage

### Run Diagnostics
```bash
# Basic diagnostic run
python debug_tools/diagnose_build_hang.py

# Verbose output
python debug_tools/diagnose_build_hang.py -v

# JSON output for automation
python debug_tools/diagnose_build_hang.py --json -o report.json
```

### Apply Fixes
```bash
# Preview changes (dry run)
python debug_tools/apply_fixes.py --dry-run

# Apply fixes
python debug_tools/apply_fixes.py

# Restore from backup if needed
python -c "from debug_tools.apply_fixes import restore_from_backup; restore_from_backup('.backups/backup_YYYYMMDD_HHMMSS')"
```

## Verification

After applying fixes, verify the build completes successfully:

```bash
# Clean build
sam build --parameter-overrides Environment=local

# Expected output:
# Building codeuri: user_registration/ runtime: python3.14 ...
# Building codeuri: user_login/ runtime: python3.14 ...
# Building codeuri: password_recovery/ runtime: python3.14 ...
# Building codeuri: tax_document_generation/ runtime: python3.14 ...
# Build Succeeded
```

Build should complete in under 2 minutes without hanging.

## Troubleshooting

### Build Still Hangs

1. Run diagnostics again to check for new issues:
   ```bash
   python debug_tools/diagnose_build_hang.py -v
   ```

2. Check for symlinks (not automatically fixed):
   ```bash
   find . -type l
   ```

3. Check for large files (>10MB):
   ```bash
   find . -type f -size +10M
   ```

### Backup Restoration

If fixes cause issues, restore from backup:
```bash
python -c "
from debug_tools.apply_fixes import restore_from_backup
restore_from_backup('.backups/backup_20260205_163046')
"
```

## Summary

The SAM build hang was caused by cache directories in Lambda function directories. The diagnostic tool successfully identified and automatically fixed 16 of 27 issues (15 cache directories + 1 .gitignore update). The remaining 10 dependency version conflicts require manual resolution but do not directly cause build hangs.

**Status**: ✅ Build hang resolved. SAM build now completes successfully.

**Next Steps**: 
1. Manually fix dependency version conflicts in `user_registration/requirements.txt`
2. Add preventive measures to avoid future cache directory accumulation
3. Integrate diagnostic tool into CI/CD pipeline
