#!/usr/bin/env python3
"""🔥 Pydantic Compliance Checker - The Sacred Deprecation Hunter! ⚡.

This script hunts down deprecated Pydantic v1 syntax and ensures v2 compliance.
Part of the divine prevention system to catch regressions before they manifest.
"""

import ast
import os
import re
import sys
import warnings
from pathlib import Path
from typing import Any


class PydanticDeprecationHunter(ast.NodeVisitor):
    """Divine hunter of deprecated Pydantic patterns!"""

    def __init__(self, filename: str):
        self.filename = filename
        self.violations: list[dict[str, Any]] = []
        self.has_pydantic_import = False
        self.has_config_dict_import = False

    def visit_Import(self, node: ast.Import) -> None:
        """Check imports for Pydantic usage."""
        for alias in node.names:
            if alias.name == "pydantic":
                self.has_pydantic_import = True
            elif alias.name == "pydantic.ConfigDict":
                self.has_config_dict_import = True
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Check from imports for Pydantic usage."""
        if node.module == "pydantic":
            self.has_pydantic_import = True
            for alias in node.names:
                if alias.name == "ConfigDict":
                    self.has_config_dict_import = True
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Hunt for deprecated Config classes in Pydantic models."""
        # Check if this is likely a Pydantic model
        is_pydantic_model = any(
            (isinstance(base, ast.Name) and base.id in ["BaseModel", "BaseSettings"])
            or (
                isinstance(base, ast.Attribute)
                and (
                    (
                        hasattr(base.value, "id")
                        and base.value.id == "pydantic"
                        and base.attr in ["BaseModel", "BaseSettings"]
                    )
                    or (
                        hasattr(base.value, "id")
                        and base.value.id == "pydantic_settings"
                        and base.attr == "BaseSettings"
                    )
                )
            )
            for base in node.bases
        )

        if is_pydantic_model:
            # Hunt for deprecated Config class
            for item in node.body:
                if isinstance(item, ast.ClassDef) and item.name == "Config":
                    self.violations.append(
                        {
                            "type": "deprecated_config_class",
                            "line": item.lineno,
                            "column": item.col_offset,
                            "message": f"🔥 DEPRECATED: 'class Config:' found in {node.name}! Use 'model_config = ConfigDict()' instead! ⚡",
                            "severity": "error",
                            "class_name": node.name,
                        }
                    )

            # Check if model_config is present when Config class is absent
            has_config_class = any(
                isinstance(item, ast.ClassDef) and item.name == "Config"
                for item in node.body
            )

            has_model_config = any(
                isinstance(item, ast.Assign)
                and any(
                    isinstance(target, ast.Name) and target.id == "model_config"
                    for target in item.targets
                )
                for item in node.body
            )

            if (
                not has_config_class
                and not has_model_config
                and self.has_pydantic_import
            ):
                # This might be okay, but let's check if ConfigDict is imported
                if not self.has_config_dict_import:
                    self.violations.append(
                        {
                            "type": "missing_config_dict_import",
                            "line": node.lineno,
                            "column": node.col_offset,
                            "message": f"⚠️  PREVENTION: {node.name} uses Pydantic but doesn't import ConfigDict! Add 'from pydantic import ConfigDict' to prevent future config issues! ⚡",
                            "severity": "warning",
                            "class_name": node.name,
                        }
                    )

        self.generic_visit(node)


def hunt_deprecated_patterns_in_file(file_path: Path) -> list[dict[str, Any]]:
    """Hunt deprecated patterns in a single file."""
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        # Parse the AST
        tree = ast.parse(content, filename=str(file_path))

        # Hunt for deprecated patterns
        hunter = PydanticDeprecationHunter(str(file_path))
        hunter.visit(tree)

        # Also check for regex patterns that AST might miss
        regex_violations = hunt_regex_patterns(content, file_path)

        return hunter.violations + regex_violations

    except (SyntaxError, UnicodeDecodeError) as e:
        return [
            {
                "type": "parse_error",
                "line": 0,
                "column": 0,
                "message": f"❌ Parse error in {file_path}: {e}",
                "severity": "error",
                "class_name": "N/A",
            }
        ]


