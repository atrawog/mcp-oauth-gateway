#!/usr/bin/env python3
"""Check if all requirements for running tests are met
According to CLAUDE.md - tests MUST use real OAuth tokens!
"""

import os
import sys

from dotenv import load_dotenv


# Load .env file
load_dotenv()


def check_oauth_token():
    """Check if GATEWAY_OAUTH_ACCESS_TOKEN or GATEWAY_OAUTH_JWT_TOKEN exists in environment."""
    token = os.getenv("GATEWAY_OAUTH_ACCESS_TOKEN") or os.getenv(
        "GATEWAY_OAUTH_JWT_TOKEN"
    )
    if not token:
        print("❌ GATEWAY_OAUTH_ACCESS_TOKEN not found in environment!")
        print("   Tests require REAL OAuth tokens per CLAUDE.md")
        print("   Run: just generate-github-token")
        return False
    print("✅ GATEWAY_OAUTH_ACCESS_TOKEN found in environment")
    return True


def check_services():
    """Check if required services are configured."""
    required_vars = [
        "BASE_DOMAIN",
        "GITHUB_CLIENT_ID",
        "GITHUB_CLIENT_SECRET",
        "GATEWAY_JWT_SECRET",
        "REDIS_PASSWORD",
    ]

    all_present = True
    for var in required_vars:
        if not os.getenv(var):
            print(f"❌ {var} not set in environment")
            all_present = False
        else:
            print(f"✅ {var} is configured")

    return all_present


def main():
    print("=" * 64)
    print("SACRED TEST REQUIREMENTS CHECK")
    print("According to CLAUDE.md: NO FAKE TOKENS ALLOWED!")
    print("=" * 64)
    print()

    oauth_ok = check_oauth_token()
    print()
    services_ok = check_services()

    if not oauth_ok or not services_ok:
        print("\n" + "=" * 64)
        print("TEST REQUIREMENTS NOT MET!")
        print("=" * 64)

        if not oauth_ok:
            print("\nTo get a REAL OAuth token:")
            print("1. Run: just generate-github-token")
            print("2. Follow the device flow instructions")
            print("3. Token will be saved to .env")

        if not services_ok:
            print("\nMake sure all required environment variables are set in .env")

        return 1
    print("\n✅ All test requirements met!")
    print("   Tests can now use REAL OAuth tokens as required by CLAUDE.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
