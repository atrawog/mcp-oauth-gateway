#!/usr/bin/env python3
"""
Manage OAuth registrations and tokens in Redis
Following the sacred commandments - direct access to real data!
"""
import asyncio
import json
import os
import sys
import base64
from datetime import datetime
from typing import Optional, List, Dict
import redis.asyncio as redis
from dotenv import load_dotenv
from tabulate import tabulate

# Load environment
load_dotenv()

# Redis connection details
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")

# Check if we should connect via Docker
import subprocess
try:
    # Check if Redis is running in Docker
    result = subprocess.run(
        ["docker", "compose", "ps", "--services", "--filter", "status=running"],
        capture_output=True,
        text=True,
        check=True
    )
    if "redis" in result.stdout:
        # Get Redis container port mapping
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
    """Get async Redis client"""
    return await redis.from_url(
        REDIS_URL,
        password=REDIS_PASSWORD,
        decode_responses=True
    )


def decode_jwt_payload(token: str) -> Optional[Dict]:
    """Decode JWT payload without verification"""
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None
        
        # Add padding if needed
        payload_part = parts[1]
        payload_part += '=' * (4 - len(payload_part) % 4)
        
        payload_json = base64.urlsafe_b64decode(payload_part)
        return json.loads(payload_json)
    except Exception:
        return None


def format_timestamp(ts: int) -> str:
    """Format Unix timestamp to readable date"""
    try:
        return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
    except:
        return "N/A"


async def list_registrations():
    """List all OAuth client registrations"""
    client = await get_redis_client()
    
    try:
        # Find all client registrations
        keys = await client.keys("oauth:client:*")
        
        if not keys:
            print("No client registrations found.")
            return
        
        registrations = []
        for key in keys:
            data = await client.get(key)
            if data:
                client_data = json.loads(data)
                client_id = key.split(":")[-1]
                
                # Handle redirect_uris properly
                redirect_uris = client_data.get("redirect_uris", [])
                if isinstance(redirect_uris, str):
                    # If it's stored as a string, try to parse it
                    try:
                        redirect_uris = json.loads(redirect_uris)
                    except:
                        redirect_uris = [redirect_uris]
                
                # Handle timestamp - could be client_id_issued_at or created_at
                created_at = client_data.get("client_id_issued_at", client_data.get("created_at", 0))
                
                registrations.append([
                    client_id,
                    client_data.get("client_name", "N/A"),
                    client_data.get("scope", "N/A"),
                    ", ".join(redirect_uris) if isinstance(redirect_uris, list) else str(redirect_uris),
                    format_timestamp(created_at)
                ])
        
        print("\n=== OAuth Client Registrations ===")
        print(tabulate(
            registrations,
            headers=["Client ID", "Name", "Scope", "Redirect URIs", "Created"],
            tablefmt="grid"
        ))
        print(f"\nTotal registrations: {len(registrations)}")
        
    finally:
        await client.aclose()


async def list_tokens():
    """List all active OAuth tokens"""
    client = await get_redis_client()
    
    try:
        # Find all tokens
        token_keys = await client.keys("oauth:token:*")
        
        if not token_keys:
            print("No active tokens found.")
            return
        
        tokens = []
        for key in token_keys:
            token_data = await client.get(key)
            if token_data:
                # Try to parse as JSON (stored token info)
                try:
                    payload = json.loads(token_data)
                    # This is the token payload stored directly
                except:
                    # Maybe it's a JWT token string
                    payload = decode_jwt_payload(token_data)
                
                if payload:
                    jti = key.split(":")[-1]
                    ttl = await client.ttl(key)
                    
                    # Handle both JWT claims (iat/exp) and stored fields (created_at/expires_at)
                    issued_at = payload.get("iat", payload.get("created_at", 0))
                    expires_at = payload.get("exp", payload.get("expires_at", 0))
                    
                    tokens.append([
                        jti[:12] + "...",
                        payload.get("username", "N/A"),
                        payload.get("client_id", "N/A"),
                        payload.get("scope", "N/A"),
                        format_timestamp(issued_at),
                        format_timestamp(expires_at),
                        f"{ttl}s" if ttl > 0 else "No TTL"
                    ])
        
        print("\n=== Active OAuth Tokens ===")
        print(tabulate(
            tokens,
            headers=["JTI", "User", "Client ID", "Scope", "Issued", "Expires", "TTL"],
            tablefmt="grid"
        ))
        print(f"\nTotal tokens: {len(tokens)}")
        
        # Also check refresh tokens
        refresh_keys = await client.keys("oauth:refresh:*")
        if refresh_keys:
            print(f"\nRefresh tokens found: {len(refresh_keys)}")
        
    finally:
        await client.aclose()


