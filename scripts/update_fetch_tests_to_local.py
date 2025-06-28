#!/usr/bin/env python3
"""Update fetch tests to use local services instead of external URLs for speed.

This script follows CLAUDE.md commandments and updates all fetch tests to use
local MCP services (like echo) instead of fetching external URLs.
"""

import re
from pathlib import Path


def update_fetch_test_file(file_path: Path) -> bool:
    """Update a single fetch test file to use local URLs."""
    print(f"Processing {file_path}...")

    try:
        content = file_path.read_text()
        original_content = content

        # Check if already updated
        if "test_fetch_speedup_utils" in content:
            print(f"  ✓ Already updated: {file_path}")
            return False

        # Add import if not present
        if "from .test_fetch_speedup_utils import" not in content:
            # Find where to add import (after other imports)
            if "from .test_constants import" in content:
                # Add after test_constants imports
                lines = content.split("\n")
                for i, line in enumerate(lines):
                    if line.startswith("from .test_constants import"):
                        # Find the last test_constants import
                        j = i
                        while j < len(lines) - 1 and (
                            lines[j + 1].startswith("from .test_constants import") or lines[j + 1].strip() == ""
                        ):
                            j += 1
                        # Insert after the last one
                        lines.insert(
                            j + 1,
                            "from .test_fetch_speedup_utils import get_local_test_url, verify_mcp_gateway_response",
                        )
                        content = "\n".join(lines)
                        break
            elif "import" in content:
                # Add after first import block
                lines = content.split("\n")
                for i, line in enumerate(lines):
                    if line.startswith(("import ", "from ")):
                        # Find end of import block
                        j = i
                        while j < len(lines) - 1 and (
                            lines[j + 1].strip() == "" or lines[j + 1].startswith(("import ", "from "))
                        ):
                            j += 1
                        lines.insert(
                            j + 1,
                            "\nfrom .test_fetch_speedup_utils import get_local_test_url, verify_mcp_gateway_response",
                        )
                        content = "\n".join(lines)
                        break

        # Replace example.com URLs with local test URL calls
        replacements = [
            # Direct URL replacements
            (r'"https://example\.com"', "get_local_test_url()"),
            (r"'https://example\.com'", "get_local_test_url()"),
            (r'"http://example\.com"', "get_local_test_url()"),
            (r"'http://example\.com'", "get_local_test_url()"),
            # In arguments
            (r'\{"url": "https://example\.com"\}', '{"url": get_local_test_url()}'),
            (r"\{'url': 'https://example\.com'\}", "{'url': get_local_test_url()}"),
            # Update test descriptions
            (r"fetch.*example\.com", "fetch local test URL"),
            (r"Example Domain", "MCP OAuth Gateway"),
        ]

        for pattern, replacement in replacements:
            content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)

        # Update assertions looking for "Example Domain"
        content = re.sub(
            r'assert\s+"Example\s+Domain"\s+in\s+(\w+)',
            r"assert verify_mcp_gateway_response(\1)",
            content,
        )

        # Update print statements
        content = re.sub(r"Found 'Example Domain'", "Verified MCP OAuth Gateway response", content)

        # Write back if changed
        if content != original_content:
            file_path.write_text(content)
            print(f"  ✅ Updated: {file_path}")
            return True
        print(f"  ℹ️  No changes needed: {file_path}")
        return False

    except Exception as e:
        print(f"  ❌ Error updating {file_path}: {e}")
        return False


def main():
    """Update all fetch test files."""
    tests_dir = Path(__file__).parent.parent / "tests"

    # Find all fetch test files
    fetch_test_files = list(tests_dir.glob("test_mcp_fetch*.py"))
    fetchs_test_files = list(tests_dir.glob("test_mcp_fetchs*.py"))
    all_files = fetch_test_files + fetchs_test_files

    print(f"Found {len(all_files)} fetch test files to check")

    updated_count = 0
    for file_path in sorted(all_files):
        if update_fetch_test_file(file_path):
            updated_count += 1

    print(f"\n✅ Updated {updated_count} files")

    # Also check test_mcp_complete.py which might have fetch tests
    complete_file = tests_dir / "test_mcp_complete.py"
    if complete_file.exists():
        print(f"\nChecking {complete_file}...")
        if update_fetch_test_file(complete_file):
            updated_count += 1

    print(f"\n🎉 Total files updated: {updated_count}")


if __name__ == "__main__":
    main()
