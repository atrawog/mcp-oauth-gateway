#!/usr/bin/env python3
"""Debug token structure in Redis"""
import asyncio
import json
import os
import redis.asyncio as redis
from dotenv import load_dotenv

load_dotenv()

async def debug_structure():
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
        # Get sample token
        token_keys = await client.keys("oauth:token:*")
        if token_keys:
            key = token_keys[0]
            value = await client.get(key)
            print(f"Token key: {key}")
            print(f"Raw value: {value}")
            
            # Parse as JSON
            try:
                data = json.loads(value)
                print("\nParsed as JSON:")
                for k, v in data.items():
                    print(f"  {k}: {v} (type: {type(v).__name__})")
            except:
                print("Failed to parse as JSON")
        
        # Also check client registration
        client_keys = await client.keys("oauth:client:*")
        if client_keys:
            key = client_keys[0]
            value = await client.get(key)
            print(f"\n\nClient key: {key}")
            print(f"Raw value: {value[:200]}...")
            
            # Parse as JSON
            try:
                data = json.loads(value)
                print("\nParsed as JSON:")
                for k, v in data.items():
                    if k != "redirect_uris":
                        print(f"  {k}: {v} (type: {type(v).__name__})")
            except:
                print("Failed to parse as JSON")
                
    finally:
        await client.aclose()

if __name__ == "__main__":
    asyncio.run(debug_structure())