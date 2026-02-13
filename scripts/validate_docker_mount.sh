#!/usr/bin/env bash
#
# validate_docker_mount.sh - Validate Docker can bind-mount SAM build artifacts
#
# Tests whether Docker can successfully create a bind mount from the
# .aws-sam/build/ directory into a container. This verifies that the
# current project path is compatible with Docker's mount mechanism.
#
# Exit codes:
#   0 - Docker mount succeeded (path is compatible)
#   1 - Docker mount failed, Docker not running, or build artifacts missing
#
# Usage:
#   bash scripts/validate_docker_mount.sh
#   make validate-docker-mount
#
# Requirements: 4.1, 4.2, 4.3, 4.4

set -euo pipefail

# --- Color codes ---
RED='\033[0;31m'
YELLOW='\033[0;33m'
GREEN='\033[0;32m'
BOLD='\033[1m'
RESET='\033[0m'

echo -e "${BOLD}Docker Mount Validation${RESET}"
echo "======================="
echo ""

# --- Check Docker is running (Requirement 4.4) ---
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}${BOLD}ERROR:${RESET}${RED} Docker is not running.${RESET}"
    echo ""
    echo "Docker Desktop must be running to validate bind mounts."
    echo ""
    echo -e "${BOLD}Fix:${RESET}"
    echo "  1. Open Docker Desktop"
    echo "  2. Wait for it to finish starting (whale icon stops animating)"
    echo "  3. Re-run this script: ${GREEN}make validate-docker-mount${RESET}"
    exit 1
fi

echo -e "Docker status: ${GREEN}running${RESET}"
echo ""

# --- Check .aws-sam/build/ exists (Requirement 4.1) ---
BUILD_DIR="$(pwd)/.aws-sam/build"

if [[ ! -d "${BUILD_DIR}" ]]; then
    echo -e "${RED}${BOLD}ERROR:${RESET}${RED} Build artifacts not found.${RESET}"
    echo ""
    echo "Expected directory:"
    echo "  ${BUILD_DIR}"
    echo ""
    echo "SAM build artifacts must exist before Docker can mount them."
    echo ""
    echo -e "${BOLD}Fix:${RESET} Run SAM build first:"
    echo "  ${GREEN}sam build --parameter-overrides Environment=local${RESET}"
    exit 1
fi

echo "Build directory:"
echo "  ${BUILD_DIR}"
echo ""

# --- Pick first subdirectory in .aws-sam/build/ as test directory ---
TEST_DIR=""
for entry in "${BUILD_DIR}"/*/; do
    if [[ -d "${entry}" ]]; then
        TEST_DIR="${entry%/}"
        break
    fi
done

if [[ -z "${TEST_DIR}" ]]; then
    echo -e "${RED}${BOLD}ERROR:${RESET}${RED} No Lambda function directories found in build artifacts.${RESET}"
    echo ""
    echo "The build directory exists but contains no function subdirectories:"
    echo "  ${BUILD_DIR}"
    echo ""
    echo -e "${BOLD}Fix:${RESET} Rebuild with SAM:"
    echo "  ${GREEN}sam build --parameter-overrides Environment=local${RESET}"
    exit 1
fi

FUNCTION_NAME="$(basename "${TEST_DIR}")"
echo "Testing mount with: ${FUNCTION_NAME}"
echo "  ${TEST_DIR}"
echo ""

# --- Attempt Docker bind mount (Requirements 4.1, 4.2, 4.3) ---
echo "Running Docker bind-mount test..."
echo ""

DOCKER_OUTPUT=""
DOCKER_EXIT=0
DOCKER_OUTPUT=$(docker run --rm -v "${TEST_DIR}:/var/task:ro" alpine ls /var/task 2>&1) || DOCKER_EXIT=$?

if [[ ${DOCKER_EXIT} -eq 0 ]]; then
    echo -e "${GREEN}${BOLD}SUCCESS:${RESET}${GREEN} Docker mount is working — path is compatible.${RESET}"
    echo ""
    echo "Docker successfully bind-mounted:"
    echo "  ${TEST_DIR} → /var/task"
    echo ""
    echo "Contents visible in container:"
    echo "${DOCKER_OUTPUT}" | sed 's/^/  /'
    echo ""
    echo "You can run ${GREEN}sam local start-api${RESET} from this path."
    exit 0
else
    echo -e "${RED}${BOLD}FAILED:${RESET}${RED} Docker bind mount failed.${RESET}"
    echo ""
    echo "Attempted to mount:"
    echo "  ${TEST_DIR} → /var/task"
    echo ""
    if [[ -n "${DOCKER_OUTPUT}" ]]; then
        echo "Docker error output:"
        echo "${DOCKER_OUTPUT}" | sed 's/^/  /'
        echo ""
    fi
    echo -e "${BOLD}Remediation:${RESET}"
    echo "  The most common cause is spaces in the project path."
    echo "  Docker cannot create bind-mount source paths that contain spaces."
    echo ""
    echo "  1. Check your path: ${GREEN}make check-path${RESET}"
    echo "  2. Fix your path:   ${GREEN}make fix-path${RESET}"
    echo "  3. Then re-run:     ${GREEN}make validate-docker-mount${RESET}"
    exit 1
fi
