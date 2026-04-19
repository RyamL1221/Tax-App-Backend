# Password Reset Flow — Frontend Spec

## Overview

The backend sends a password reset email containing a link like:

```
https://your-frontend.com/reset-password?token=<base64-encoded-token>
```

The frontend needs two pages and two API calls.

## API Base URLs

| Environment | API Base URL |
|---|---|
| Local | `http://localhost:3000` |
| Dev | `https://85w8zp9zpj.execute-api.us-east-1.amazonaws.com/Prod` |

---

## 1. Forgot Password Page (`/forgot-password`)

User enters their email to request a reset link.

### Request

```
POST /auth/forgot-password
Content-Type: application/json

{ "email": "user@example.com" }
```

### Responses

| Status | Body | Meaning |
|---|---|---|
| `200` | `{"message": "If an account exists with that email, a password reset link has been sent."}` | Always returned, even if email doesn't exist (prevents enumeration) |
| `400` | `{"error": "ValidationError", "message": "..."}` | Missing or invalid email |
| `429` | `{"error": "RateLimitExceeded", "message": "Too many requests. Please try again later."}` | Rate limited. Check `Retry-After` header (seconds) |
| `500` | `{"error": "InternalError", "message": "An unexpected error occurred. Please try again later."}` | Server error |

### UX Notes

- Always show a success message on 200 ("Check your email"), never reveal whether the account exists
- Handle 429 with a countdown or "try again later" message

---

## 2. Reset Password Page (`/reset-password?token=...`)

User lands here from the email link. Read `token` from the query string.

### Request

```
POST /auth/reset-password
Content-Type: application/json

{
  "token": "<token-from-query-string>",
  "new_password": "NewSecurePass123!"
}
```

### Password Requirements (validate client-side too)

- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit
- At least one special character (any non-alphanumeric)

### Responses

| Status | Body | Meaning |
|---|---|---|
| `200` | `{"message": "Password has been successfully reset."}` | Success — redirect to login |
| `400` | `{"error": "ValidationError", "message": "..."}` | Missing fields or password doesn't meet requirements. The `message` field has the specific issue (e.g., "Password must contain at least one uppercase letter") |
| `401` | `{"error": "InvalidToken", "message": "The reset token is invalid, expired, or has already been used."}` | Bad, expired, or used token — show error, link back to forgot password |
| `500` | `{"error": "InternalError", "message": "An unexpected error occurred. Please try again later."}` | Server error |

### Possible Validation Messages (400)

These are the exact strings the backend returns:

- `"Reset token is required"`
- `"New password is required"`
- `"Reset token must be a string"`
- `"New password must be a string"`
- `"Invalid request format"`
- `"Invalid JSON format"`
- `"Password must be at least 8 characters"`
- `"Password must contain at least one uppercase letter"`
- `"Password must contain at least one lowercase letter"`
- `"Password must contain at least one digit"`
- `"Password must contain at least one special character"`

### UX Notes

- If no `token` query param is present, show an error or redirect to `/forgot-password`
- On 200, redirect to `/login` with a success toast
- On 401, show "This link has expired or already been used" with a link to request a new one
- Tokens expire after 1 hour

---

## Flow Summary

```
User clicks "Forgot Password"
  → Frontend: GET /forgot-password (page)
  → User enters email, submits
  → Frontend: POST /auth/forgot-password { email }
  → Show "Check your email" message

User clicks link in email
  → Frontend: GET /reset-password?token=abc123 (page)
  → User enters new password, submits
  → Frontend: POST /auth/reset-password { token, new_password }
  → On success: redirect to /login
```

---

## CORS

The backend returns these headers on all responses:

```
Access-Control-Allow-Origin: <configured per environment>
Access-Control-Allow-Headers: Content-Type,Authorization
Access-Control-Allow-Methods: POST,OPTIONS
```

The frontend origin is already whitelisted per environment:

| Environment | Allowed Origin |
|---|---|
| Local | `http://localhost:3001` |
| Dev | `https://tax-app-git-dev-ryaml1221-ryan.vercel.app` |
| Prod | `https://the-tax-app.vercel.app` |
