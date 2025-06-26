#!/usr/bin/env python3
"""Fix all hardcoded client names in test files for parallel execution safety."""

import re
from pathlib import Path


def get_test_files_with_issues() -> list[tuple[Path, list[str]]]:
    """Get all test files that have hardcoded client names."""
    issues = []
    test_dir = Path("tests")

    for test_file in test_dir.glob("test_*.py"):
        if test_file.name == "test_constants.py":
            continue

        content = test_file.read_text()
        file_issues = []

        # Check for hardcoded TEST patterns
        if re.search(r'["\']TEST test_\w+["\']', content):
            file_issues.append("hardcoded_test_pattern")

        # Check for "test-client" literals
        if '"test-client"' in content or "'test-client'" in content:
            file_issues.append("test_client_literal")

        # Check for client_name in JSON with hardcoded values
        if re.search(r'"client_name":\s*"TEST [^"]*"', content):
            file_issues.append("json_client_name")

        if file_issues:
            issues.append((test_file, file_issues))

    return issues


def fix_test_file(filepath: Path, issue_types: list[str]) -> bool:
    """Fix hardcoded client names in a test file."""
    content = filepath.read_text()
    original_content = content

    # Track if we need to add unique_client_name to imports

    # Fix different patterns
    if "hardcoded_test_pattern" in issue_types or "json_client_name" in issue_types:
        # Find all test functions that use hardcoded TEST patterns
        test_funcs = re.findall(r"(?:async )?def (test_\w+)\([^)]*\):", content)

        for func_name in test_funcs:
            # Check if this function uses TEST pattern
            func_pattern = rf"((?:async )?def {func_name}\()([^)]*)\):"
            func_match = re.search(func_pattern, content)

            if func_match:
                # Check if function body contains TEST pattern
                func_start = func_match.end()
                # Find the end of the function (next def or class or end of file)
                next_def = content.find("\ndef ", func_start)
                next_async_def = content.find("\nasync def ", func_start)
                next_class = content.find("\nclass ", func_start)

                ends = [pos for pos in [next_def, next_async_def, next_class, len(content)] if pos > func_start]
                func_end = min(ends)

                func_body = content[func_start:func_end]

                # Check if this function uses TEST pattern
                if f'"TEST {func_name}"' in func_body or f"'TEST {func_name}'" in func_body:
                    # Add unique_client_name parameter if not present
                    params = func_match.group(2)
                    if "unique_client_name" not in params:
                        new_params = params + ", unique_client_name" if params.strip() else "unique_client_name"
                        content = content.replace(func_match.group(0), f"{func_match.group(1)}{new_params}):")

                    # Replace the hardcoded name with fixture
                    content = content.replace(f'"TEST {func_name}"', "unique_client_name")
                    content = content.replace(f"'TEST {func_name}'", "unique_client_name")

        # Fix client_name in JSON objects
        content = re.sub(r'"client_name":\s*"TEST [^"]*"', '"client_name": unique_client_name', content)

    if "test_client_literal" in issue_types:
        # For test-client literals, we need different approaches based on context

        # First, find if it's used in clientInfo for MCP protocol
        if '"clientInfo":' in content or "'clientInfo':" in content:
            # These are likely MCP protocol client info, not OAuth clients
            # Replace with unique names for these too
            content = re.sub(
                r'("clientInfo":\s*\{[^}]*"name":\s*)"test-client"', r'\1f"test-{unique_test_id}"', content
            )
            content = re.sub(
                r"('clientInfo':\s*\{[^}]*'name':\s*)'test-client'", r"\1f'test-{unique_test_id}'", content
            )

            # Check if we need to add unique_test_id to function parameters
            test_funcs = re.findall(r"(?:async )?def (test_\w+)\([^)]*\):", content)
            for func_name in test_funcs:
                func_pattern = rf"((?:async )?def {func_name}\()([^)]*)\):"
                func_match = re.search(func_pattern, content)
                if func_match:
                    params = func_match.group(2)
                    if "unique_test_id" not in params and 'f"test-{unique_test_id}"' in content:
                        new_params = params + ", unique_test_id" if params.strip() else "unique_test_id"
                        content = content.replace(func_match.group(0), f"{func_match.group(1)}{new_params}):")

        # For other test-client usages, replace with TEST_CLIENT_NAME from constants
        # But only if it's not in clientInfo context
        remaining_test_client = re.findall(r'["\']test-client["\']', content)
        if remaining_test_client:
            # Add import if needed
            if "from .test_constants import TEST_CLIENT_NAME" not in content:
                # Find where to add the import
                import_section = re.search(r"(from \.test_constants import[^\n]+)\n", content)
                if import_section:
                    imports = import_section.group(1)
                    if "TEST_CLIENT_NAME" not in imports:
                        new_imports = imports + "\nfrom .test_constants import TEST_CLIENT_NAME"
                        content = content.replace(imports, new_imports)

            # Replace remaining test-client with TEST_CLIENT_NAME
            content = content.replace('"test-client"', "TEST_CLIENT_NAME")
            content = content.replace("'test-client'", "TEST_CLIENT_NAME")

    # Write back if changed
    if content != original_content:
        filepath.write_text(content)
        return True
    return False


