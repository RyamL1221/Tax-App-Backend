# Lambda Import Patterns Guide

## Overview

This guide explains the correct import patterns for AWS Lambda functions deployed with AWS SAM (Serverless Application Model). Understanding these patterns is critical for avoiding import errors when your Lambda functions run in the AWS Lambda runtime environment.

## Table of Contents

- [The Problem](#the-problem)
- [Why Direct Imports Are Required](#why-direct-imports-are-required)
- [Import Pattern Rules](#import-pattern-rules)
- [Examples](#examples)
- [Working Reference Implementations](#working-reference-implementations)
- [Common Mistakes](#common-mistakes)
- [Troubleshooting](#troubleshooting)

## The Problem

When AWS SAM builds a Lambda function with a `CodeUri` pointing to a directory (e.g., `CodeUri: tax_document_generation/`), it copies the **contents** of that directory to `/var/task/` in the Lambda runtime container. This means:

1. Your modules are placed at the **root level** of `/var/task/`
2. There is **no parent package directory** in the Lambda runtime
3. Imports that reference the package name will **fail**

### Example of the Problem

**Project Structure:**
```
tax_document_generation/
├── __init__.py
├── app.py
├── exceptions.py
└── jwt_validator.py
```

**SAM template.yaml:**
```yaml
GenerateTaxDocumentFunction:
  Type: AWS::Serverless::Function
  Properties:
    CodeUri: tax_document_generation/
    Handler: app.lambda_handler
```

**Lambda Runtime Structure (after SAM build):**
```
/var/task/
├── app.py
├── exceptions.py
└── jwt_validator.py
```

**❌ INCORRECT - This will fail:**
```python
# In jwt_validator.py
from tax_document_generation.exceptions import AuthenticationError
```

**Error:**
```
Unable to import module 'app': No module named 'tax_document_generation'
```

**✅ CORRECT - This will work:**
```python
# In jwt_validator.py
from exceptions import AuthenticationError
```

## Why Direct Imports Are Required

### SAM Build Process

When SAM builds your Lambda function:

1. **Copies directory contents** to the Lambda package
2. **Flattens the structure** - modules are at root level
3. **Sets `/var/task/` as the working directory** in the Lambda runtime
4. **Python's import system** looks for modules in `/var/task/`

### What Happens in the Lambda Runtime

```python
# Python's module search path in Lambda runtime:
sys.path = [
    '/var/task',           # Your Lambda code is here
    '/opt/python',         # Lambda layers
    '/var/runtime',        # Python runtime
    # ... other paths
]
```

When you write `from tax_document_generation.exceptions import ...`:
- Python looks for `/var/task/tax_document_generation/exceptions.py`
- But the file is actually at `/var/task/exceptions.py`
- **Result: ImportError**

When you write `from exceptions import ...`:
- Python looks for `/var/task/exceptions.py`
- The file exists at this location
- **Result: Success**

## Import Pattern Rules

### Rule 1: Production Code Uses Direct Imports

**Production code** = Code that runs in the Lambda runtime (all `.py` files in your Lambda directory except tests)

✅ **CORRECT:**
```python
# Direct imports - no package prefix
from exceptions import ValidationError, AuthenticationError
from models import GenerationRequest
from jwt_validator import validate_jwt
from user_repository import get_user_by_email
```

❌ **INCORRECT:**
```python
# Package-prefixed imports - will fail in Lambda
from tax_document_generation.exceptions import ValidationError
from tax_document_generation.models import GenerationRequest
from tax_document_generation.jwt_validator import validate_jwt
```

### Rule 2: Test Code Uses Package-Prefixed Imports

**Test code** = Code in your `tests/` directory that runs locally with pytest

✅ **CORRECT:**
```python
# Package-prefixed imports for tests
from tax_document_generation.exceptions import ValidationError
from tax_document_generation.jwt_validator import validate_jwt
from tax_document_generation.app import lambda_handler
```

**Why?** Tests run from the project root where `tax_document_generation/` exists as a proper Python package with an `__init__.py` file.

### Rule 3: Standard Library and External Packages Are Unchanged

Imports from the Python standard library or external packages (installed via `requirements.txt`) work the same way in both production and test code:

```python
# These work everywhere - no changes needed
import json
import os
import logging
from typing import Dict, Any
import boto3
import jwt
from datetime import datetime
```

### Rule 4: Add Current Directory to Path (Optional Pattern)

Some Lambda functions add the current directory to Python's path explicitly:

```python
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

# Then use direct imports
from exceptions import ValidationError
from models import GenerationRequest
```

This pattern is **optional** but can help ensure imports work correctly. It's used in the `password_recovery` Lambda functions.

## Examples

### Example 1: Lambda Handler (Production Code)

**File: `tax_document_generation/app.py`**

```python
"""
Main Lambda Handler for Tax Document Generation
"""

import os
import json
import logging
from typing import Dict, Any

# ✅ CORRECT: Direct imports for local modules
from exceptions import (
    AuthenticationError,
    ValidationError,
    TemplateNotFoundError,
    GenerationError,
    S3Error
)
from models import GenerationRequest
from jwt_validator import validate_jwt
from input_validator import validate_form_data
from template_retriever import get_template
from document_generator import generate_document
from output_persister import store_output
from response_formatter import success_response, error_response

# ✅ CORRECT: Standard library and external packages unchanged
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Handle tax document generation requests."""
    try:
        # Extract JWT token from Authorization header
        auth_header = event.get('headers', {}).get('Authorization', '')
        token = auth_header.replace('Bearer ', '')
        
        # Validate JWT and extract user ID
        jwt_secret = os.environ.get('JWT_SECRET_KEY')
        payload = validate_jwt(token, jwt_secret)
        user_id = payload['userId']
        
        # Parse and validate request body
        body = json.loads(event.get('body', '{}'))
        validate_form_data(body)
        
        # Generate document
        request = GenerationRequest(**body)
        template = get_template(request.form_type)
        document = generate_document(template, request)
        output_url = store_output(document, user_id)
        
        return success_response(output_url)
        
    except AuthenticationError as e:
        return error_response(str(e), 401)
    except ValidationError as e:
        return error_response(str(e), 400)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return error_response("Internal server error", 500)
```

### Example 2: Supporting Module (Production Code)

**File: `tax_document_generation/jwt_validator.py`**

```python
"""
JWT validation module for authentication.
"""

import jwt
from typing import Dict

# ✅ CORRECT: Direct import for local exception
from exceptions import AuthenticationError


def validate_jwt(token: str, secret: str) -> Dict[str, str]:
    """
    Validate a JWT token and return the payload.
    
    Args:
        token: JWT token string
        secret: Secret key for validation
        
    Returns:
        Decoded JWT payload
        
    Raises:
        AuthenticationError: If token is invalid or expired
    """
    if not token or not secret:
        raise AuthenticationError("Token and secret must be non-empty")
    
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        
        if 'userId' not in payload:
            raise AuthenticationError("Token missing required userId claim")
        
        return payload
        
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Token has expired")
    except jwt.InvalidSignatureError:
        raise AuthenticationError("Invalid token signature")
    except jwt.InvalidTokenError:
        raise AuthenticationError("Invalid token format")
```

### Example 3: Test File (Test Code)

**File: `tax_document_generation/tests/test_jwt_validator_unit.py`**

```python
"""
Unit tests for JWT validator module.
"""

import pytest
import jwt
from datetime import datetime, timedelta

# ✅ CORRECT: Package-prefixed imports for tests
from tax_document_generation.jwt_validator import validate_jwt
from tax_document_generation.exceptions import AuthenticationError


class TestValidateJWT:
    """Unit tests for validate_jwt function."""
    
    def test_valid_token_returns_payload(self):
        """Test that a valid JWT token returns the decoded payload."""
        secret = "test-secret-key-at-least-32-characters-long"
        user_id = "user-123"
        payload = {
            "userId": user_id,
            "email": "test@example.com",
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=1)
        }
        token = jwt.encode(payload, secret, algorithm="HS256")
        
        result = validate_jwt(token, secret)
        
        assert result["userId"] == user_id
        assert result["email"] == "test@example.com"
    
    def test_expired_token_raises_authentication_error(self):
        """Test that an expired JWT token raises AuthenticationError."""
        secret = "test-secret-key-at-least-32-characters-long"
        payload = {
            "userId": "user-123",
            "iat": datetime.utcnow() - timedelta(hours=2),
            "exp": datetime.utcnow() - timedelta(hours=1)
        }
        token = jwt.encode(payload, secret, algorithm="HS256")
        
        with pytest.raises(AuthenticationError) as exc_info:
            validate_jwt(token, secret)
        
        assert "expired" in str(exc_info.value).lower()
```

### Example 4: Exception Definitions (Production Code)

**File: `tax_document_generation/exceptions.py`**

```python
"""
Custom exceptions for tax document generation.
"""


class AuthenticationError(Exception):
    """Raised when JWT authentication fails."""
    pass


class ValidationError(Exception):
    """Raised when input validation fails."""
    pass


class TemplateNotFoundError(Exception):
    """Raised when a form template cannot be found."""
    pass


class GenerationError(Exception):
    """Raised when document generation fails."""
    pass


class S3Error(Exception):
    """Raised when S3 operations fail."""
    pass
```

**Note:** This file doesn't import anything from the local package, so there's no import pattern to worry about.

## Working Reference Implementations

The following Lambda functions in this project already use the correct import patterns and serve as reference implementations:

### 1. User Login Lambda

**Location:** `user_login/`

**Key Files:**
- `user_login/app.py` - Main handler with direct imports
- `user_login/user_repository.py` - Uses direct imports for local modules
- `user_login/tests/test_lambda_handler_integration.py` - Uses package-prefixed imports

**Example from `user_login/app.py`:**
```python
from validator import validate_login_data, ValidationError
from user_repository import get_user_by_email, UserNotFoundError, DatabaseError
from password_verifier import verify_password, InvalidCredentialsError
from token_generator import generate_jwt_token
from response_formatter import (
    success_response,
    validation_error_response,
    authentication_error_response,
    internal_error_response
)
```

**Example from `user_login/tests/test_lambda_handler_integration.py`:**
```python
from user_login.app import lambda_handler
from user_login.app import UserNotFoundError, DatabaseError
```

### 2. User Registration Lambda

**Location:** `user_registration/`

**Key Files:**
- `user_registration/app.py` - Main handler with direct imports
- `user_registration/user_repository.py` - Uses direct imports for local modules
- `user_registration/tests/test_lambda_handler_integration.py` - Uses package-prefixed imports

**Example from `user_registration/app.py`:**
```python
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from validator import ValidationError, validate_registration_data
from password_hasher import hash_password
from user_repository import create_user, DuplicateUserError, DatabaseError
from response_formatter import (
    success_response,
    validation_error_response,
    duplicate_user_response,
    internal_error_response
)
```

### 3. Password Recovery Lambda

**Location:** `password_recovery/`

**Key Files:**
- `password_recovery/forgot_password_handler.py` - Uses sys.path pattern
- `password_recovery/reset_password_handler.py` - Uses sys.path pattern

**Example pattern:**
```python
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from input_validator import validate_email, ValidationError
from token_generator import generate_reset_token
from user_repository import get_user_by_email, UserNotFoundError
```

## Common Mistakes

### Mistake 1: Using Relative Imports with Dot Notation

❌ **INCORRECT:**
```python
from .exceptions import ValidationError
from .models import GenerationRequest
```

**Why it fails:** Relative imports require a parent package, which doesn't exist in the Lambda runtime.

✅ **CORRECT:**
```python
from exceptions import ValidationError
from models import GenerationRequest
```

### Mistake 2: Using Package-Prefixed Imports in Production Code

❌ **INCORRECT:**
```python
from tax_document_generation.exceptions import ValidationError
from tax_document_generation.jwt_validator import validate_jwt
```

**Why it fails:** The `tax_document_generation` package doesn't exist in the Lambda runtime.

✅ **CORRECT:**
```python
from exceptions import ValidationError
from jwt_validator import validate_jwt
```

### Mistake 3: Using Direct Imports in Test Code

❌ **INCORRECT (but might work accidentally):**
```python
# In tests/test_jwt_validator.py
from jwt_validator import validate_jwt  # Might work if tests/ is in the same directory
```

**Why it's wrong:** Tests should import from the package to ensure they're testing the actual package structure.

✅ **CORRECT:**
```python
# In tests/test_jwt_validator.py
from tax_document_generation.jwt_validator import validate_jwt
```

### Mistake 4: Mixing Import Styles

❌ **INCORRECT:**
```python
# In production code
from exceptions import ValidationError  # Direct import
from tax_document_generation.models import GenerationRequest  # Package-prefixed import
```

**Why it's wrong:** Inconsistent import styles make the code confusing and the second import will fail.

✅ **CORRECT:**
```python
# In production code
from exceptions import ValidationError
from models import GenerationRequest
```

## Troubleshooting

### Error: "Unable to import module 'app': No module named 'tax_document_generation'"

**Cause:** Production code is using package-prefixed imports.

**Solution:** Change all imports in production code to direct imports:
```python
# Change this:
from tax_document_generation.exceptions import ValidationError

# To this:
from exceptions import ValidationError
```

### Error: "Unable to import module 'app': attempted relative import with no known parent package"

**Cause:** Production code is using relative imports with dot notation.

**Solution:** Change relative imports to direct imports:
```python
# Change this:
from .exceptions import ValidationError

# To this:
from exceptions import ValidationError
```

### Error: "ModuleNotFoundError: No module named 'tax_document_generation'" (in tests)

**Cause:** Tests are using direct imports instead of package-prefixed imports.

**Solution:** Change test imports to use the package prefix:
```python
# Change this:
from jwt_validator import validate_jwt

# To this:
from tax_document_generation.jwt_validator import validate_jwt
```

### Tests Pass But Lambda Fails

**Cause:** Production code is using package-prefixed imports that work in tests but fail in Lambda.

**Solution:** 
1. Review all production code files (excluding `tests/` directory)
2. Change all package-prefixed imports to direct imports
3. Keep test imports unchanged (they should use package-prefixed imports)
4. Rebuild and redeploy: `sam build && sam deploy`

### Verification Commands

**Check for problematic imports in production code:**
```bash
# Search for package-prefixed imports in production code (excluding tests)
grep -r "from tax_document_generation\." tax_document_generation/*.py

# Should return no results (or only test files)
```

**Check for relative imports in production code:**
```bash
# Search for relative imports in production code
grep -r "from \." tax_document_generation/*.py

# Should return no results (or only test files)
```

**Verify Lambda builds successfully:**
```bash
sam build
# Should complete without errors
```

**Test Lambda locally:**
```bash
sam local invoke GenerateTaxDocumentFunction --event test-event.json
# Should not show import errors
```

## Summary

### Quick Reference

| Context | Import Pattern | Example |
|---------|---------------|---------|
| **Production Code** | Direct imports | `from exceptions import ValidationError` |
| **Test Code** | Package-prefixed | `from tax_document_generation.exceptions import ValidationError` |
| **Standard Library** | Normal imports | `import json` |
| **External Packages** | Normal imports | `import boto3` |

### Key Takeaways

1. **Production code** (Lambda functions) must use **direct imports** without package prefixes
2. **Test code** should use **package-prefixed imports** to test the actual package structure
3. **SAM flattens your directory structure** in the Lambda runtime, removing the parent package
4. **Standard library and external packages** are imported normally in both contexts
5. **Reference implementations** exist in `user_login/`, `user_registration/`, and `password_recovery/`

### When in Doubt

- Look at the working Lambda functions (`user_login`, `user_registration`) for examples
- Remember: If it's running in Lambda, use direct imports
- Remember: If it's running in tests, use package-prefixed imports

## Additional Resources

- [AWS SAM Documentation](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/what-is-sam.html)
- [Python Import System](https://docs.python.org/3/reference/import.html)
- [AWS Lambda Execution Environment](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtime-environment.html)

## Related Documentation

- `README.md` - Project setup and deployment guide
- `template.yaml` - SAM template defining Lambda functions
- `IMPORT_FIX_SUMMARY.md` - Summary of import fixes applied to tax_document_generation
