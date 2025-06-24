#!/usr/bin/env python3
"""Fix Claude.ai registration issue by creating an alias for the old client_id.

This is a temporary workaround for Claude.ai's failure to update stored credentials.
"""

import asyncio
import json
import os
from datetime import UTC
from datetime import datetime

import redis.asyncio as redis
from dotenv import load_dotenv


# Load environment
load_dotenv()


async def create_client_alias():
    """Create an alias from old client_id to new one."""
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
        # Test connection
        await redis_client.ping()
        print("✅ Connected to Redis")

        # The problematic client IDs
        old_client_id = "client_lZAJc-CiOsqwTZ2hAOls9A"
        new_client_id = "client_wPYp_tWEuj8xV4LukRwltA"

        # Check if new client exists
        new_client_data = await redis_client.get(f"oauth:client:{new_client_id}")
        if not new_client_data:
            print(f"❌ New client {new_client_id} not found!")
            return

        # Parse new client data
        new_client = json.loads(new_client_data)
        print(f"✅ Found new Claude.ai registration: {new_client.get('client_name')}")

        # Create a copy with the old client_id
        # This allows Claude.ai to continue using the old ID
        old_client = new_client.copy()
        old_client["client_id"] = old_client_id
        old_client["_note"] = "Alias for Claude.ai compatibility"
        old_client["_real_client_id"] = new_client_id
        old_client["_created_at"] = datetime.now(UTC).isoformat()

        # Store the alias
        await redis_client.set(f"oauth:client:{old_client_id}", json.dumps(old_client))

        print(f"✅ Created alias: {old_client_id} → {new_client_id}")
        print(
            "⚠️  This is a temporary workaround. Claude.ai should update their implementation."
        )

    finally:
        await redis_client.aclose()


async def main():
    """Main entry point."""
    print("🔧 Claude.ai Registration Fix")
    print("=" * 60)

    await create_client_alias()

    print("\n✅ Fix applied. Claude.ai should now be able to authenticate.")
    print(
        "📝 Note: This creates an alias so the old client_id points to the new registration."
    )


if __name__ == "__main__":
    asyncio.run(main())
