#!/usr/bin/env bash
#
# check_docker_path.sh - Diagnose Docker mount path compatibility
#
# Inspects the current working directory for path segments that are
# incompatible with Docker bind mounts on macOS. Specifically checks
# for spaces in the path and iCloud Drive path segments.
#
# Exit codes:
#   0 - Path is Docker-compatible (no spaces)
#   1 - Path is Docker-incompatible (contains spaces or pwd failed)
#
# Usage:
#   bash scripts/check_docker_path.sh
#   make check-path
#
# Requirements: 1.1, 1.2, 1.3, 1.4, 1.5

set -euo pipefail

# --- Color codes ---
RED='\033[0;31m'
YELLOW='\033[0;33m'
GREEN='\033[0;32m'
BOLD='\033[1m'
RESET='\033[0m'

# --- Get current working directory ---
CWD="$(pwd 2>/dev/null)" || {
    echo -e "${RED}${BOLD}ERROR:${RESET}${RED} Unable to determine the current working directory.${RESET}"
    echo "The 'pwd' command failed. This can happen if the directory has been"
    echo "deleted or you lack permissions to access it."
    exit 1
}

echo -e "${BOLD}Docker Path Compatibility Check${RESET}"
echo "================================"
echo ""
echo "Current path:"
echo "  ${CWD}"
echo ""

# --- Check for spaces using shell pattern matching ---
case "${CWD}" in
    *" "*)
        # Path contains spaces — Docker-incompatible
        echo -e "${RED}${BOLD}INCOMPATIBLE:${RESET}${RED} Path contains spaces${RESET}"
        echo ""

        # Report specific segments that contain spaces
        echo "Segments with spaces:"
        IFS='/' read -ra SEGMENTS <<< "${CWD}"
        for segment in "${SEGMENTS[@]}"; do
            if [[ -n "${segment}" ]] && [[ "${segment}" == *" "* ]]; then
                echo -e "  ${YELLOW}→ '${segment}'${RESET}"
            fi
        done
        echo ""

        # Check for iCloud Drive path segment
        if [[ "${CWD}" == *"Mobile Documents/com~apple~CloudDocs"* ]]; then
            echo -e "${YELLOW}${BOLD}iCloud Drive detected:${RESET}"
            echo -e "${YELLOW}  This project is inside an iCloud Drive synced directory.${RESET}"
            echo -e "${YELLOW}  The 'Mobile Documents' segment in the iCloud path contains${RESET}"
            echo -e "${YELLOW}  a space that causes Docker mount failures on macOS.${RESET}"
            echo ""
        fi

        echo "Docker cannot create bind-mount source paths that contain spaces."
        echo "This causes 'sam local start-api' to fail with 500 errors."
        echo ""
        echo -e "${BOLD}Fix:${RESET} Run ${GREEN}make fix-path${RESET} to create a symlink from a space-free path."
        exit 1
        ;;
    *)
        # Path has no spaces — Docker-compatible
        echo -e "${GREEN}${BOLD}COMPATIBLE:${RESET}${GREEN} Path is Docker-compatible (no spaces detected)${RESET}"
        echo ""
        echo "Docker bind mounts should work correctly from this path."
        exit 0
        ;;
esac
