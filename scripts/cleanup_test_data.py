#!/usr/bin/env python3
"""Divine Test Data Cleanup Script - CLAUDE.md Compliant!
Cleanses the Redis sanctuary of test-created OAuth artifacts.

Identifies test registrations by client_name starting with "TEST "
Example: "TEST test_oauth_flow", "TEST test_registration", etc.

Following the sacred commandments:
- NO MOCKING - works with real Redis
- Uses blessed tools (pixi run)
- Respects the sacred key patterns
"""

import json
import os
import sys
from datetime import datetime

import redis

# SACRED LAW: Load configuration from .env
from dotenv import load_dotenv


load_dotenv()

# Redis connection from blessed environment
# For scripts running outside containers, use localhost
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")


class TestDataCleaner:
    """Sacred cleanser of test artifacts."""

    def __init__(self):
        self.redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            password=REDIS_PASSWORD,
            decode_responses=True
        )
        # Sacred test naming pattern: "TEST testname"
        self.test_prefix = "TEST "

    def is_test_client(self, client_id: str) -> bool:
        """Divine detection of test-created clients."""
        # Check client ID
        if client_id.startswith(self.test_prefix):
            return True

        # Also check the client_name in registration data
        try:
            client_data = self.redis_client.get(f"oauth:client:{client_id}")
            if client_data:
                data = json.loads(client_data)
                client_name = data.get('client_name', '')
                return client_name.startswith(self.test_prefix)
        except:
            pass

        return False

    def find_test_registrations(self) -> list[dict]:
        """Seek out test registrations in the Redis sanctuary."""
        test_registrations = []

        # Sacred pattern: oauth:client:*
        for key in self.redis_client.scan_iter("oauth:client:*"):
            client_id = key.split(":")[-1]

            if self.is_test_client(client_id):
                try:
                    data = self.redis_client.get(key)
                    if data:
                        client_data = json.loads(data)
                        client_data['redis_key'] = key
                        client_data['client_id'] = client_id
                        test_registrations.append(client_data)
                except Exception as e:
                    print(f"⚠️  Error reading {key}: {e}")

        return test_registrations

    def find_related_tokens(self, client_id: str) -> dict[str, list[str]]:
        """Find all tokens blessed by this client."""
        related = {
            'access_tokens': [],
            'refresh_tokens': [],
            'authorization_codes': [],
            'states': []
        }

        # Search for access tokens
        for key in self.redis_client.scan_iter("oauth:token:*"):
            try:
                token_data = self.redis_client.get(key)
                if token_data:
                    token_info = json.loads(token_data)
                    if token_info.get('client_id') == client_id:
                        related['access_tokens'].append(key)
            except:
                pass

        # Search for refresh tokens
        for key in self.redis_client.scan_iter("oauth:refresh:*"):
            try:
                token_data = self.redis_client.get(key)
                if token_data:
                    token_info = json.loads(token_data)
                    if token_info.get('client_id') == client_id:
                        related['refresh_tokens'].append(key)
            except:
                pass

        # Search for authorization codes
        for key in self.redis_client.scan_iter("oauth:code:*"):
            try:
                code_data = self.redis_client.get(key)
                if code_data:
                    code_info = json.loads(code_data)
                    if code_info.get('client_id') == client_id:
                        related['authorization_codes'].append(key)
            except:
                pass

        return related

    def show_test_data(self):
        """Divine revelation of test artifacts."""
        print("🔍 Seeking test artifacts in Redis sanctuary...\n")

        registrations = self.find_test_registrations()

        if not registrations:
            print("✨ No test registrations found - Redis is pure!")
            return

        print(f"Found {len(registrations)} test registrations:\n")

        total_artifacts = 0
        for reg in registrations:
            client_id = reg['client_id']
            created = reg.get('created_at', 'Unknown')

            print(f"📋 Client: {client_id}")
            print(f"   Created: {created}")

            # Find related artifacts
            related = self.find_related_tokens(client_id)

            artifact_count = sum(len(v) for v in related.values())
            total_artifacts += artifact_count + 1  # +1 for the registration itself

            print("   Related artifacts:")
            print(f"     - Access tokens: {len(related['access_tokens'])}")
            print(f"     - Refresh tokens: {len(related['refresh_tokens'])}")
            print(f"     - Auth codes: {len(related['authorization_codes'])}")
            print()

        print(f"\n📊 Total test artifacts: {total_artifacts}")

    def cleanup_test_data(self, dry_run: bool = True):
        """Sacred cleansing ritual for test data."""
        if dry_run:
            print("🔍 DRY RUN - Showing what would be deleted...\n")
        else:
            print("🧹 EXECUTING CLEANUP - Purging test artifacts...\n")

        registrations = self.find_test_registrations()

        if not registrations:
            print("✨ No test registrations found - Redis is already pure!")
            return

        total_deleted = 0

        for reg in registrations:
            client_id = reg['client_id']
            redis_key = reg['redis_key']

            print(f"\n{'Would delete' if dry_run else 'Deleting'} client: {client_id}")

            # Find and delete related tokens
            related = self.find_related_tokens(client_id)

            # Delete all related artifacts
            keys_to_delete = [redis_key]  # Start with the client registration

            for artifact_type, keys in related.items():
                if keys:
                    print(f"  - {len(keys)} {artifact_type}")
                    keys_to_delete.extend(keys)

            if not dry_run:
                # DIVINE DELETION RITUAL
                for key in keys_to_delete:
                    self.redis_client.delete(key)
                print(f"  ✅ Deleted {len(keys_to_delete)} artifacts")
            else:
                print(f"  Would delete {len(keys_to_delete)} artifacts")

            total_deleted += len(keys_to_delete)

        print(f"\n{'Would delete' if dry_run else 'Deleted'} {total_deleted} total artifacts")

        if dry_run:
            print("\n💡 Run with --execute to actually delete these artifacts")

    def cleanup_expired_tokens(self):
        """Purge tokens whose time has come."""
        print("🕐 Checking for expired tokens...\n")

        expired_count = 0

        # Check access tokens
        for key in self.redis_client.scan_iter("oauth:token:*"):
            try:
                token_data = self.redis_client.get(key)
                if token_data:
                    token_info = json.loads(token_data)
                    exp = token_info.get('exp', 0)

                    if exp < datetime.utcnow().timestamp():
                        print(f"🗑️  Deleting expired token: {key}")
                        self.redis_client.delete(key)
                        expired_count += 1
            except Exception as e:
                print(f"⚠️  Error processing {key}: {e}")

        print(f"\n✅ Deleted {expired_count} expired tokens")


def main():
    """Divine entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Sacred test data cleanup utility - CLAUDE.md compliant!"
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Show test data without deleting"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually delete test data (default is dry run)"
    )
    parser.add_argument(
        "--expired",
        action="store_true",
        help="Also cleanup expired tokens"
    )

    args = parser.parse_args()

    cleaner = TestDataCleaner()

    try:
        if args.show:
            cleaner.show_test_data()
        elif args.expired:
            cleaner.cleanup_expired_tokens()
        else:
            # Default to cleanup with dry run unless --execute
            cleaner.cleanup_test_data(dry_run=not args.execute)
    except redis.ConnectionError:
        print("❌ Failed to connect to Redis. Is the service running?")
        print("   Run 'just up' to start services")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Divine error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