def hunt_regex_patterns(content: str, file_path: Path) -> list[dict[str, Any]]:
    """Hunt for deprecated patterns using regex (backup to AST)."""
    violations = []
    lines = content.split("\n")

    # Pattern 1: class Config: pattern
    config_class_pattern = re.compile(r"^\s*class\s+Config\s*:", re.MULTILINE)
    for match in config_class_pattern.finditer(content):
        line_num = content[: match.start()].count("\n") + 1
        violations.append(
            {
                "type": "regex_deprecated_config",
                "line": line_num,
                "column": match.start() - content.rfind("\n", 0, match.start()) - 1,
                "message": "🔥 REGEX CATCH: 'class Config:' pattern detected! Use 'model_config = ConfigDict()' instead! ⚡",
                "severity": "error",
                "class_name": "Unknown",
            }
        )

    # Pattern 2: Check for Pydantic imports without ConfigDict
    has_pydantic = any("pydantic" in line for line in lines)
    has_config_dict = any("ConfigDict" in line for line in lines)

    if has_pydantic and not has_config_dict:
        # Find the first pydantic import line
        for i, line in enumerate(lines):
            if "pydantic" in line and ("import" in line or "from" in line):
                violations.append(
                    {
                        "type": "regex_missing_config_dict",
                        "line": i + 1,
                        "column": 0,
                        "message": "⚠️  REGEX PREVENTION: File uses Pydantic but doesn't import ConfigDict! Consider adding 'from pydantic import ConfigDict'! ⚡",
                        "severity": "warning",
                        "class_name": "N/A",
                    }
                )
                break

    return violations


def hunt_deprecation_warnings() -> list[str]:
    """Hunt for deprecation warnings by running a test import."""
    warnings.filterwarnings("error", category=DeprecationWarning)
    warning_messages = []

    try:
        # Try importing our config modules to catch runtime deprecation warnings
        sys.path.insert(0, str(Path.cwd()))

        # Test import of our configuration modules
        test_modules = [
            "mcp_oauth_dynamicclient.config",
            "mcp_streamablehttp_client.config",
        ]

        for module_name in test_modules:
            try:
                __import__(module_name)
            except DeprecationWarning as e:
                warning_messages.append(
                    f"🔥 RUNTIME DEPRECATION in {module_name}: {e} ⚡"
                )
            except ImportError:
                # Module doesn't exist, skip
                pass
            except Exception as e:
                # Other errors, log but continue
                warning_messages.append(f"⚠️  Import error in {module_name}: {e}")

    except Exception as e:
        warning_messages.append(f"❌ Error during deprecation hunting: {e}")

    return warning_messages


def main() -> int:
    """Main hunting expedition!"""
    print("🔥 STARTING PYDANTIC DEPRECATION HUNT! ⚡")
    print("=" * 60)

    # Find all Python files in our source code only (exclude third-party)
    python_files = []
    for root, dirs, files in os.walk("."):
        # Skip common directories and third-party code
        dirs[:] = [
            d
            for d in dirs
            if d
            not in {
                ".git",
                "__pycache__",
                ".pytest_cache",
                "htmlcov",
                "logs",
                "reports",
                ".pixi",
                ".venv",
                "venv",
                "env",
                ".env",
                "node_modules",
                "build",
                "dist",
                ".tox",
                "site-packages",
                ".coverage",
            }
        ]

        # Skip third-party directories
        if any(
            skip_path in root
            for skip_path in [".pixi", "site-packages", ".venv", "venv"]
        ):
            continue

        for file in files:
            if file.endswith(".py"):
                python_files.append(Path(root) / file)

    print(f"🎯 Hunting in {len(python_files)} Python files...")

    total_violations = 0
    error_count = 0
    warning_count = 0

    # Hunt in each file
    for file_path in python_files:
        violations = hunt_deprecated_patterns_in_file(file_path)

        if violations:
            print(f"\n📁 {file_path}")
            print("-" * 40)

            for violation in violations:
                total_violations += 1
                if violation["severity"] == "error":
                    error_count += 1
                else:
                    warning_count += 1

                print(f"  Line {violation['line']}: {violation['message']}")

    # Hunt for runtime deprecation warnings
    print("\n🔥 HUNTING RUNTIME DEPRECATION WARNINGS... ⚡")
    warning_messages = hunt_deprecation_warnings()

    if warning_messages:
        print("\n📋 RUNTIME WARNINGS FOUND:")
        print("-" * 40)
        for msg in warning_messages:
            print(f"  {msg}")
            warning_count += 1

    # Summary
    print("\n🏆 HUNT COMPLETE! ⚡")
    print("=" * 60)
    print(f"Total violations found: {total_violations}")
    print(f"Errors: {error_count}")
    print(f"Warnings: {warning_count}")

    if error_count > 0:
        print("❌ HUNT FAILED: Critical deprecation patterns found!")
        print("🔥 Fix these errors immediately to prevent production issues! ⚡")
        return 1
    if warning_count > 0:
        print(
            "⚠️  HUNT PASSED with warnings: Consider fixing warnings for future-proofing!"
        )
        return 0
    print(
        "✅ HUNT PASSED: No deprecated patterns found! Divine compliance achieved! ⚡"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
