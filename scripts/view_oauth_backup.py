#!/usr/bin/env python3
"""View contents of OAuth backup file
Following the divine commandments of CLAUDE.md.
"""
import json
import sys
from pathlib import Path


def view_backup(filepath: str):
    """Display backup contents in a readable format."""
    # Load backup
    try:
        with open(filepath) as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"❌ Backup file not found: {filepath}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error loading backup: {e}")
        sys.exit(1)

    # Display header
    print("🔐 OAuth Backup Contents")
    print("=" * 80)
    print(f"📁 File: {filepath}")
    print(f"📅 Created: {data.get('timestamp', 'Unknown')}")
    print("=" * 80)

    # Display metadata
    metadata = data.get("metadata", {})
    print("\n📊 Summary:")
    print(f"  • Registrations: {metadata.get('total_registrations', 0)}")
    print(f"  • Access Tokens: {metadata.get('total_tokens', 0)}")
    print(f"  • Refresh Tokens: {metadata.get('total_refresh_tokens', 0)}")
    print(f"  • Sessions: {metadata.get('total_sessions', 0)}")

    # Display registrations
    if data.get("registrations"):
        print("\n📦 Client Registrations:")
        print("-" * 80)
        for client_id, reg_data in data["registrations"].items():
            value = reg_data.get("value", "{}")
            ttl = reg_data.get("ttl", -1)

            try:
                reg_info = json.loads(value)
                print(f"\n  Client ID: {client_id}")
                print(f"  Name: {reg_info.get('client_name', 'Unknown')}")
                print(f"  Created: {reg_info.get('client_id_issued_at', 'Unknown')}")
                print(f"  Redirect URIs: {', '.join(reg_info.get('redirect_uris', []))}")
                print(f"  TTL: {ttl} seconds" if ttl > 0 else "  TTL: No expiry")
            except:
                print(f"\n  Client ID: {client_id}")
                print(f"  Data: {value[:100]}..." if len(value) > 100 else f"  Data: {value}")

    # Display tokens
    if data.get("tokens"):
        print("\n\n🔑 Access Tokens:")
        print("-" * 80)
        for jti, token_data in data["tokens"].items():
            value = token_data.get("value", "{}")
            ttl = token_data.get("ttl", -1)

            try:
                token_info = json.loads(value)
                print(f"\n  JTI: {jti}")
                print(f"  User: {token_info.get('username', 'Unknown')}")
                print(f"  Client ID: {token_info.get('client_id', 'Unknown')}")
                print(f"  Scope: {token_info.get('scope', 'Unknown')}")
                print(f"  Issued: {token_info.get('iat', 'Unknown')}")
                print(f"  TTL: {ttl} seconds ({ttl/3600:.1f} hours)" if ttl > 0 else "  TTL: No expiry")
            except:
                print(f"\n  JTI: {jti}")
                print(f"  Data: {value[:100]}..." if len(value) > 100 else f"  Data: {value}")

    # Display user tokens
    if data.get("user_tokens"):
        print("\n\n👤 User Token Lists:")
        print("-" * 80)
        for username, token_data in data["user_tokens"].items():
            value = token_data.get("value", "[]")
            data_type = token_data.get("type", "string")

            try:
                if data_type == "list":
                    tokens = json.loads(value)
                    print(f"\n  User: {username}")
                    print(f"  Tokens: {len(tokens)}")
                    for _i, token in enumerate(tokens[:3]):  # Show first 3
                        print(f"    • {token}")
                    if len(tokens) > 3:
                        print(f"    ... and {len(tokens) - 3} more")
                else:
                    print(f"\n  User: {username}")
                    print(f"  Data: {value[:100]}..." if len(value) > 100 else f"  Data: {value}")
            except:
                print(f"\n  User: {username}")
                print("  Error parsing data")

    # Display refresh tokens count
    if data.get("refresh_tokens"):
        print("\n\n🔄 Refresh Tokens:")
        print("-" * 80)
        print(f"  Total: {len(data['refresh_tokens'])} tokens")
        # Show first few
        for _i, (token_id, token_data) in enumerate(list(data["refresh_tokens"].items())[:3]):
            print(f"  • {token_id[:20]}...")
        if len(data["refresh_tokens"]) > 3:
            print(f"  ... and {len(data['refresh_tokens']) - 3} more")

    print("\n" + "=" * 80)
    print("✅ End of backup contents")


def main():
    """Main entry point."""
    if len(sys.argv) != 2:
        # Try to find latest backup
        backup_dir = Path("./backups")
        if backup_dir.exists():
            backups = sorted(backup_dir.glob("oauth-backup-*.json"), reverse=True)
            if backups:
                print(f"Usage: {sys.argv[0]} <backup-file>")
                print(f"\nExample: {sys.argv[0]} {backups[0]}")
                sys.exit(1)

        print(f"Usage: {sys.argv[0]} <backup-file>")
        sys.exit(1)

    filepath = sys.argv[1]
    view_backup(filepath)


if __name__ == "__main__":
    main()
