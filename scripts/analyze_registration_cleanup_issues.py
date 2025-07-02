#!/usr/bin/env python3
"""Analyze test files to identify OAuth registration cleanup issues.

This script examines all test files to find patterns where OAuth client
registrations might not be properly cleaned up.
"""

import ast
import re
from pathlib import Path


class RegistrationAnalyzer(ast.NodeVisitor):
    """AST visitor to analyze OAuth registration patterns in tests."""

    def __init__(self, filename: str):
        self.filename = filename
        self.issues = []
        self.uses_registered_client = False
        self.uses_context_manager = False
        self.has_cleanup = False
        self.registrations = []
        self.cleanups = []
        self.in_try_finally = False
        self.current_function = None

    def visit_FunctionDef(self, node):
        """Track current function."""
        old_function = self.current_function
        self.current_function = node.name
        self.generic_visit(node)
        self.current_function = old_function

    def visit_AsyncFunctionDef(self, node):
        """Track current async function."""
        old_function = self.current_function
        self.current_function = node.name

        # Check if using registered_client fixture
        if any(arg.arg == "registered_client" for arg in node.args.args):
            self.uses_registered_client = True

        self.generic_visit(node)
        self.current_function = old_function

    def visit_Call(self, node):
        """Detect registration and cleanup calls."""
        # Check for POST to /register
        if isinstance(node.func, ast.Attribute) and node.func.attr == "post" and len(node.args) > 0:
            # Check if it's a registration call
            if isinstance(node.args[0], ast.JoinedStr):
                for part in node.args[0].values:
                    if isinstance(part, ast.Constant) and "/register" in str(part.value):
                        self.registrations.append({"function": self.current_function, "line": node.lineno})

            elif isinstance(node.args[0], ast.Constant) and "/register" in str(node.args[0].value):
                self.registrations.append({"function": self.current_function, "line": node.lineno})

        # Check for DELETE to /register/{client_id}
        if isinstance(node.func, ast.Attribute) and node.func.attr == "delete" and len(node.args) > 0:
            if isinstance(node.args[0], ast.JoinedStr | ast.Constant):
                self.cleanups.append({"function": self.current_function, "line": node.lineno})
                self.has_cleanup = True

        # Check for RegisteredClientContext usage
        if isinstance(node.func, ast.Name) and node.func.id == "RegisteredClientContext":
            self.uses_context_manager = True

        self.generic_visit(node)

    def visit_Try(self, node):
        """Track try/finally blocks."""
        old_in_try_finally = self.in_try_finally
        if node.finalbody:
            self.in_try_finally = True
        self.generic_visit(node)
        self.in_try_finally = old_in_try_finally

    def analyze(self):
        """Analyze for potential issues."""
        if self.registrations and not (self.uses_registered_client or self.uses_context_manager):
            if not self.has_cleanup:
                self.issues.append(
                    {
                        "type": "NO_CLEANUP",
                        "message": f"Creates {len(self.registrations)} registration(s) without any cleanup",
                        "registrations": self.registrations,
                    }
                )
            elif len(self.cleanups) < len(self.registrations):
                self.issues.append(
                    {
                        "type": "INCOMPLETE_CLEANUP",
                        "message": f"Creates {len(self.registrations)} registration(s) but only has {len(self.cleanups)} cleanup(s)",
                        "registrations": self.registrations,
                        "cleanups": self.cleanups,
                    }
                )
            elif not self.in_try_finally:
                self.issues.append(
                    {
                        "type": "NO_TRY_FINALLY",
                        "message": "Has cleanup but not in try/finally block - won't clean on failure",
                        "registrations": self.registrations,
                        "cleanups": self.cleanups,
                    }
                )

        return self.issues


def analyze_file(filepath: Path) -> list[dict]:
    """Analyze a single test file for registration cleanup issues."""
    try:
        with open(filepath) as f:
            content = f.read()

        # Quick check if file might have registrations
        if "/register" not in content:
            return []

        tree = ast.parse(content)
        analyzer = RegistrationAnalyzer(str(filepath))
        analyzer.visit(tree)
        return analyzer.analyze()

    except Exception as e:
        print(f"Error analyzing {filepath}: {e}")
        return []


def find_test_client_patterns(filepath: Path) -> list[tuple[int, str]]:
    """Find lines that might create 'test-client' registrations."""
    patterns = []
    try:
        with open(filepath) as f:
            for line_num, line in enumerate(f, 1):
                # Look for patterns that might create simple "test-client" names
                if re.search(r'["\']test-client["\']', line, re.IGNORECASE) or (
                    "client_name" in line and "test" in line.lower()
                ):
                    patterns.append((line_num, line.strip()))
    except Exception:
        pass
    return patterns


def main():
    """Main analysis function."""
    print("🔍 Analyzing OAuth Registration Cleanup Issues\n")

    tests_dir = Path("/home/atrawog/mcp-oauth-gateway/tests")
    test_files = list(tests_dir.glob("test_*.py"))

    all_issues = {}
    test_client_files = []

    for filepath in sorted(test_files):
        issues = analyze_file(filepath)
        if issues:
            all_issues[filepath.name] = issues

        # Check for test-client patterns
        patterns = find_test_client_patterns(filepath)
        if patterns:
            test_client_files.append((filepath.name, patterns))

    # Report findings
    if all_issues:
        print("❌ Files with Registration Cleanup Issues:\n")
        for filename, issues in all_issues.items():
            print(f"📄 {filename}")
            for issue in issues:
                print(f"   ⚠️  {issue['type']}: {issue['message']}")
                if "registrations" in issue:
                    for reg in issue["registrations"]:
                        print(f"      - Registration at line {reg['line']} in {reg['function']}()")
                if "cleanups" in issue:
                    for cleanup in issue["cleanups"]:
                        print(f"      - Cleanup at line {cleanup['line']} in {cleanup['function']}()")
            print()
    else:
        print("✅ No obvious registration cleanup issues found!\n")

    if test_client_files:
        print("\n🔍 Files with 'test-client' Patterns:\n")
        for filename, patterns in test_client_files:
            print(f"📄 {filename}")
            for line_num, line in patterns:
                print(f"   Line {line_num}: {line}")
            print()

    # Summary
    print("\n📊 Summary:")
    print(f"   - Files analyzed: {len(test_files)}")
    print(f"   - Files with issues: {len(all_issues)}")
    print(f"   - Files with test-client patterns: {len(test_client_files)}")

    # Recommendations
    print("\n💡 Recommendations:")
    print("1. Always use 'registered_client' fixture or RegisteredClientContext for registrations")
    print("2. If manual cleanup is needed, always use try/finally blocks")
    print("3. Ensure every registration has a corresponding cleanup")
    print("4. Use unique client names with timestamps/UUIDs to avoid conflicts")
    print("5. Run 'just run cleanup_test_registrations' regularly to clean orphaned registrations")


if __name__ == "__main__":
    main()
