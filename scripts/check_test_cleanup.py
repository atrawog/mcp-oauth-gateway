#!/usr/bin/env python3
"""Check test files for OAuth client registration cleanup.
This script identifies tests that create registrations but don't clean them up.
"""

import re
from pathlib import Path


def find_register_posts(content):
    """Find all POST requests to /register endpoint."""
    # Look for patterns like:
    # - .post(f"{AUTH_BASE_URL}/register"
    # - .post("https://auth.domain/register"
    # - response = await http_client.post(...register...)
    pattern = r'\.post\s*\(\s*[^)]*["\'].*?/register["\']'
    matches = list(re.finditer(pattern, content, re.MULTILINE | re.DOTALL))
    return [(m.start(), m.group()) for m in matches]


def find_cleanups(content):
    """Find cleanup patterns for registrations."""
    cleanup_patterns = [
        # Delete with registration_access_token
        r"\.delete\s*\(\s*[^)]*register.*registration_access_token",
        # registered_client fixture usage
        r'registered_client["\'\s,\)]',
        # Finally blocks with delete
        r"finally:.*?\.delete.*?register",
    ]

    cleanups = []
    for pattern in cleanup_patterns:
        matches = list(
            re.finditer(pattern, content, re.MULTILINE | re.DOTALL | re.IGNORECASE)
        )
        cleanups.extend([(m.start(), pattern) for m in matches])

    return cleanups


def check_client_names(content):
    """Find client names that don't start with TEST."""
    # Look for client_name patterns
    pattern = r'["\']client_name["\']\s*:\s*["\']([^"\']+)["\']'
    matches = re.findall(pattern, content)

    non_test_names = []
    for name in matches:
        if not name.startswith("TEST"):
            non_test_names.append(name)

    return non_test_names


def analyze_test_file(filepath):
    """Analyze a single test file."""
    with open(filepath) as f:
        content = f.read()

    # Skip conftest.py
    if filepath.name == "conftest.py":
        return None

    register_posts = find_register_posts(content)
    cleanups = find_cleanups(content)
    non_test_names = check_client_names(content)

    # Check if file uses registered_client fixture
    uses_fixture = "registered_client" in content

    if register_posts or non_test_names:
        return {
            "file": filepath.name,
            "register_posts": len(register_posts),
            "cleanups": len(cleanups),
            "uses_fixture": uses_fixture,
            "non_test_names": non_test_names,
            "missing_cleanup": len(register_posts) > 0
            and len(cleanups) == 0
            and not uses_fixture,
        }

    return None


def main():
    """Main function to check all test files."""
    tests_dir = Path(__file__).parent.parent / "tests"

    print("Checking test files for OAuth client registration cleanup...\n")

    issues = []

    for test_file in sorted(tests_dir.glob("test_*.py")):
        result = analyze_test_file(test_file)
        if result:
            issues.append(result)

    # Report findings
    print("=== Files with missing cleanup ===")
    for issue in issues:
        if issue["missing_cleanup"]:
            print(f"\n❌ {issue['file']}:")
            print(f"   - Creates {issue['register_posts']} registrations")
            print(f"   - Has {issue['cleanups']} cleanup calls")
            print(f"   - Uses fixture: {issue['uses_fixture']}")

    print("\n=== Files with non-TEST client names ===")
    for issue in issues:
        if issue["non_test_names"]:
            print(f"\n⚠️  {issue['file']}:")
            for name in issue["non_test_names"]:
                print(f"   - '{name}' should start with 'TEST'")

    print("\n=== Summary ===")
    missing_cleanup = [i for i in issues if i["missing_cleanup"]]
    non_test_names = [i for i in issues if i["non_test_names"]]

    print(f"Files with missing cleanup: {len(missing_cleanup)}")
    print(f"Files with non-TEST names: {len(non_test_names)}")

    if missing_cleanup:
        print("\nFiles that need cleanup added:")
        for issue in missing_cleanup:
            print(f"  - {issue['file']}")


if __name__ == "__main__":
    main()
