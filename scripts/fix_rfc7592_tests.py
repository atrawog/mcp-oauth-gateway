#!/usr/bin/env python3
"""Fix RFC 7592 compliance tests to include unique_client_name parameter."""

import re
from pathlib import Path


def fix_rfc7592_tests():
    file_path = Path("/home/atrawog/mcp-oauth-gateway/tests/test_rfc7592_compliance.py")

    with open(file_path) as f:
        content = f.read()

    # List of test functions that need fixing
    test_functions = [
        "test_rfc7592_get_client_configuration",
        "test_rfc7592_put_update_client",
        "test_rfc7592_delete_client",
        "test_rfc7592_requires_correct_bearer_token",
        "test_rfc7592_client_isolation",
    ]

    changes_made = 0

    for test_name in test_functions:
        # Find the function definition
        pattern = rf"@pytest\.mark\.asyncio\s+async def {test_name}\(([^)]*)\):"
        match = re.search(pattern, content)

        if match:
            current_params = match.group(1)
            # Check if unique_client_name is already in the parameters
            if "unique_client_name" not in current_params:
                # Add unique_client_name and unique_test_id to the parameters
                new_params = current_params.rstrip()
                if new_params and not new_params.endswith(","):
                    new_params += ", "
                new_params += "unique_client_name, unique_test_id"

                # Replace the function definition
                old_def = f"@pytest.mark.asyncio\nasync def {test_name}({current_params}):"
                new_def = f"@pytest.mark.asyncio\nasync def {test_name}({new_params}):"

                content = content.replace(old_def, new_def)
                changes_made += 1
                print(f"✅ Fixed {test_name}")

    if changes_made > 0:
        with open(file_path, "w") as f:
            f.write(content)
        print(f"\n🎉 Fixed {changes_made} test functions in test_rfc7592_compliance.py")
    else:
        print("❌ No changes were needed")


if __name__ == "__main__":
    fix_rfc7592_tests()
