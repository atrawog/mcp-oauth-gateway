#!/usr/bin/env python3
"""
Capture MCP client environment variables from command output and save to .env
This version supports interactive input (e.g., entering authorization codes)
"""
import subprocess
import sys
import re
import os
import tempfile
from pathlib import Path

ENV_FILE = Path(__file__).parent.parent / ".env"

def save_env_var(key: str, value: str):
    """Save or update an environment variable in .env file"""
    lines = []
    found = False
    
    if ENV_FILE.exists():
        with open(ENV_FILE) as f:
            for line in f:
                if line.strip().startswith(f"{key}="):
                    lines.append(f"{key}={value}\n")
                    found = True
                else:
                    lines.append(line)
    
    if not found:
        lines.append(f"\n{key}={value}\n")
    
    with open(ENV_FILE, "w") as f:
        f.writelines(lines)

def extract_env_vars(output: str):
    """Extract export statements from output"""
    env_vars = {}
    pattern = r'^export\s+(MCP_CLIENT_[A-Z_]+)=(.+)$'
    
    for line in output.split('\n'):
        match = re.match(pattern, line.strip())
        if match:
            key = match.group(1)
            value = match.group(2).strip()
            # Skip empty or None values
            if value and value != "None":
                env_vars[key] = value
    
    return env_vars

def main():
    # Get command from arguments
    if len(sys.argv) < 2:
        print("Usage: capture_mcp_env_interactive.py <command...>")
        sys.exit(1)
    
    # Pass environment variables through
    env = os.environ.copy()
    
    # Create a temporary file to capture output
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as tmp_file:
        tmp_filename = tmp_file.name
    
    try:
        # Run the command with tee to capture output while allowing interaction
        # Use script command to preserve interactivity
        cmd = ['script', '-q', '-c', ' '.join(sys.argv[1:]), tmp_filename]
        
        # Run with full terminal interaction
        result = subprocess.run(cmd, env=env)
        
        # Read the captured output
        with open(tmp_filename, 'r') as f:
            output = f.read()
        
        # Clean ANSI escape sequences from script output
        import re
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        output = ansi_escape.sub('', output)
        
        # Extract and save environment variables
        env_vars = extract_env_vars(output)
        
        if env_vars:
            print(f"\n📝 Saving {len(env_vars)} MCP client variables to .env...")
            for key, value in env_vars.items():
                save_env_var(key, value)
                print(f"   ✅ Saved {key}")
            print("\n✅ MCP client credentials saved to .env!")
        else:
            print("\n⚠️  No MCP client variables found in output")
            
        sys.exit(result.returncode)
        
    finally:
        # Clean up temp file
        if os.path.exists(tmp_filename):
            os.unlink(tmp_filename)

if __name__ == "__main__":
    main()