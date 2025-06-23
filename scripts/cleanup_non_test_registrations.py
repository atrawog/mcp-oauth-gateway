#!/usr/bin/env python3
"""Clean up non-TEST prefix registrations (except MCP OAuth Gateway Client)."""
import asyncio
import os

import httpx
from dotenv import load_dotenv


# Load environment variables
load_dotenv()

AUTH_BASE_URL = f"https://auth.{os.getenv('BASE_DOMAIN')}"
ADMIN_TOKEN = os.getenv("GATEWAY_OAUTH_ACCESS_TOKEN")

async def cleanup_registrations():
    """Clean up test registrations that don't start with TEST."""
    if not ADMIN_TOKEN:
        print("❌ No GATEWAY_OAUTH_ACCESS_TOKEN found!")
        return

    async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
        # Get all registrations
        response = await client.get(
            f"{AUTH_BASE_URL}/admin/clients",
            headers={"Authorization": f"Bearer {ADMIN_TOKEN}"}
        )

        if response.status_code != 200:
            print(f"❌ Failed to list clients: {response.status_code}")
            return

        clients = response.json()
        to_delete = []

        for client_id, client_data in clients.items():
            name = client_data.get('client_name', '')

            # Skip MCP OAuth Gateway Client and clients starting with TEST
            if name == "MCP OAuth Gateway Client" or name.startswith("TEST"):
                continue

            # These are the problematic ones
            if name in ["Test Client", "Edge Case Test"]:
                to_delete.append((client_id, name))
                print(f"Found non-TEST client to delete: {client_id} - {name}")

        # Delete them
        for client_id, name in to_delete:
            print(f"Deleting {client_id} - {name}...")
            # First get the registration token
            # Since we don't have the registration_access_token, we'll use admin endpoint
            response = await client.delete(
                f"{AUTH_BASE_URL}/admin/clients/{client_id}",
                headers={"Authorization": f"Bearer {ADMIN_TOKEN}"}
            )
            if response.status_code in (204, 404):
                print("  ✅ Deleted")
            else:
                print(f"  ❌ Failed: {response.status_code}")

if __name__ == "__main__":
    asyncio.run(cleanup_registrations())
