#!/usr/bin/env python3
"""Comment out tests that use httpbin.org."""

import re
from pathlib import Path


def comment_out_test_method(content, test_name):
    """Comment out a specific test method."""
    # Find the test method start
    pattern = rf"(\n?)([ \t]*@pytest\.mark\.[^\n]*\n)*([ \t]*async def {test_name}\([^)]*\):[^\n]*\n)"

    match = re.search(pattern, content, re.MULTILINE)
    if not match:
        return content, False

    start_pos = match.start()
    indent = len(match.group(3)) - len(match.group(3).lstrip())

    # Find the end of the method (next method or class at same or lower indentation)
    end_pattern = rf"\n(?=[ \t]{{0,{indent}}}(?:async )?def|[ \t]{{0,{indent}}}class|\Z)"
    end_match = re.search(end_pattern, content[match.end() :])

    end_pos = match.end() + end_match.start() if end_match else len(content)

    # Extract the test method
    test_method = content[start_pos:end_pos]

    # Comment it out
    lines = test_method.split("\n")
    commented_lines = []

    # Add explanation at the top
    if lines[0].strip() == "":
        commented_lines.append("")
    commented_lines.extend(
        [
            f"{' ' * indent}# REMOVED: This test used httpbin.org which violates our testing principles.",
            f"{' ' * indent}# Per CLAUDE.md: Test against real deployed services (our own), not external ones.",
        ]
    )

    # Comment out each line
    for line in lines:
        if line.strip():
            commented_lines.append(f"{' ' * indent}# {line[indent:] if len(line) > indent else line}")
        else:
            commented_lines.append(f"{' ' * indent}#")

    # Replace in content
    new_content = content[:start_pos] + "\n".join(commented_lines) + content[end_pos:]

    return new_content, True


def main():
    """Comment out httpbin.org tests."""
    files_to_process = [
        (
            "tests/test_mcp_fetchs_real_content.py",
            [
                "test_fetchs_httpbin_endpoints",
                "test_fetchs_redirect_following",
                "test_fetchs_different_content_types",
                "test_fetchs_response_size_handling",
                "test_fetchs_status_code_handling",
            ],
        ),
        (
            "tests/test_mcp_fetchs_complete.py",
            [
                "test_fetchs_with_mcp_client_token",
                "test_fetchs_max_length_parameter",
                "test_fetchs_custom_headers_and_user_agent",
                "test_fetchs_post_method_with_body",
                "test_fetchs_error_handling",
                "test_fetchs_concurrent_requests",
            ],
        ),
        ("tests/test_mcp_fetchs_mcp_compliance.py", ["test_mcp_fetchs_tool_definition"]),
        ("tests/test_mcp_fetchs_security.py", ["test_fetchs_header_injection_prevention"]),
    ]

    for file_path, test_names in files_to_process:
        path = Path(file_path)
        if not path.exists():
            print(f"✗ File not found: {file_path}")
            continue

        with open(path) as f:
            content = f.read()

        modified = False

        for test_name in test_names:
            content, changed = comment_out_test_method(content, test_name)
            if changed:
                print(f"  ✓ Commented out {test_name}")
                modified = True
            else:
                print(f"  ✗ Could not find {test_name}")

        if modified:
            with open(path, "w") as f:
                f.write(content)
            print(f"✓ Modified {file_path}")
        else:
            print(f"  No changes made to {file_path}")


if __name__ == "__main__":
    main()
