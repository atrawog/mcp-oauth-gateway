#!/usr/bin/env python3
"""Fix _initialize_session calls to include unique_test_id parameter."""

import re
from pathlib import Path


def fix_initialize_session_calls():
    file_path = Path("/home/atrawog/mcp-oauth-gateway/tests/test_mcp_echo_integration.py")

    with open(file_path) as f:
        content = f.read()

    # Fix the calls to _initialize_session
    # Pattern to find the calls
    pattern = r"await self\._initialize_session\(http_client, mcp_echo_url, gateway_auth_headers\)"
    replacement = r"await self._initialize_session(http_client, mcp_echo_url, gateway_auth_headers, unique_test_id)"

    new_content = re.sub(pattern, replacement, content)

    if new_content != content:
        with open(file_path, "w") as f:
            f.write(new_content)

        # Count how many replacements were made
        count = len(re.findall(pattern, content))
        print(f"✅ Fixed {count} calls to _initialize_session in test_mcp_echo_integration.py")
    else:
        print("❌ No changes were needed")


if __name__ == "__main__":
    fix_initialize_session_calls()
