# Tax App Backend API Documentation for Frontend Integration

## Overview

This document provides comprehensive API documentation for the Tax App Backend, designed specifically for frontend developers who need to integrate with our authentication and tax document generation services. The backend is built using AWS Lambda functions with API Gateway, providing a RESTful API with JWT-based authentication. All endpoints return JSON responses and support CORS for cross-origin requests from your frontend application.

## Base URL and Environment

For local development, the API is available at `http://localhost:3000`. All endpoints use standard HTTP methods (POST, GET) and require appropriate headers. The API follows RESTful conventions with clear endpoint categorization: authentication endpoints are prefixed with `/auth`, document generation endpoints with `/documents`, and a health check endpoint at `/hello`. All responses include CORS headers allowing requests from any origin during development.

## Authentication Flow

The authentication system uses JWT (JSON Web Tokens) for stateless authentication. When a user successfully logs in, the API returns a JWT token that must be included in the Authorization header for all protected endpoints. The token contains the user's ID and email, and is signed with a secure secret key. Tokens expire after 24 hours, after which the user must log in again. There is no logout endpoint because JWT authentication is stateless - simply discard the token on the client side to log out.

## API Endpoints

### User Registration

**Endpoint:** `POST /auth/register`

**Purpose:** Create a new user account in the system.

**Authentication Required:** No

**Request Headers:** Content-Type must be set to `application/json`.

**Request Body Schema:** The request body must be a JSON object containing three required fields. The `email` field must be a valid email address format and will be used as the unique identifier for the user account. The `name` field should contain the user's full name as a string. The `password` field must be at least 8 characters long and will be securely hashed using bcrypt before storage. Here's the complete schema: `{"email": "string (required, valid email format)", "name": "string (required, max 100 characters)", "password": "string (required, min 8 characters)"}`.

**Example Request:**
```json
{
  "email": "user@example.com",
  "name": "John Doe",
  "password": "SecurePass123!"
}
```

**Success Response (201 Created):** When registration is successful, the API returns a 201 status code with a JSON body containing a success message and the registered email address: `{"message": "User registered successfully", "email": "user@example.com"}`.

**Error Responses:** If the email is already registered, you'll receive a 409 Conflict status with `{"error": "User already exists"}`. For validation errors such as invalid email format or password too short, expect a 400 Bad Request with `{"error": "Validation error message"}`. Any server errors return 500 Internal Server Error with `{"error": "Internal server error"}`.

**Security Notes:** Passwords are hashed using bcrypt with 12 rounds before storage. The API never returns password hashes in responses. Email addresses are case-insensitive and stored in lowercase.



### User Login

**Endpoint:** `POST /auth/login`

**Purpose:** Authenticate a user and receive a JWT token for accessing protected endpoints.

**Authentication Required:** No

**Request Headers:** Content-Type must be set to `application/json`.

**Request Body Schema:** The login request requires two fields: `email` (string, the user's registered email address) and `password` (string, the user's password). Both fields are required. The schema is: `{"email": "string (required)", "password": "string (required)"}`.

**Example Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Success Response (200 OK):** Upon successful authentication, the API returns a JSON object containing a JWT token, the user's email, and their user ID. The token should be stored securely (such as in localStorage or a secure cookie) and included in the Authorization header for subsequent requests to protected endpoints. The response format is: `{"token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...", "email": "user@example.com", "userId": "user@example.com"}`. The token is a long string (typically 200+ characters) that encodes the user's information and expiration time.

**Error Responses:** If the email doesn't exist or the password is incorrect, you'll receive a 401 Unauthorized status with `{"error": "Invalid credentials"}`. This generic message prevents user enumeration attacks. For validation errors like missing fields, expect 400 Bad Request with `{"error": "Validation error message"}`. Server errors return 500 with `{"error": "Internal server error"}`.

