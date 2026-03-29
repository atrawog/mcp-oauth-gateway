#!/usr/bin/env python3
"""Check that all services are built, running, and healthy before tests."""

import asyncio
import json
import os
import subprocess
import sys
import time

from rich.console import Console

console = Console()


def run_command(cmd: list[str]) -> tuple[int, str, str]:
    """Run a command and return exit code, stdout, and stderr."""
    try:
        result = subprocess.run(cmd, check=False, capture_output=True, text=True)
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)


def is_service_disabled(service_name: str) -> tuple[bool, str]:
    """Check if a service is disabled via environment variables."""
    # Map of service names to their enable environment variables
    service_env_map = {
        "mcp-fetch": "MCP_FETCH_ENABLED",
        "mcp-echo-stateful": "MCP_ECHO_STATEFUL_ENABLED",
        "mcp-echo-stateless": "MCP_ECHO_STATELESS_ENABLED",
        "mcp-everything": "MCP_EVERYTHING_ENABLED",
        "mcp-fetchs": "MCP_FETCHS_ENABLED",
        "mcp-filesystem": "MCP_FILESYSTEM_ENABLED",
        "mcp-memory": "MCP_MEMORY_ENABLED",
        "mcp-playwright": "MCP_PLAYWRIGHT_ENABLED",
        "mcp-sequentialthinking": "MCP_SEQUENTIALTHINKING_ENABLED",
        "mcp-time": "MCP_TIME_ENABLED",
        "mcp-tmux": "MCP_TMUX_ENABLED",
    }

    env_var = service_env_map.get(service_name)
    if env_var and os.getenv(env_var, "false").lower() != "true":
        return True, env_var
    return False, ""


def check_docker_service(service_name: str) -> bool:
    """Check if a Docker service is running."""
    # Check if service is disabled
    disabled, env_var = is_service_disabled(service_name)
    if disabled:
        console.print(f"[yellow]⊝ Service {service_name} is disabled via {env_var}[/yellow]")
        return True  # Consider it "passing" since it's intentionally disabled

    # Check if service is running
    cmd = [
        "docker",
        "compose",
        "-f",
        "docker-compose.includes.yml",
        "ps",
        service_name,
        "--format",
        "json",
    ]
    code, stdout, stderr = run_command(cmd)

    if code != 0:
        console.print(f"[red]✗ Failed to check {service_name}: {stderr}[/red]")
        return False

    if not stdout.strip():
        console.print(f"[red]✗ Service {service_name} is not running[/red]")
        return False

    # Parse and check service state
    try:
        service_info = json.loads(stdout.strip())
        state = service_info.get("State", "unknown")
        if state == "running":
            console.print(f"[green]✓ Service {service_name} is running[/green]")
            return True
        console.print(f"[red]✗ Service {service_name} is in state: {state}[/red]")
        return False
    except Exception:
        console.print(f"[yellow]⚠ Could not parse {service_name} status[/yellow]")
        return False


def check_network_exists() -> bool:
    """Check if the public network exists."""
    cmd = ["docker", "network", "ls", "--format", "{{.Name}}"]
    code, stdout, stderr = run_command(cmd)

    if code != 0:
        console.print(f"[red]✗ Failed to list networks: {stderr}[/red]")
        return False

    if "public" in stdout:
        console.print("[green]✓ Network 'public' exists[/green]")
        return True
    console.print("[red]✗ Network 'public' does not exist[/red]")
    return False


def check_volumes_exist() -> bool:
    """Check if required volumes exist."""
    required_volumes = ["traefik-certificates", "redis-data", "coverage-data"]
    cmd = ["docker", "volume", "ls", "--format", "{{.Name}}"]
    code, stdout, stderr = run_command(cmd)

    if code != 0:
        console.print(f"[red]✗ Failed to list volumes: {stderr}[/red]")
        return False

    existing_volumes = stdout.strip().split("\n")
    all_exist = True

    for volume in required_volumes:
        if volume in existing_volumes:
            console.print(f"[green]✓ Volume '{volume}' exists[/green]")
        else:
            console.print(f"[red]✗ Volume '{volume}' does not exist[/red]")
            all_exist = False

    return all_exist


