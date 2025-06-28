#!/usr/bin/env python3
"""Fix error response checks in tests to match OAuth 2.0 compliant format.

The auth service returns OAuth 2.0 compliant errors:
    {"error": "error_code", "error_description": "message"}

But many tests expect:
    {"detail": {"error": "error_code", "error_description": "message"}}

This script fixes all test files to expect the correct format.
"""

import re
from pathlib import Path


def fix_error_checks(content: str) -> str:
    """Fix error response checks to match OAuth 2.0 format."""
    # Pattern 1: error["detail"]["error"] -> error["error"]
    content = re.sub(r'error\["detail"\]\["error"\]', 'error["error"]', content)

    # Pattern 2: error["detail"]["error_description"] -> error["error_description"]
    content = re.sub(r'error\["detail"\]\["error_description"\]', 'error["error_description"]', content)

    # Pattern 3: error.get("detail", {}).get("error") -> error.get("error")
    content = re.sub(r'error\.get\("detail", \{\}\)\.get\("error"\)', 'error.get("error")', content)

    # Pattern 4: error.get("detail", {}).get("error_description") -> error.get("error_description")
    content = re.sub(
        r'error\.get\("detail", \{\}\)\.get\("error_description"',
        'error.get("error_description"',
        content,
    )

    # Pattern 5: "detail" in error and ... error["detail"]["..."] checks
    # This is more complex, handle specific cases

    # Pattern 6: assert error["detail"] == "..." -> assert error.get("error_description") == "..."
    content = re.sub(
        r'assert error\["detail"\] == "([^"]+)"',
        r'assert error.get("error_description") == "\1"',
        content,
    )

    # Pattern 7: error_data["detail"]["error"] -> error_data["error"]
    content = re.sub(r'error_data\["detail"\]\["error"\]', 'error_data["error"]', content)

    # Pattern 8: error_data["detail"]["error_description"] -> error_data["error_description"]
    content = re.sub(r'error_data\["detail"\]\["error_description"\]', 'error_data["error_description"]', content)

    # Pattern 9: json_response["detail"]["error"] -> json_response["error"]
    content = re.sub(r'json_response\["detail"\]\["error"\]', 'json_response["error"]', content)

    # Pattern 10: response.json()["detail"]["error"] -> response.json()["error"]
    content = re.sub(r'response\.json\(\)\["detail"\]\["error"\]', 'response.json()["error"]', content)

    return content


def main():
    """Fix all test files."""
    tests_dir = Path("/home/atrawog/AI/atrawog/mcp-oauth-gateway/tests")

    # Find all Python test files
    test_files = list(tests_dir.glob("test_*.py"))

    fixed_count = 0

    for test_file in test_files:
        original_content = test_file.read_text()
        fixed_content = fix_error_checks(original_content)

        if fixed_content != original_content:
            test_file.write_text(fixed_content)
            print(f"Fixed: {test_file.name}")
            fixed_count += 1

    print(f"\nFixed {fixed_count} test files")
    print("OAuth 2.0 compliant error format now expected in all tests")


if __name__ == "__main__":
    main()
