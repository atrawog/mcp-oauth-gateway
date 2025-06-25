#!/usr/bin/env python3
"""
Final comprehensive fix for all error response patterns.

OAuth 2.0 compliant format: {"error": "...", "error_description": "..."}
Tests should NOT expect: {"detail": {"error": "...", "error_description": "..."}}
"""

import re
from pathlib import Path


def fix_all_patterns(content: str) -> str:
    """Fix all error response patterns comprehensively."""
    
    # Pattern 1: error.get("detail", {}).get("error_description", ...)
    content = re.sub(
        r'error\.get\("detail", \{\}\)\.get\(\s*"error_description"[^)]*\)',
        'error.get("error_description", "")',
        content
    )
    
    # Pattern 2: error.get("detail", {}).get("error", ...)
    content = re.sub(
        r'error\.get\("detail", \{\}\)\.get\(\s*"error"[^)]*\)',
        'error.get("error", "")',
        content
    )
    
    # Pattern 3: Multi-line patterns with assertions
    # "... in error.get("detail", {}).get("error_description", "")"
    content = re.sub(
        r'in error\.get\("detail", \{\}\)\.get\(\s*"error_description"[^)]*\)',
        'in error.get("error_description", "")',
        content
    )
    
    # Pattern 4: Handle cases where the pattern is split across lines
    lines = content.split('\n')
    fixed_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Check for multi-line error.get("detail", {}).get patterns
        if 'error.get("detail", {}).get(' in line and line.strip().endswith('('):
            # This line starts a multi-line pattern
            j = i + 1
            # Find the closing parenthesis
            while j < len(lines) and ')' not in lines[j]:
                j += 1
            
            # Reconstruct the pattern
            full_pattern = ' '.join(lines[i:j+1])
            
            # Fix it
            if '"error_description"' in full_pattern:
                fixed = re.sub(
                    r'error\.get\("detail", \{\}\)\.get\(\s*"error_description"[^)]*\)',
                    'error.get("error_description", "")',
                    full_pattern
                )
            elif '"error"' in full_pattern:
                fixed = re.sub(
                    r'error\.get\("detail", \{\}\)\.get\(\s*"error"[^)]*\)',
                    'error.get("error", "")',
                    full_pattern
                )
            else:
                fixed = full_pattern
            
            # Replace the lines
            fixed_lines.append(fixed)
            i = j + 1
        else:
            fixed_lines.append(line)
            i += 1
    
    content = '\n'.join(fixed_lines)
    
    # Pattern 5: json_response["detail"]["error_description"] patterns
    content = re.sub(
        r'json_response\["detail"\]\["error_description"\]',
        'json_response["error_description"]',
        content
    )
    
    # Pattern 6: json_response["detail"]["error"] patterns
    content = re.sub(
        r'json_response\["detail"\]\["error"\]',
        'json_response["error"]',
        content
    )
    
    # Pattern 7: Fix test_coverage_improvements.py specific pattern
    # where it checks both formats
    content = re.sub(
        r'if "detail" in json_response:\s*assert json_response\["error"\] == "([^"]+)"\s*else:\s*assert json_response\["error"\] == "\1"',
        'assert json_response["error"] == "\\1"',
        content,
        flags=re.MULTILINE | re.DOTALL
    )
    
    return content


def main():
    """Fix all test files."""
    tests_dir = Path("/home/atrawog/AI/atrawog/mcp-oauth-gateway/tests")
    
    # Find all Python test files
    test_files = list(tests_dir.glob("test_*.py"))
    
    fixed_count = 0
    
    for test_file in test_files:
        original_content = test_file.read_text()
        fixed_content = fix_all_patterns(original_content)
        
        if fixed_content != original_content:
            test_file.write_text(fixed_content)
            print(f"Fixed: {test_file.name}")
            fixed_count += 1
    
    print(f"\nFixed {fixed_count} test files")
    print("All error response patterns should now match OAuth 2.0 format")


if __name__ == "__main__":
    main()