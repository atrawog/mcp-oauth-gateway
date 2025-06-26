#!/usr/bin/env python3
"""Analyze error checking patterns in test files."""

import re
from collections import defaultdict
from pathlib import Path


def analyze_error_patterns():
    """Find all error checking patterns in test files."""
    tests_dir = Path("/home/atrawog/AI/atrawog/mcp-oauth-gateway/tests")

    patterns = defaultdict(list)

    # Define regex patterns to find
    error_patterns = {
        'error["detail"]': r'error\["detail"\]',
        'error["error"]': r'error\["error"\]',
        'error["error_description"]': r'error\["error_description"\]',
        'error.get("detail")': r'error\.get\(["\'"]detail["\'"]',
        'json_response["detail"]': r'json_response\["detail"\]',
        'error_data["detail"]': r'error_data\["detail"\]',
        '"detail" in error': r'["\'"]detail["\'"] in error',
        '"error" in error': r'["\'"]error["\'"] in error',
        "response.json()": r"response\.json\(\)",
        'error["code"]': r'error\["code"\]',
        'error["message"]': r'error\["message"\]',
        'error["loc"]': r'error\["loc"\]',
    }

    for test_file in tests_dir.glob("test_*.py"):
        content = test_file.read_text()

        for pattern_name, regex in error_patterns.items():
            matches = re.findall(regex, content)
            if matches:
                patterns[pattern_name].append({"file": test_file.name, "count": len(matches)})

    # Print results
    print("Error checking patterns found in test files:\n")
    for pattern_name, files in sorted(patterns.items()):
        total = sum(f["count"] for f in files)
        print(f"{pattern_name}: {total} occurrences in {len(files)} files")
        for file_info in sorted(files, key=lambda x: x["count"], reverse=True)[:5]:
            print(f"  - {file_info['file']}: {file_info['count']}")
        print()

    # Find unique error access patterns
    print("\nAnalyzing unique error access patterns:")

    unique_patterns = set()
    for test_file in tests_dir.glob("test_*.py"):
        content = test_file.read_text()

        # Find all error variable access patterns
        error_access = re.findall(r'(error(?:\["[^"]+"\]|\.[a-zA-Z_]+|\[\'[^\']+\'\])+)', content)
        unique_patterns.update(error_access)

        # Find json_response patterns
        json_patterns = re.findall(r'(json_response(?:\["[^"]+"\]|\.[a-zA-Z_]+)+)', content)
        unique_patterns.update(json_patterns)

        # Find error_data patterns
        error_data_patterns = re.findall(r'(error_data(?:\["[^"]+"\]|\.[a-zA-Z_]+)+)', content)
        unique_patterns.update(error_data_patterns)

    print("\nUnique patterns found:")
    for pattern in sorted(unique_patterns):
        print(f"  - {pattern}")


if __name__ == "__main__":
    analyze_error_patterns()
