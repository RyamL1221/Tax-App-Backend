# Docker Path Fix — Spaces in Project Path

## Problem

When running `sam local start-api`, all Lambda function invocations fail with **500 Internal Server Error**. The SAM CLI output shows Docker mount errors like:

```
Error: Error while creating mount source path '/Users/ryan/Library/Mobile Documents/com~apple~CloudDocs/Documents/VSCode/Tax-App-Backend/.aws-sam/build/UserLoginFunction': mkdir /Users/ryan/Library/Mobile: permission denied
```

Docker splits the path at the space in `Mobile Documents`, tries to `mkdir /Users/ryan/Library/Mobile`, and fails. Every Lambda container initialization hits this error, making local development impossible.

## Root Cause

The project lives inside **iCloud Drive**, whose macOS filesystem path contains a space:

```
/Users/<you>/Library/Mobile Documents/com~apple~CloudDocs/Documents/...
                     ^^^^^^^^^^^^^^^^
                     Space here breaks Docker bind mounts
```

Docker on macOS cannot create bind-mount source paths that contain spaces. When SAM CLI tells Docker to mount `.aws-sam/build/<FunctionName>` into a Lambda container, Docker's internal `mkdir` misinterprets the space as a path separator and fails.

This affects **any** project path with spaces, but iCloud Drive is the most common cause because `Mobile Documents` is baked into the iCloud filesystem structure.

## Quick Fix

Three steps to get local development working:

### Step 1: Check Your Path

```bash
make check-path
```

This runs the diagnostic script and tells you whether your current path is Docker-compatible. If you see **INCOMPATIBLE**, continue to Step 2.

### Step 2: Create a Symlink

```bash
make fix-path
```

This creates a symbolic link from `~/Projects/Tax-App-Backend` (no spaces) pointing to your actual project directory. The symlink approach:

- **Does not move any files** — your project stays in iCloud Drive
- **Preserves iCloud sync** — the symlink points to the real directory, so iCloud continues syncing normally
- **Requires no code changes** — everything works the same, just from a different path

To use a custom target path instead of the default:

```bash
bash scripts/fix_docker_path.sh ~/dev/tax-app
```

The target path must not contain spaces.

### Step 3: Work From the Symlinked Path

```bash
cd ~/Projects/Tax-App-Backend
sam build --parameter-overrides Environment=local
sam local start-api --docker-network tax-app-network --env-vars env.json
```

**Important:** You must `cd` into the symlinked path before running SAM commands. Running from the original iCloud path will still fail.

## SAM CLI `--mount-symlinks` Flag

SAM CLI **v1.120+** introduced security changes in response to [CVE-2025-3047](https://github.com/aws/aws-sam-cli/security) and [CVE-2025-3048](https://github.com/aws/aws-sam-cli/security) that changed how symlinks are handled during Docker mounts. By default, newer SAM CLI versions may refuse to follow symlinks when mounting build artifacts into containers.

If you see errors about symlinks not being resolved or mount paths not matching after applying the fix, add the `--mount-symlinks` flag:

```bash
sam local start-api --mount-symlinks --docker-network tax-app-network --env-vars env.json
```

This flag tells SAM CLI to resolve symlinks on the host before passing paths to Docker, restoring the previous behavior.

**Check your SAM CLI version:**

```bash
sam --version
```

- **v1.119 and earlier:** No flag needed — symlinks are followed by default.
- **v1.120 and later:** Add `--mount-symlinks` if you get symlink-related mount errors.

## Troubleshooting

### Docker Desktop Is Not Running

**Symptom:** `make validate-docker-mount` reports "Docker is not running."

**Fix:**
1. Open Docker Desktop
2. Wait for it to finish starting (the whale icon stops animating)
3. Re-run the command

### Build Artifacts Are Missing

**Symptom:** `make validate-docker-mount` reports "Build artifacts not found."

**Fix:** Run SAM build first:

```bash
sam build --parameter-overrides Environment=local
```

Then re-run validation:

```bash
make validate-docker-mount
```

### Permission Denied Creating Symlink

**Symptom:** `make fix-path` fails with "Permission denied."

**Fix:**
- Ensure you have write permission to the parent directory (default: `~/Projects/`)
- Try a different target path: `bash scripts/fix_docker_path.sh ~/dev/Tax-App-Backend`
- As a last resort, use `sudo`: `sudo bash scripts/fix_docker_path.sh`

### Symlink Already Exists

**Symptom:** `make fix-path` warns that the target path already exists.

**Fix:** The script will prompt you to confirm overwriting. If the existing symlink already points to your project, the script detects this and reports "ALREADY CONFIGURED" — no action needed.

### SAM Still Fails After Fix

**Symptom:** You created the symlink but `sam local start-api` still shows mount errors.

**Checklist:**
1. **Are you in the symlinked path?** Run `pwd` — it should show `~/Projects/Tax-App-Backend`, not the iCloud path.
2. **Did you rebuild?** Run `sam build --parameter-overrides Environment=local` from the symlinked path.
3. **SAM CLI v1.120+?** Add `--mount-symlinks` flag (see section above).
4. **Validate the mount:** Run `make validate-docker-mount` to test Docker directly.

### Verifying the Fix End-to-End

Run all three checks in sequence:

```bash
cd ~/Projects/Tax-App-Backend
make check-path              # Should report COMPATIBLE
make validate-docker-mount   # Should report SUCCESS (requires Docker + build artifacts)
sam local start-api --docker-network tax-app-network --env-vars env.json
```

## How It Works

The symlink approach is simple and non-invasive:

```
~/Projects/Tax-App-Backend  (symlink, no spaces)
    │
    └──→  /Users/you/Library/Mobile Documents/com~apple~CloudDocs/.../Tax-App-Backend  (real directory)
```

- **Docker sees:** `~/Projects/Tax-App-Backend/.aws-sam/build/...` — a path with no spaces, so bind mounts succeed.
- **iCloud sees:** The real directory at its original location — sync continues normally.
- **Git sees:** No difference — symlinks are transparent to Git operations.
- **Your editor sees:** You can open either path. Both point to the same files.

The symlink is a standard Unix symbolic link created with `ln -s`. It has zero performance overhead and no impact on file operations.

## Available Make Targets

| Target | Command | Description |
|--------|---------|-------------|
| `make check-path` | `scripts/check_docker_path.sh` | Check if current path is Docker-compatible |
| `make fix-path` | `scripts/fix_docker_path.sh` | Create symlink to a space-free path |
| `make validate-docker-mount` | `scripts/validate_docker_mount.sh` | Test Docker bind mount with build artifacts |

## Related Documentation

- [LocalStack & SAM Setup](LOCALSTACK_SAM_SETUP.md) — Local development environment setup
- [Quick Reference](QUICK_REFERENCE.md) — Common commands and patterns
- [SAM Build Guidelines](../../.kiro/steering/sam-build-guidelines.md) — Build troubleshooting
