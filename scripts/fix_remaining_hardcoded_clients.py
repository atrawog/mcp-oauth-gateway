#!/usr/bin/env python3
"""Fix remaining hardcoded client names in test files to use unique identifiers.

This script updates all remaining hardcoded client names to use unique_test_id
to enable proper parallel test execution.
"""

import re
from pathlib import Path


def find_and_fix_client_names(file_path: Path) -> list[tuple[int, str, str]]:
    """Find and fix hardcoded client names in a file."""
    with open(file_path) as f:
        content = f.read()

    original_content = content
    changes = []

    # Patterns to replace - each tuple is (pattern, replacement, description)
    replacements = [
        # Simple client names that need unique_test_id appended
        (
            r'"clientInfo":\s*{\s*"name":\s*"test-proxy-client"',
            '"clientInfo": {"name": f"test-proxy-{unique_test_id}"',
            "test-proxy-client",
        ),
        (
            r'"clientInfo":\s*{\s*"name":\s*"session-test"',
            '"clientInfo": {"name": f"session-{unique_test_id}"',
            "session-test",
        ),
        (
            r'"clientInfo":\s*{\s*"name":\s*"persistent-client"',
            '"clientInfo": {"name": f"persistent-{unique_test_id}"',
            "persistent-client",
        ),
        (r'"clientInfo":\s*{\s*"name":\s*"flow-test"', '"clientInfo": {"name": f"flow-{unique_test_id}"', "flow-test"),
        (
            r'"clientInfo":\s*{\s*"name":\s*"helper-test"',
            '"clientInfo": {"name": f"helper-{unique_test_id}"',
            "helper-test",
        ),
        (r'"clientInfo":\s*{\s*"name":\s*"auth-test"', '"clientInfo": {"name": f"auth-{unique_test_id}"', "auth-test"),
        (
            r'"clientInfo":\s*{\s*"name":\s*"version-test"',
            '"clientInfo": {"name": f"version-{unique_test_id}"',
            "version-test",
        ),
        (
            r'"clientInfo":\s*{\s*"name":\s*"large-request-test"',
            '"clientInfo": {"name": f"large-{unique_test_id}"',
            "large-request-test",
        ),
        (r'"clientInfo":\s*{\s*"name":\s*"perf-test"', '"clientInfo": {"name": f"perf-{unique_test_id}"', "perf-test"),
        # Client names with numbers
        (
            r'"clientInfo":\s*{\s*"name":\s*"client-1"',
            '"clientInfo": {"name": f"client-1-{unique_test_id}"',
            "client-1",
        ),
        (
            r'"clientInfo":\s*{\s*"name":\s*"client-2"',
            '"clientInfo": {"name": f"client-2-{unique_test_id}"',
            "client-2",
        ),
        # Special case for concurrent sessions with f-string
        (
            r'f"concurrent-session-{session_num}"',
            r'f"concurrent-session-{session_num}-{unique_test_id}"',
            "concurrent-session pattern",
        ),
        # Special case for concurrent clients
        (
            r'f"concurrent-client-{request_id}"',
            r'f"concurrent-client-{request_id}-{unique_test_id}"',
            "concurrent-client pattern",
        ),
        # Initialize method parameter patterns
        (r'\.initialize\("helper-test"\)', '.initialize(f"helper-{unique_test_id}")', "initialize helper-test"),
        (r'client_name: str = "test-client"', "client_name: str = None", "default client_name parameter"),
        # Health check special case - don't modify as it's a standard health check
        # (r'"clientInfo":\s*{\s*"name":\s*"healthcheck"', '"clientInfo": {"name": "healthcheck"', "healthcheck - skipped"),
    ]

    # Apply replacements
    for pattern, replacement, description in replacements:
        if re.search(pattern, content):
            new_content = re.sub(pattern, replacement, content)
            if new_content != content:
                # Find line numbers where changes occurred
                lines = content.split("\n")
                new_lines = new_content.split("\n")
                for i, (old_line, new_line) in enumerate(zip(lines, new_lines, strict=False)):
                    if old_line != new_line:
                        changes.append((i + 1, description, new_line.strip()))
                content = new_content

    # Handle the special case in MCPClientHelper where we need to update the initialize method
    if "def initialize(self, client_name: str = None)" in content:
        # Find the method and update its body
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if "def initialize(self, client_name: str = None)" in line:
                # Look for the json construction in the next few lines
                for j in range(i, min(i + 20, len(lines))):
                    if '"clientInfo": {"name": client_name' in lines[j]:
                        # Need to add a default value check
                        indent = len(lines[j]) - len(lines[j].lstrip())
                        # Insert a line before to set default
                        new_line = " " * (indent - 8) + "if client_name is None:\n"
                        new_line += " " * (indent - 4) + 'client_name = f"test-{unique_test_id}"\n'
                        # Find where to insert (before the json construction)
                        insert_at = None
                        for k in range(j, i, -1):
                            if "response = await" in lines[k]:
                                insert_at = k
                                break
                        if insert_at:
                            lines.insert(insert_at, new_line.rstrip())
                            changes.append((insert_at + 1, "Added default client_name handling", new_line.strip()))
                            content = "\n".join(lines)
                            break
                break

    # Write back if changes were made
    if content != original_content:
        with open(file_path, "w") as f:
            f.write(content)

    return changes


