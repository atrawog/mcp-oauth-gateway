#!/usr/bin/env python3
"""Fix remaining error response checks in tests.

Some tests have mixed patterns where they check for "detail"
but then access error["error"] directly. Fix these inconsistencies.
"""

import re
from pathlib import Path


def fix_mixed_patterns(content: str) -> str:
    """Fix mixed error access patterns."""
    # Fix cases where we check "detail" in error but then access error["error"] directly
    # Pattern: assert "detail" in error ... assert error["error"] ==
    lines = content.split('\n')
    fixed_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Look for patterns where we check "detail" in error
        if 'assert "detail" in error' in line:
            # Look ahead for error["error"] or error["error_description"] access
            j = i + 1
            while j < len(lines) and j < i + 10:  # Check next 10 lines
                if 'error["error"]' in lines[j] and 'error["detail"]["error"]' not in lines[j]:
                    # This line accesses error["error"] directly, should be error["detail"]["error"]
                    lines[j] = lines[j].replace('error["error"]', 'error["detail"]["error"]')
                elif 'error["error_description"]' in lines[j] and 'error["detail"]["error_description"]' not in lines[j]:
                    # This line accesses error["error_description"] directly
                    lines[j] = lines[j].replace('error["error_description"]', 'error["detail"]["error_description"]')
                j += 1

        fixed_lines.append(lines[i])
        i += 1

    content = '\n'.join(fixed_lines)

    # Fix specific mixed patterns in test_claude_ai_routing_scenario.py
    # This file has a unique pattern where it checks detail but then accesses error directly
    if "test_claude_ai_routing_scenario" in str(Path.cwd()):
        content = re.sub(
            r'assert "detail" in error\s*\n\s*assert "error" in error\["detail"\]\s*\n\s*assert error\["error"\]',
            'assert "detail" in error\n        assert "error" in error["detail"]\n        assert error["detail"]["error"]',
            content
        )

    # Fix test_coverage_gaps.py patterns where it uses error.get with mixed patterns
    # Pattern: error.get("error") but also error.get("detail", {}).get(...)
    content = re.sub(
        r'assert error\.get\("error"\) == "([^"]+)"\s*\n\s*assert ([^"]+ in )?error\.get\("detail", \{\}\)\.get\(\s*"error_description"',
        r'assert error.get("error") == "\1"\n        assert \2error.get("error_description"',
        content,
        flags=re.MULTILINE
    )

    return content


def fix_test_file(file_path: Path) -> bool:
    """Fix a single test file. Returns True if changes were made."""
    original_content = file_path.read_text()
    fixed_content = fix_mixed_patterns(original_content)

    if fixed_content != original_content:
        file_path.write_text(fixed_content)
        return True
    return False


def main():
    """Fix specific test files with remaining issues."""
    tests_dir = Path("/home/atrawog/AI/atrawog/mcp-oauth-gateway/tests")

    # Target specific files that still have issues
    target_files = [
        "test_claude_ai_routing_scenario.py",
        "test_coverage_gaps.py",
        "test_traefik_routing.py",
        "test_coverage_improvements.py",
    ]

    fixed_count = 0

    for filename in target_files:
        test_file = tests_dir / filename
        if test_file.exists():
            if fix_test_file(test_file):
                print(f"Fixed: {filename}")
                fixed_count += 1

    print(f"\nFixed {fixed_count} test files")

    # Also run a general pass on all test files to catch any remaining issues
    for test_file in tests_dir.glob("test_*.py"):
        if test_file.name not in target_files:  # Skip already processed files
            if fix_test_file(test_file):
                print(f"Also fixed: {test_file.name}")
                fixed_count += 1

    print(f"Total files fixed: {fixed_count}")


if __name__ == "__main__":
    main()
