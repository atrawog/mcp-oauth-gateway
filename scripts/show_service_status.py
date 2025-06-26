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


def get_health_status(container_name):
    """Get health status of a container."""
    try:
        result = subprocess.run(
            ["docker", "inspect", container_name, "--format", "{{json .State.Health}}"],
            capture_output=True,
            text=True,
            check=True,
        )

        if result.stdout.strip() == "null":
            return "no health check"

        health = json.loads(result.stdout.strip())
        return health.get("Status", "unknown")

    except subprocess.CalledProcessError:
        return "not found"
    except json.JSONDecodeError:
        return "error"


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

    print()
    print("=== Detailed Health Status ===")
    print()

    # Check health for each service
    services = [
        "traefik",
        "auth",
        "redis",
        "mcp-fetch",
        "mcp-fetchs",
        "mcp-filesystem",
        "mcp-memory",
        "mcp-playwright",
        "mcp-sequentialthinking",
        "mcp-time",
        "mcp-tmux",
        "mcp-echo",
        "mcp-everything",
    ]

    for service in services:
        health = get_health_status(service)
        print(f"{service}: {health}")

        # If unhealthy, show more details
        if health == "unhealthy":
            try:
                result = subprocess.run(["docker", "inspect", service], capture_output=True, text=True, check=True)
                data = json.loads(result.stdout)
                if data and data[0].get("State", {}).get("Health", {}).get("Log"):
                    last_log = data[0]["State"]["Health"]["Log"][-1]
                    output = last_log.get("Output", "").strip()
                    if output:
                        print(f"  Last health check output: {output[:100]}...")
            except:
                pass


if __name__ == "__main__":
    main()
