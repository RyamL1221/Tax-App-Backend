"""
Docker Path Utilities for detecting and resolving Docker mount path issues.

This module provides functions to analyze filesystem paths for Docker
compatibility, specifically detecting spaces and iCloud Drive path segments
that cause Docker bind-mount failures on macOS.

Docker on macOS fails to mount bind volumes when the host path contains spaces.
The most common case is projects stored in iCloud Drive, where the path includes
``Mobile Documents/com~apple~CloudDocs``.

Usage:
    from docker_path_utils import is_docker_compatible, validate_target_path

    compatible, reasons = is_docker_compatible("/Users/ryan/Library/Mobile Documents/...")
    if not compatible:
        for reason in reasons:
            print(f"Issue: {reason}")
"""

import os
from typing import List, Tuple


# iCloud Drive path segment that causes Docker mount failures
ICLOUD_DRIVE_SEGMENT = "Mobile Documents/com~apple~CloudDocs"


def has_spaces(path: str) -> bool:
    """
    Detect whether a filesystem path contains any space characters.

    Args:
        path: The filesystem path string to check.

    Returns:
        True if the path contains at least one space character, False otherwise.
    """
    return " " in path


def find_space_segments(path: str) -> List[str]:
    """
    Return path segments (directory or file names) that contain spaces.

    Splits the path by the OS path separator and returns only those
    segments that contain at least one space character. Empty segments
    (from leading separators or double separators) are ignored.

    Args:
        path: The filesystem path string to analyze.

    Returns:
        A list of path segment strings that contain spaces.
        Returns an empty list if no segments contain spaces.
    """
    segments = path.split(os.sep)
    return [segment for segment in segments if segment and " " in segment]


def is_icloud_path(path: str) -> bool:
    """
    Detect whether a path passes through the iCloud Drive directory.

    Checks for the presence of the ``Mobile Documents/com~apple~CloudDocs``
    segment, which is the macOS iCloud Drive storage path. This path always
    contains a space in ``Mobile Documents`` and is a common source of
    Docker mount failures.

    Args:
        path: The filesystem path string to check.

    Returns:
        True if the path contains the iCloud Drive path pattern,
        False otherwise.
    """
    return ICLOUD_DRIVE_SEGMENT in path


def is_docker_compatible(path: str) -> Tuple[bool, List[str]]:
    """
    Check whether a path is compatible with Docker bind mounts.

    A path is Docker-compatible if it contains no space characters.
    When incompatible, returns a list of human-readable reasons
    explaining why the path is problematic.

    Args:
        path: The filesystem path string to evaluate.

    Returns:
        A tuple of (is_compatible, reasons) where:
        - is_compatible is True if the path has no spaces, False otherwise.
        - reasons is a list of strings describing incompatibility issues.
          Empty when the path is compatible.
    """
    reasons: List[str] = []

    if has_spaces(path):
        space_segments = find_space_segments(path)
        if space_segments:
            segments_display = ", ".join(f"'{s}'" for s in space_segments)
            reasons.append(
                f"Path contains spaces in segments: {segments_display}"
            )
        else:
            # Space exists but not in a discrete segment (e.g., trailing space)
            reasons.append("Path contains space characters")

        if is_icloud_path(path):
            reasons.append(
                "Path passes through iCloud Drive "
                "(Mobile Documents/com~apple~CloudDocs), "
                "which causes Docker mount failures on macOS"
            )

    return (len(reasons) == 0, reasons)


def validate_target_path(target: str) -> Tuple[bool, str]:
    """
    Validate that a symlink target path contains no spaces.

    Used to verify that a proposed symlink destination is suitable
    for Docker bind mounts before creating the symlink.

    Args:
        target: The proposed symlink target path string.

    Returns:
        A tuple of (is_valid, message) where:
        - is_valid is True if the target path has no spaces, False otherwise.
        - message is a success confirmation or an error description.
    """
    if not target:
        return (False, "Target path must not be empty")

    if has_spaces(target):
        space_segments = find_space_segments(target)
        if space_segments:
            segments_display = ", ".join(f"'{s}'" for s in space_segments)
            return (
                False,
                f"Target path must not contain spaces. "
                f"Segments with spaces: {segments_display}",
            )
        return (False, "Target path must not contain spaces")

    return (True, "Target path is valid (no spaces)")
