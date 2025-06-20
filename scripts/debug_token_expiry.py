#!/usr/bin/env python3
"""Debug token expiry logic"""
import asyncio
import json
import os
import time
from datetime import datetime
import redis.asyncio as redis
from dotenv import load_dotenv

load_dotenv()

async def debug_expiry():
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
            check=True
        )
        if port_result.stdout.strip():
            host, port = port_result.stdout.strip().split(":")
            REDIS_URL = f"redis://{host}:{port}"
    except:
        pass
    
    client = await redis.from_url(
        REDIS_URL,
        password=REDIS_PASSWORD,
        decode_responses=True
    )
    
    try:
        now = int(time.time())
        print(f"Current time: {now} ({datetime.fromtimestamp(now)})")
        print("=" * 60)
        
        # Check all tokens
        token_keys = await client.keys("oauth:token:*")
        print(f"\nChecking {len(token_keys)} tokens:\n")
        
        for key in token_keys:
            token_data = await client.get(key)
            if token_data:
                try:
                    payload = json.loads(token_data)
                    expires_at = payload.get("expires_at", 0)
                    created_at = payload.get("created_at", 0)
                    
                    ttl = await client.ttl(key)
                    
                    print(f"Token: {key}")
                    print(f"  Created: {datetime.fromtimestamp(created_at)} ({created_at})")
                    print(f"  Expires: {datetime.fromtimestamp(expires_at)} ({expires_at})")
                    print(f"  Redis TTL: {ttl} seconds")
                    print(f"  Time until expiry: {expires_at - now} seconds")
                    print(f"  Is expired: {expires_at < now}")
                    print()
                except Exception as e:
                    print(f"Error parsing {key}: {e}")
                    print(f"  Raw data: {token_data[:100]}...")
                    print()
                    
    finally:
        await client.aclose()

if __name__ == "__main__":
    asyncio.run(debug_expiry())