**Security Notes:** The API uses constant-time password comparison to prevent timing attacks. Failed login attempts are logged but there's currently no rate limiting (though this may be added in future versions). The JWT token contains the user's email and ID, issued timestamp, and expiration timestamp. Tokens are signed using HS256 algorithm and expire after 24 hours.

**Token Usage:** To use the token in subsequent requests, include it in the Authorization header as a Bearer token: `Authorization: Bearer YOUR_JWT_TOKEN_HERE`. The token must be included exactly as returned, without modification.



### Forgot Password

**Endpoint:** `POST /auth/forgot-password`

**Purpose:** Initiate the password reset process by sending a reset link to the user's email.

**Authentication Required:** No

**Request Headers:** Content-Type must be set to `application/json`.

**Request Body Schema:** The request requires only the user's email address: `{"email": "string (required, valid email format)"}`.

**Example Request:**
```json
{
  "email": "user@example.com"
}
```

**Success Response (200 OK):** The API always returns the same success message regardless of whether the email exists in the system. This prevents user enumeration attacks where an attacker could determine which email addresses are registered. The response is: `{"message": "If an account exists with that email, a password reset link has been sent."}`. If the email exists, a reset token is generated and an email is sent to the user with a reset link. The token is valid for 1 hour.

**Rate Limiting:** This endpoint is rate-limited to prevent abuse. Users can request a maximum of 5 password resets per hour from the same IP address. If the limit is exceeded, you'll receive a 429 Too Many Requests status with `{"error": "Too many requests. Please try again later."}`.

**Error Responses:** For validation errors like invalid email format, expect 400 Bad Request with `{"error": "Invalid email format"}`. Server errors return 500 with `{"error": "Internal server error"}`.

**Security Notes:** Reset tokens are cryptographically secure random strings that are hashed before storage using SHA-256. The plain token is sent via email, but only the hash is stored in the database. Tokens expire after 1 hour and can only be used once. The email contains a link in the format: `http://your-frontend-url/reset-password?token=RESET_TOKEN_HERE`.

**Email Configuration:** In local development, emails are logged to the console rather than actually sent. In production, emails are sent via AWS SES from the configured FROM_EMAIL address.



### Reset Password

**Endpoint:** `POST /auth/reset-password`

**Purpose:** Complete the password reset process using a valid reset token.

**Authentication Required:** No (uses reset token instead)

**Request Headers:** Content-Type must be set to `application/json`.

**Request Body Schema:** The request requires two fields: the reset token received via email and the new password. The schema is: `{"token": "string (required, the reset token from email)", "newPassword": "string (required, min 8 characters)"}`.

**Example Request:**
```json
{
  "token": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
  "newPassword": "NewSecurePass123!"
}
```

**Success Response (200 OK):** When the password is successfully reset, the API returns: `{"message": "Password reset successfully"}`. The reset token is marked as used and cannot be reused. All existing JWT tokens for this user are invalidated by incrementing the user's session version number, forcing the user to log in again with their new password.

**Error Responses:** If the token is invalid, expired, or already used, you'll receive a 400 Bad Request with `{"error": "Invalid or expired reset token"}`. For validation errors like password too short, expect 400 with `{"error": "Password must be at least 8 characters"}`. Server errors return 500 with `{"error": "Internal server error"}`.

**Security Notes:** The new password is hashed using bcrypt with 12 rounds before storage. The reset token is validated by comparing its SHA-256 hash against stored hashes. Tokens can only be used once - attempting to reuse a token will fail. The session version increment ensures that any existing JWT tokens become invalid, requiring the user to log in again. This prevents unauthorized access if someone had obtained the user's old JWT token.

**Token Expiration:** Reset tokens expire after 1 hour from creation. The expiration is checked before allowing the password reset. Expired tokens cannot be used even if they haven't been marked as used.



### Generate Tax Document

**Endpoint:** `POST /documents/generate`

**Purpose:** Generate a filled IRS Form 1099-DIV PDF document with user-provided data.

**Authentication Required:** Yes (JWT token required)

