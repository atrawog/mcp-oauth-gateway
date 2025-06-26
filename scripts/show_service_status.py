#!/usr/bin/env python3
"""Show service status and health information."""

import json
import subprocess


def get_container_status():
    """Get status of all containers."""
    try:
        # Get all running containers
        result = subprocess.run(["docker", "ps", "--format", "json"], capture_output=True, text=True, check=True)

        containers = []
        for line in result.stdout.strip().split("\n"):
            if line:
                container = json.loads(line)
                name = container.get("Names", "")
                # Filter for our services
                if any(svc in name for svc in ["traefik", "auth", "redis", "mcp-"]):
                    containers.append(container)

        return containers
    except subprocess.CalledProcessError as e:
        print(f"Error getting container status: {e}")
        return []


def main():
    """Show service status and health."""
    print("=== Service Status and Health ===")
    print()

    # Get container status
    containers = get_container_status()

    # Print container table
    print(f"{'CONTAINER':<30} {'STATUS':<40} {'STATE'}")
    print("-" * 80)

    for container in containers:
        name = container.get("Names", "unknown")
        status = container.get("Status", "unknown")
        state = container.get("State", "unknown")
        print(f"{name:<30} {status:<40} {state}")


if __name__ == "__main__":
    main()
