#!/usr/bin/env python3
"""Fix OAuth registration cleanup issues in test files.

This script automatically updates test files to ensure proper cleanup
of OAuth client registrations.
"""

import re
from pathlib import Path


# Test files with known cleanup issues
FILES_TO_FIX = {
    "test_coverage_improvements.py": [
        ("test_concurrent_token_operations", "missing cleanup for concurrent registration"),
        ("test_callback_github_error", "missing cleanup"),
        ("test_update_client_invalid_token", "missing cleanup"),
        ("test_get_client_with_expired_secret", "missing cleanup"),
        ("test_authorize_with_unsupported_response_type", "missing cleanup"),
    ],
    "test_auth_error_paths.py": [
        ("test_registration_empty_redirect_uris", "incomplete cleanup"),
        ("test_create_token_with_user_tracking", "has cleanup but could fail"),
    ],
    "test_mcp_client_oauth.py": [
        ("test_client_reregistration", "creates 2 registrations but only cleans up 1"),
    ],
    "test_mcp_oauth_dynamicclient.py": [
        ("test_client_registration_validation", "creates 3 registrations without cleanup"),
    ],
    "test_pkce_s256_enforcement.py": [
        ("test_pkce_plain_method_rejected", "needs try/finally"),
        ("test_pkce_s256_proper_validation", "needs try/finally"),
    ],
    "test_registration_security.py": [
        ("ALL", "needs try/finally blocks"),
    ],
    "test_rfc7592_compliance.py": [
        ("ALL", "needs try/finally blocks"),
    ],
    "test_rfc7592_security.py": [
        ("ALL", "needs try/finally blocks"),
    ],
    "test_rfc_compliance.py": [
        ("test_registration_invalid_redirect_uri_rfc7591", "missing cleanup"),
        ("test_registration_missing_redirect_uris_rfc7591", "missing cleanup"),
    ],
    "test_sacred_seals_compliance.py": [
        ("ALL", "needs try/finally blocks"),
    ],
}


def add_fixture_to_test(test_file: Path, function_name: str):
    """Add registered_client fixture to a test function if not present."""
    content = test_file.read_text()

    # Check if function already uses registered_client
    if re.search(rf"def {function_name}\(.*registered_client.*\)", content):
        print(f"  ✓ {function_name} already uses registered_client fixture")
        return False

    # Find the function definition
    pattern = rf"(async def {function_name}\([^)]*)"
    match = re.search(pattern, content)

    if match:
        old_def = match.group(1)
        # Add registered_client to parameters
        new_def = f"{old_def}registered_client)" if old_def.endswith("(") else f"{old_def}, registered_client"

        content = content.replace(old_def, new_def)
        test_file.write_text(content)
        print(f"  ✓ Added registered_client fixture to {function_name}")
        return True

    return False


def wrap_in_context_manager(test_file: Path, function_name: str):
    """Wrap registration code in RegisteredClientContext."""
    content = test_file.read_text()

    # Check if already using context manager
    if "RegisteredClientContext" in content:
        print(f"  ✓ {function_name} already uses RegisteredClientContext")
        return False

    # This is more complex and would require AST manipulation
    # For now, just flag it for manual review
    print(f"  ⚠️  {function_name} needs manual update to use RegisteredClientContext")
    return False


def add_cleanup_code(test_file: Path, function_name: str):
    """Add cleanup code for registrations."""
    content = test_file.read_text()

    # Look for registration without cleanup
    if f"def {function_name}" in content:
        # Check if there's already a cleanup
        func_start = content.find(f"def {function_name}")
        func_end = content.find("\n\n    def ", func_start + 1)
        if func_end == -1:
            func_end = content.find("\n\nclass ", func_start + 1)
        if func_end == -1:
            func_end = len(content)

        func_content = content[func_start:func_end]

        if "cleanup_client_registration" in func_content or "delete" in func_content:
            print(f"  ✓ {function_name} already has cleanup code")
            return False

        print(f"  ⚠️  {function_name} needs cleanup code added - manual review required")
        return False

    return False


def main():
    """Main function to fix registration cleanup issues."""
    print("🔧 Fixing OAuth Registration Cleanup Issues\n")

    tests_dir = Path("/home/atrawog/mcp-oauth-gateway/tests")

    # First, add import for RegisteredClientContext to conftest if needed
    conftest = tests_dir / "conftest.py"
    if conftest.exists():
        content = conftest.read_text()
        if "from conftest import RegisteredClientContext" not in content:
            # No need to import in conftest itself
            pass

    fixed_count = 0
    manual_count = 0

    for filename, issues in FILES_TO_FIX.items():
        filepath = tests_dir / filename
        if not filepath.exists():
            print(f"❌ {filename} not found")
            continue

        print(f"\n📄 Processing {filename}:")

        for function_name, issue in issues:
            if function_name == "ALL":
                print("  ⚠️  All functions in this file need try/finally blocks - manual review required")
                manual_count += 1
                continue

            # Try different fix strategies
            if "missing cleanup" in issue:
                if add_fixture_to_test(filepath, function_name):
                    fixed_count += 1
                else:
                    manual_count += 1
            elif "try/finally" in issue:
                print(f"  ⚠️  {function_name} needs try/finally block - manual review required")
                manual_count += 1
            else:
                manual_count += 1

    print("\n📊 Summary:")
    print(f"   - Automatically fixed: {fixed_count}")
    print(f"   - Need manual review: {manual_count}")

    print("\n💡 Manual Fix Instructions:")
    print("1. For tests that create registrations directly:")
    print("   - Replace with 'registered_client' fixture")
    print("   - Or use 'RegisteredClientContext' from conftest.py")
    print("\n2. For tests that need try/finally:")
    print("   ```python")
    print("   from conftest import RegisteredClientContext")
    print("   ")
    print("   async with RegisteredClientContext(http_client) as ctx:")
    print("       client_data = await ctx.register_client({...})")
    print("       # Test code here")
    print("       # Cleanup happens automatically")
    print("   ```")
    print("\n3. Update TEST_CLIENT_NAME in .env to include timestamp:")
    print("   TEST_CLIENT_NAME=test-client-{timestamp}")
    print("   This prevents conflicts between test runs")


if __name__ == "__main__":
    main()
