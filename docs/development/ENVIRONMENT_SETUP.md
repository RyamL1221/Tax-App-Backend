# Environment Configuration Guide

## Environment Files Overview

This project uses multiple environment files for different purposes:

### 📄 `.env.example` ✅ **COMMIT THIS**
- **Purpose**: Template showing required environment variables
- **Contains**: Placeholder/dummy values only
- **Usage**: Copy to `.env` and fill in real values
- **Safe to commit**: YES - no real credentials

### 📄 `.env.local` ✅ **COMMIT THIS**
- **Purpose**: LocalStack development configuration
- **Contains**: Test credentials (`test`/`test`) for local AWS emulation
- **Usage**: Use for local development with LocalStack
- **Safe to commit**: YES - only contains test credentials

### 📄 `.env` ❌ **NEVER COMMIT**
- **Purpose**: Real AWS credentials for deployment
- **Contains**: Actual AWS access keys and secrets
- **Usage**: Personal/production credentials
- **Safe to commit**: NO - contains real secrets
- **Status**: Already in `.gitignore` ✅

## Setup Instructions

### For New Developers

1. **Create and activate virtual environment:**
   ```bash
   # Create virtual environment
   python3 -m venv venv
   
   # Activate it
   source venv/bin/activate  # macOS/Linux
   # venv\Scripts\activate   # Windows
   ```

2. **Copy the example file:**
   ```bash
   cp .env.example .env
   ```

3. **Fill in your real AWS credentials in `.env`:**
   ```bash
   AWS_ACCESS_KEY_ID=your-real-access-key
   AWS_SECRET_ACCESS_KEY=your-real-secret-key
   ```

4. **For local development, use `.env.local`:**
   ```bash
   source .env.local
   make localstack-start
   ```

### Environment File Usage

| File | Purpose | Commit? | Contains Real Secrets? |
|------|---------|---------|----------------------|
| `.env.example` | Template | ✅ Yes | ❌ No |
| `.env.local` | LocalStack | ✅ Yes | ❌ No (test only) |
| `.env` | Real AWS | ❌ No | ✅ Yes |

## Security Best Practices

✅ **DO:**
- Commit `.env.example` and `.env.local`
- Keep `.env` in `.gitignore`
- Use different credentials for dev/staging/prod
- Rotate credentials regularly
- Use AWS IAM roles when possible

❌ **DON'T:**
- Commit `.env` with real credentials
- Share credentials in chat/email
- Use production credentials for local development
- Hardcode credentials in source code

## Verification

Check what's being tracked by git:

```bash
# This should show .env.example and .env.local
git ls-files | grep env

# This should NOT show .env
git status --ignored | grep .env
```

## Questions?

If you accidentally committed `.env`:
1. Remove it from git: `git rm --cached .env`
2. Rotate your AWS credentials immediately
3. Add `.env` to `.gitignore` (already done)
4. Commit the changes
