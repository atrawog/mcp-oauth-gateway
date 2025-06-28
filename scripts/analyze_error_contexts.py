#!/usr/bin/env python3
"""Analyze error checking contexts in test files."""

import re
from collections import defaultdict
from pathlib import Path


def find_error_contexts():
    """Find error checking patterns with their context."""
    tests_dir = Path("/home/atrawog/AI/atrawog/mcp-oauth-gateway/tests")

    contexts = defaultdict(list)

    for test_file in tests_dir.glob("test_*.py"):
        lines = test_file.read_text().splitlines()

        for i, line in enumerate(lines):
            # Check for error variable assignment
            if "response.json()" in line and i + 1 < len(lines):
                # Look for what variable it's assigned to
                match = re.search(r"(\w+)\s*=\s*response\.json\(\)", line)
                if match:
                    var_name = match.group(1)
                    # Look at next few lines to see how it's used
                    context_lines = []
                    for j in range(i, min(i + 10, len(lines))):
                        if var_name in lines[j]:
                            context_lines.append(lines[j].strip())

                    if context_lines:
                        contexts[test_file.name].append(
                            {
                                "var": var_name,
                                "line": i + 1,
                                "usage": context_lines[:5],  # First 5 usages
                            },
                        )

    # Categorize the patterns
    print("Error response handling patterns:\n")

    # Group by variable name patterns
    var_patterns = defaultdict(list)
    for file_name, file_contexts in contexts.items():
        for ctx in file_contexts:
            var_patterns[ctx["var"]].append((file_name, ctx))

    # Print most common variable names
    print("Common variable names for response.json():")
    for var_name, occurrences in sorted(var_patterns.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"\n{var_name}: {len(occurrences)} occurrences")
        # Show a few examples
        for file_name, ctx in occurrences[:3]:
            print(f"  File: {file_name}, Line: {ctx['line']}")
            for usage in ctx["usage"][:2]:
                print(f"    {usage}")

    # Look for specific error checking patterns
    print("\n\nError checking patterns by structure:")

    structure_patterns = {
        "Direct detail access": r'error\["detail"\]',
        "Safe detail access": r'error\.get\("detail"',
        "Nested error access": r'error\["detail"\]\["error"\]',
        "Direct error field": r'error\["error"\]',
        "JSON response detail": r'json_response\["detail"\]',
        "Error data pattern": r'error_data\["detail"\]',
        "Detail in check": r'"detail" in error',
        "Error in check": r'"error" in error',
    }

    for pattern_name, regex in structure_patterns.items():
        files_with_pattern = []
        for test_file in tests_dir.glob("test_*.py"):
            content = test_file.read_text()
            if re.search(regex, content):
                count = len(re.findall(regex, content))
                files_with_pattern.append((test_file.name, count))

        if files_with_pattern:
            print(f"\n{pattern_name}:")
            for file_name, count in sorted(files_with_pattern, key=lambda x: x[1], reverse=True)[:5]:
                print(f"  - {file_name}: {count} times")


if __name__ == "__main__":
    find_error_contexts()
