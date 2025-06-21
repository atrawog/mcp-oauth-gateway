#!/usr/bin/env python3
"""Test script for mcp-streamablehttp-client."""

import os
import subprocess
import sys
import json

def test_mcp_client():
    """Test the MCP client with the everything server."""
    
    # Get credentials from environment
    server_url = "https://mcp-everything.atradev.org/mcp"
    token = os.getenv("MCP_CLIENT_ACCESS_TOKEN")
    
    if not token:
        print("Error: MCP_CLIENT_ACCESS_TOKEN not set in environment")
        return 1
    
    print(f"Testing MCP client with server: {server_url}")
    print(f"Token (first 20 chars): {token[:20]}...")
    
    # Test the authentication first
    print("\n1. Testing authentication...")
    cmd = [
        "pixi", "run", "mcp-streamablehttp-client",
        "--server-url", server_url,
        "--test-auth"
    ]
    
    env = os.environ.copy()
    env["MCP_SERVER_URL"] = server_url
    env["MCP_CLIENT_ACCESS_TOKEN"] = token
    
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    print(f"Auth test result: {result.returncode}")
    print(f"Stdout: {result.stdout}")
    if result.stderr:
        print(f"Stderr: {result.stderr}")
    
    # Test with --token flag
    print("\n2. Testing token status...")
    cmd = [
        "pixi", "run", "mcp-streamablehttp-client",
        "--server-url", server_url,
        "--token"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    print(f"Token test result: {result.returncode}")
    print(f"Stdout: {result.stdout}")
    if result.stderr:
        print(f"Stderr: {result.stderr}")
    
    # Try a simple command
    print("\n3. Testing a command...")
    cmd = [
        "pixi", "run", "mcp-streamablehttp-client",
        "--server-url", server_url,
        "--command", "echo test"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    print(f"Command result: {result.returncode}")
    print(f"Stdout: {result.stdout}")
    if result.stderr:
        print(f"Stderr: {result.stderr}")
    
    return 0

if __name__ == "__main__":
    sys.exit(test_mcp_client())