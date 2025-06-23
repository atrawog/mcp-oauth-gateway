#!/usr/bin/env python3
"""Replace all pytest.skip() calls for missing tokens with pytest.fail()
This ensures tests FAIL HARD when tokens are missing instead of being skipped.
"""
import re
from pathlib import Path


def replace_skip_with_fail(file_path):
    """Replace token-related skips with fails in a test file."""
    with open(file_path) as f:
        content = f.read()

    original_content = content

    # Pattern to match pytest.skip calls related to tokens/credentials
    patterns = [
        # Match pytest.skip("...TOKEN...") with various quotes
        (r'pytest\.skip\((["\'])([^"\']*(?:TOKEN|token|ACCESS|access|CLIENT|client|credentials)[^"\']*)(\1)\)',
         r'pytest.fail(\1\2 - TESTS MUST NOT BE SKIPPED!\3)'),

        # Match multi-line pytest.skip
        (r'pytest\.skip\(\s*(["\'])([^"\']*(?:TOKEN|token|ACCESS|access|CLIENT|client|credentials)[^"\']*)(\1)\s*\)',
         r'pytest.fail(\1\2 - TESTS MUST NOT BE SKIPPED!\3)'),
    ]

    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content, flags=re.IGNORECASE | re.MULTILINE)

    if content != original_content:
        with open(file_path, 'w') as f:
            f.write(content)
        return True
    return False

def main():
    """Replace all token-related skips with fails."""
    test_dir = Path(__file__).parent.parent / "tests"

    modified_files = []

    for test_file in test_dir.glob("test_*.py"):
        if replace_skip_with_fail(test_file):
            modified_files.append(test_file.name)

    if modified_files:
        print(f"Modified {len(modified_files)} test files to FAIL instead of SKIP:")
        for f in modified_files:
            print(f"  - {f}")
    else:
        print("No test files needed modification")

if __name__ == "__main__":
    main()
