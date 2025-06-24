#!/usr/bin/env python3
"""Remove or comment out tests that use httpbin.org.

Per CLAUDE.md sacred commandments:
- Test against real deployed services (our own), not external third-party services
- httpbin.org causes timeouts and unreliability
"""

import re
from pathlib import Path


def remove_httpbin_tests(file_path: Path):
    """Remove or comment out test methods that use httpbin.org."""
    with open(file_path) as f:
        content = f.read()

    # Pattern to find test methods that contain httpbin.org
    # This regex finds complete test methods (from async def to the next def/class)
    pattern = r'(\n\s*@pytest\.mark\.[^\n]*\n)*(\s*async def test_[^(]+\([^)]*\):[^\n]*\n(?:(?!^\s*(?:async )?def|^class).*\n)*)'

    modified = False
    new_content = content

    for match in re.finditer(pattern, content, re.MULTILINE):
        test_block = match.group(0)
        if 'httpbin.org' in test_block:
            # Comment out the entire test block
            commented_block = '\n'.join(f'# {line}' if line.strip() else '#'
                                       for line in test_block.split('\n'))
            # Add explanation comment
            explanation = (
                '\n# REMOVED: This test used httpbin.org which violates our testing principles.\n'
                '# Per CLAUDE.md: Test against real deployed services (our own), not external ones.\n'
                '# httpbin.org causes timeouts and unreliability.\n'
            )
            new_content = new_content.replace(test_block, explanation + commented_block)
            modified = True

    if modified:
        with open(file_path, 'w') as f:
            f.write(new_content)
        return True
    return False


def main():
    """Remove httpbin.org tests from all test files."""
    test_files = [
        'tests/test_mcp_fetchs_mcp_compliance.py',
        'tests/test_mcp_fetchs_real_content.py',
        'tests/test_mcp_fetchs_security.py',
        'tests/test_mcp_fetchs_complete.py'
    ]

    total_modified = 0
    for file_name in test_files:
        file_path = Path(file_name)
        if file_path.exists():
            if remove_httpbin_tests(file_path):
                print(f"✓ Modified {file_path}")
                total_modified += 1
            else:
                print(f"  No httpbin.org tests found in {file_path}")
        else:
            print(f"✗ File not found: {file_path}")

    print(f"\nTotal files modified: {total_modified}")


if __name__ == "__main__":
    main()
