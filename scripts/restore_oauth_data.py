#!/usr/bin/env python3
"""
Restore OAuth Data to Redis
Following the divine commandments of CLAUDE.md - NO MOCKING!
"""
import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

import redis.asyncio as redis
from dotenv import load_dotenv

# Load environment - SACRED LAW!
load_dotenv()


class OAuthRestore:
    """Divine restoration service for OAuth artifacts"""
    
    def __init__(self):
        # Redis connection from environment - NO HARDCODING!
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        redis_password = os.getenv('REDIS_PASSWORD')
        
        # If we're running on the host and Redis URL points to 'redis' hostname,
        # change it to localhost (Redis is exposed on host ports)
        if 'redis://' in redis_url and 'redis:' in redis_url:
            # Check if we're in a container
            if not os.path.exists('/.dockerenv'):
                # We're on the host, use localhost
                redis_url = redis_url.replace('redis:', 'localhost:')
        
        # Parse Redis URL
        if redis_url.startswith('redis://'):
            # Remove redis:// prefix and any path
            url_parts = redis_url.replace('redis://', '').split('/')
            host_port = url_parts[0]
            
            # Check for authentication
            if '@' in host_port:
                # Format: user:pass@host:port
                auth_part, host_port = host_port.split('@')
                if ':' in auth_part:
                    _, password = auth_part.split(':', 1)
                    self.redis_password = password or self.redis_password
                host_port = host_port
            
            # Parse host and port
            if ':' in host_port:
                self.redis_host, port = host_port.split(':')
                self.redis_port = int(port)
            else:
                self.redis_host = host_port
                self.redis_port = 6379
        else:
            self.redis_host = 'localhost'
            self.redis_port = 6379
        
        self.redis_password = redis_password
        self.redis_client = None
        
        # Backup directory
        self.backup_dir = Path("./backups")
    
    async def connect(self):
        """Establish connection to Redis"""
        self.redis_client = await redis.Redis(
            host=self.redis_host,
            port=self.redis_port,
            password=self.redis_password,
            decode_responses=True
        )
        
        # Test connection
        try:
            await self.redis_client.ping()
            print(f"✅ Connected to Redis at {self.redis_host}:{self.redis_port}")
        except Exception as e:
            print(f"❌ Failed to connect to Redis: {e}")
            sys.exit(1)
    
    async def list_backups(self) -> list:
        """List available backup files"""
        if not self.backup_dir.exists():
            return []
        
        backups = []
        for i, filepath in enumerate(sorted(self.backup_dir.glob("oauth-backup-*.json"), reverse=True)):
            stat = filepath.stat()
            
            # Load metadata
            try:
                with open(filepath) as f:
                    data = json.load(f)
                
                backups.append({
                    "index": i + 1,
                    "filename": filepath.name,
                    "path": str(filepath),
                    "size_mb": stat.st_size / (1024 * 1024),
                    "created": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                    "timestamp": data.get("timestamp", "Unknown"),
                    "registrations": data["metadata"]["total_registrations"],
                    "tokens": data["metadata"]["total_tokens"],
                    "refresh_tokens": data["metadata"]["total_refresh_tokens"],
                    "sessions": data["metadata"]["total_sessions"]
                })
            except Exception as e:
                print(f"⚠️  Error reading {filepath.name}: {e}")
        
        return backups
    
    async def check_existing_data(self) -> Dict[str, int]:
        """Check what data currently exists in Redis"""
        patterns = {
            "registrations": "oauth:client:*",
            "tokens": "oauth:token:*",
            "refresh_tokens": "oauth:refresh:*",
            "user_tokens": "oauth:user_tokens:*",
            "states": "oauth:state:*",
            "codes": "oauth:code:*",
            "sessions": "redis:session:*"
        }
        
        counts = {}
        for category, pattern in patterns.items():
            cursor = 0
            count = 0
            
            while True:
                cursor, keys = await self.redis_client.scan(
                    cursor, match=pattern, count=100
                )
                count += len(keys)
                if cursor == 0:
                    break
            
            counts[category] = count
        
        return counts
    
    async def restore_from_backup(self, backup_path: str, dry_run: bool = False, clear_existing: bool = False):
        """Restore OAuth data from backup file"""
        # Load backup
        print(f"\n📂 Loading backup from: {backup_path}")
        
        try:
            with open(backup_path) as f:
                backup_data = json.load(f)
        except Exception as e:
            print(f"❌ Failed to load backup: {e}")
            return False
        
        # Show backup info
        print(f"\n📊 Backup Information:")
        print(f"  • Created: {backup_data.get('timestamp', 'Unknown')}")
        print(f"  • Registrations: {backup_data['metadata']['total_registrations']}")
        print(f"  • Access Tokens: {backup_data['metadata']['total_tokens']}")
        print(f"  • Refresh Tokens: {backup_data['metadata']['total_refresh_tokens']}")
        print(f"  • Sessions: {backup_data['metadata']['total_sessions']}")
        
        # Check existing data
        existing_counts = await self.check_existing_data()
        has_existing = any(count > 0 for count in existing_counts.values())
        
        if has_existing:
            print(f"\n⚠️  WARNING: Existing data found in Redis:")
            for category, count in existing_counts.items():
                if count > 0:
                    print(f"  • {category}: {count}")
            
            if not clear_existing:
                print("\n❌ Aborting restore. Use --clear to overwrite existing data.")
                return False
            else:
                print("\n🗑️  Clearing existing data...")
                if not dry_run:
                    await self.clear_all_oauth_data()
        
        if dry_run:
            print("\n🔍 DRY RUN - No changes will be made")
        
        # Restore each category
        restored_counts = {
            "registrations": 0,
            "tokens": 0,
            "refresh_tokens": 0,
            "user_tokens": 0,
            "states": 0,
            "codes": 0,
            "sessions": 0
        }
        
        # Define key prefixes
        prefixes = {
            "registrations": "oauth:client:",
            "tokens": "oauth:token:",
            "refresh_tokens": "oauth:refresh:",
            "user_tokens": "oauth:user_tokens:",
            "states": "oauth:state:",
            "codes": "oauth:code:",
            "sessions": ""  # Session keys already include full path
        }
        
        for category, prefix in prefixes.items():
            if category not in backup_data:
                continue
            
            print(f"\n🔄 Restoring {category}...")
            
            for key, data in backup_data[category].items():
                try:
                    # Construct full key
                    if category == "sessions":
                        full_key = key  # Session keys are already full
                    else:
                        full_key = f"{prefix}{key}"
                    
                    value = data["value"]
                    ttl = data.get("ttl", -1)
                    key_type = data.get("type", "string")  # Default to string for old backups
                    
                    if not dry_run:
                        # Restore based on data type
                        if key_type == "string":
                            await self.redis_client.set(full_key, value)
                        elif key_type == "list":
                            # Clear existing list and restore
                            await self.redis_client.delete(full_key)
                            items = json.loads(value)
                            if items:
                                await self.redis_client.rpush(full_key, *items)
                        elif key_type == "set":
                            # Clear existing set and restore
                            await self.redis_client.delete(full_key)
                            items = json.loads(value)
                            if items:
                                await self.redis_client.sadd(full_key, *items)
                        elif key_type == "hash":
                            # Clear existing hash and restore
                            await self.redis_client.delete(full_key)
                            hash_data = json.loads(value)
                            if hash_data:
                                await self.redis_client.hset(full_key, mapping=hash_data)
                        
                        # Set TTL if applicable
                        if ttl > 0:
                            await self.redis_client.expire(full_key, ttl)
                    
                    # Show progress for important items
                    if category in ["registrations", "tokens"]:
                        if "parsed" in data:
                            parsed = data["parsed"]
                            if category == "registrations":
                                client_name = parsed.get("client_name", "Unknown")
                                print(f"  ✅ {full_key} → {client_name}")
                            elif category == "tokens":
                                username = parsed.get("username", "Unknown")
                                client_id = parsed.get("client_id", "Unknown")
                                print(f"  ✅ {full_key} → {username} ({client_id})")
                    
                    restored_counts[category] += 1
                    
                except Exception as e:
                    print(f"  ❌ Failed to restore {full_key}: {e}")
            
            print(f"  ✅ Restored {restored_counts[category]} {category}")
        
        # Summary
        print(f"\n📊 Restore Summary:")
        for category, count in restored_counts.items():
            if count > 0:
                print(f"  • {category}: {count}")
        
        if dry_run:
            print("\n✅ DRY RUN completed - no changes were made")
        else:
            print("\n✅ Restore completed successfully!")
        
        return True
    
    async def clear_all_oauth_data(self):
        """Clear all OAuth data from Redis"""
        patterns = [
            "oauth:client:*",
            "oauth:token:*",
            "oauth:refresh:*",
            "oauth:user_tokens:*",
            "oauth:state:*",
            "oauth:code:*",
            "redis:session:*"
        ]
        
        total_deleted = 0
        for pattern in patterns:
            cursor = 0
            while True:
                cursor, keys = await self.redis_client.scan(
                    cursor, match=pattern, count=100
                )
                
                if keys:
                    deleted = await self.redis_client.delete(*keys)
                    total_deleted += deleted
                
                if cursor == 0:
                    break
        
        print(f"  🗑️  Deleted {total_deleted} existing keys")
    
    async def cleanup(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.aclose()


async def main():
    """Divine restoration orchestration"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Restore OAuth data from backup")
    parser.add_argument("--list", action="store_true", help="List available backups")
    parser.add_argument("--file", type=str, help="Backup file to restore from")
    parser.add_argument("--latest", action="store_true", help="Restore from latest backup")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be restored without making changes")
    parser.add_argument("--clear", action="store_true", help="Clear existing data before restore")
    
    args = parser.parse_args()
    
    restore = OAuthRestore()
    
    try:
        await restore.connect()
        
        print("🔐 OAuth Data Restore Service")
        print("=" * 60)
        
        # List backups
        backups = await restore.list_backups()
        
        if args.list or (not args.file and not args.latest):
            if not backups:
                print("\n❌ No backups found in ./backups/")
                return
            
            print("\n📋 Available Backups:")
            print("-" * 80)
            print(f"{'#':>3} {'Filename':<35} {'Created':<20} {'Regs':<6} {'Tokens':<8} {'Size':<8}")
            print("-" * 80)
            
            for backup in backups:
                print(f"{backup['index']:>3} {backup['filename']:<35} {backup['created']:<20} "
                      f"{backup['registrations']:<6} {backup['tokens']:<8} {backup['size_mb']:.2f} MB")
            
            if not args.list:
                print("\nUse --file <filename> or --latest to restore a backup")
            return
        
        # Determine which backup to use
        if args.latest:
            if not backups:
                print("\n❌ No backups found")
                return
            backup_path = backups[0]["path"]
        else:
            # Check if it's a full path or just filename
            if os.path.exists(args.file):
                backup_path = args.file
            else:
                backup_path = restore.backup_dir / args.file
                if not backup_path.exists():
                    print(f"\n❌ Backup file not found: {args.file}")
                    return
        
        # Perform restore
        await restore.restore_from_backup(
            str(backup_path),
            dry_run=args.dry_run,
            clear_existing=args.clear
        )
        
    finally:
        await restore.cleanup()


if __name__ == "__main__":
    asyncio.run(main())