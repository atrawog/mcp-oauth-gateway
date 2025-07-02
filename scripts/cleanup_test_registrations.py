#!/usr/bin/env python3
"""Cleanup script for removing all test client registrations."""

import asyncio
import json
import os
from datetime import UTC

import httpx
import redis.asyncio as redis
from rich.console import Console
from rich.table import Table


console = Console()

# Configuration from environment
AUTH_BASE_URL = f"https://auth.{os.getenv('BASE_DOMAIN', 'atratest.org')}"
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
GATEWAY_OAUTH_ACCESS_TOKEN = os.getenv("GATEWAY_OAUTH_ACCESS_TOKEN", "")


async def cleanup_test_registrations():
    """Remove all test client registrations from Redis."""
    if not GATEWAY_OAUTH_ACCESS_TOKEN:
        console.print("[red]❌ No GATEWAY_OAUTH_ACCESS_TOKEN found![/red]")
        console.print("Run: just generate-github-token")
        return

    # Connect to Redis
    r = redis.Redis(host="localhost", port=6379, password=REDIS_PASSWORD, decode_responses=True)

    try:
        # Get all client registrations
        client_keys = await r.keys("oauth:client:*")

        console.print(f"Found {len(client_keys)} total client registrations")

        # Track test clients
        test_clients = []
        deleted_count = 0
        error_count = 0

        async with httpx.AsyncClient(timeout=10.0, verify=True) as http_client:
            for key in client_keys:
                client_data = await r.get(key)
                if client_data:
                    try:
                        client = json.loads(client_data)
                        client_name = client.get("client_name", "")

                        # Check if it's a test client
                        if any(test_word in client_name.lower() for test_word in ["test", "concurrent"]):
                            test_clients.append(client)

                            # Try to delete using RFC 7592 endpoint
                            if "registration_access_token" in client and "client_id" in client:
                                console.print(f"Deleting: {client_name} ({client['client_id']})")

                                try:
                                    delete_response = await http_client.delete(
                                        f"{AUTH_BASE_URL}/register/{client['client_id']}",
                                        headers={"Authorization": f"Bearer {client['registration_access_token']}"},
                                    )

                                    if delete_response.status_code == 204:
                                        deleted_count += 1
                                        console.print("  [green]✓ Deleted successfully[/green]")
                                    elif delete_response.status_code == 404:
                                        # Already deleted, just clean up Redis
                                        await r.delete(key)
                                        deleted_count += 1
                                        console.print("  [yellow]✓ Already deleted, cleaned Redis[/yellow]")
                                    else:
                                        error_count += 1
                                        console.print(f"  [red]✗ Failed: {delete_response.status_code}[/red]")
                                except Exception as e:
                                    error_count += 1
                                    console.print(f"  [red]✗ Error: {e}[/red]")
                                    # Try to clean up Redis anyway
                                    await r.delete(key)
                            else:
                                # No registration access token, just clean Redis
                                await r.delete(key)
                                deleted_count += 1
                                console.print("  [yellow]✓ Cleaned from Redis (no access token)[/yellow]")
                    except json.JSONDecodeError:
                        console.print(f"[red]Failed to parse client data for {key}[/red]")

        # Summary
        console.print("\n[bold]Summary:[/bold]")
        console.print(f"Total test clients found: {len(test_clients)}")
        console.print(f"[green]Successfully deleted: {deleted_count}[/green]")
        if error_count > 0:
            console.print(f"[red]Errors: {error_count}[/red]")

        # Show remaining clients
        remaining_keys = await r.keys("oauth:client:*")
        remaining_count = 0

        table = Table(title="Remaining Client Registrations")
        table.add_column("Client ID", style="cyan")
        table.add_column("Client Name", style="magenta")
        table.add_column("Created", style="green")

        for key in remaining_keys:
            client_data = await r.get(key)
            if client_data:
                try:
                    client = json.loads(client_data)
                    remaining_count += 1

                    # Format timestamp if available
                    created_at = client.get("client_id_issued_at", "")
                    if created_at:
                        from datetime import datetime

                        created_at = datetime.fromtimestamp(created_at, tz=UTC).strftime("%Y-%m-%d %H:%M:%S")

                    table.add_row(client.get("client_id", "Unknown"), client.get("client_name", "Unknown"), created_at)
                except json.JSONDecodeError:
                    pass

        if remaining_count > 0:
            console.print(f"\n[bold]Remaining registrations: {remaining_count}[/bold]")
            console.print(table)
        else:
            console.print("\n[green]✅ All test registrations cleaned up![/green]")

    finally:
        await r.aclose()


if __name__ == "__main__":
    asyncio.run(cleanup_test_registrations())
