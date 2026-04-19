#!/usr/bin/env python3
"""
Manual test script for verify_sam_build.py CLI.

This script tests various CLI scenarios to ensure the command-line interface
works correctly with different arguments and edge cases.

Usage:
    python debug_tools/test_cli_verification.py
"""

import subprocess
import sys
from typing import Tuple


def run_command(cmd: str) -> Tuple[int, str]:
    """
    Run a shell command and return exit code and output.
    
    Args:
        cmd: Command to run
        
    Returns:
        Tuple of (exit_code, output)
    """
    print(f"\n{'='*70}")
    print(f"Running: {cmd}")
    print('='*70)
    
    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True
    )
    
    output = result.stdout + result.stderr
    print(output)
    print(f"Exit code: {result.returncode}")
    
    return result.returncode, output


def test_single_lambda():
    """Test checking a single Lambda function."""
    print("\n" + "="*70)
    print("TEST: Single Lambda verification")
    print("="*70)
    
    exit_code, output = run_command("python debug_tools/verify_sam_build.py user_login")
    
    # Should exit with 1 (issues found) since build doesn't exist
    assert exit_code == 1, f"Expected exit code 1, got {exit_code}"
    assert "UserLoginFunction" in output, "Should mention Lambda function name"
    assert "Build directory does not exist" in output or "Build issues" in output, "Should report build issues"
    
    print("✅ Single Lambda test passed")


def test_all_lambdas():
    """Test checking all Lambda functions."""
    print("\n" + "="*70)
    print("TEST: All Lambdas verification")
    print("="*70)
    
    exit_code, output = run_command("python debug_tools/verify_sam_build.py --all")
    
    # Should exit with 1 (issues found)
    assert exit_code == 1, f"Expected exit code 1, got {exit_code}"
    assert "Summary:" in output, "Should include summary"
    
    print("✅ All Lambdas test passed")


def test_verbose_mode():
    """Test verbose output mode."""
    print("\n" + "="*70)
    print("TEST: Verbose mode")
    print("="*70)
    
    exit_code, output = run_command("python debug_tools/verify_sam_build.py user_login --verbose")
    
    # Should include detailed information
    assert "Source mtime:" in output or "DEBUG" in output, "Should include verbose details"
    
    print("✅ Verbose mode test passed")


def test_invalid_lambda():
    """Test with invalid Lambda name."""
    print("\n" + "="*70)
    print("TEST: Invalid Lambda name")
    print("="*70)
    
    exit_code, output = run_command("python debug_tools/verify_sam_build.py nonexistent_lambda")
    
    # Should exit with 1 (error)
    assert exit_code == 1, f"Expected exit code 1, got {exit_code}"
    assert "not found in template.yaml" in output, "Should report Lambda not found"
    
    print("✅ Invalid Lambda test passed")


def test_no_arguments():
    """Test with no arguments."""
    print("\n" + "="*70)
    print("TEST: No arguments")
    print("="*70)
    
    exit_code, output = run_command("python debug_tools/verify_sam_build.py 2>&1")
    
    # Should exit with 2 (argument error)
    assert exit_code == 2, f"Expected exit code 2, got {exit_code}"
    assert "Either specify a lambda_dir or use --all" in output, "Should show error message"
    
    print("✅ No arguments test passed")


def test_conflicting_arguments():
    """Test with conflicting arguments."""
    print("\n" + "="*70)
    print("TEST: Conflicting arguments")
    print("="*70)
    
    exit_code, output = run_command("python debug_tools/verify_sam_build.py user_login --all 2>&1")
    
    # Should exit with 2 (argument error)
    assert exit_code == 2, f"Expected exit code 2, got {exit_code}"
    assert "Cannot specify both lambda_dir and --all" in output, "Should show error message"
    
    print("✅ Conflicting arguments test passed")


def test_help_output():
    """Test help output."""
    print("\n" + "="*70)
    print("TEST: Help output")
    print("="*70)
    
    exit_code, output = run_command("python debug_tools/verify_sam_build.py --help")
    
    # Should exit with 0 (success)
    assert exit_code == 0, f"Expected exit code 0, got {exit_code}"
    assert "usage:" in output, "Should show usage"
    assert "Examples:" in output, "Should show examples"
    assert "--all" in output, "Should document --all flag"
    assert "--verbose" in output, "Should document --verbose flag"
    
    print("✅ Help output test passed")


def main():
    """Run all CLI tests."""
    print("\n" + "="*70)
    print("CLI VERIFICATION TEST SUITE")
    print("="*70)
    
    tests = [
        test_single_lambda,
        test_all_lambdas,
        test_verbose_mode,
        test_invalid_lambda,
        test_no_arguments,
        test_conflicting_arguments,
        test_help_output,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"❌ Test failed: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ Test error: {e}")
            failed += 1
    
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Passed: {passed}/{len(tests)}")
    print(f"Failed: {failed}/{len(tests)}")
    
    if failed == 0:
        print("\n✅ All CLI tests passed!")
        return 0
    else:
        print(f"\n❌ {failed} test(s) failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
