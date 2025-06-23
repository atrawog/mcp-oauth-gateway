#!/usr/bin/env python3
"""Debug Redis token storage."""

import asyncio
import os

import redis.asyncio as redis
from dotenv import load_dotenv


load_dotenv()


async def debug_tokens():
    # Connect to Redis
    REDIS_URL = "redis://localhost:6379"
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")

    # Try to get port mapping
    import subprocess

    try:
        port_result = subprocess.run(
            ["docker", "compose", "port", "redis", "6379"],
            capture_output=True,
            text=True,
            check=True,
        )
        if port_result.stdout.strip():
            host, port = port_result.stdout.strip().split(":")
            REDIS_URL = f"redis://{host}:{port}"
    except:
        pass

    client = await redis.from_url(
        REDIS_URL, password=REDIS_PASSWORD, decode_responses=True
    )

    try:
        # Get all token keys
        token_keys = await client.keys("oauth:token:*")
        print(f"Found {len(token_keys)} token keys")

        # Sample a few
        for i, key in enumerate(token_keys[:5]):
            print(f"\nKey {i + 1}: {key}")
            value = await client.get(key)
            print(f"Value type: {type(value)}")
            print(f"Value length: {len(value) if value else 0}")
            if value:
                print(f"First 100 chars: {value[:100]}...")
    finally:
        await client.aclose()


if __name__ == "__main__":
    asyncio.run(debug_tokens())
