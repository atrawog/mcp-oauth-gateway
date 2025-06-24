#!/usr/bin/env python3
"""Fix syntax errors caused by incorrectly placed timeout parameters."""

import re
from pathlib import Path


def fix_timeout_syntax_errors(content: str) -> str:
    """Fix syntax errors where timeout was added incorrectly."""
    # Pattern 1: Fix lines that have ), timeout=30.0)
    pattern1 = r'\)\s*,\s*timeout=30\.0\)'
    replacement1 = ', timeout=30.0)'
    content = re.sub(pattern1, replacement1, content)

    # Pattern 2: Fix lines where timeout was added after closing bracket
    # e.g., }, timeout=30.0)
    pattern2 = r'\}\s*,\s*timeout=30\.0\)'
    replacement2 = '}, timeout=30.0)'
    content = re.sub(pattern2, replacement2, content)

    # Pattern 3: Fix double closing parentheses with timeout
    # e.g., )), timeout=30.0)
    pattern3 = r'\)\)\s*,\s*timeout=30\.0\)'
    replacement3 = ', timeout=30.0))'
    content = re.sub(pattern3, replacement3, content)

    # Pattern 4: Fix lines where assert split incorrectly
    # Look for assert response.status_code == followed by newline and indented value
    pattern4 = r'assert response\.status_code ==\s*\n\s+(\w+)'
    replacement4 = r'assert response.status_code == \1'
    content = re.sub(pattern4, replacement4, content, flags=re.MULTILINE)

    return content


def fix_httpx_timeout_placement(content: str) -> str:
    """Fix timeout placement in httpx calls."""
    lines = content.split('\n')
    fixed_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Check if this line ends with a method call and next line has timeout
        if i + 1 < len(lines) and re.search(r'http_client\.(get|post|put|delete|patch)\([^)]*$', line):
            next_line = lines[i + 1]
            # If next line starts with timeout parameter
            if re.match(r'\s*,?\s*timeout=', next_line):
                # Merge the lines properly
                fixed_lines.append(line.rstrip() + next_line.strip())
                i += 2
                continue

        fixed_lines.append(line)
        i += 1

    return '\n'.join(fixed_lines)


def main():
    """Process all test files to fix syntax errors."""
    test_dir = Path("tests")
    if test_dir.exists():
        for test_file in test_dir.glob("test_*.py"):
            try:
                content = test_file.read_text()
                original_content = content

                content = fix_timeout_syntax_errors(content)
                content = fix_httpx_timeout_placement(content)

                if content != original_content:
                    test_file.write_text(content)
                    print(f"Fixed syntax errors in: {test_file}")

            except Exception as e:
                print(f"Error processing {test_file}: {e}")


if __name__ == "__main__":
    main()