def build_services() -> bool:
    """Build all services."""
    console.print("\n[yellow]Building all services...[/yellow]")
    cmd = ["docker", "compose", "-f", "docker-compose.includes.yml", "build"]
    code, stdout, stderr = run_command(cmd)

    if code != 0:
        console.print(f"[red]✗ Failed to build services: {stderr}[/red]")
        return False

    console.print("[green]✓ All services built successfully[/green]")
    return True


def start_services() -> bool:
    """Start all services."""
    console.print("\n[yellow]Starting all services...[/yellow]")
    cmd = ["docker", "compose", "-f", "docker-compose.includes.yml", "up", "-d"]
    code, stdout, stderr = run_command(cmd)

    if code != 0:
        console.print(f"[red]✗ Failed to start services: {stderr}[/red]")
        return False

    console.print("[green]✓ All services started[/green]")
    return True


async def wait_for_services(max_wait: int = 60) -> bool:
    """Wait for all services to be healthy using Docker health checks."""
    console.print(f"\n[yellow]Waiting for Docker health checks (max {max_wait}s)...[/yellow]")

    services_to_check = ["traefik", "auth", "redis"]

    # Add mcp-fetch if enabled
    if os.getenv("MCP_FETCH_ENABLED", "false").lower() == "true":
        services_to_check.append("mcp-fetch")

    # Add mcp-echo if enabled
    if os.getenv("MCP_ECHO_STATEFUL_ENABLED", "false").lower() == "true":
        services_to_check.append("mcp-echo-stateful")

    # Add mcp-echo-stateless if enabled
    if os.getenv("MCP_ECHO_STATELESS_ENABLED", "false").lower() == "true":
        services_to_check.append("mcp-echo-stateless")

    # Add mcp-everything if enabled
    if os.getenv("MCP_EVERYTHING_ENABLED", "false").lower() == "true":
        services_to_check.append("mcp-everything")

    # Add other MCP services if enabled
    optional_services = [
        ("mcp-fetchs", "MCP_FETCHS_ENABLED"),
        ("mcp-filesystem", "MCP_FILESYSTEM_ENABLED"),
        ("mcp-memory", "MCP_MEMORY_ENABLED"),
        ("mcp-playwright", "MCP_PLAYWRIGHT_ENABLED"),
        ("mcp-sequentialthinking", "MCP_SEQUENTIALTHINKING_ENABLED"),
        ("mcp-time", "MCP_TIME_ENABLED"),
        ("mcp-tmux", "MCP_TMUX_ENABLED"),
    ]

    for service_name, env_var in optional_services:
        if os.getenv(env_var, "false").lower() == "true":
            services_to_check.append(service_name)

    start_time = time.time()

    while time.time() - start_time < max_wait:
        all_healthy = True
        unhealthy_services = []

        for service in services_to_check:
            cmd = ["docker", "inspect", service, "--format", "{{.State.Health.Status}}"]
            code, stdout, stderr = run_command(cmd)

            if code != 0:
                console.print(f"[red]✗ Failed to inspect {service}: {stderr}[/red]")
                all_healthy = False
                unhealthy_services.append(service)
                continue

            health_status = stdout.strip()

            if health_status == "":
                # No health check defined, check if running
                cmd = ["docker", "inspect", service, "--format", "{{.State.Status}}"]
                code, stdout, stderr = run_command(cmd)
                if code != 0 or stdout.strip() != "running":
                    all_healthy = False
                    unhealthy_services.append(f"{service} (not running)")
            elif health_status != "healthy":
                all_healthy = False
                unhealthy_services.append(f"{service} ({health_status})")

        if all_healthy:
            console.print("[green]✓ All services are healthy according to Docker[/green]")
            return True

        # Show progress
        elapsed = int(time.time() - start_time)
        console.print(
            f"\r[yellow]Waiting... {elapsed}s (unhealthy: {', '.join(unhealthy_services)})[/yellow]",
            end="",
        )
        await asyncio.sleep(2)

    console.print(f"\n[red]✗ Timeout waiting for services to be healthy[/red]")
    return False


