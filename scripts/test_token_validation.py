#!/usr/bin/env python3
"""Test that pytest fails early with invalid tokens."""

import os
import subprocess
import sys

# Colors
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RESET = "\033[0m"

def test_invalid_token_behavior():
    """Test what happens when we run pytest with an invalid token."""
    # Save current token
    original_token = os.environ.get("GATEWAY_OAUTH_ACCESS_TOKEN", "")
    
    # Test 1: Missing token
    print(f"\n{YELLOW}Test 1: Running pytest with missing token...{RESET}")
    os.environ.pop("GATEWAY_OAUTH_ACCESS_TOKEN", None)
    
    result = subprocess.run(
        ["pixi", "run", "pytest", "--collect-only"],
        capture_output=True,
        text=True
    )
    
    print(f"Exit code: {result.returncode}")
    if "Token validation failed" in result.stderr or result.returncode != 0:
        print(f"{GREEN}✓ Pytest failed early as expected{RESET}")
    else:
        print(f"{RED}✗ Pytest did not fail early!{RESET}")
    
    # Test 2: Invalid token
    print(f"\n{YELLOW}Test 2: Running pytest with invalid token...{RESET}")
    os.environ["GATEWAY_OAUTH_ACCESS_TOKEN"] = "invalid.token.here"
    
    result = subprocess.run(
        ["pixi", "run", "pytest", "--collect-only"],
        capture_output=True,
        text=True
    )
    
    print(f"Exit code: {result.returncode}")
    if "Token validation failed" in result.stderr or result.returncode != 0:
        print(f"{GREEN}✓ Pytest failed early as expected{RESET}")
    else:
        print(f"{RED}✗ Pytest did not fail early!{RESET}")
    
    # Test 3: Expired token
    print(f"\n{YELLOW}Test 3: Running pytest with expired token...{RESET}")
    # Create an expired JWT (exp set to past)
    expired_token = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0IiwiZXhwIjoxMDAwMDAwMDAwfQ.invalid"
    os.environ["GATEWAY_OAUTH_ACCESS_TOKEN"] = expired_token
    
    result = subprocess.run(
        ["pixi", "run", "pytest", "--collect-only"],
        capture_output=True,
        text=True
    )
    
    print(f"Exit code: {result.returncode}")
    if "Token validation failed" in result.stderr or result.returncode != 0:
        print(f"{GREEN}✓ Pytest failed early as expected{RESET}")
    else:
        print(f"{RED}✗ Pytest did not fail early!{RESET}")
    
    # Restore original token
    if original_token:
        os.environ["GATEWAY_OAUTH_ACCESS_TOKEN"] = original_token
    
    print(f"\n{YELLOW}Analysis of pytest stderr output:{RESET}")
    print(result.stderr[:500] if result.stderr else "No stderr output")

if __name__ == "__main__":
    test_invalid_token_behavior()