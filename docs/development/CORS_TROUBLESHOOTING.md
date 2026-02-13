# CORS Troubleshooting Guide

## Overview

This guide helps you troubleshoot and test CORS (Cross-Origin Resource Sharing) issues in the Tax-App-Backend API. CORS is a security mechanism that allows web applications from one origin to access resources from another origin.

## Quick Reference

### Common CORS Headers

```
Access-Control-Allow-Origin: *
Access-Control-Allow-Headers: Content-Type,Authorization
Access-Control-Allow-Methods: GET,POST,OPTIONS
```

### Preflight Request

Browsers send an OPTIONS request before the actual request to check if CORS is allowed:

```bash
curl -i -X OPTIONS http://localhost:3000/auth/login \
  -H "Origin: http://localhost:3001" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type,Authorization"
```

**Expected Response:**
- Status: 200 OK
- Headers: Access-Control-Allow-Origin, Access-Control-Allow-Methods, Access-Control-Allow-Headers

## Testing CORS Locally

### Prerequisites

1. LocalStack running:
   ```bash
   docker ps | grep localstack
   ```

2. SAM built:
   ```bash
   sam build --parameter-overrides Environment=local
   ```

### Start SAM Local API

```bash
sam local start-api --docker-network tax-app-network --env-vars env.json --port 3000
```

### Test OPTIONS Request (Preflight)

```bash
curl -i -X OPTIONS http://localhost:3000/auth/login \
  -H "Origin: http://localhost:3001" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type,Authorization"
```

**What to check:**
- ✅ Status code is 200
- ✅ `Access-Control-Allow-Origin: *` header present
- ✅ `Access-Control-Allow-Methods` includes POST and OPTIONS
- ✅ `Access-Control-Allow-Headers` includes Content-Type and Authorization
- ✅ Response body is empty

### Test POST Request with CORS

```bash
curl -i -X POST http://localhost:3000/auth/login \
  -H "Content-Type: application/json" \
  -H "Origin: http://localhost:3001" \
  -d '{"email":"test@example.com","password":"TestPass123!"}'
```

**What to check:**
- ✅ Response includes CORS headers (regardless of status code)
- ✅ `Access-Control-Allow-Origin: *` header present
- ✅ `Access-Control-Allow-Headers` includes Authorization
- ✅ Error responses also include CORS headers

### Test from Frontend

1. Start your frontend at http://localhost:3001
2. Start backend at http://localhost:3000 (SAM local)
3. Attempt login from frontend
4. Open browser DevTools → Network tab
5. Check for:
   - OPTIONS request to /auth/login (status 200)
   - POST request to /auth/login (with your expected status)
   - No CORS errors in console

## Common CORS Issues

### Issue 1: Preflight Request Fails

**Symptom:**
```
Access to fetch at 'http://localhost:3000/auth/login' from origin 'http://localhost:3001' 
has been blocked by CORS policy: Response to preflight request doesn't pass access control check: 
It does not have HTTP ok status.
```

**Cause:** OPTIONS request not returning 200 status

**Solution:**
1. Verify Lambda handles OPTIONS method:
   ```python
   if event.get('httpMethod') == 'OPTIONS':
       return {
           'statusCode': 200,
           'headers': {
               'Access-Control-Allow-Origin': '*',
               'Access-Control-Allow-Headers': 'Content-Type,Authorization',
               'Access-Control-Allow-Methods': 'POST,OPTIONS'
           },
           'body': ''
       }
   ```

2. Verify template.yaml has OPTIONS event:
   ```yaml
   Events:
     LoginUserOptions:
       Type: Api
       Properties:
         Path: /auth/login
         Method: options
   ```

### Issue 2: Missing Authorization Header

**Symptom:**
```
Access to fetch at 'http://localhost:3000/auth/login' from origin 'http://localhost:3001' 
has been blocked by CORS policy: Request header field authorization is not allowed by 
Access-Control-Allow-Headers in preflight response.
```

**Cause:** Authorization not in Access-Control-Allow-Headers

