#!/usr/bin/env python3
"""Backup OAuth Data from Redis.

Following the divine commandments of CLAUDE.md - NO MOCKING!
"""

import asyncio
import json
import os
import sys
from datetime import UTC
from datetime import datetime
from pathlib import Path

import redis.asyncio as redis
from dotenv import load_dotenv


# Load environment - SACRED LAW!
load_dotenv()


class OAuthBackup:
    """Divine backup service for OAuth artifacts."""

    def __init__(self):
        # Redis connection from environment - NO HARDCODING!
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        redis_password = os.getenv("REDIS_PASSWORD")

        # If we're running on the host and Redis URL points to 'redis' hostname,
        # change it to localhost (Redis is exposed on host ports)
        if "redis://" in redis_url and "redis:" in redis_url:
            # Check if we're in a container
            if not os.path.exists("/.dockerenv"):
                # We're on the host, use localhost
                redis_url = redis_url.replace("redis:", "localhost:")

        # Parse Redis URL
        if redis_url.startswith("redis://"):
            # Remove redis:// prefix and any path
            url_parts = redis_url.replace("redis://", "").split("/")
            host_port = url_parts[0]

            # Check for authentication
            if "@" in host_port:
                # Format: user:pass@host:port
                auth_part, host_port = host_port.split("@")
                if ":" in auth_part:
                    _, password = auth_part.split(":", 1)
                    self.redis_password = password or self.redis_password

            # Parse host and port
            if ":" in host_port:
                self.redis_host, port = host_port.split(":")
                self.redis_port = int(port)
            else:
                self.redis_host = host_port
                self.redis_port = 6379
        else:
            self.redis_host = "localhost"
            self.redis_port = 6379

        self.redis_password = redis_password
        self.redis_client = None

        # Backup directory
        self.backup_dir = Path("./backups")
        self.backup_dir.mkdir(exist_ok=True)

    async def connect(self):
        """Establish connection to Redis."""
        self.redis_client = await redis.Redis(
            host=self.redis_host,
            port=self.redis_port,
            password=self.redis_password,
            decode_responses=True,
        )

        # Test connection
        try:
            await self.redis_client.ping()
            print(f"✅ Connected to Redis at {self.redis_host}:{self.redis_port}")
        except Exception as e:
            print(f"❌ Failed to connect to Redis: {e}")
            sys.exit(1)

    async def backup_all_data(self) -> dict:
        """Backup all OAuth-related data from Redis."""
        backup_data = {
            "timestamp": datetime.now(UTC).isoformat(),
            "registrations": {},
            "tokens": {},
            "refresh_tokens": {},
            "user_tokens": {},
            "states": {},
            "codes": {},
            "sessions": {},
            "metadata": {
                "total_registrations": 0,
                "total_tokens": 0,
                "total_refresh_tokens": 0,
                "total_sessions": 0,
            },
        }

        # Pattern definitions
        patterns = {
            "registrations": "oauth:client:*",
            "tokens": "oauth:token:*",
            "refresh_tokens": "oauth:refresh:*",
            "user_tokens": "oauth:user_tokens:*",
            "states": "oauth:state:*",
            "codes": "oauth:code:*",
            "sessions": "redis:session:*",
        }

        # Backup each category
        for category, pattern in patterns.items():
            print(f"\n🔍 Backing up {category}...")
            cursor = 0
            count = 0

            while True:
                cursor, keys = await self.redis_client.scan(cursor, match=pattern, count=100)

                for key in keys:
                    try:
                        # Determine key type
                        key_type = await self.redis_client.type(key)
                        ttl = await self.redis_client.ttl(key)

                        # Handle different data types
                        if key_type == "string":
                            value = await self.redis_client.get(key)
                        elif key_type == "list":
                            # For user_tokens, it's a list
                            value = await self.redis_client.lrange(key, 0, -1)
                            value = json.dumps(value)  # Convert to JSON string for storage
                        elif key_type == "set":
                            value = list(await self.redis_client.smembers(key))
                            value = json.dumps(value)
                        elif key_type == "hash":
                            value = await self.redis_client.hgetall(key)
                            value = json.dumps(value)
                        else:
                            print(f"  ⚠️  Unsupported type {key_type} for key {key}")
                            continue

                        # Store with metadata
                        key_data = {
                            "value": value,
                            "type": key_type,
                            "ttl": ttl if ttl > 0 else -1,  # -1 means no expiry
                        }

                        # Try to parse JSON values for display
                        try:
                            if key_type == "string":
                                parsed_value = json.loads(value)
                                key_data["parsed"] = parsed_value

                                # Extract useful info for display
                                if category == "registrations":
                                    client_name = parsed_value.get("client_name", "Unknown")
                                    print(f"  📦 {key} → {client_name}")
                                elif category == "tokens":
                                    client_id = parsed_value.get("client_id", "Unknown")
                                    username = parsed_value.get("username", "Unknown")
                                    print(f"  🔑 {key} → {username} ({client_id})")
                            elif category == "user_tokens" and key_type == "list":
                                tokens = json.loads(value)
                                print(f"  👤 {key} → {len(tokens)} tokens")
                        except (json.JSONDecodeError, KeyError, TypeError):
                            # Not JSON or display not needed - this is expected for some Redis values
                            pass

                        # Remove prefix for cleaner storage
                        clean_key = key.split(":", 2)[-1] if ":" in key else key

                        if category == "sessions":
                            # Handle session data specially
                            if "state" in key:
                                backup_data["sessions"][clean_key] = key_data
                            # Skip message queues for now
                        else:
                            backup_data[category][clean_key] = key_data

                        count += 1
                    except Exception as e:
                        print(f"  ⚠️  Error backing up {key}: {e}")

                if cursor == 0:
                    break

            # Update metadata
            if category in ["registrations", "tokens", "refresh_tokens", "sessions"]:
                backup_data["metadata"][f"total_{category}"] = count

            print(f"  ✅ Backed up {count} {category}")

        return backup_data

    async def save_backup(self, backup_data: dict, filename: str | None = None) -> str:
        """Save backup data to file."""
        if not filename:
            timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
            filename = f"oauth-backup-{timestamp}.json"

        filepath = self.backup_dir / filename

        # Save with pretty formatting
        with open(filepath, "w") as f:
            json.dump(backup_data, f, indent=2, sort_keys=True)

        # Calculate file size
        size_bytes = filepath.stat().st_size
        size_mb = size_bytes / (1024 * 1024)

        print(f"\n💾 Backup saved to: {filepath}")
        print(f"📊 File size: {size_mb:.2f} MB ({size_bytes:,} bytes)")

        return str(filepath)

    async def list_backups(self) -> list[dict]:
        """List all available backups."""
        backups = []

        for filepath in sorted(self.backup_dir.glob("oauth-backup-*.json"), reverse=True):
            stat = filepath.stat()

            # Load metadata
            with open(filepath) as f:
                data = json.load(f)

            backups.append(
                {
                    "filename": filepath.name,
                    "path": str(filepath),
                    "size_mb": stat.st_size / (1024 * 1024),
                    "created": datetime.fromtimestamp(stat.st_mtime, tz=UTC).isoformat(),
                    "timestamp": data.get("timestamp"),
                    "registrations": data["metadata"]["total_registrations"],
                    "tokens": data["metadata"]["total_tokens"],
                    "refresh_tokens": data["metadata"]["total_refresh_tokens"],
                    "sessions": data["metadata"]["total_sessions"],
                },
            )

        return backups

    async def cleanup(self):
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.aclose()


async def main():
    """Divine backup orchestration."""
    backup = OAuthBackup()

    try:
        await backup.connect()

        print("🔐 OAuth Data Backup Service")
        print("=" * 60)

        # Create backup
        print("Creating backup...")
        backup_data = await backup.backup_all_data()

        # Save to file
        await backup.save_backup(backup_data)

        # Summary
        print("\n📊 Backup Summary:")
        print(f"  • Registrations: {backup_data['metadata']['total_registrations']}")
        print(f"  • Access Tokens: {backup_data['metadata']['total_tokens']}")
        print(f"  • Refresh Tokens: {backup_data['metadata']['total_refresh_tokens']}")
        print(f"  • Sessions: {backup_data['metadata']['total_sessions']}")

        print("\n✅ Backup completed successfully!")

    finally:
        await backup.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
