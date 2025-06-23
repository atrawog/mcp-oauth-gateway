#!/usr/bin/env python3
"""OAuth token refresh script for MCP OAuth Gateway
Automatically refreshes expired tokens using refresh token.
"""
import asyncio
import json
import os
import sys
import time

import httpx


def get_env_var(name: str, required: bool = True) -> str:
    """Get environment variable."""
    value = os.getenv(name)
    if required and not value:
        print(f"❌ Required environment variable {name} not found!")
        sys.exit(1)
    return value


def update_env_file(token_data: dict):
    """Update .env file with new tokens."""
    env_file = ".env"

    try:
        # Read current .env file
        with open(env_file) as f:
            lines = f.readlines()

        # Update token lines
        updated_lines = []
        updated_vars = set()

        for line in lines:
            line = line.strip()
            if line.startswith('GATEWAY_OAUTH_ACCESS_TOKEN='):
                updated_lines.append(f"GATEWAY_OAUTH_ACCESS_TOKEN={token_data['access_token']}\n")
                updated_vars.add('GATEWAY_OAUTH_ACCESS_TOKEN')
            elif line.startswith('GATEWAY_OAUTH_REFRESH_TOKEN=') and 'refresh_token' in token_data:
                updated_lines.append(f"GATEWAY_OAUTH_REFRESH_TOKEN={token_data['refresh_token']}\n")
                updated_vars.add('GATEWAY_OAUTH_REFRESH_TOKEN')
            else:
                updated_lines.append(line + '\n' if line else '\n')

        # Add any missing variables
        if 'GATEWAY_OAUTH_ACCESS_TOKEN' not in updated_vars:
            updated_lines.append(f"GATEWAY_OAUTH_ACCESS_TOKEN={token_data['access_token']}\n")

        if 'refresh_token' in token_data and 'GATEWAY_OAUTH_REFRESH_TOKEN' not in updated_vars:
            updated_lines.append(f"GATEWAY_OAUTH_REFRESH_TOKEN={token_data['refresh_token']}\n")

        # Write back to file
        with open(env_file, 'w') as f:
            f.writelines(updated_lines)

        print(f"✅ Updated {env_file} with new tokens")

    except Exception as e:
        print(f"❌ Failed to update .env file: {e}")
        print("You may need to manually update the tokens:")
        print(f"GATEWAY_OAUTH_ACCESS_TOKEN={token_data['access_token']}")
        if 'refresh_token' in token_data:
            print(f"GATEWAY_OAUTH_REFRESH_TOKEN={token_data['refresh_token']}")


async def refresh_token() -> bool:
    """Refresh OAuth token using refresh token."""
    print("🔄 Attempting to refresh OAuth tokens...")

    # Get required variables
    refresh_token = get_env_var("GATEWAY_OAUTH_REFRESH_TOKEN")
    client_id = get_env_var("GATEWAY_OAUTH_CLIENT_ID")
    client_secret = get_env_var("GATEWAY_OAUTH_CLIENT_SECRET")
    base_domain = get_env_var("BASE_DOMAIN")

    token_url = f"https://auth.{base_domain}/token"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                token_url,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                    "client_id": client_id,
                    "client_secret": client_secret
                },
                headers={
                    "Content-Type": "application/x-www-form-urlencoded"
                }
            )

        if response.status_code == 200:
            token_data = response.json()

            # Decode new token to check validity
            new_token = token_data.get('access_token')
            if new_token:
                try:
                    # Decode without verification for inspection only
                    import base64
                    parts = new_token.split('.')
                    if len(parts) == 3:
                        payload_part = parts[1]
                        payload_part += '=' * (4 - len(payload_part) % 4)
                        payload_json = base64.urlsafe_b64decode(payload_part)
                        payload = json.loads(payload_json)
                    else:
                        raise ValueError("Invalid JWT format")
                    exp = payload.get('exp', 0)
                    now = int(time.time())

                    print("✅ Token refresh successful!")
                    print(f"   New token expires: {time.ctime(exp)}")
                    print(f"   Valid for: {(exp - now) / 3600:.1f} hours")

                    # Update .env file
                    update_env_file(token_data)
                    return True

                except Exception as e:
                    print(f"❌ New token validation failed: {e}")
                    return False
            else:
                print(f"❌ No access token in response: {token_data}")
                return False

        else:
            print(f"❌ Token refresh failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('error', 'Unknown error')}")
                print(f"   Description: {error_data.get('error_description', 'No description')}")
            except:
                print(f"   Response: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Token refresh request failed: {e}")
        return False


async def main():
    """Main refresh function."""
    print("🔄 OAUTH TOKEN REFRESH")
    print("=" * 40)

    # Check if refresh is needed
    oauth_token = os.getenv("GATEWAY_OAUTH_ACCESS_TOKEN")
    if oauth_token:
        try:
            # Decode without verification for inspection only
            import base64
            parts = oauth_token.split('.')
            if len(parts) == 3:
                payload_part = parts[1]
                payload_part += '=' * (4 - len(payload_part) % 4)
                payload_json = base64.urlsafe_b64decode(payload_part)
                payload = json.loads(payload_json)
            else:
                raise ValueError("Invalid JWT format")
            exp = payload.get('exp', 0)
            now = int(time.time())

            if exp > now:
                remaining = exp - now
                print(f"ℹ️  Current token is still valid for {remaining/3600:.1f} hours")
                print("   Refresh not needed, but proceeding anyway...")
        except:
            print("⚠️  Cannot decode current token, proceeding with refresh...")

    success = await refresh_token()

    print("=" * 40)
    if success:
        print("✅ TOKEN REFRESH COMPLETED!")
        print("   You can now run tests with fresh tokens.")
    else:
        print("❌ TOKEN REFRESH FAILED!")
        print("   You may need to regenerate tokens:")
        print("   just generate-github-token")

    return success


if __name__ == "__main__":
    if asyncio.run(main()):
        sys.exit(0)
    else:
        sys.exit(1)