**Solution:**
Update CORS headers in response_formatter.py:
```python
def _get_cors_headers() -> Dict[str, str]:
    return {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type,Authorization",  # Include Authorization
        "Access-Control-Allow-Methods": "POST,OPTIONS"
    }
```

### Issue 3: CORS Headers Missing in Error Responses

**Symptom:** Preflight succeeds but actual request fails with CORS error

**Cause:** Error responses don't include CORS headers

**Solution:**
Ensure all response functions use `_get_cors_headers()`:
```python
def error_response(message: str, status_code: int) -> Dict[str, Any]:
    return {
        'statusCode': status_code,
        'headers': _get_cors_headers(),  # Always include CORS headers
        'body': json.dumps({'error': message})
    }
```

### Issue 4: SAM Local Not Handling OPTIONS

**Symptom:** OPTIONS request returns 403 or 500

**Cause:** SAM local may not automatically handle OPTIONS with MOCK integration

**Solution:**
Add explicit OPTIONS handling in Lambda handler (see Issue 1 solution)

## CORS Configuration Locations

### 1. API Gateway (template.yaml)

```yaml
ServerlessRestApi:
  Type: AWS::Serverless::Api
  Properties:
    Cors:
      AllowOrigin: "'*'"
      AllowHeaders: "'Content-Type,Authorization'"
      AllowMethods: "'GET,POST,OPTIONS'"
```

### 2. Lambda Response Headers (response_formatter.py)

```python
def _get_cors_headers() -> Dict[str, str]:
    return {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type,Authorization",
        "Access-Control-Allow-Methods": "POST,OPTIONS"
    }
```

### 3. Lambda Handler (app.py)

```python
# Handle OPTIONS requests for CORS preflight
if event.get('httpMethod') == 'OPTIONS':
    return {
        'statusCode': 200,
        'headers': _get_cors_headers(),
        'body': ''
    }
```

## Testing Checklist

- [ ] LocalStack is running and healthy
- [ ] SAM build completed successfully
- [ ] SAM local API is running on port 3000
- [ ] OPTIONS request returns 200 status
- [ ] OPTIONS response includes all required CORS headers
- [ ] POST request includes CORS headers
- [ ] Error responses include CORS headers
- [ ] Frontend can successfully make requests
- [ ] No CORS errors in browser console

## Production Considerations

### Environment-Specific Origins

For production, consider restricting origins:

```python
import os

def _get_cors_headers() -> Dict[str, str]:
    # Allow specific origin in production
    origin = os.environ.get('ALLOWED_ORIGIN', '*')
    return {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": origin,
        "Access-Control-Allow-Headers": "Content-Type,Authorization",
        "Access-Control-Allow-Methods": "POST,OPTIONS"
    }
```

### Security Best Practices

1. **Restrict Origins**: Use specific origins instead of `*` in production
2. **Limit Methods**: Only allow methods your API actually uses
3. **Limit Headers**: Only allow headers your API needs
4. **Credentials**: If using credentials, set `Access-Control-Allow-Credentials: true`

## Debugging Tools

### Browser DevTools

1. Open DevTools (F12)
2. Go to Network tab
3. Filter by "XHR" or "Fetch"
4. Look for:
   - OPTIONS request (preflight)
   - Actual request (POST, GET, etc.)
   - Response headers
   - Console errors

### curl with Verbose Output

```bash
curl -v -X OPTIONS http://localhost:3000/auth/login \
  -H "Origin: http://localhost:3001" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type,Authorization"
```

### Postman

Postman automatically handles CORS, so it won't show CORS issues. Use browser or curl for CORS testing.

## Related Documentation

- [CORS MDN Documentation](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS)
- [AWS API Gateway CORS](https://docs.aws.amazon.com/apigateway/latest/developerguide/how-to-cors.html)
- [SAM CORS Configuration](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-property-api-corsconfiguration.html)

## Summary

CORS issues are typically caused by:
1. OPTIONS requests not returning 200 status
2. Missing or incorrect CORS headers
3. Headers not matching between preflight and actual request
4. Error responses not including CORS headers

Always ensure:
- Lambda handles OPTIONS method explicitly
- All responses include CORS headers
- Headers are consistent across all response types
- API Gateway CORS configuration matches Lambda headers
