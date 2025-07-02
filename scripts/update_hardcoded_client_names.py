#!/usr/bin/env python3
"""Update tests using hardcoded client names to use proper fixtures.

This script helps identify and suggest fixes for tests that use:
- TEST_CLIENT_NAME constant directly
- Hardcoded "TEST test_something" patterns
- Other hardcoded client names
"""

import re
from pathlib import Path


# Files identified as having hardcoded client names
FILES_TO_CHECK = [
    "test_additional_coverage.py",
    "test_claude_integration.py",
    "test_coverage_gaps.py",
    "test_coverage_gaps_specific.py",
    "test_mcp_oauth_dynamicclient.py",
    "test_oauth_flow.py",
    "test_registration_security.py",
]

# Patterns to look for
PATTERNS = [
    (r'"client_name":\s*TEST_CLIENT_NAME', "Uses TEST_CLIENT_NAME constant"),
    (r'"client_name":\s*"TEST\s+test_[^"]*"', "Hardcoded TEST test_* pattern"),
    (r'"client_name":\s*"test-client"', 'Hardcoded "test-client"'),
    (r"'client_name':\s*'test[^']*'", "Hardcoded test client name"),
]


def analyze_file(filepath: Path) -> list[tuple[int, str, str]]:
    """Analyze a file for hardcoded client names.

    Returns list of (line_number, line_content, issue_description)
    """
    issues = []

    try:
        with open(filepath) as f:
            lines = f.readlines()

        for line_num, line in enumerate(lines, 1):
            for pattern, description in PATTERNS:
                if re.search(pattern, line):
                    issues.append((line_num, line.strip(), description))

    except Exception as e:
        print(f"Error reading {filepath}: {e}")

    return issues


def suggest_fix(line: str, issue: str) -> str:
    """Suggest a fix for the identified issue."""
    if "TEST_CLIENT_NAME" in line:
        return line.replace("TEST_CLIENT_NAME", "unique_client_name")
    if "TEST test_" in line:
        # Extract the test name if possible
        match = re.search(r'"TEST\s+test_([^"]*)"', line)
        if match:
            return re.sub(r'"TEST\s+test_[^"]*"', "unique_client_name", line)
    elif "test-client" in line:
        return line.replace('"test-client"', "unique_client_name")

    return line.replace('"test', 'unique_client_name  # Was: "test')


def check_fixture_usage(filepath: Path, line_num: int) -> str:
    """Check if the test function uses proper fixtures."""
    try:
        with open(filepath) as f:
            lines = f.readlines()

        # Look backwards from the issue line to find the function definition
        for i in range(line_num - 1, max(0, line_num - 20), -1):
            if "def test_" in lines[i] or "async def test_" in lines[i]:
                func_line = lines[i]
                if "unique_client_name" in func_line:
                    return "✅ Already has unique_client_name fixture"
                if "registered_client" in func_line:
                    return "✅ Already has registered_client fixture"
                return "❌ Missing fixture - add unique_client_name or registered_client"

    except Exception:
        pass

    return "❓ Could not determine fixture usage"


def main():
    """Main function to analyze and suggest fixes."""
    print("🔍 Analyzing Tests for Hardcoded Client Names\n")

    tests_dir = Path("/home/atrawog/mcp-oauth-gateway/tests")
    total_issues = 0

    for filename in FILES_TO_CHECK:
        filepath = tests_dir / filename
        if not filepath.exists():
            print(f"❌ {filename} not found")
            continue

        issues = analyze_file(filepath)
        if issues:
            print(f"\n📄 {filename} ({len(issues)} issues)")
            print("-" * 80)

            for line_num, line, issue in issues:
                total_issues += 1
                print(f"Line {line_num}: {issue}")
                print(f"  Current: {line}")
                print(f"  Suggest: {suggest_fix(line, issue)}")
                fixture_status = check_fixture_usage(filepath, line_num)
                print(f"  Fixture: {fixture_status}")
                print()

    print(f"\n📊 Summary: {total_issues} hardcoded client names found")

    print("\n💡 Fix Instructions:")
    print("1. Add fixture to test function signature:")
    print("   async def test_something(http_client, unique_client_name):")
    print("\n2. Use the fixture in registration:")
    print("   'client_name': unique_client_name")
    print("\n3. Or use registered_client fixture for automatic cleanup:")
    print("   async def test_something(http_client, registered_client):")
    print("   client_data = registered_client")


if __name__ == "__main__":
    main()