def add_missing_imports(filepath: Path):
    """Ensure necessary imports are present."""
    content = filepath.read_text()

    # Check if file uses unique_client_name or unique_test_id
    uses_unique_client = "unique_client_name" in content
    uses_unique_test_id = "unique_test_id" in content

    if uses_unique_client or uses_unique_test_id:
        # These are fixtures, no imports needed
        pass


def main():
    print("🔧 Fixing hardcoded client names in test files...")
    print("=" * 60)

    # Get files with issues
    files_with_issues = get_test_files_with_issues()

    if not files_with_issues:
        print("✅ No hardcoded client names found!")
        return

    print(f"\n📋 Found {len(files_with_issues)} files with hardcoded client names:")

    # Group by issue type
    by_issue = {"hardcoded_test_pattern": [], "test_client_literal": [], "json_client_name": []}

    for filepath, issues in files_with_issues:
        for issue in issues:
            by_issue[issue].append(filepath.name)

    for issue_type, files in by_issue.items():
        if files:
            print(f"\n{issue_type}: {len(files)} files")
            for f in sorted(files)[:5]:
                print(f"  - {f}")
            if len(files) > 5:
                print(f"  ... and {len(files) - 5} more")

    # Ask for confirmation
    print("\n⚠️  This will modify the test files to use unique client names.")
    response = input("Proceed with fixes? (y/N): ")

    if response.lower() != "y":
        print("Aborted.")
        return

    # Fix each file
    fixed_count = 0
    for filepath, issues in files_with_issues:
        try:
            if fix_test_file(filepath, issues):
                print(f"✅ Fixed {filepath.name}")
                fixed_count += 1
            else:
                print(f"⚠️  No changes needed for {filepath.name}")
        except Exception as e:
            print(f"❌ Error fixing {filepath.name}: {e}")

    print(f"\n✨ Fixed {fixed_count} files!")

    # Create a verification script
    verify_script = '''#!/usr/bin/env python3
"""Verify that all tests still pass after client name fixes."""

import subprocess
import sys

def run_tests():
    # Run a subset of tests that were modified
    test_files = [
        "tests/test_auth_error_paths.py",
        "tests/test_mcp_client_oauth.py",
        "tests/test_mcp_echo_client_full.py",
        "tests/test_sacred_seals_compliance.py",
    ]

    print("🧪 Running modified tests to verify fixes...")

    for test_file in test_files:
        print(f"\\nTesting {test_file}...")
        result = subprocess.run(
            ["just", "test", test_file, "-v"],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            print(f"❌ {test_file} failed!")
            print(result.stdout)
            print(result.stderr)
            return False
        else:
            print(f"✅ {test_file} passed!")

    return True

if __name__ == "__main__":
    if run_tests():
        print("\\n✅ All modified tests pass!")
    else:
        print("\\n❌ Some tests failed. Please check the output above.")
        sys.exit(1)
'''

    verify_path = Path("scripts/verify_client_fixes.py")
    verify_path.write_text(verify_script)
    verify_path.chmod(0o755)

    print(f"\n📝 Created verification script: {verify_path}")
    print("   Run it with: python scripts/verify_client_fixes.py")

    print("\n🎯 Next steps:")
    print("1. Run the verification script to ensure tests still pass")
    print("2. Run parallel tests: just test-n 4")
    print("3. Check for any remaining conflicts")


if __name__ == "__main__":
    main()
