#!/usr/bin/env python3
"""Purge expired OAuth tokens from Redis
Can be run manually or via cron/systemd timer.
"""
import asyncio
import json
import os
import sys
import time
from datetime import datetime

import redis.asyncio as redis
from dotenv import load_dotenv


# Load environment
load_dotenv()

# Redis connection details
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")

# Check if we should connect via Docker
import subprocess


try:
    result = subprocess.run(
        ["docker", "compose", "ps", "--services", "--filter", "status=running"],
        capture_output=True,
        text=True,
        check=True
    )
    if "redis" in result.stdout:
        port_result = subprocess.run(
            ["docker", "compose", "port", "redis", "6379"],
            capture_output=True,
            text=True,
            check=True
        )
        if port_result.stdout.strip():
            host, port = port_result.stdout.strip().split(":")
            REDIS_URL = f"redis://{host}:{port}"
except:
    pass


async def get_redis_client():
    """Get async Redis client."""
    return await redis.from_url(
        REDIS_URL,
        password=REDIS_PASSWORD,
        decode_responses=True
    )


def check_token_expiry(token_data: str) -> tuple[bool, int]:
    """Check if token is expired. Returns (is_expired, expires_at_timestamp)."""
    try:
        # Try to parse as JSON (stored token info)
        try:
            payload = json.loads(token_data)
        except:
            # Maybe it's a JWT token string - decode it
            import base64
            parts = token_data.split('.')
            if len(parts) != 3:
                return False, 0

            payload_part = parts[1]
            payload_part += '=' * (4 - len(payload_part) % 4)
            payload_json = base64.urlsafe_b64decode(payload_part)
            payload = json.loads(payload_json)

        # Check for expiration in either format
        expires_at = payload.get("exp", payload.get("expires_at", 0))
        now = int(time.time())

        return expires_at < now, expires_at
    except Exception:
        return False, 0


async def purge_expired_tokens(dry_run: bool = False):
    """Purge all expired tokens from Redis."""
    client = await get_redis_client()

    try:
        print(f"{'[DRY RUN] ' if dry_run else ''}Starting token purge at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        # Statistics
        stats = {
            "access_tokens_checked": 0,
            "access_tokens_expired": 0,
            "refresh_tokens_checked": 0,
            "refresh_tokens_expired": 0,
            "auth_codes_checked": 0,
            "auth_codes_expired": 0,
            "auth_states_checked": 0,
            "auth_states_expired": 0,
            "total_deleted": 0
        }

        # Check access tokens
        token_keys = await client.keys("oauth:token:*")
        stats["access_tokens_checked"] = len(token_keys)

        for key in token_keys:
            token_data = await client.get(key)
            if token_data:
                is_expired, expires_at = check_token_expiry(token_data)
                if is_expired:
                    if not dry_run:
                        await client.delete(key)
                    stats["access_tokens_expired"] += 1
                    print(f"{'Would delete' if dry_run else 'Deleted'} expired access token: {key} (expired: {datetime.fromtimestamp(expires_at)})")

        # Check refresh tokens (they have TTL but let's verify)
        refresh_keys = await client.keys("oauth:refresh:*")
        stats["refresh_tokens_checked"] = len(refresh_keys)

        for key in refresh_keys:
            ttl = await client.ttl(key)
            if ttl <= 0:  # TTL expired or no TTL
                if not dry_run:
                    await client.delete(key)
                stats["refresh_tokens_expired"] += 1
                print(f"{'Would delete' if dry_run else 'Deleted'} expired refresh token: {key}")

        # Check auth codes (should have short TTL)
        code_keys = await client.keys("oauth:code:*")
        stats["auth_codes_checked"] = len(code_keys)

        for key in code_keys:
            ttl = await client.ttl(key)
            if ttl <= 0:  # TTL expired or no TTL
                if not dry_run:
                    await client.delete(key)
                stats["auth_codes_expired"] += 1
                print(f"{'Would delete' if dry_run else 'Deleted'} expired auth code: {key}")

        # Check auth states (should have very short TTL - 5 minutes)
        state_keys = await client.keys("oauth:state:*")
        stats["auth_states_checked"] = len(state_keys)

        for key in state_keys:
            ttl = await client.ttl(key)
            if ttl <= 0:  # TTL expired or no TTL
                if not dry_run:
                    await client.delete(key)
                stats["auth_states_expired"] += 1
                print(f"{'Would delete' if dry_run else 'Deleted'} expired auth state: {key}")

        # Calculate totals
        stats["total_deleted"] = (
            stats["access_tokens_expired"] +
            stats["refresh_tokens_expired"] +
            stats["auth_codes_expired"] +
            stats["auth_states_expired"]
        )

        # Print summary
        print("\n" + "=" * 60)
        print(f"{'[DRY RUN] ' if dry_run else ''}Purge Summary:")
        print(f"  Access Tokens: {stats['access_tokens_expired']}/{stats['access_tokens_checked']} expired")
        print(f"  Refresh Tokens: {stats['refresh_tokens_expired']}/{stats['refresh_tokens_checked']} expired")
        print(f"  Auth Codes: {stats['auth_codes_expired']}/{stats['auth_codes_checked']} expired")
        print(f"  Auth States: {stats['auth_states_expired']}/{stats['auth_states_checked']} expired")
        print(f"\n  Total {'would be ' if dry_run else ''}deleted: {stats['total_deleted']}")

        # Also clean up orphaned data
        if not dry_run and stats["total_deleted"] > 0:
            print("\nCleaning up orphaned user token indexes...")
            user_token_keys = await client.keys("oauth:user_tokens:*")
            for key in user_token_keys:
                # Check if user has any active tokens
                username = key.split(":")[-1]
                has_active_tokens = False

                # Check all tokens for this user
                all_token_keys = await client.keys("oauth:token:*")
                for token_key in all_token_keys:
                    token_data = await client.get(token_key)
                    if token_data:
                        try:
                            payload = json.loads(token_data)
                            if payload.get("username") == username:
                                has_active_tokens = True
                                break
                        except:
                            pass

                if not has_active_tokens:
                    await client.delete(key)
                    print(f"  Removed orphaned user token index: {key}")

        print(f"\n✅ Purge completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    finally:
        await client.aclose()


async def main():
    """Main entry point."""
    dry_run = "--dry-run" in sys.argv or "-n" in sys.argv

    if "--help" in sys.argv or "-h" in sys.argv:
        print("Usage: purge_expired_tokens.py [--dry-run|-n]")
        print("\nOptions:")
        print("  --dry-run, -n  Show what would be deleted without actually deleting")
        print("\nThis script purges all expired OAuth tokens from Redis.")
        sys.exit(0)

    await purge_expired_tokens(dry_run=dry_run)


if __name__ == "__main__":
    asyncio.run(main())