**Request Headers:** You must include two headers: `Content-Type: application/json` and `Authorization: Bearer YOUR_JWT_TOKEN`. The JWT token must be obtained from a successful login.

**Request Body Schema:** The request body must contain two top-level fields: `documentType` (currently only "1099-DIV" is supported) and `formData` (an object containing all the form field values). The complete schema is: `{"documentType": "string (required, must be '1099-DIV')", "formData": "object (required, see detailed schema below)"}`.

**Form Data Schema:** The formData object contains all the fields for the 1099-DIV form. Required fields are: `calendarYear` (string, 4-digit year like "2024"), `payerName` (string, max 100 characters), `payerTIN` (string, format XX-XXXXXXX), `recipientName` (string, max 100 characters), `recipientTIN` (string, format XXX-XX-XXXX), and `totalOrdinaryDividends` (decimal as string, like "1000.00"). All other fields are optional.

**Optional Form Fields:** The form supports numerous optional fields including: `voided` (boolean, marks form as voided), `corrected` (boolean, marks form as corrected), `secondTinNotification` (boolean, indicates second TIN notification), payer address fields (`payerStreetAddress`, `payerCity`, `payerState`, `payerCountry`, `payerZip`, `payerTelephoneNumber`), recipient address fields (`recipientStreetAddress`, `recipientCity`, `recipientState`, `recipientCountry`, `recipientZip`), dividend fields (`qualifiedDividends`), capital gains fields (`totalCapitalGainDistributions`, `unrecapturedSection1250Gain`, `section1202Gain`, `collectibles28Gain`, `section897OrdinaryDividends`, `section897CapitalGain`), distribution fields (`nondividendDistributions`, `cashLiquidationDistributions`, `noncashLiquidationDistributions`), tax fields (`federalIncomeTaxWithheld`, `foreignTaxPaid`, `foreignCountry`), other fields (`section199ADividends`, `investmentExpenses`, `fatcaFilingRequirement`, `exemptInterestDividends`, `specifiedPrivateActivityBondInterest`), state tax fields for up to two states (`state`, `stateIdentificationNumber`, `stateTaxWithheld`, `state2`, `stateIdentificationNumber2`, `stateTaxWithheld2`), and `accountNumber`.

**Minimal Example Request:**
```json
{
  "documentType": "1099-DIV",
  "formData": {
    "calendarYear": "2024",
    "payerName": "Example Corporation",
    "payerTIN": "12-3456789",
    "recipientName": "John Doe",
    "recipientTIN": "123-45-6789",
    "totalOrdinaryDividends": "1000.00"
  }
}
```

**Complete Example Request:**
```json
{
  "documentType": "1099-DIV",
  "formData": {
    "calendarYear": "2024",
    "corrected": true,
    "payerName": "Example Investment Corporation",
    "payerTIN": "12-3456789",
    "payerStreetAddress": "123 Wall Street",
    "payerCity": "New York",
    "payerState": "NY",
    "payerZip": "10005",
    "payerTelephoneNumber": "(555) 123-4567",
    "recipientName": "John Doe",
    "recipientTIN": "123-45-6789",
    "recipientStreetAddress": "456 Oak Avenue",
    "recipientCity": "Los Angeles",
    "recipientState": "CA",
    "recipientZip": "90001",
    "totalOrdinaryDividends": "1000.00",
    "qualifiedDividends": "800.00",
    "totalCapitalGainDistributions": "500.00",
    "federalIncomeTaxWithheld": "150.00",
    "section199ADividends": "300.00",
    "foreignTaxPaid": "75.00",
    "foreignCountry": "United Kingdom",
    "state": "NY",
    "stateIdentificationNumber": "12-3456789",
    "stateTaxWithheld": "50.00",
    "accountNumber": "1234567890"
  }
}
```



