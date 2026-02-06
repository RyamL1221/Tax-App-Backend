# API Endpoint Migration Guide

## Overview

The API endpoints have been reorganized with proper categorization for better structure and scalability.

## Endpoint Changes

### Authentication Endpoints (`/auth/*`)

All authentication and user management endpoints now use the `/auth` prefix:

| Old Endpoint | New Endpoint | Description |
|-------------|--------------|-------------|
| `POST /register` | `POST /auth/register` | User registration |
| `POST /login` | `POST /auth/login` | User login |
| `POST /forgot-password` | `POST /auth/forgot-password` | Request password reset |
| `POST /reset-password` | `POST /auth/reset-password` | Reset password with token |

### Document Endpoints (`/documents/*`)

Tax document generation endpoints now use the `/documents` prefix:

| Old Endpoint | New Endpoint | Description |
|-------------|--------------|-------------|
| `POST /generate` | `POST /documents/generate` | Generate tax documents |

### Test Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /hello` | Health check (unchanged) |

## Updated Files

The following files have been updated to reflect the new endpoint structure:

1. **template.yaml** - SAM template with Lambda function event paths
2. **docs/development/postman_collection.json** - Postman collection for API testing

## Migration Steps

### For Local Development

1. **Rebuild SAM**:
   ```bash
   sam build --parameter-overrides Environment=local
   ```

2. **Restart SAM Local API**:
   ```bash
   sam local start-api --docker-network tax-app-network --env-vars env.json
   ```

3. **Test New Endpoints**:
   ```bash
   # Register
   curl -X POST http://localhost:3000/auth/register \
     -H "Content-Type: application/json" \
     -d '{"email":"test@example.com","name":"Test","password":"SecurePass123!"}'
   
   # Login
   curl -X POST http://localhost:3000/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email":"test@example.com","password":"SecurePass123!"}'
   
   # Generate Document (requires JWT token)
   curl -X POST http://localhost:3000/documents/generate \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     -d '{"documentType":"1099-DIV","formData":{...}}'
   ```

### For Production Deployment

1. **Build for Production**:
   ```bash
   sam build --parameter-overrides Environment=production
   ```

2. **Deploy**:
   ```bash
   sam deploy --parameter-overrides Environment=production
   ```

3. **Update Frontend/Client Applications**:
   - Update all API endpoint URLs to use new paths
   - Test all authentication flows
   - Test document generation

## Postman Collection

The Postman collection has been updated with all new endpoint paths. Import the updated collection:

```
docs/development/postman_collection.json
```

All requests in the collection now use the new endpoint structure:
- Authentication requests use `/auth/*` paths
- Document generation requests use `/documents/*` paths
- JWT token is automatically saved and used in subsequent requests

## Benefits of New Structure

1. **Better Organization**: Clear separation between authentication and document operations
2. **Scalability**: Easy to add new endpoints under appropriate categories
3. **API Versioning**: Future-ready for versioning (e.g., `/v1/auth/*`, `/v2/auth/*`)
4. **Clarity**: Endpoint purpose is immediately clear from the path
5. **RESTful Design**: Follows REST API best practices

## Future Endpoint Additions

The new structure makes it easy to add related endpoints:

### Authentication Category
- `GET /auth/profile` - Get user profile
- `PUT /auth/profile` - Update user profile
- `DELETE /auth/account` - Delete user account

### Documents Category
- `GET /documents` - List user's documents
- `GET /documents/{id}` - Get specific document
- `DELETE /documents/{id}` - Delete document
- `GET /documents/{id}/download` - Download document

## Verification

All endpoints have been tested and verified working:

✅ `POST /auth/register` - User registration working
✅ `POST /auth/login` - User login working (returns JWT token)
✅ `POST /auth/forgot-password` - Password recovery working
✅ `POST /auth/reset-password` - Password reset working
✅ `POST /documents/generate` - Document generation working (requires JWT)
✅ `GET /hello` - Health check working

## Troubleshooting

### "Missing Authentication Token" Error

This error typically means:
1. **Wrong endpoint path** - Make sure you're using the new paths with `/auth` or `/documents` prefix
2. **SAM not rebuilt** - Run `sam build --parameter-overrides Environment=local` and restart SAM
3. **SAM not running** - Start SAM with `sam local start-api --docker-network tax-app-network --env-vars env.json`

**Quick Test**:
```bash
curl -X POST http://localhost:3000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}'
```

Expected response: `{"error": "Invalid credentials"}` (401) - This means the endpoint is working!

### Old Endpoints Not Working

If you're still using old endpoint paths, you'll receive a 404 error. Update to the new paths:
- `/register` → `/auth/register`
- `/login` → `/auth/login`
- `/forgot-password` → `/auth/forgot-password`
- `/reset-password` → `/auth/reset-password`
- `/generate` → `/documents/generate`

### SAM Local Not Reflecting Changes

1. Stop SAM local API (Ctrl+C)
2. Rebuild: `sam build --parameter-overrides Environment=local`
3. Restart: `sam local start-api --docker-network tax-app-network --env-vars env.json`

### Postman Collection Not Updated

Re-import the collection from `docs/development/postman_collection.json` to get the latest endpoint paths.

## Questions?

For issues or questions about the endpoint migration, refer to:
- `docs/development/LOCALSTACK_SAM_SETUP.md` - Local development setup
- `docs/development/QUICK_REFERENCE.md` - Quick command reference
- `README.md` - Project overview
