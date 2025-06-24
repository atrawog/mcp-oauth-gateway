#!/usr/bin/env python3
"""Fix invalid noqa directives in test files."""

import re
from pathlib import Path


def fix_invalid_noqa_directives(content: str) -> str:
    """Fix invalid noqa directives that were incorrectly placed."""
    # Pattern to find lines with invalid noqa directives at the end of function signatures
    pattern = r'(\s+)(wait_for_services|capsys|caplog|tmp_path|monkeypatch),?\s*#\s*noqa:\s*ARG002\):'
    replacement = r'\1\2):  # noqa: ARG002'

    content = re.sub(pattern, replacement, content)

    # Also fix lines where noqa was added at the wrong place
    # Pattern: parameter, noqa ARG002 at wrong position
    pattern2 = r'(wait_for_services|capsys|caplog|tmp_path|monkeypatch),\s*#\s*noqa:\s*ARG002(\s*\):)'
    replacement2 = r'\1\2  # noqa: ARG002'

    content = re.sub(pattern2, replacement2, content)

    return content


def main():
    """Process all test files to fix noqa directives."""
    test_dir = Path("tests")
    if test_dir.exists():
        for test_file in test_dir.glob("test_*.py"):
            try:
                content = test_file.read_text()
                original_content = content

                content = fix_invalid_noqa_directives(content)

                if content != original_content:
                    test_file.write_text(content)
                    print(f"Fixed noqa directives in: {test_file}")

            except Exception as e:
                print(f"Error processing {test_file}: {e}")


if __name__ == "__main__":
    main()
