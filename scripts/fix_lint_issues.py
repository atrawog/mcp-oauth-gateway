#!/usr/bin/env python3
"""Script to systematically fix common lint issues based on root cause analysis."""

import re
from pathlib import Path


def fix_arg002_in_tests(content: str) -> str:
    """Fix ARG002 errors for pytest fixtures in test files.
    
    Root cause: Pytest fixtures like wait_for_services are dependency injection
    that ensure preconditions but don't need explicit usage in test body.
    """
    # Pattern to find test method parameters that commonly cause ARG002
    patterns = [
        # wait_for_services fixture
        (r'(\s+)(wait_for_services)(,?)(\s*)$', r'\1\2,  # noqa: ARG002\3\4'),
        (r'(\s+)(wait_for_services)(\):)', r'\1\2,  # noqa: ARG002\3'),
        # Other common fixture parameters that might not be used
        (r'(\s+)(capsys|caplog|tmp_path|monkeypatch)(,?)(\s*)$',
         r'\1\2,  # noqa: ARG002\3\4'),
    ]

    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE)

    return content


def fix_http_status_codes(content: str) -> str:
    """Replace magic numbers with HTTP status constants.
    
    Root cause: Hardcoded HTTP status codes reduce maintainability.
    """
    # Add import if not present
    if "from .test_constants import" in content and "HTTP_" not in content:
        # Find the last test_constants import line
        import_pattern = r'(from \.test_constants import .*?)(\n)'
        match = re.search(import_pattern, content)
        if match:
            imports = match.group(1)
            # Add HTTP constants to imports
            new_imports = imports + "\nfrom .test_constants import HTTP_OK"
            new_imports += "\nfrom .test_constants import HTTP_CREATED"
            new_imports += "\nfrom .test_constants import HTTP_NO_CONTENT"
            new_imports += "\nfrom .test_constants import HTTP_UNAUTHORIZED"
            new_imports += "\nfrom .test_constants import HTTP_NOT_FOUND"
            new_imports += "\nfrom .test_constants import HTTP_UNPROCESSABLE_ENTITY"
            content = content.replace(imports, new_imports)

    # Replace common status codes
    replacements = [
        (r'status_code == 200\b', 'status_code == HTTP_OK'),
        (r'status_code == 201\b', 'status_code == HTTP_CREATED'),
        (r'status_code == 204\b', 'status_code == HTTP_NO_CONTENT'),
        (r'status_code == 400\b', 'status_code == HTTP_BAD_REQUEST'),
        (r'status_code == 401\b', 'status_code == HTTP_UNAUTHORIZED'),
        (r'status_code == 403\b', 'status_code == HTTP_FORBIDDEN'),
        (r'status_code == 404\b', 'status_code == HTTP_NOT_FOUND'),
        (r'status_code == 422\b', 'status_code == HTTP_UNPROCESSABLE_ENTITY'),
        (r'status_code == 500\b', 'status_code == HTTP_INTERNAL_SERVER_ERROR'),
    ]

    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content)

    return content


def fix_docstring_formatting(content: str) -> str:
    """Fix D205 errors - add blank line after docstring summary.
    
    Root cause: PEP 257 requires blank line after summary in multi-line docstrings.
    """
    # Pattern: """Summary line\nMore text without blank line
    pattern = r'("""[^"\n]+)\n(\s+)([^"\s])'
    replacement = r'\1\n\n\2\3'

    return re.sub(pattern, replacement, content)


def fix_line_length(content: str) -> str:
    """Fix E501 errors - break long lines.
    
    Root cause: Lines exceed 88 character limit.
    """
    lines = content.split('\n')
    fixed_lines = []

    for line in lines:
        if len(line) > 88:
            # Handle common patterns
            if 'assert' in line and '==' in line:
                # Break assertions after operators
                if ' == ' in line:
                    parts = line.split(' == ', 1)
                    if len(parts) == 2:
                        indent = len(line) - len(line.lstrip())
                        fixed_lines.append(parts[0] + ' ==')
                        fixed_lines.append(' ' * (indent + 4) + parts[1])
                        continue

            elif 'f"' in line or "f'" in line:
                # Break f-strings at logical points
                # This is complex, so just mark for manual review
                fixed_lines.append(line + '  # TODO: Break long line')
                continue

        fixed_lines.append(line)

    return '\n'.join(fixed_lines)


def fix_timeout_issues(content: str) -> str:
    """Add timeout to HTTP requests to fix S501.
    
    Root cause: HTTP requests without timeout can hang indefinitely.
    """
    # Pattern for httpx calls without timeout
    patterns = [
        # await http_client.get/post/put/delete without timeout
        (r'(await http_client\.(get|post|put|delete|patch)\([^)]+)(\))',
         r'\1, timeout=30.0\3'),
        # httpx.AsyncClient() without timeout
        (r'(httpx\.AsyncClient\(\s*)(\))',
         r'\1timeout=30.0\2'),
    ]

    for pattern, replacement in patterns:
        # Check if timeout not already present
        def replace_if_no_timeout(match):
            if 'timeout' not in match.group(0):
                return re.sub(pattern, replacement, match.group(0))
            return match.group(0)

        content = re.sub(pattern, replace_if_no_timeout, content)

    return content


def process_file(file_path: Path) -> None:
    """Process a single file to fix lint issues."""
    try:
        content = file_path.read_text()
        original_content = content

        # Apply fixes based on file type
        if file_path.name.startswith('test_'):
            content = fix_arg002_in_tests(content)
            content = fix_http_status_codes(content)

        # Apply general fixes
        content = fix_docstring_formatting(content)
        content = fix_line_length(content)

        if 'httpx' in content:
            content = fix_timeout_issues(content)

        # Write back if changed
        if content != original_content:
            file_path.write_text(content)
            print(f"Fixed: {file_path}")

    except Exception as e:
        print(f"Error processing {file_path}: {e}")


def main():
    """Main entry point."""
    # Process test files
    test_dir = Path("tests")
    if test_dir.exists():
        for test_file in test_dir.glob("test_*.py"):
            process_file(test_file)

    # Process source files
    for src_dir in Path(".").glob("*/src"):
        for py_file in src_dir.rglob("*.py"):
            process_file(py_file)


if __name__ == "__main__":
    main()
