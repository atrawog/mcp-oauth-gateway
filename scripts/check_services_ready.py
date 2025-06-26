#!/usr/bin/env python3
"""Check that all services are built, running, and healthy before tests."""

import asyncio
import os
import subprocess
import sys
import time


# Color codes for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"


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
        "mcp-echo": "MCP_ECHO_ENABLED",
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
        print(
            f"{YELLOW}⊝ Service {service_name} is disabled via {env_var}{RESET}"
        )
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
        print(f"{RED}✗ Failed to check {service_name}: {stderr}{RESET}")
        return False

    if not stdout.strip():
        print(f"{RED}✗ Service {service_name} is not running{RESET}")
        return False

    # Parse and check service state
    import json
    try:
        service_info = json.loads(stdout.strip())
        state = service_info.get("State", "unknown")
        if state == "running":
            print(f"{GREEN}✓ Service {service_name} is running{RESET}")
            return True
        print(f"{RED}✗ Service {service_name} is in state: {state}{RESET}")
        return False
    except:
        print(f"{YELLOW}⚠ Could not parse {service_name} status{RESET}")
        return False


def check_network_exists() -> bool:
    """Check if the public network exists."""
    cmd = ["docker", "network", "ls", "--format", "{{.Name}}"]
    code, stdout, stderr = run_command(cmd)

    if code != 0:
        print(f"{RED}✗ Failed to list networks: {stderr}{RESET}")
        return False

    if "public" in stdout:
        print(f"{GREEN}✓ Network 'public' exists{RESET}")
        return True
    print(f"{RED}✗ Network 'public' does not exist{RESET}")
    return False


def check_volumes_exist() -> bool:
    """Check if required volumes exist."""
    required_volumes = ["traefik-certificates", "redis-data", "coverage-data"]
    cmd = ["docker", "volume", "ls", "--format", "{{.Name}}"]
    code, stdout, stderr = run_command(cmd)

    if code != 0:
        print(f"{RED}✗ Failed to list volumes: {stderr}{RESET}")
        return False

    existing_volumes = stdout.strip().split("\n")
    all_exist = True

    for volume in required_volumes:
        if volume in existing_volumes:
            print(f"{GREEN}✓ Volume '{volume}' exists{RESET}")
        else:
            print(f"{RED}✗ Volume '{volume}' does not exist{RESET}")
            all_exist = False

    return all_exist


def build_services() -> bool:
    """Build all services."""
    print(f"\n{YELLOW}Building all services...{RESET}")
    cmd = ["docker", "compose", "-f", "docker-compose.includes.yml", "build"]
    code, stdout, stderr = run_command(cmd)

    if code != 0:
        print(f"{RED}✗ Failed to build services: {stderr}{RESET}")
        return False

    print(f"{GREEN}✓ All services built successfully{RESET}")
    return True


def start_services() -> bool:
    """Start all services."""
    print(f"\n{YELLOW}Starting all services...{RESET}")
    cmd = ["docker", "compose", "-f", "docker-compose.includes.yml", "up", "-d"]
    code, stdout, stderr = run_command(cmd)

    if code != 0:
        print(f"{RED}✗ Failed to start services: {stderr}{RESET}")
        return False

    print(f"{GREEN}✓ All services started{RESET}")
    return True


async def wait_for_services(max_wait: int = 60) -> bool:
    """Wait for all services to be healthy using Docker health checks."""
    print(f"\n{YELLOW}Waiting for Docker health checks (max {max_wait}s)...{RESET}")

    services_to_check = ["traefik", "auth", "redis"]

    # Add mcp-fetch if enabled
    if os.getenv("MCP_FETCH_ENABLED", "false").lower() == "true":
        services_to_check.append("mcp-fetch")

    # Add mcp-echo if enabled
    if os.getenv("MCP_ECHO_ENABLED", "false").lower() == "true":
        services_to_check.append("mcp-echo")

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
                print(f"{RED}✗ Failed to inspect {service}: {stderr}{RESET}")
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
            print(f"{GREEN}✓ All services are healthy according to Docker{RESET}")
            return True

        # Show progress
        elapsed = int(time.time() - start_time)
        print(
            f"\r{YELLOW}Waiting... {elapsed}s (unhealthy: {', '.join(unhealthy_services)}){RESET}",
            end="",
            flush=True,
        )
        await asyncio.sleep(2)

    print(f"\n{RED}✗ Timeout waiting for services to be healthy{RESET}")
    return False


def check_basic_config() -> bool:
    """Check that basic configuration is present (tokens validated in test setup)."""
    print(f"\n{YELLOW}Checking basic configuration...{RESET}")

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
            print(f"{GREEN}✓ {var_name} is configured ({description}){RESET}")
        else:
            print(f"{RED}✗ {var_name} is missing or too short ({description}){RESET}")
            all_present = False

    print(f"{YELLOW}Note: Full token validation happens during test setup via refresh_and_validate_tokens(){RESET}")
    return all_present


async def main():
    """Main check function."""
    print(f"{YELLOW}{'=' * 60}{RESET}")
    print(f"{YELLOW}Pre-test Service Check{RESET}")
    print(f"{YELLOW}{'=' * 60}{RESET}")

    # First, generate the docker-compose includes file
    print(f"\n{YELLOW}Generating docker-compose includes...{RESET}")
    gen_cmd = ["python", "scripts/generate_compose_includes.py"]
    code, stdout, stderr = run_command(gen_cmd)
    if code != 0:
        print(f"{RED}✗ Failed to generate docker-compose includes: {stderr}{RESET}")
        return 1

    checks = []

    # Check network and volumes
    print(f"\n{YELLOW}Checking Docker resources...{RESET}")
    checks.append(("Network", check_network_exists()))
    checks.append(("Volumes", check_volumes_exist()))

    # Build services if needed
    base_services = ["traefik", "auth", "redis"]
    if os.getenv("MCP_FETCH_ENABLED", "false").lower() == "true":
        base_services.append("mcp-fetch")
    if os.getenv("MCP_ECHO_ENABLED", "false").lower() == "true":
        base_services.append("mcp-echo")
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
    print(f"\n{YELLOW}Checking service status...{RESET}")
    for service in base_services:
        checks.append((f"Service {service}", check_docker_service(service)))

    # Wait for health
    checks.append(("Docker Health Checks", await wait_for_services()))

    # Check basic config (full token validation happens in test setup)
    checks.append(("Basic Config", check_basic_config()))

    # Summary
    print(f"\n{YELLOW}{'=' * 60}{RESET}")
    print(f"{YELLOW}Summary:{RESET}")
    print(f"{YELLOW}{'=' * 60}{RESET}")

    all_passed = True
    for check_name, passed in checks:
        status = f"{GREEN}✓ PASS{RESET}" if passed else f"{RED}✗ FAIL{RESET}"
        print(f"{check_name}: {status}")
        if not passed:
            all_passed = False

    print(f"{YELLOW}{'=' * 60}{RESET}")

    if all_passed:
        print(f"{GREEN}✅ All checks passed! Ready to run tests.{RESET}")
        return 0
    print(f"{RED}❌ Some checks failed. Please fix the issues above.{RESET}")
    return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
