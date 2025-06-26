#!/usr/bin/env python3
"""Fix RFC 7592 compliance tests - add missing parameters and fix hardcoded assertions."""

import re
from pathlib import Path


def fix_rfc7592_tests():
    file_path = Path("/home/atrawog/mcp-oauth-gateway/tests/test_rfc7592_compliance.py")

    with open(file_path) as f:
        content = f.read()

    # First, fix the remaining test functions that need parameters
    missing_param_tests = [
        "test_rfc7592_malformed_requests",
        "test_rfc7592_concurrent_updates",
        "test_rfc7592_client_lifetime_handling",
    ]

    changes_made = 0

    for test_name in missing_param_tests:
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
                print(f"✅ Fixed {test_name} parameters")

    # Now fix the hardcoded assertions
    # Fix the PUT update test - the assertion expects "TEST Updated Name via RFC 7592"
    old_put_assertion = 'assert persisted["client_name"] == "TEST Updated Name via RFC 7592"'
    new_put_assertion = 'assert "Updated Name via RFC 7592" in persisted["client_name"]  # Should contain update text'
    if old_put_assertion in content:
        content = content.replace(old_put_assertion, new_put_assertion)
        changes_made += 1
        print("✅ Fixed PUT update client name assertion")

    # Fix the client isolation test - assertion expects "TEST Client 2"
    old_isolation_assertion = 'assert response.json()["client_name"] == "TEST Client 2"'
    new_isolation_assertion = 'assert "Client 2" in response.json()["client_name"]  # Should contain Client 2'
    if old_isolation_assertion in content:
        content = content.replace(old_isolation_assertion, new_isolation_assertion)
        changes_made += 1
        print("✅ Fixed client isolation assertion")

    # Fix the PUT request that hardcodes the client name
    old_put_data = '"client_name": "TEST Updated Name via RFC 7592"'
    new_put_data = '"client_name": f"{unique_client_name} Updated Name via RFC 7592"'
    if old_put_data in content:
        content = content.replace(old_put_data, new_put_data)
        changes_made += 1
        print("✅ Fixed PUT request client name")

    # Fix the Client 2 hardcoded name in PUT request
    old_client2_put = '"client_name": "TEST Client 2"'
    new_client2_put = '"client_name": f"{unique_client_name}-2 Client 2"'
    if old_client2_put in content:
        content = content.replace(old_client2_put, new_client2_put)
        changes_made += 1
        print("✅ Fixed Client 2 PUT request name")

    if changes_made > 0:
        with open(file_path, "w") as f:
            f.write(content)
        print(f"\n🎉 Made {changes_made} fixes in test_rfc7592_compliance.py")
    else:
        print("❌ No changes were needed")


if __name__ == "__main__":
    fix_rfc7592_tests()
