#!/usr/bin/env python3
"""Fix the broken import statements in test files."""

import os
import re


test_dir = "tests"

# Files with broken imports
files_to_fix = [
    "test_additional_coverage.py",
    "test_auth_error_paths.py",
    "test_coverage_gaps.py",
    "test_coverage_gaps_specific.py",
    "test_existing_oauth_credentials.py",
    "test_mcp_fetch_example_com.py",
    "test_mcp_fetch_simple.py",
    "test_mcp_protocol_version_strict.py",
]

for filename in files_to_fix:
    filepath = os.path.join(test_dir, filename)

    with open(filepath) as f:
        content = f.read()

    # Fix the pattern where jwt import got mixed with test_constants import
    content = re.sub(
        r"from \.test_constants import \(\nfrom \.jwt_test_helper import encode as jwt_encode\n(.*?)\)",
        r"from .jwt_test_helper import encode as jwt_encode\nfrom .test_constants import (\n\1)",
        content,
        flags=re.DOTALL,
    )

    with open(filepath, "w") as f:
        f.write(content)

    print(f"Fixed {filename}")