**Success Response (200 OK):** When the document is successfully generated, the API returns a JSON object containing the job ID, status, and S3 keys for the template and output. The response format is: `{"jobId": "unique-job-id", "status": "COMPLETED", "documentType": "1099-DIV", "templateKey": "templates/1099-DIV.pdf", "outputKey": "outputs/1099-DIV-job-id.pdf", "message": "Document generated successfully"}`. The outputKey can be used to retrieve the generated PDF from S3 storage.

**Error Responses:** If the JWT token is missing or invalid, you'll receive a 401 Unauthorized with `{"error": "Unauthorized"}`. For validation errors like missing required fields or invalid field formats, expect 400 Bad Request with a descriptive error message such as `{"error": "Missing required field: calendarYear"}` or `{"error": "Invalid TIN format"}`. If the document type is not supported, you'll get 400 with `{"error": "Unsupported document type"}`. Server errors during PDF generation return 500 with `{"error": "Internal server error"}`.

**Field Validation Rules:** All monetary values must be provided as strings with up to 2 decimal places (e.g., "1000.00"). TIN fields must follow specific formats: payer TIN uses EIN format (XX-XXXXXXX) and recipient TIN uses SSN format (XXX-XX-XXXX), though hyphens are optional. State codes must be valid two-letter U.S. state abbreviations in uppercase. The calendar year must be a 4-digit year string. Boolean fields accept true or false values.

