#!/usr/bin/env python3
"""Fix remaining test files - add missing unique_client_name parameters."""

import re
from pathlib import Path


def fix_test_parameters(file_path: Path, test_functions: list):
    """Fix test function parameters in a file."""
    with open(file_path) as f:
        content = f.read()

    changes_made = 0

    for test_name in test_functions:
        # Find the function definition - handle both @pytest.mark.asyncio and regular def
        patterns = [
            rf"@pytest\.mark\.asyncio\s+async def {test_name}\(([^)]*)\):",
            rf"async def {test_name}\(([^)]*)\):",
        ]

        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                current_params = match.group(1)
                # Check if unique_client_name is already in the parameters
                if "unique_client_name" not in current_params and "unique_test_id" not in current_params:
                    # Add unique_client_name and unique_test_id to the parameters
                    new_params = current_params.rstrip()
                    if new_params and not new_params.endswith(","):
                        new_params += ", "
                    new_params += "unique_client_name, unique_test_id"

                    # Replace the function definition
                    old_def = match.group(0)
                    new_def = old_def.replace(f"({current_params})", f"({new_params})")

                    content = content.replace(old_def, new_def)
                    changes_made += 1
                    print(f"  ✅ Fixed {test_name}")
                break

    if changes_made > 0:
        with open(file_path, "w") as f:
            f.write(content)

    return changes_made


def main():
    """Fix all remaining test files."""
    tests_dir = Path("/home/atrawog/mcp-oauth-gateway/tests")

    # Files and their failing tests
    files_to_fix = {
        "test_rfc7592_security.py": [
            "test_rfc7592_rejects_oauth_bearer_tokens",
            "test_rfc7592_authentication_edge_cases",
            "test_rfc7592_rate_limiting",
            "test_rfc7592_sql_injection_attempts",
            "test_rfc7592_timing_attack_resistance",
        ],
        "test_rfc_compliance.py": [
            "test_registration_valid_redirect_uris_rfc7591",
            "test_registration_missing_redirect_uris_rfc7591",
            "test_registration_invalid_redirect_uri_rfc7591",
        ],
    }

    total_changes = 0

    for file_name, test_functions in files_to_fix.items():
        file_path = tests_dir / file_name
        if file_path.exists():
            print(f"\n📝 Fixing {file_name}:")
            changes = fix_test_parameters(file_path, test_functions)
            total_changes += changes
            if changes == 0:
                print("  ❌ No changes needed")
        else:
            print(f"\n❌ File not found: {file_name}")

    print(f"\n🎉 Total fixes applied: {total_changes}")


if __name__ == "__main__":
    main()