async def delete_registration(client_id: str):
    """Delete a specific client registration and ALL associated tokens"""
    client = await get_redis_client()
    
    try:
        key = f"oauth:client:{client_id}"
        
        # Check if exists
        if not await client.exists(key):
            print(f"❌ Client registration '{client_id}' not found.")
            return
        
        # Get client info before deletion
        data = await client.get(key)
        client_data = json.loads(data) if data else {}
        
        # Delete the registration
        await client.delete(key)
        
        print(f"✅ Deleted client registration:")
        print(f"   Client ID: {client_id}")
        print(f"   Name: {client_data.get('client_name', 'N/A')}")
        print(f"   Scope: {client_data.get('scope', 'N/A')}")
        
        # Find and delete ALL tokens for this client
        deleted_access_tokens = 0
        deleted_refresh_tokens = 0
        
        # Delete access tokens
        token_keys = await client.keys("oauth:token:*")
        for token_key in token_keys:
            token_data = await client.get(token_key)
            if token_data:
                # Try to parse stored token data
                try:
                    payload = json.loads(token_data)
                except:
                    payload = decode_jwt_payload(token_data)
                
                if payload and payload.get("client_id") == client_id:
                    await client.delete(token_key)
                    deleted_access_tokens += 1
        
        # Delete refresh tokens
        refresh_keys = await client.keys("oauth:refresh:*")
        for refresh_key in refresh_keys:
            # Refresh tokens might store client_id differently
            # For now, we'll need to check the associated access token
            # or store client_id with refresh token
            # TODO: Implement refresh token client association
            pass
        
        # Delete any authorization codes
        code_keys = await client.keys("oauth:code:*")
        deleted_codes = 0
        for code_key in code_keys:
            code_data = await client.get(code_key)
            if code_data:
                try:
                    code_info = json.loads(code_data)
                    if code_info.get("client_id") == client_id:
                        await client.delete(code_key)
                        deleted_codes += 1
                except:
                    pass
        
        # Summary
        print(f"\n📊 Deletion Summary:")
        print(f"   Access tokens deleted: {deleted_access_tokens}")
        if deleted_codes:
            print(f"   Auth codes deleted: {deleted_codes}")
        print(f"\n✅ Client '{client_id}' and all associated data has been removed.")
            
    finally:
        await client.aclose()


async def delete_token(jti: str):
    """Delete a specific token by JTI"""
    client = await get_redis_client()
    
    try:
        # Try both full and partial JTI
        keys_to_try = [
            f"oauth:token:{jti}",
            # Also search for partial match
        ]
        
        # If partial JTI, search for it
        if len(jti) < 20:
            all_keys = await client.keys("oauth:token:*")
            for key in all_keys:
                if jti in key:
                    keys_to_try.append(key)
        
        deleted = False
        for key in keys_to_try:
            if await client.exists(key):
                # Get token info before deletion
                token_data = await client.get(key)
                payload = decode_jwt_payload(token_data) if token_data else None
                
                await client.delete(key)
                
                print(f"✅ Deleted token:")
                print(f"   JTI: {key.split(':')[-1]}")
                if payload:
                    print(f"   User: {payload.get('username', 'N/A')}")
                    print(f"   Client: {payload.get('client_id', 'N/A')}")
                
                deleted = True
                break
        
        if not deleted:
            print(f"❌ Token with JTI '{jti}' not found.")
            
    finally:
        await client.aclose()


