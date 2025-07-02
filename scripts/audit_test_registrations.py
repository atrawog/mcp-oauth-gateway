#!/usr/bin/env python3
"""Audit test files to find direct client registrations and check for proper cleanup."""

import os
from pathlib import Path


def find_registration_calls(file_path):
    """Find all client registration calls in a Python file."""
    with open(file_path) as f:
        content = f.read()

    registrations = []
    cleanups = []
    uses_fixture = False
    uses_context_manager = False

    # Check for registered_client fixture usage
    if "registered_client" in content and "def test" in content:
        uses_fixture = True

    # Check for RegisteredClientContext usage
    if "RegisteredClientContext" in content:
        uses_context_manager = True

    # Find direct registration calls
    if ".post(" in content and "/register" in content:
        # Count occurrences
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if ".post(" in line and "/register" in line:
                registrations.append(i + 1)
            if "cleanup_client_registration" in line or "delete_response" in line:
                cleanups.append(i + 1)

    return {
        "path": file_path,
        "registrations": registrations,
        "cleanups": cleanups,
        "uses_fixture": uses_fixture,
        "uses_context_manager": uses_context_manager,
    }


def main():
    test_dir = Path("tests")
    results = []

    # Find all test files
    for test_file in test_dir.glob("test_*.py"):
        result = find_registration_calls(test_file)
        if result["registrations"]:
            results.append(result)

    # Generate report
    print("=" * 80)
    print("OAuth Client Registration Audit Report")
    print("=" * 80)
    print()

    needs_update = []
    properly_handled = []

    for result in results:
        rel_path = os.path.relpath(result["path"])
        num_registrations = len(result["registrations"])
        num_cleanups = len(result["cleanups"])

        if result["uses_fixture"]:
            properly_handled.append(result)
            status = "✅ Uses registered_client fixture"
        elif result["uses_context_manager"]:
            properly_handled.append(result)
            status = "✅ Uses RegisteredClientContext"
        elif num_cleanups >= num_registrations:
            properly_handled.append(result)
            status = "✅ Has manual cleanup"
        else:
            needs_update.append(result)
            status = "❌ NEEDS UPDATE - Missing cleanup"

        print(f"{rel_path}:")
        print(f"  Registrations: {num_registrations} (lines: {result['registrations']})")
        print(f"  Cleanups: {num_cleanups}")
        print(f"  Status: {status}")
        print()

    # Summary
    print("=" * 80)
    print("Summary:")
    print(f"  Total files with registrations: {len(results)}")
    print(f"  ✅ Properly handled: {len(properly_handled)}")
    print(f"  ❌ Need updates: {len(needs_update)}")
    print()

    if needs_update:
        print("Files that need updating:")
        for result in needs_update:
            rel_path = os.path.relpath(result["path"])
            print(f"  - {rel_path}")
        print()
        print("Recommended fixes:")
        print("1. Use the 'registered_client' fixture for simple cases")
        print("2. Use 'RegisteredClientContext' for complex cases with multiple registrations")
        print("3. Add manual cleanup using 'cleanup_client_registration' helper")
    else:
        print("🎉 All test files properly handle client registration cleanup!")


if __name__ == "__main__":
    main()