def check_basic_config() -> bool:
    """Check that basic configuration is present (tokens validated in test setup)."""
    console.print("\n[yellow]Checking basic configuration...[/yellow]")

    # Only check critical variables needed for service startup
    # Token validation is now centralized in refresh_and_validate_tokens()
    basic_vars = [
        ("BASE_DOMAIN", "Base domain for services"),
        ("REDIS_PASSWORD", "Redis password"),
    ]

    all_present = True

    for var_name, description in basic_vars:
        value = os.getenv(var_name)
        if value and len(value) > 1:  # Basic check that it's not empty
            console.print(f"[green]✓ {var_name} is configured ({description})[/green]")
        else:
            console.print(f"[red]✗ {var_name} is missing or too short ({description})[/red]")
            all_present = False

    console.print("[yellow]Note: Full token validation happens during test setup via refresh_and_validate_tokens()[/yellow]")
    return all_present


async def main():
    """Main check function."""
    console.print(f"[yellow]{'=' * 60}[/yellow]")
    console.print("[yellow]Pre-test Service Check[/yellow]")
    console.print(f"[yellow]{'=' * 60}[/yellow]")

    # First, generate the docker-compose includes file
    console.print("\n[yellow]Generating docker-compose includes...[/yellow]")
    gen_cmd = ["python", "scripts/generate_compose_includes.py"]
    code, stdout, stderr = run_command(gen_cmd)
    if code != 0:
        console.print(f"[red]✗ Failed to generate docker-compose includes: {stderr}[/red]")
        return 1

    checks = []

    # Check network and volumes
    console.print("\n[yellow]Checking Docker resources...[/yellow]")
    checks.append(("Network", check_network_exists()))
    checks.append(("Volumes", check_volumes_exist()))

    # Build services if needed
    base_services = ["traefik", "auth", "redis"]
    if os.getenv("MCP_FETCH_ENABLED", "false").lower() == "true":
        base_services.append("mcp-fetch")
    if os.getenv("MCP_ECHO_STATEFUL_ENABLED", "false").lower() == "true":
        base_services.append("mcp-echo-stateful")
    if os.getenv("MCP_ECHO_STATELESS_ENABLED", "false").lower() == "true":
        base_services.append("mcp-echo-stateless")
    if os.getenv("MCP_EVERYTHING_ENABLED", "false").lower() == "true":
        base_services.append("mcp-everything")

    # Add other MCP services if enabled
    optional_services = [
        ("mcp-fetchs", "MCP_FETCHS_ENABLED"),
        ("mcp-filesystem", "MCP_FILESYSTEM_ENABLED"),
        ("mcp-memory", "MCP_MEMORY_ENABLED"),
        ("mcp-playwright", "MCP_PLAYWRIGHT_ENABLED"),
        ("mcp-sequentialthinking", "MCP_SEQUENTIALTHINKING_ENABLED"),
        ("mcp-time", "MCP_TIME_ENABLED"),
        ("mcp-tmux", "MCP_TMUX_ENABLED"),
    ]

    for service_name, env_var in optional_services:
        if os.getenv(env_var, "false").lower() == "true":
            base_services.append(service_name)

    if not all(check_docker_service(s) for s in base_services):
        checks.append(("Build", build_services()))
        checks.append(("Start", start_services()))

    # Check running services
    console.print("\n[yellow]Checking service status...[/yellow]")
    for service in base_services:
        checks.append((f"Service {service}", check_docker_service(service)))

    # Wait for health
    checks.append(("Docker Health Checks", await wait_for_services()))

    # Check basic config (full token validation happens in test setup)
    checks.append(("Basic Config", check_basic_config()))

    # Summary
    console.print(f"\n[yellow]{'=' * 60}[/yellow]")
    console.print("[yellow]Summary:[/yellow]")
    console.print(f"[yellow]{'=' * 60}[/yellow]")

    all_passed = True
    for check_name, passed in checks:
        status = "[green]✓ PASS[/green]" if passed else "[red]✗ FAIL[/red]"
        console.print(f"{check_name}: {status}")
        if not passed:
            all_passed = False

    console.print(f"[yellow]{'=' * 60}[/yellow]")

    if all_passed:
        console.print("[green]✅ All checks passed! Ready to run tests.[/green]")
        return 0
    console.print("[red]❌ Some checks failed. Please fix the issues above.[/red]")
    return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
