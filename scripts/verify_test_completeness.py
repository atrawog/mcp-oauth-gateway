#!/usr/bin/env python3
"""Sacred Test Completeness Verifier - Ensures tests follow CLAUDE.md.

This script checks that tests verify ACTUAL results, not just status codes!
"""

import ast
import sys
from pathlib import Path


class TestCompletenessChecker(ast.NodeVisitor):
    """Check tests for completeness violations."""

    def __init__(self, filename):
        self.filename = filename
        self.violations = []
        self.current_function = None
        self.has_status_check = False
        self.has_content_check = False
        self.has_functionality_check = False

    def visit_FunctionDef(self, node):
        if node.name.startswith("test_"):
            self.current_function = node.name
            self.has_status_check = False
            self.has_content_check = False
            self.has_functionality_check = False

            # Visit the function body
            self.generic_visit(node)

            # Check for violations after visiting the function
            if self.has_status_check and not (self.has_content_check or self.has_functionality_check):
                self.violations.append(
                    {
                        "function": self.current_function,
                        "line": node.lineno,
                        "issue": "Only checks status code - MUST verify actual functionality!",
                    }
                )

            self.current_function = None
        else:
            self.generic_visit(node)

    def visit_Compare(self, node):
        """Check for status code comparisons."""
        if self.current_function:
            # Check if comparing status_code
            if isinstance(node.left, ast.Attribute) and (
                hasattr(node.left.value, "attr")
                and node.left.value.attr == "response"
                and node.left.attr == "status_code"
            ):
                self.has_status_check = True

        self.generic_visit(node)

    def visit_Assert(self, node):
        """Check what assertions are verifying."""
        if self.current_function and isinstance(node.test, ast.Compare):
            # Check if asserting on content/result
            if isinstance(node.test.left, ast.Str):
                return

            # Look for content/result checks
            if isinstance(node.test.left, ast.Name):
                if node.test.left.id in ["content", "result", "data", "body"]:
                    self.has_content_check = True

            # Look for "in" comparisons (e.g., "Example Domain" in content)
            for op in node.test.ops:
                if isinstance(op, ast.In):
                    self.has_content_check = True

        self.generic_visit(node)

    def visit_Call(self, node):
        """Check for JSON parsing and result validation."""
        if self.current_function and isinstance(node.func, ast.Attribute) and node.func.attr == "json":
            # Check for response.json() calls
            self.has_functionality_check = True

        self.generic_visit(node)


def check_test_file(filepath):
    """Check a single test file for completeness."""
    with open(filepath) as f:
        content = f.read()

    # Skip files that are properly marked as failing
    if "pytest.fail(" in content and "SACRED VIOLATION" in content:
        return []

    try:
        tree = ast.parse(content)
        checker = TestCompletenessChecker(filepath)
        checker.visit(tree)
        return checker.violations
    except SyntaxError as e:
        print(f"❌ Syntax error in {filepath}: {e}")
        return []


def main():
    """Check all test files for completeness violations."""
    test_dir = Path(__file__).parent.parent / "tests"
    violations_found = False

    print("=" * 64)
    print("SACRED TEST COMPLETENESS VERIFICATION")
    print("According to CLAUDE.md: Tests MUST verify actual functionality!")
    print("=" * 64)
    print()

    test_files = list(test_dir.glob("test_*.py"))

    for test_file in sorted(test_files):
        # Skip conftest and constants
        if test_file.name in ["conftest.py", "test_constants.py"]:
            continue

        violations = check_test_file(test_file)

        if violations:
            violations_found = True
            print(f"\n❌ VIOLATIONS in {test_file.name}:")
            for v in violations:
                print(f"   Line {v['line']}: {v['function']}()")
                print(f"   Issue: {v['issue']}")

    if violations_found:
        print("\n" + "=" * 64)
        print("VIOLATIONS FOUND! Tests are incomplete!")
        print("Tests MUST:")
        print("  1. Check actual response content, not just status codes")
        print("  2. Verify the functionality actually works")
        print("  3. Use REAL OAuth tokens, not fakes")
        print("  4. FAIL if the functionality doesn't work 100%")
        print("=" * 64)
        return 1
    print("\n✅ All tests appear to check actual functionality!")
    print("   (This is a basic check - manual review still recommended)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
