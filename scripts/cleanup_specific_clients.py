#!/usr/bin/env python3
"""Clean up specific client registrations by name."""
import json
import os

import redis
from dotenv import load_dotenv


# Load environment variables
load_dotenv()

# Redis connection
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")

def cleanup_specific_clients():
    """Clean up specific client names."""
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        password=REDIS_PASSWORD,
        decode_responses=True
    )

    # Names to clean up
    cleanup_names = ["Test Client", "Edge Case Test"]

    print("🧹 Cleaning up specific client registrations...")

    # Get all client keys
    client_keys = redis_client.keys("oauth:client:*")
    deleted = 0

    for key in client_keys:
        try:
            client_data = redis_client.get(key)
            if client_data:
                client = json.loads(client_data)
                client_name = client.get('client_name', '')

                if client_name in cleanup_names:
                    client_id = key.split(':')[-1]
                    print(f"Deleting client: {client_id} - {client_name}")

                    # Delete all related keys
                    redis_client.delete(key)
                    redis_client.delete(f"oauth:client_secret:{client_id}")
                    redis_client.delete(f"oauth:registration_token:{client_id}")

                    # Delete any tokens for this client
                    token_keys = redis_client.keys("oauth:token:*")
                    for token_key in token_keys:
                        token_data = redis_client.get(token_key)
                        if token_data:
                            try:
                                token = json.loads(token_data)
                                if token.get('client_id') == client_id:
                                    redis_client.delete(token_key)
                            except:
                                pass

                    deleted += 1
                    print("  ✅ Deleted")

        except Exception as e:
            print(f"  ❌ Error processing {key}: {e}")

    print(f"\nDeleted {deleted} clients")

if __name__ == "__main__":
    cleanup_specific_clients()
