#!/usr/bin/env python3
"""Debug Claude.ai OAuth issue."""

import asyncio
import json
import os
from datetime import datetime

import redis.asyncio as redis
from dotenv import load_dotenv


load_dotenv()


async def main():
    # Redis connection
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    redis_password = os.getenv("REDIS_PASSWORD")

    # Handle localhost for host execution
    if "redis://" in redis_url and "redis:" in redis_url and not os.path.exists("/.dockerenv"):
        redis_url = redis_url.replace("redis:", "localhost:")

    # Parse Redis URL
    redis_host = "localhost"
    redis_port = 6379

    if redis_url.startswith("redis://"):
        url_parts = redis_url.replace("redis://", "").split("/")
        host_port = url_parts[0]

        if ":" in host_port:
            redis_host, port = host_port.split(":")
            redis_port = int(port)
        else:
            redis_host = host_port
            redis_port = 6379

    # Connect to Redis
    redis_client = await redis.Redis(
        host=redis_host, port=redis_port, password=redis_password, decode_responses=True
    )

    try:
        await redis_client.ping()
        print("🔍 Debugging Claude.ai OAuth Issue")
        print("=" * 80)

        # The problematic client ID
        old_client_id = "client_lZAJc-CiOsqwTZ2hAOls9A"

        # Check if it exists
        old_client_data = await redis_client.get(f"oauth:client:{old_client_id}")
        if old_client_data:
            print("✅ Old client ID still exists in Redis!")
            client = json.loads(old_client_data)
            print(f"   Name: {client.get('client_name')}")
            print(f"   Redirect URIs: {client.get('redirect_uris')}")
        else:
            print(f"❌ Old client ID {old_client_id} NOT found (deleted)")

        # Find all Claude.ai registrations
        print("\n📋 All Claude.ai related registrations:")
        print("-" * 80)

        cursor = 0
        claude_clients = []

        while True:
            cursor, keys = await redis_client.scan(
                cursor, match="oauth:client:*", count=100
            )

            for key in keys:
                client_data = await redis_client.get(key)
                if client_data:
                    try:
                        client = json.loads(client_data)
                        # Check if it's Claude-related
                        if "claude" in client.get(
                            "client_name", ""
                        ).lower() or "claude.ai" in str(
                            client.get("redirect_uris", [])
                        ):
                            client_id = key.split(":")[-1]
                            claude_clients.append(
                                {
                                    "id": client_id,
                                    "name": client.get("client_name"),
                                    "redirect_uris": client.get("redirect_uris"),
                                    "created": client.get("client_id_issued_at"),
                                }
                            )
                    except:
                        pass

            if cursor == 0:
                break

        # Display Claude clients
        for client in sorted(claude_clients, key=lambda x: x.get("created", 0)):
            print(f"\nClient ID: {client['id']}")
            print(f"Name: {client['name']}")
            print(f"Redirect URIs: {client['redirect_uris']}")
            if client["created"]:
                print(
                    f"Created: {datetime.fromtimestamp(client['created']).isoformat()}"
                )

        if not claude_clients:
            print("No Claude.ai registrations found")

        # Check OAuth states
        print("\n\n📋 Recent OAuth states:")
        print("-" * 80)

        cursor = 0
        states = []

        while True:
            cursor, keys = await redis_client.scan(
                cursor, match="oauth:state:*", count=100
            )

            for key in keys:
                state_data = await redis_client.get(key)
                ttl = await redis_client.ttl(key)
                if state_data:
                    try:
                        data = json.loads(state_data)
                        if data.get("client_id") == old_client_id:
                            states.append(
                                {
                                    "state": key.split(":")[-1],
                                    "client_id": data.get("client_id"),
                                    "redirect_uri": data.get("redirect_uri"),
                                    "ttl": ttl,
                                }
                            )
                    except:
                        pass

            if cursor == 0:
                break

        for state in states[:5]:  # Show last 5
            print(f"\nState: {state['state'][:20]}...")
            print(f"Client ID: {state['client_id']}")
            print(f"TTL: {state['ttl']} seconds")

    finally:
        await redis_client.aclose()


if __name__ == "__main__":
    asyncio.run(main())
