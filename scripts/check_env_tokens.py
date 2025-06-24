#!/usr/bin/env python3
"""Check environment tokens and categorize them as required vs testing."""

import os
import sys
from pathlib import Path


# Color codes for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"
BOLD = "\033[1m"

# Token categories
REQUIRED_TOKENS = {
    "GITHUB_CLIENT_ID": "GitHub OAuth App ID (create at github.com/settings/developers)",
    "GITHUB_CLIENT_SECRET": "GitHub OAuth App Secret (from the same OAuth App)",
    "GATEWAY_JWT_SECRET": "JWT signing secret (run: just generate-jwt-secret)",
    "JWT_PRIVATE_KEY_B64": "RSA private key for JWT (run: just generate-rsa-keys)",
    "REDIS_PASSWORD": "Redis authentication password (run: just generate-redis-password)",
    "BASE_DOMAIN": "Your actual domain (e.g., yourdomain.com)",
    "ACME_EMAIL": "Email for Let's Encrypt certificates",
    "ALLOWED_GITHUB_USERS": "Comma-separated GitHub users or * for all",
}

TESTING_TOKENS = {
    "GITHUB_PAT": "GitHub Personal Access Token (run: just generate-github-token)",
    "GATEWAY_OAUTH_ACCESS_TOKEN": "Test OAuth access token",
    "GATEWAY_OAUTH_REFRESH_TOKEN": "Test OAuth refresh token",
    "GATEWAY_OAUTH_CLIENT_ID": "Test OAuth client ID",
    "GATEWAY_OAUTH_CLIENT_SECRET": "Test OAuth client secret",
    "MCP_CLIENT_ACCESS_TOKEN": "MCP client test access token (run: just mcp-client-token)",
    "MCP_CLIENT_REFRESH_TOKEN": "MCP client test refresh token",
    "MCP_CLIENT_ID": "MCP test client ID",
    "MCP_CLIENT_SECRET": "MCP test client secret",
}

CONFIGURATION_TOKENS = {
    "JWT_ALGORITHM": "JWT algorithm (default: RS256)",
    "ACCESS_TOKEN_LIFETIME": "Access token lifetime in seconds",
    "REFRESH_TOKEN_LIFETIME": "Refresh token lifetime in seconds",
    "SESSION_TIMEOUT": "Session timeout in seconds",
    "CLIENT_LIFETIME": "Client registration lifetime (0 = eternal)",
    "MCP_PROTOCOL_VERSION": "MCP protocol version",
    "MCP_PROTOCOL_VERSIONS_SUPPORTED": "Supported MCP protocol versions",
    "MCP_CORS_ORIGINS": "CORS allowed origins",
}


def load_env() -> dict[str, str]:
    """Load environment variables from .env file."""
    env_vars = os.environ.copy()
    env_file = Path(".env")

    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    env_vars[key.strip()] = value.strip()

    return env_vars


def check_token(env_vars: dict[str, str], token: str, description: str) -> tuple[bool, str]:
    """Check if a token exists and return status."""
    value = env_vars.get(token, "")

    if not value:
        return False, f"{RED}✗ Missing{RESET}"
    if value.startswith("your_") or value.startswith("xxx...") or value == "":
        return False, f"{YELLOW}⚠ Not configured (placeholder value){RESET}"
    # Truncate for display
    if len(value) > 20:
        display_value = f"{value[:8]}...{value[-8:]}"
    else:
        display_value = value
    return True, f"{GREEN}✓ Set ({display_value}){RESET}"


def main():
    """Check all environment tokens."""
    print(f"\n{BOLD}🔍 MCP OAuth Gateway - Environment Token Check{RESET}\n")

    # Load environment
    env_vars = load_env()

    if not Path(".env").exists():
        print(f"{RED}✗ .env file not found!{RESET}")
        print(f"  Run: {BLUE}cp .env.example .env{RESET}")
        sys.exit(1)

    # Check required tokens
    print(f"{BOLD}🔴 REQUIRED TOKENS (Gateway won't start without these):{RESET}\n")
    required_missing = []

    for token, description in REQUIRED_TOKENS.items():
        exists, status = check_token(env_vars, token, description)
        if not exists:
            required_missing.append(token)
        print(f"  {token:30} {status}")
        print(f"  {'':<30} {description}\n")

    # Check configuration tokens
    print(f"\n{BOLD}🟡 CONFIGURATION TOKENS (Have defaults but should be reviewed):{RESET}\n")

    for token, description in CONFIGURATION_TOKENS.items():
        exists, status = check_token(env_vars, token, description)
        print(f"  {token:30} {status}")
        print(f"  {'':<30} {description}\n")

    # Check testing tokens
    print(f"\n{BOLD}🟢 TESTING TOKENS (Only needed for automated tests):{RESET}\n")

    for token, description in TESTING_TOKENS.items():
        exists, status = check_token(env_vars, token, description)
        print(f"  {token:30} {status}")
        print(f"  {'':<30} {description}\n")

    # Summary
    print(f"\n{BOLD}📊 SUMMARY:{RESET}\n")

    if required_missing:
        print(f"{RED}✗ Missing {len(required_missing)} required tokens:{RESET}")
        for token in required_missing:
            print(f"  - {token}")
        print(f"\n{YELLOW}To fix:{RESET}")
        print("  1. Create GitHub OAuth App at https://github.com/settings/developers")
        print(f"  2. Run: {BLUE}just generate-all-secrets{RESET}")
        print("  3. Edit .env and add GitHub client ID/secret")
        print(f"\n{RED}The gateway will NOT start without these tokens!{RESET}")
        sys.exit(1)
    else:
        print(f"{GREEN}✓ All required tokens are configured!{RESET}")
        print(f"\n{BLUE}The gateway can start with just these required tokens.{RESET}")
        print(f"{BLUE}Testing tokens are only needed if you plan to run the test suite.{RESET}")

        # Check if any testing tokens are configured
        test_tokens_configured = sum(1 for token in TESTING_TOKENS if check_token(env_vars, token, "")[0])
        if test_tokens_configured > 0:
            print(f"\n{GREEN}ℹ️  {test_tokens_configured} testing tokens are also configured.{RESET}")
        else:
            print(f"\n{YELLOW}ℹ️  No testing tokens configured (this is fine for production).{RESET}")
            print("  To run tests, generate test tokens with:")
            print(f"  - {BLUE}just generate-github-token{RESET} (for GitHub PAT)")
            print(f"  - {BLUE}just mcp-client-token{RESET} (for MCP client testing)")


if __name__ == "__main__":
    main()
