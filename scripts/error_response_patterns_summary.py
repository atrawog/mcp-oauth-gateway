#!/usr/bin/env python3
"""Summarize error response patterns in the test suite."""

import re
from collections import Counter
from collections import defaultdict
from pathlib import Path


def analyze_error_patterns():
    """Analyze and summarize all error checking patterns."""
    tests_dir = Path("/home/atrawog/AI/atrawog/mcp-oauth-gateway/tests")

    # Pattern categories
    patterns = {
        "direct_detail_access": [],
        "safe_detail_access": [],
        "nested_error_access": [],
        "error_field_only": [],
        "json_response_detail": [],
        "error_data_detail": [],
        "in_checks": [],
        "other_patterns": [],
    }

    # Stats
    stats = Counter()

    for test_file in tests_dir.glob("test_*.py"):
        content = test_file.read_text()
        lines = content.splitlines()

        for i, line in enumerate(lines):
            # Direct detail access: error["detail"]
            if re.search(r'error\["detail"\]', line) and 'error["detail"]["error"]' not in line:
                patterns["direct_detail_access"].append({"file": test_file.name, "line": i + 1, "code": line.strip()})
                stats["direct_detail_access"] += 1

            # Safe detail access: error.get("detail")
            if re.search(r'error\.get\(["\'"]detail["\'"]', line):
                patterns["safe_detail_access"].append({"file": test_file.name, "line": i + 1, "code": line.strip()})
                stats["safe_detail_access"] += 1

            # Nested error access: error["detail"]["error"] or error["detail"]["error_description"]
            if re.search(r'error\["detail"\]\["error', line):
                patterns["nested_error_access"].append({"file": test_file.name, "line": i + 1, "code": line.strip()})
                stats["nested_error_access"] += 1

            # Direct error field: error["error"] or error["error_description"]
            if re.search(r'error\["(error|error_description)"\]', line) and 'error["detail"]' not in line:
                patterns["error_field_only"].append({"file": test_file.name, "line": i + 1, "code": line.strip()})
                stats["error_field_only"] += 1

            # JSON response patterns
            if re.search(r'json_response\["detail"\]', line):
                patterns["json_response_detail"].append({"file": test_file.name, "line": i + 1, "code": line.strip()})
                stats["json_response_detail"] += 1

            # Error data patterns
            if re.search(r'error_data\["detail"\]', line):
                patterns["error_data_detail"].append({"file": test_file.name, "line": i + 1, "code": line.strip()})
                stats["error_data_detail"] += 1

            # "in" checks
            if re.search(r'["\'](detail|error|error_description)["\'] in error', line):
                patterns["in_checks"].append({"file": test_file.name, "line": i + 1, "code": line.strip()})
                stats["in_checks"] += 1

    # Print summary
    print("ERROR RESPONSE PATTERNS SUMMARY")
    print("=" * 80)
    print("\nBased on the auth service implementation (mcp_oauth_dynamicclient):")
    print("- HTTPException is raised with detail={'error': '...', 'error_description': '...'}")
    print("- The exception handler returns this detail as JSON")
    print("- So error responses have structure: {'detail': {'error': '...', 'error_description': '...'}}")
    print("\nPATTERN STATISTICS:")
    print("-" * 80)

    total = sum(stats.values())
    for pattern_type, count in stats.most_common():
        percentage = (count / total * 100) if total > 0 else 0
        print(f"{pattern_type:25} {count:4} ({percentage:5.1f}%)")

    print(f"\nTotal error checks: {total}")

    # Show examples of each pattern
    print("\nPATTERN EXAMPLES:")
    print("-" * 80)

    pattern_descriptions = {
        "direct_detail_access": 'Direct detail access (error["detail"]) - May fail if detail missing',
        "safe_detail_access": 'Safe detail access (error.get("detail")) - Handles missing detail',
        "nested_error_access": 'Nested error access (error["detail"]["error"]) - Standard pattern',
        "error_field_only": 'Direct error field (error["error"]) - Non-standard, may be legacy',
        "json_response_detail": 'JSON response pattern (json_response["detail"]) - Variable naming',
        "error_data_detail": 'Error data pattern (error_data["detail"]) - Variable naming',
        "in_checks": 'Existence checks ("detail" in error) - Safe but incomplete',
    }

    for pattern_type, description in pattern_descriptions.items():
        if patterns[pattern_type]:
            print(f"\n{description}:")
            # Show up to 3 examples
            for example in patterns[pattern_type][:3]:
                print(f"  {example['file']}:{example['line']}")
                print(f"    {example['code']}")

    # Identify inconsistent patterns
    print("\nINCONSISTENT PATTERNS THAT NEED FIXING:")
    print("-" * 80)

    # Files with mixed patterns
    file_patterns = defaultdict(set)
    for pattern_type, examples in patterns.items():
        for example in examples:
            file_patterns[example["file"]].add(pattern_type)

    mixed_files = {f: p for f, p in file_patterns.items() if len(p) > 1}
    if mixed_files:
        print("\nFiles with mixed error checking patterns:")
        for file, pattern_types in sorted(mixed_files.items()):
            print(f"  {file}: {', '.join(sorted(pattern_types))}")

    # Direct error field access (non-standard)
    if patterns["error_field_only"]:
        print(f"\nFiles using non-standard error['error'] pattern ({len(patterns['error_field_only'])} occurrences):")
        files = {ex["file"] for ex in patterns["error_field_only"]}
        for f in sorted(files)[:10]:
            print(f"  - {f}")

    print("\nRECOMMENDATIONS:")
    print("-" * 80)
    print("1. Standardize on error['detail']['error'] for error code checks")
    print("2. Use error.get('detail', {}).get('error') for safe access when unsure")
    print("3. Always check 'detail' exists before accessing nested fields")
    print("4. Consider creating a helper function for consistent error checking")


if __name__ == "__main__":
    analyze_error_patterns()