**Multi-Copy Generation:** The API automatically generates all four required copies of the 1099-DIV form: Copy A (for IRS), Copy 1 (for recipient's state tax return), Copy 2 (for recipient's records), and Copy B (for recipient's federal tax return). All copies are included in a single PDF file with the data properly filled on each copy.

**PDF Output Details:** The generated PDF is stored in S3 and contains all four copies of the form with your data filled in. The PDF uses the official IRS 1099-DIV template and ensures all fields are visible in Adobe Reader, Preview, and Chrome PDF viewer. Checkboxes (voided, corrected, secondTinNotification, fatcaFilingRequirement) are rendered as static graphics for maximum compatibility. The calendar year appears on all four copies as required by IRS regulations.

**Job Tracking:** Each document generation request creates a job record in the database with a unique job ID. The job tracks the status (PENDING, RUNNING, COMPLETED, FAILED), timestamps, and S3 keys. You can use the job ID for future reference or to implement job status polling if needed.



### Health Check

**Endpoint:** `GET /hello`

**Purpose:** Verify that the API is running and accessible.

**Authentication Required:** No

**Request Headers:** None required.

**Success Response (200 OK):** Returns a simple JSON object: `{"message": "hello world"}`. This endpoint is useful for health checks, monitoring, and verifying that your frontend can reach the backend API.

**Error Responses:** If the API is down or unreachable, you'll receive a network error or timeout. This endpoint should always return 200 if the API is functioning.

## Common Response Headers

All API responses include CORS headers to allow cross-origin requests from your frontend application. The headers are: `Access-Control-Allow-Origin: *` (allows requests from any origin), `Access-Control-Allow-Headers: Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token` (specifies allowed request headers), `Access-Control-Allow-Methods: GET,POST,OPTIONS` (specifies allowed HTTP methods), and `Content-Type: application/json` (all responses are JSON formatted).

## Error Handling Best Practices

When integrating with the API, implement proper error handling for different status codes. For 400 Bad Request errors, display the error message to the user as it contains specific validation feedback. For 401 Unauthorized errors, redirect the user to the login page and clear any stored JWT tokens. For 409 Conflict errors (like duplicate email during registration), inform the user that the resource already exists. For 429 Too Many Requests errors, implement exponential backoff and inform the user to try again later. For 500 Internal Server Error responses, display a generic error message and log the error for debugging. Always check the response status code before parsing the JSON body.

## Authentication Token Management

Store the JWT token securely after successful login. For web applications, localStorage or sessionStorage are common choices, though secure HTTP-only cookies provide better security. Include the token in the Authorization header for all protected endpoints using the format: `Authorization: Bearer YOUR_TOKEN_HERE`. Implement token expiration handling by checking for 401 responses and redirecting to login when the token expires. Tokens expire after 24 hours, so you may want to implement automatic token refresh or prompt the user to log in again. When the user logs out, simply remove the token from storage - there's no logout endpoint because JWT authentication is stateless.

## Field Naming Conventions

All field names in the API use camelCase convention for consistency. Payer-related fields are prefixed with "payer" (e.g., payerName, payerTIN, payerCity). Recipient-related fields are prefixed with "recipient" (e.g., recipientName, recipientTIN, recipientCity). This makes it easy to identify which party each field belongs to. Monetary values are named descriptively (e.g., totalOrdinaryDividends, qualifiedDividends, federalIncomeTaxWithheld). Boolean fields use descriptive names without "is" prefix (e.g., voided, corrected, fatcaFilingRequirement).



## Data Type Guidelines

Understanding the correct data types for each field is crucial for successful API integration. String fields should be sent as JSON strings enclosed in double quotes. This includes text fields like names and addresses, as well as formatted fields like TINs and phone numbers. Decimal fields representing monetary values must be sent as strings (not numbers) with up to 2 decimal places, for example "1000.00" not 1000.00. This prevents floating-point precision issues. Boolean fields should be sent as JSON boolean values (true or false) without quotes. The calendar year field, despite representing a number, should be sent as a string like "2024" to maintain consistency with IRS form requirements.

## Address Field Formats

The API supports two formats for address fields to maintain backward compatibility. The new recommended format uses separate fields for each component: payerCity, payerState, and payerZip as individual fields. For example: `{"payerCity": "New York", "payerState": "NY", "payerZip": "10005"}`. The old deprecated format combines city, state, and ZIP in a single field: `{"payerCity": "New York, NY 10005"}`. While both formats are currently accepted, the old format is deprecated and will be removed in a future version. A deprecation warning will be logged when the old format is detected. Please use the new separate format for all new implementations. The same applies to recipient address fields.

## Multi-State Tax Reporting

The 1099-DIV form supports reporting state tax information for up to two states, which is useful when dividends are subject to tax withholding in multiple states. For the first state, use the fields: state, stateIdentificationNumber, and stateTaxWithheld. For a second state, use the fields with a "2" suffix: state2, stateIdentificationNumber2, and stateTaxWithheld2. Each state's fields should be provided together as a set. If only one state is applicable, only use the first set of fields without the "2" suffix. Both states are optional - you can omit state tax information entirely if not applicable. Example: `{"state": "NY", "stateIdentificationNumber": "12-3456789", "stateTaxWithheld": "50.00", "state2": "CA", "stateIdentificationNumber2": "98-7654321", "stateTaxWithheld2": "25.00"}`.

## Checkbox Fields

Several fields in the 1099-DIV form are checkboxes that accept boolean values. The voided field marks the form as voided, indicating it should be disregarded. The corrected field marks the form as a correction of a previously filed form. The secondTinNotification field indicates that the IRS has notified the payer twice within three calendar years that the payee provided an incorrect TIN, triggering backup withholding requirements. The fatcaFilingRequirement field indicates FATCA filing requirement. All checkbox fields are optional and default to false if not provided. While both voided and corrected can technically be set to true simultaneously, this may not be valid according to IRS guidelines and will generate a warning.

## Validation Error Messages

The API provides specific validation error messages to help you identify and fix issues. Common validation errors include: "Missing required field: fieldName" when a required field is not provided, "Invalid email format" when the email doesn't match the expected pattern, "Password must be at least 8 characters" when the password is too short, "Invalid TIN format" when TIN fields don't match the expected format (XX-XXXXXXX for payer, XXX-XX-XXXX for recipient), "Invalid state code" when a state field doesn't contain a valid two-letter abbreviation, "Unsupported document type" when documentType is not "1099-DIV", and "Invalid calendar year format" when calendarYear is not a 4-digit year string. Always display these error messages to the user to help them correct their input.



## Rate Limiting

Currently, only the forgot password endpoint implements rate limiting to prevent abuse. Users can request a maximum of 5 password resets per hour from the same IP address. If this limit is exceeded, the API returns a 429 Too Many Requests status with the message "Too many requests. Please try again later." Your frontend should handle this gracefully by displaying an appropriate message to the user and implementing exponential backoff before retrying. Other endpoints do not currently have rate limiting, but this may be added in future versions, so implement your frontend to handle 429 responses on all endpoints.

## Security Considerations

When integrating with the API, follow these security best practices. Never log or display JWT tokens in your application - they should be treated as sensitive credentials. Store tokens securely and transmit them only over HTTPS in production. Implement proper CSRF protection if storing tokens in cookies. Always validate user input on the frontend before sending to the API, even though the backend also validates. Never store passwords in localStorage or any client-side storage. Clear tokens from storage when the user logs out or when you receive a 401 Unauthorized response. Implement proper error handling to avoid leaking sensitive information in error messages. Use HTTPS for all API requests in production to prevent token interception.

## Testing the API

For testing during development, you can use tools like curl, Postman, or your browser's developer tools. Here are some example curl commands. To register a new user: `curl -X POST http://localhost:3000/auth/register -H "Content-Type: application/json" -d '{"email":"test@example.com","name":"Test User","password":"SecurePass123!"}'`. To login: `curl -X POST http://localhost:3000/auth/login -H "Content-Type: application/json" -d '{"email":"test@example.com","password":"SecurePass123!"}'`. To generate a document (replace YOUR_TOKEN with actual token): `curl -X POST http://localhost:3000/documents/generate -H "Content-Type: application/json" -H "Authorization: Bearer YOUR_TOKEN" -d '{"documentType":"1099-DIV","formData":{"calendarYear":"2024","payerName":"Test Corp","payerTIN":"12-3456789","recipientName":"John Doe","recipientTIN":"123-45-6789","totalOrdinaryDividends":"1000.00"}}'`. To check API health: `curl http://localhost:3000/hello`.

## Postman Collection

A complete Postman collection with all endpoints and example requests is available at `docs/development/postman_collection.json`. Import this collection into Postman for easy API testing. The collection includes pre-configured requests for all endpoints, environment variables for the base URL and JWT token, and example request bodies for all scenarios. The collection automatically saves the JWT token from login responses and uses it in subsequent requests to protected endpoints.

## Future Enhancements

The API is actively being developed and future versions may include additional features. Planned enhancements include: support for additional tax form types beyond 1099-DIV, job status polling endpoint to check document generation progress, document retrieval endpoint to download generated PDFs directly from the API, user profile management endpoints (get profile, update profile, delete account), rate limiting on all endpoints for better security, token refresh endpoint to extend token expiration without requiring re-login, and webhook support for asynchronous document generation notifications. Check the API documentation regularly for updates and new features.

## Support and Troubleshooting

If you encounter issues while integrating with the API, first check that you're using the correct endpoint URLs with the proper HTTP methods. Verify that all required fields are included in your requests with the correct data types. Ensure JWT tokens are included in the Authorization header for protected endpoints using the Bearer scheme. Check the API response status codes and error messages for specific guidance. Review the example requests in this documentation to ensure your request format matches. For persistent issues, check the backend logs for detailed error information. The API logs all requests and errors with timestamps and context for debugging.

## Conclusion

This documentation provides everything you need to integrate your frontend application with the Tax App Backend API. The API follows RESTful conventions, uses standard HTTP status codes, and provides clear error messages to help you build a robust integration. All endpoints support CORS for cross-origin requests, making it easy to develop and test your frontend locally. The JWT-based authentication system is stateless and secure, requiring only that you store and transmit the token properly. For tax document generation, the API handles all the complexity of PDF form filling, multi-copy generation, and IRS compliance, allowing you to focus on building a great user experience. Start with the minimal examples provided and gradually add optional fields as needed for your use case.