def main():
    """Main function to fix hardcoded client names."""
    # Get the tests directory
    project_root = Path(__file__).parent.parent
    tests_dir = project_root / "tests"

    # Files to check based on our analysis
    files_to_check = [
        "test_mcp_client_oauth.py",
        "test_mcp_client_proxy.py",
        "test_mcp_playwright_integration.py",
        "test_mcp_proxy_fixed.py",
    ]

    total_changes = 0

    for file_name in files_to_check:
        file_path = tests_dir / file_name
        if file_path.exists():
            changes = find_and_fix_client_names(file_path)
            if changes:
                print(f"\n📝 Fixed {file_name}:")
                for line_num, description, new_line in changes:
                    print(f"   Line {line_num}: {description}")
                    if len(new_line) > 80:
                        print(f"   → {new_line[:77]}...")
                    else:
                        print(f"   → {new_line}")
                total_changes += len(changes)
            else:
                print(f"\n✅ {file_name}: No changes needed")

    print(f"\n🎉 Total fixes applied: {total_changes}")

    # Also check for any remaining patterns in all test files
    print("\n🔍 Scanning all test files for any remaining hardcoded patterns...")
    remaining_patterns = [
        r'"name":\s*"[^"]*-client[^"]*"(?![^{]*unique_test_id)',
        r'"name":\s*"test-[^"]*"(?![^{]*unique_test_id)',
        r'"name":\s*"client-\d+"(?![^{]*unique_test_id)',
    ]

    remaining_issues = []
    for test_file in tests_dir.glob("test_*.py"):
        with open(test_file) as f:
            content = f.read()

        for pattern in remaining_patterns:
            matches = list(re.finditer(pattern, content))
            for match in matches:
                # Skip if it's in a comment or docstring
                line_start = content.rfind("\n", 0, match.start()) + 1
                line_end = content.find("\n", match.end())
                line = content[line_start:line_end]
                if not (line.strip().startswith("#") or line.strip().startswith('"')):
                    # Also skip if "healthcheck" as that's a special case
                    if '"healthcheck"' not in match.group(0):
                        line_num = content[: match.start()].count("\n") + 1
                        remaining_issues.append((test_file.name, line_num, match.group(0)))

    if remaining_issues:
        print(f"\n⚠️  Found {len(remaining_issues)} potential remaining issues:")
        for file_name, line_num, match in remaining_issues[:10]:  # Show first 10
            print(f"   {file_name}:{line_num} - {match}")
        if len(remaining_issues) > 10:
            print(f"   ... and {len(remaining_issues) - 10} more")
    else:
        print("\n✅ No remaining hardcoded client name patterns found!")


if __name__ == "__main__":
    main()
