#!/usr/bin/env python3
"""Automatically fix hardcoded client names in test files."""

import re
from pathlib import Path


# Files identified with hardcoded client names from earlier analysis
FILES_TO_FIX = {
    "test_auth_error_paths.py": ["TEST pattern"],
    "test_mcp_ai_hostnames.py": ["TEST pattern"],
    "test_mcp_client_oauth.py": ["TEST pattern", "test-client"],
    "test_mcp_client_proxy.py": ["test-client"],
    "test_mcp_echo_client_full.py": ["test-client"],
    "test_mcp_echo_integration.py": ["test-client"],
    "test_mcp_everything_client_full.py": ["test-client"],
    "test_mcp_fetch_complete.py": ["TEST pattern"],
    "test_mcp_fetch_oauth_debug.py": ["test-client"],
    "test_mcp_fetchs_mcp_compliance.py": ["test-client"],
    "test_mcp_memory_integration.py": ["test-client"],
    "test_mcp_playwright_integration.py": ["test-client"],
    "test_mcp_proxy.py": ["test-client"],
    "test_mcp_proxy_fixed.py": ["test-client"],
    "test_mcp_tmux_integration.py": ["test-client"],
    "test_pkce_s256_enforcement.py": ["TEST pattern"],
    "test_register_security.py": ["TEST pattern"],
    "test_rfc7592_compliance.py": ["TEST pattern"],
    "test_rfc7592_security.py": ["TEST pattern"],
    "test_rfc_compliance.py": ["TEST pattern"],
    "test_sacred_seals_compliance.py": ["TEST pattern"],
}


def fix_test_pattern_in_function(content: str, func_name: str) -> str:
    """Fix TEST pattern in a specific function."""
    # Find the function definition
    func_pattern = rf"((?:async )?def {func_name}\()([^)]*)\):"
    func_match = re.search(func_pattern, content)

    if not func_match:
        return content

    # Check if unique_client_name is already in parameters
    params = func_match.group(2)
    if "unique_client_name" not in params:
        # Add unique_client_name parameter
        new_params = params + ", unique_client_name" if params.strip() else "unique_client_name"
        content = content.replace(func_match.group(0), f"{func_match.group(1)}{new_params}):")

    # Replace TEST patterns with unique_client_name
    content = content.replace(f'"TEST {func_name}"', "unique_client_name")
    content = content.replace(f"'TEST {func_name}'", "unique_client_name")

    return content


def fix_test_client_literals(content: str) -> str:
    """Fix test-client literals based on context."""
    # For clientInfo in MCP protocols - use f-string with unique_test_id
    content = re.sub(r'("clientInfo":\s*\{[^}]*"name":\s*)"test-client"', r'\1f"test-{unique_test_id}"', content)
    content = re.sub(r"('clientInfo':\s*\{[^}]*'name':\s*)'test-client'", r"\1f'test-{unique_test_id}'", content)

    # Check if we need unique_test_id parameter
    if 'f"test-{unique_test_id}"' in content or "f'test-{unique_test_id}'" in content:
        # Find all test functions
        test_funcs = re.findall(r"(?:async )?def (test_\w+)\([^)]*\):", content)
        for func_name in test_funcs:
            func_pattern = rf"((?:async )?def {func_name}\()([^)]*)\):"
            func_match = re.search(func_pattern, content)
            if func_match:
                params = func_match.group(2)
                if "unique_test_id" not in params:
                    new_params = params + ", unique_test_id" if params.strip() else "unique_test_id"
                    content = content.replace(func_match.group(0), f"{func_match.group(1)}{new_params}):")

    return content


def fix_file(filepath: Path, issues: list) -> bool:
    """Fix a single file."""
    content = filepath.read_text()
    original = content

    if "TEST pattern" in issues:
        # Find all test functions with TEST patterns
        test_matches = re.findall(r'"TEST (test_\w+)"', content)
        test_matches.extend(re.findall(r"'TEST (test_\w+)'", content))

        for func_name in set(test_matches):
            content = fix_test_pattern_in_function(content, func_name)

        # Fix JSON client_name patterns
        content = re.sub(r'"client_name":\s*"TEST ([^"]*)"', '"client_name": unique_client_name', content)

    if "test-client" in issues:
        content = fix_test_client_literals(content)

    if content != original:
        filepath.write_text(content)
        return True
    return False


def main():
    print("🔧 Automatically fixing hardcoded client names...")
    print("=" * 60)

    fixed_count = 0
    error_count = 0

    for filename, issues in FILES_TO_FIX.items():
        filepath = Path("tests") / filename
        if not filepath.exists():
            print(f"⚠️  {filename} not found")
            continue

        try:
            if fix_file(filepath, issues):
                print(f"✅ Fixed {filename}")
                fixed_count += 1
            else:
                print(f"ℹ️  No changes needed for {filename}")
        except Exception as e:
            print(f"❌ Error fixing {filename}: {e}")
            error_count += 1

    print("\n📊 Summary:")
    print(f"  - Fixed: {fixed_count} files")
    print(f"  - Errors: {error_count} files")
    print(f"  - Total: {len(FILES_TO_FIX)} files")

    if fixed_count > 0:
        print("\n✨ Fixes applied successfully!")
        print("\n🎯 Next steps:")
        print("1. Run tests to verify: just test -n 4")
        print("2. Check specific fixed files: just test tests/test_auth_error_paths.py")


if __name__ == "__main__":
    main()
