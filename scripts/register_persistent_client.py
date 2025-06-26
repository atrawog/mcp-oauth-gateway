#!/usr/bin/env python3
"""Register a persistent OAuth client that will survive restarts."""

import asyncio
import json
import os
import sys

import httpx
import redis.asyncio as redis


# Add parent directory to path to import test_constants
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tests.test_constants import AUTH_BASE_URL
from tests.test_constants import REDIS_PASSWORD
from tests.test_constants import TEST_CLIENT_NAME
from tests.test_constants import TEST_CLIENT_SCOPE
from tests.test_constants import TEST_OAUTH_CALLBACK_URL


async def register_persistent_client():
    """Register a client and verify it persists in Redis."""
    # Register client via API
    async with httpx.AsyncClient(verify=True) as client:
        registration_data = {
            "redirect_uris": [TEST_OAUTH_CALLBACK_URL],
            "client_name": f"Persistent {TEST_CLIENT_NAME}",
            "scope": TEST_CLIENT_SCOPE,
        }

        response = await client.post(f"{AUTH_BASE_URL}/register", json=registration_data)

        if response.status_code == 201:
            client_data = response.json()
            print("✅ Client registered successfully!")
            print(f"   Client ID: {client_data['client_id']}")
            print(f"   Client Secret: {client_data['client_secret']}")

            # Save to .env.test for test usage
            with open(".env.test", "w") as f:
                f.write(f"TEST_CLIENT_ID={client_data['client_id']}\n")
                f.write(f"TEST_CLIENT_SECRET={client_data['client_secret']}\n")

            # Verify in Redis directly
            # Import REDIS_URL from test_constants
            from tests.test_constants import REDIS_URL

            redis_client = await redis.from_url(REDIS_URL, decode_responses=True)

            try:
                # Check if client exists in Redis
                client_key = f"oauth:client:{client_data['client_id']}"
                exists = await redis_client.exists(client_key)

                if exists:
                    stored_data = await redis_client.hgetall(client_key)
                    print("\n✅ Client verified in Redis!")
                    print(f"   Key: {client_key}")
                    print(f"   Data: {json.dumps(stored_data, indent=2)}")

                    # Check TTL (should be -1 for no expiration)
                    ttl = await redis_client.ttl(client_key)
                    print(f"   TTL: {ttl} (-1 means no expiration)")
                else:
                    print("\n❌ Client not found in Redis!")

            finally:
                await redis_client.aclose()

            return client_data
        print(f"❌ Registration failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return None


async def verify_persistence():
    """Check if previously registered clients still exist."""
    # Try to load from .env.test
    if os.path.exists(".env.test"):
        with open(".env.test") as f:
            lines = f.readlines()

        test_client_id = None
        for line in lines:
            if line.startswith("TEST_CLIENT_ID="):
                test_client_id = line.strip().split("=")[1]
                break

        if test_client_id:
            # Check Redis directly
            redis_client = await redis.from_url(f"redis://:{REDIS_PASSWORD}@localhost:6379/0", decode_responses=True)

            try:
                client_key = f"oauth:client:{test_client_id}"
                exists = await redis_client.exists(client_key)

                if exists:
                    print(f"\n✅ Previous client {test_client_id} still exists in Redis!")
                    data = await redis_client.hgetall(client_key)
                    print(f"   Created at: {data.get('created_at', 'unknown')}")
                else:
                    print(f"\n❌ Previous client {test_client_id} not found in Redis")

            finally:
                await redis_client.aclose()


async def main():
    print("=== Testing OAuth Client Persistence ===\n")

    # First check if any previous clients exist
    await verify_persistence()

    # Register a new client
    print("\n=== Registering New Client ===")
    client = await register_persistent_client()

    if client:
        print("\n✅ Client registration complete!")
        print("\nTo test persistence:")
        print("1. Run 'just down' to stop services")
        print("2. Run 'just up' to restart services")
        print("3. Run this script again to verify the client still exists")


if __name__ == "__main__":
    asyncio.run(main())