async def delete_all_registrations():
    """Delete ALL client registrations"""
    client = await get_redis_client()
    
    try:
        keys = await client.keys("oauth:client:*")
        
        if not keys:
            print("No client registrations to delete.")
            return
        
        # Confirm
        print(f"⚠️  This will delete {len(keys)} client registrations!")
        confirm = input("Are you sure? (yes/no): ")
        
        if confirm.lower() != "yes":
            print("Cancelled.")
            return
        
        # Delete all registrations
        deleted = await client.delete(*keys)
        print(f"✅ Deleted {deleted} client registrations")
        
        # Also delete orphaned tokens
        token_keys = await client.keys("oauth:token:*")
        if token_keys:
            token_deleted = await client.delete(*token_keys)
            print(f"   Also deleted {token_deleted} associated tokens")
            
    finally:
        await client.aclose()


async def delete_all_tokens():
    """Delete ALL tokens"""
    client = await get_redis_client()
    
    try:
        # Find all token types
        access_keys = await client.keys("oauth:token:*")
        refresh_keys = await client.keys("oauth:refresh:*")
        
        total_keys = len(access_keys) + len(refresh_keys)
        
        if total_keys == 0:
            print("No tokens to delete.")
            return
        
        # Confirm
        print(f"⚠️  This will delete:")
        print(f"   - {len(access_keys)} access tokens")
        print(f"   - {len(refresh_keys)} refresh tokens")
        confirm = input("Are you sure? (yes/no): ")
        
        if confirm.lower() != "yes":
            print("Cancelled.")
            return
        
        # Delete all tokens
        deleted = 0
        if access_keys:
            deleted += await client.delete(*access_keys)
        if refresh_keys:
            deleted += await client.delete(*refresh_keys)
            
        print(f"✅ Deleted {deleted} tokens")
        
    finally:
        await client.aclose()


async def show_stats():
    """Show OAuth statistics"""
    client = await get_redis_client()
    
    try:
        # Count different types
        clients = len(await client.keys("oauth:client:*"))
        tokens = len(await client.keys("oauth:token:*"))
        refresh = len(await client.keys("oauth:refresh:*"))
        states = len(await client.keys("oauth:state:*"))
        codes = len(await client.keys("oauth:code:*"))
        user_tokens = len(await client.keys("oauth:user_tokens:*"))
        
        print("\n=== OAuth Statistics ===")
        print(f"Client Registrations: {clients}")
        print(f"Access Tokens:        {tokens}")
        print(f"Refresh Tokens:       {refresh}")
        print(f"Auth States:          {states}")
        print(f"Auth Codes:           {codes}")
        print(f"User Token Indexes:   {user_tokens}")
        
        # Get some user stats
        if user_tokens > 0:
            user_keys = await client.keys("oauth:user_tokens:*")
            users = [key.split(":")[-1] for key in user_keys]
            print(f"\nActive users: {', '.join(users)}")
            
    finally:
        await client.aclose()


async def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: manage_oauth_data.py <command> [args]")
        print("\nCommands:")
        print("  list-registrations    - Show all client registrations")
        print("  list-tokens          - Show all active tokens")
        print("  delete-registration <client_id> - Delete specific registration")
        print("  delete-token <jti>   - Delete specific token")
        print("  delete-all-registrations - Delete ALL registrations")
        print("  delete-all-tokens    - Delete ALL tokens")
        print("  stats                - Show OAuth statistics")
        sys.exit(1)
    
    command = sys.argv[1]
    
    try:
        if command == "list-registrations":
            await list_registrations()
        elif command == "list-tokens":
            await list_tokens()
        elif command == "delete-registration":
            if len(sys.argv) < 3:
                print("❌ Please provide client_id")
                sys.exit(1)
            await delete_registration(sys.argv[2])
        elif command == "delete-token":
            if len(sys.argv) < 3:
                print("❌ Please provide token JTI")
                sys.exit(1)
            await delete_token(sys.argv[2])
        elif command == "delete-all-registrations":
            await delete_all_registrations()
        elif command == "delete-all-tokens":
            await delete_all_tokens()
        elif command == "stats":
            await show_stats()
        else:
            print(f"❌ Unknown command: {command}")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())