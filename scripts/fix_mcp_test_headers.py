#!/usr/bin/env python3
"""Fix MCP test files to include required Accept headers and fix hardcoded protocol versions.

This script addresses the root cause of 400 Bad Request errors in MCP tests:
1. Missing Accept: application/json, text/event-stream header
2. Hardcoded protocol versions instead of using MCP_PROTOCOL_VERSION
3. Missing MCP-Protocol-Version headers in some requests

Based on our debugging, the MCP servers require:
- Accept: application/json, text/event-stream
- Content-Type: application/json
- Authorization: Bearer <token>
- MCP-Protocol-Version: <version> (optional but good practice)
"""

import re
from pathlib import Path


def fix_mcp_test_file(file_path: Path):
    """Fix a single MCP test file."""
    print(f"🔧 Fixing {file_path.name}...")

    content = file_path.read_text()
    original_content = content
    fixes_applied = []

    # Fix 1: Replace hardcoded protocol version 2025-03-26 with MCP_PROTOCOL_VERSION
    if "2025-03-26" in content:
        content = content.replace('"2025-03-26"', "MCP_PROTOCOL_VERSION")
        content = content.replace("'2025-03-26'", "MCP_PROTOCOL_VERSION")
        fixes_applied.append("Fixed hardcoded protocol version 2025-03-26")

        # Ensure import of MCP_PROTOCOL_VERSION
        if "from .test_constants import MCP_PROTOCOL_VERSION" not in content:
            # Find existing test_constants imports
            import_pattern = r"(from \.test_constants import [^\n]+)"
            match = re.search(import_pattern, content)
            if match:
                existing_import = match.group(1)
                if "MCP_PROTOCOL_VERSION" not in existing_import:
                    new_import = existing_import.rstrip() + "\nfrom .test_constants import MCP_PROTOCOL_VERSION"
                    content = content.replace(existing_import, new_import)
                    fixes_applied.append("Added MCP_PROTOCOL_VERSION import")
            else:
                # Add import at the top if no test_constants import exists
                lines = content.split("\n")
                insert_index = 0
                for i, line in enumerate(lines):
                    if line.startswith(("import ", "from ")):
                        insert_index = i + 1
                    elif line.strip() == "":
                        continue
                    else:
                        break
                lines.insert(insert_index, "from .test_constants import MCP_PROTOCOL_VERSION")
                content = "\n".join(lines)
                fixes_applied.append("Added MCP_PROTOCOL_VERSION import")

    # Fix 2: Add Accept header to POST requests missing it
    # Pattern: http_client.post(..., headers={...}) where headers don't contain Accept

    # Find all header dictionaries in POST requests
    post_pattern = r"(await\s+http_client\.post\([^}]+headers\s*=\s*\{[^}]+\})"
    matches = list(re.finditer(post_pattern, content, re.DOTALL))

    for match in reversed(matches):  # Process in reverse to maintain positions
        post_call = match.group(1)

        # Check if this POST call already has Accept header
        if "Accept.*application/json.*text/event-stream" in post_call or '"Accept"' in post_call:
            continue

        # Check if this is an MCP endpoint call (has Authorization Bearer)
        if "Authorization.*Bearer" not in post_call:
            continue

        # Extract headers dict
        headers_pattern = r"headers\s*=\s*\{([^}]+)\}"
        headers_match = re.search(headers_pattern, post_call, re.DOTALL)
        if not headers_match:
            continue

        headers_content = headers_match.group(1)

        # Add Accept header if not present
        if '"Accept"' not in headers_content and "'Accept'" not in headers_content:
            # Add Accept header after the last header
            headers_content = headers_content.rstrip()
            if headers_content.endswith(","):
                new_headers = headers_content + '\n            "Accept": "application/json, text/event-stream",'
            else:
                new_headers = headers_content + ',\n            "Accept": "application/json, text/event-stream",'

            # Replace in the content
            new_post_call = post_call.replace(headers_content, new_headers)
            content = content.replace(post_call, new_post_call)
            fixes_applied.append("Added Accept header to MCP POST request")

    # Fix 3: Add Accept header to POST requests that only have Authorization
    # Pattern: headers={"Authorization": f"Bearer {token}"}
    simple_auth_pattern = r'headers\s*=\s*\{\s*"Authorization":\s*f"Bearer\s+\{[^}]+\}"\s*\}'
    matches = list(re.finditer(simple_auth_pattern, content))

    for match in reversed(matches):
        headers_dict = match.group(0)

        # Replace with full headers including Accept
        new_headers = """headers={
                    "Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}",
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream",
                }"""

        # Extract the actual token variable
        token_var_match = re.search(r"Bearer\s+\{([^}]+)\}", headers_dict)
        if token_var_match:
            token_var = token_var_match.group(1)
            new_headers = new_headers.replace("{MCP_CLIENT_ACCESS_TOKEN}", f"{{{token_var}}}")

        content = content.replace(headers_dict, new_headers)
        fixes_applied.append("Enhanced simple Authorization header to include Accept and Content-Type")

    # Fix 4: Ensure Content-Type is present in all MCP requests
    # This is less critical since it's usually there, but good to check

    # Save the file if changes were made
    if content != original_content:
        file_path.write_text(content)
        print(f"  ✅ Applied {len(fixes_applied)} fixes:")
        for fix in fixes_applied:
            print(f"    - {fix}")
        return True
    print("  ℹ️  No fixes needed")
    return False


def main():
    """Fix all MCP test files."""
    print("🔍 Finding MCP test files with potential header issues...")

    test_dir = Path("/home/atrawog/mcp-oauth-gateway/tests")
    if not test_dir.exists():
        print(f"❌ Test directory not found: {test_dir}")
        return

    # Find test files that use MCP_CLIENT_ACCESS_TOKEN (these are the MCP client tests)
    mcp_test_files = []
    for test_file in test_dir.glob("test_mcp_*.py"):
        content = test_file.read_text()
        if "MCP_CLIENT_ACCESS_TOKEN" in content:
            mcp_test_files.append(test_file)

    print(f"📁 Found {len(mcp_test_files)} MCP test files to check:")
    for f in mcp_test_files:
        print(f"  - {f.name}")

    # Fix each file
    print("\n🛠️  Starting fixes...")
    fixed_count = 0
    for test_file in mcp_test_files:
        if fix_mcp_test_file(test_file):
            fixed_count += 1

    print(f"\n✅ Fixed {fixed_count} files out of {len(mcp_test_files)} MCP test files")
    print("\n🎯 Common issues addressed:")
    print("  1. Missing Accept: application/json, text/event-stream header")
    print("  2. Hardcoded protocol version 2025-03-26 → MCP_PROTOCOL_VERSION")
    print("  3. Incomplete header dictionaries in Authorization-only requests")
    print("\n🧪 Run tests again to verify the fixes resolved the 400 Bad Request errors!")


if __name__ == "__main__":
    main()
