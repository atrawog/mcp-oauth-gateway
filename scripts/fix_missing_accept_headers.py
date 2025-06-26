#!/usr/bin/env python3
"""Fix remaining MCP test files that are missing Accept headers.

This is a more targeted fix specifically for the Accept header issue
that wasn't fully caught by the previous script.
"""

import os
import re
from pathlib import Path

def fix_headers_in_file(file_path: Path):
    """Fix headers in a single file."""
    print(f"🔧 Fixing headers in {file_path.name}...")
    
    content = file_path.read_text()
    original_content = content
    fixes_applied = []
    
    # Pattern 1: Headers with Authorization, Content-Type, and MCP-Protocol-Version but no Accept
    pattern1 = r'headers\s*=\s*\{([^}]*"Authorization"[^}]*"Content-Type"[^}]*"MCP-Protocol-Version"[^}]*)\}'
    matches = list(re.finditer(pattern1, content, re.DOTALL))
    
    for match in reversed(matches):
        headers_content = match.group(1)
        if '"Accept"' not in headers_content and "'Accept'" not in headers_content:
            # Add Accept header
            # Find the last header line and add Accept after it
            lines = headers_content.strip().split('\n')
            last_line = lines[-1].strip()
            
            if last_line.endswith(','):
                new_accept_line = '                "Accept": "application/json, text/event-stream",'
            else:
                # Add comma to last line and new Accept line
                lines[-1] = last_line + ','
                new_accept_line = '                "Accept": "application/json, text/event-stream",'
            
            lines.append(new_accept_line)
            new_headers_content = '\n'.join(lines)
            
            # Replace in content
            old_headers_block = match.group(0)
            new_headers_block = f"headers = {{{new_headers_content}}}"
            content = content.replace(old_headers_block, new_headers_block)
            fixes_applied.append("Added Accept header to headers with Content-Type and MCP-Protocol-Version")
    
    # Pattern 2: Headers with only Authorization, Content-Type but no Accept
    pattern2 = r'headers\s*=\s*\{([^}]*"Authorization"[^}]*"Content-Type"[^}]*)(?!"Accept")([^}]*)\}'
    matches = list(re.finditer(pattern2, content, re.DOTALL))
    
    for match in reversed(matches):
        full_headers = match.group(0)
        if '"Accept"' not in full_headers and "'Accept'" not in full_headers:
            # Extract the headers content
            headers_content = re.search(r'headers\s*=\s*\{([^}]*)\}', full_headers, re.DOTALL).group(1)
            
            # Add Accept header
            lines = headers_content.strip().split('\n')
            last_line = lines[-1].strip()
            
            if last_line.endswith(','):
                new_accept_line = '                "Accept": "application/json, text/event-stream",'
            else:
                lines[-1] = last_line + ','
                new_accept_line = '                "Accept": "application/json, text/event-stream",'
            
            lines.append(new_accept_line)
            new_headers_content = '\n'.join(lines)
            
            new_headers_block = f"headers = {{{new_headers_content}}}"
            content = content.replace(full_headers, new_headers_block)
            fixes_applied.append("Added Accept header to headers with Authorization and Content-Type")
    
    # Save if changes were made
    if content != original_content:
        file_path.write_text(content)
        print(f"  ✅ Applied {len(fixes_applied)} fixes:")
        for fix in fixes_applied:
            print(f"    - {fix}")
        return True
    else:
        print(f"  ℹ️  No additional fixes needed")
        return False

def main():
    """Fix all MCP test files."""
    print("🔍 Finding MCP test files that still need Accept header fixes...")
    
    test_dir = Path("/home/atrawog/mcp-oauth-gateway/tests")
    
    # Focus on the files we know have issues
    problem_files = [
        "test_mcp_client_proxy.py",
        "test_mcp_client_oauth.py", 
        "test_mcp_protocol_compliance.py",
        "test_mcp_proxy.py",
    ]
    
    fixed_count = 0
    for filename in problem_files:
        file_path = test_dir / filename
        if file_path.exists():
            if fix_headers_in_file(file_path):
                fixed_count += 1
        else:
            print(f"⚠️  File not found: {filename}")
    
    print(f"\n✅ Fixed {fixed_count} additional files")
    print("🎯 This should resolve the remaining 400 Bad Request errors!")

if __name__ == "__main__":
    main()