#!/usr/bin/env python3
"""Check Claude.ai client registrations."""

import asyncio
import json
import os

import redis.asyncio as redis
from dotenv import load_dotenv


load_dotenv()


async def check():
    redis_password = os.getenv("REDIS_PASSWORD")
    r = await redis.Redis(
        host="localhost", port=6379, password=redis_password, decode_responses=True
    )

    # Check both client IDs
    old_id = "client_lZAJc-CiOsqwTZ2hAOls9A"
    new_id = "client_wPYp_tWEuj8xV4LukRwltA"

    old_data = await r.get(f"oauth:client:{old_id}")
    new_data = await r.get(f"oauth:client:{new_id}")

    print(f"Old client ({old_id}): {'EXISTS' if old_data else 'NOT FOUND'}")
    if old_data:
        data = json.loads(old_data)
        print(f"  Name: {data.get('client_name')}")
        print(f"  Note: {data.get('_note', 'N/A')}")

    print(f"\nNew client ({new_id}): {'EXISTS' if new_data else 'NOT FOUND'}")
    if new_data:
        data = json.loads(new_data)
        print(f"  Name: {data.get('client_name')}")

    await r.aclose()


asyncio.run(check())
