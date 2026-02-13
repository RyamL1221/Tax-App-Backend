#!/usr/bin/env bash
#
# fix_docker_path.sh - Create a symlink from a space-free path to this project
#
# Creates a symbolic link from a Docker-compatible path (no spaces) to the
# current project directory. This allows SAM CLI / Docker to bind-mount
# build artifacts without failing on paths that contain spaces (e.g., the
# iCloud Drive "Mobile Documents" segment).
#
# Usage:
#   bash scripts/fix_docker_path.sh [target_path]
#   make fix-path
#
# Arguments:
#   target_path  Optional. The space-free path for the symlink.
#                Default: ~/Projects/Tax-App-Backend
#
# Exit codes:
#   0 - Symlink created (or already correct) and verified
#   1 - Failure (validation, permission, or verification error)
#
# Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6

set -euo pipefail

# --- Color codes ---
RED='\033[0;31m'
YELLOW='\033[0;33m'
GREEN='\033[0;32m'
BOLD='\033[1m'
RESET='\033[0m'

# --- Default target path ---
DEFAULT_TARGET="${HOME}/Projects/Tax-App-Backend"

# --- Parse arguments ---
TARGET_PATH="${1:-${DEFAULT_TARGET}}"

# Expand ~ if present (handles the case where the argument is passed quoted)
TARGET_PATH="${TARGET_PATH/#\~/${HOME}}"

echo -e "${BOLD}Docker Path Fix — Symlink Creator${RESET}"
echo "==================================="
echo ""
echo "Source (current project):"
echo "  $(pwd)"
echo ""
echo "Target (symlink path):"
echo "  ${TARGET_PATH}"
echo ""

# --- Validate target path has no spaces (Requirement 2.2) ---
case "${TARGET_PATH}" in
    *" "*)
        echo -e "${RED}${BOLD}ERROR:${RESET}${RED} Target path must not contain spaces.${RESET}"
        echo ""
        echo "The target path you specified contains spaces:"
        echo "  ${TARGET_PATH}"
        echo ""
        echo "Please choose a path without spaces, for example:"
        echo "  ~/Projects/Tax-App-Backend"
        exit 1
        ;;
esac

# --- Handle existing target (Requirement 2.3) ---
if [[ -e "${TARGET_PATH}" ]] || [[ -L "${TARGET_PATH}" ]]; then
    # Check if it's already a symlink pointing to our current directory
    if [[ -L "${TARGET_PATH}" ]]; then
        EXISTING_TARGET="$(readlink "${TARGET_PATH}")"
        CURRENT_DIR="$(pwd)"
        if [[ "${EXISTING_TARGET}" == "${CURRENT_DIR}" ]]; then
            echo -e "${GREEN}${BOLD}ALREADY CONFIGURED:${RESET}${GREEN} Symlink already exists and points to this project.${RESET}"
            echo ""
            echo "  ${TARGET_PATH} → ${CURRENT_DIR}"
            echo ""
            echo -e "${BOLD}Next steps:${RESET}"
            echo "  1. cd ${TARGET_PATH}"
            echo "  2. sam build --parameter-overrides Environment=local"
            echo "  3. sam local start-api --docker-network tax-app-network --env-vars env.json"
            echo ""
            echo -e "${YELLOW}Note:${RESET} If using SAM CLI v1.120+ you may need the ${BOLD}--mount-symlinks${RESET} flag:"
            echo "  sam local start-api --mount-symlinks --docker-network tax-app-network --env-vars env.json"
            exit 0
        fi
    fi

    # Target exists but is NOT a symlink to us — warn and prompt
    echo -e "${YELLOW}${BOLD}WARNING:${RESET}${YELLOW} Target path already exists:${RESET}"
    echo "  ${TARGET_PATH}"
    echo ""
    if [[ -L "${TARGET_PATH}" ]]; then
        echo "  It is a symlink pointing to: $(readlink "${TARGET_PATH}")"
    elif [[ -d "${TARGET_PATH}" ]]; then
        echo "  It is an existing directory."
    else
        echo "  It is an existing file."
    fi
    echo ""
    read -rp "Overwrite? (y/N): " CONFIRM
    case "${CONFIRM}" in
        [yY]|[yY][eE][sS])
            echo ""
            echo "Removing existing target..."
            rm -rf "${TARGET_PATH}"
            ;;
        *)
            echo ""
            echo "Aborted. No changes were made."
            exit 1
            ;;
    esac
fi

# --- Create parent directories (Requirement 2.5) ---
PARENT_DIR="$(dirname "${TARGET_PATH}")"
if [[ ! -d "${PARENT_DIR}" ]]; then
    echo "Creating parent directories: ${PARENT_DIR}"
    mkdir -p "${PARENT_DIR}"
fi

# --- Create symlink (Requirement 2.1) ---
echo "Creating symlink..."
if ! ln -s "$(pwd)" "${TARGET_PATH}" 2>/tmp/fix_docker_path_err.$$; then
    # Handle permission errors (Requirement 2.6)
    ERR_MSG="$(cat /tmp/fix_docker_path_err.$$ 2>/dev/null || true)"
    rm -f /tmp/fix_docker_path_err.$$

    if echo "${ERR_MSG}" | grep -qi "permission denied"; then
        echo -e "${RED}${BOLD}ERROR:${RESET}${RED} Permission denied creating symlink.${RESET}"
        echo ""
        echo "  Failed to create: ${TARGET_PATH}"
        echo ""
        echo "Suggestions:"
        echo "  • Check that you have write permission to: ${PARENT_DIR}"
        echo "  • Try a different target path in your home directory"
        echo "  • Run with elevated privileges if needed: sudo bash scripts/fix_docker_path.sh"
    else
        echo -e "${RED}${BOLD}ERROR:${RESET}${RED} Failed to create symlink.${RESET}"
        echo ""
        if [[ -n "${ERR_MSG}" ]]; then
            echo "  ${ERR_MSG}"
        fi
    fi
    rm -f /tmp/fix_docker_path_err.$$
    exit 1
fi
rm -f /tmp/fix_docker_path_err.$$

# --- Verify symlink (Requirement 2.4) ---
echo "Verifying symlink..."
if [[ -f "${TARGET_PATH}/template.yaml" ]]; then
    echo ""
    echo -e "${GREEN}${BOLD}SUCCESS:${RESET}${GREEN} Symlink created and verified.${RESET}"
    echo ""
    echo "  ${TARGET_PATH} → $(pwd)"
    echo ""
    echo -e "${BOLD}Next steps:${RESET}"
    echo "  1. cd ${TARGET_PATH}"
    echo "  2. sam build --parameter-overrides Environment=local"
    echo "  3. sam local start-api --docker-network tax-app-network --env-vars env.json"
    echo ""
    echo -e "${YELLOW}Note:${RESET} If using SAM CLI v1.120+ you may need the ${BOLD}--mount-symlinks${RESET} flag:"
    echo "  sam local start-api --mount-symlinks --docker-network tax-app-network --env-vars env.json"
    exit 0
else
    echo ""
    echo -e "${RED}${BOLD}ERROR:${RESET}${RED} Symlink verification failed.${RESET}"
    echo ""
    echo "  The symlink was created but 'template.yaml' is not accessible"
    echo "  through the new path:"
    echo "    ${TARGET_PATH}/template.yaml"
    echo ""
    echo "  This may indicate the symlink did not resolve correctly."
    echo "  Check that 'template.yaml' exists in the project root."
    exit 1
fi
