#!/usr/bin/env python3
"""Find all occurrences of specific environment variables in the codebase."""

import re
from pathlib import Path


# Environment variables to search for
ENV_VARS = [
    "GATEWAY_OAUTH_CLIENT_ID",
    "GATEWAY_OAUTH_CLIENT_SECRET",
    "GATEWAY_OAUTH_ACCESS_TOKEN",
    "GATEWAY_OAUTH_REFRESH_TOKEN",
    "GATEWAY_JWT_SECRET",
]

# File patterns to search
FILE_PATTERNS = ["*.py", "*.yml", "*.yaml", "justfile", "*.md"]


def find_occurrences(root_dir):
    """Find all occurrences of environment variables."""
    results = {}

    # Create regex pattern
    pattern = re.compile(r"\b(" + "|".join(ENV_VARS) + r")\b")

    for file_pattern in FILE_PATTERNS:
        if file_pattern.startswith("*."):
            # Handle glob patterns
            for path in Path(root_dir).rglob(file_pattern):
                if path.is_file() and ".git" not in str(path):
                    search_file(path, pattern, results)
        else:
            # Handle specific files
            path = Path(root_dir) / file_pattern
            if path.exists() and path.is_file():
                search_file(path, pattern, results)

    return results


def search_file(file_path, pattern, results):
    """Search for pattern in a file."""
    try:
        with open(file_path, encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                matches = pattern.findall(line)
                if matches:
                    if str(file_path) not in results:
                        results[str(file_path)] = []
                    results[str(file_path)].append(
                        {
                            "line_num": line_num,
                            "line": line.strip(),
                            "vars": list(set(matches)),
                        },
                    )
    except Exception as e:
        print(f"Error reading {file_path}: {e}")


def print_results(results):
    """Print search results organized by environment variable."""
    # Organize by variable
    by_var = {}
    for file_path, occurrences in results.items():
        for occ in occurrences:
            for var in occ["vars"]:
                if var not in by_var:
                    by_var[var] = []
                by_var[var].append(
                    {
                        "file": file_path,
                        "line_num": occ["line_num"],
                        "line": occ["line"],
                    },
                )

    # Print results
    for var in ENV_VARS:
        if var in by_var:
            print(f"\n{'=' * 80}")
            print(f"Environment Variable: {var}")
            print(f"{'=' * 80}")

            # Sort by file path and line number
            occurrences = sorted(by_var[var], key=lambda x: (x["file"], x["line_num"]))

            current_file = None
            for occ in occurrences:
                if occ["file"] != current_file:
                    current_file = occ["file"]
                    print(f"\n{current_file}:")
                print(f"  Line {occ['line_num']}: {occ['line']}")

            print(f"\nTotal occurrences of {var}: {len(occurrences)}")


if __name__ == "__main__":
    root_dir = "/home/atrawog/AI/atrawog/mcp-oauth-gateway"
    results = find_occurrences(root_dir)
    print_results(results)

    # Summary
    print(f"\n{'=' * 80}")
    print("SUMMARY")
    print(f"{'=' * 80}")
    total = sum(len(occurrences) for occurrences in results.values())
    print(f"Total files with environment variables: {len(results)}")
    print(f"Total occurrences: {total}")
