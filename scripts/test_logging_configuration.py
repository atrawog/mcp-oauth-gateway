#!/usr/bin/env python3
"""Test that all services are properly logging to the ./logs directory."""

import subprocess
import time
from pathlib import Path


def check_service_logs():
    """Check if each service is creating log files."""
    project_root = Path("/home/atrawog/mcp-oauth-gateway")
    logs_dir = project_root / "logs"

    # Expected services and their log files
    expected_services = {
        "traefik": ["traefik.log", "access.log"],
        "auth": ["auth.log"],
        "mcp-fetch": ["server.log"],
        "mcp-fetchs": ["server.log"],
        "mcp-filesystem": ["server.log"],
        "mcp-memory": ["server.log"],
        "mcp-everything": ["server.log"],
        "mcp-time": ["server.log"],
        "mcp-tmux": ["server.log"],
        "mcp-playwright": ["server.log"],
        "mcp-sequentialthinking": ["server.log"],
        "mcp-echo-stateful": ["server.log"],
        "mcp-echo-stateless": ["server.log"],
    }

    print("🔍 Checking logging configuration for all services...\n")

    all_good = True

    # Check if logs directory exists
    if not logs_dir.exists():
        print("❌ Logs directory doesn't exist at ./logs")
        return False

    # Check each service
    for service, log_files in expected_services.items():
        service_dir = logs_dir / service

        print(f"📁 Checking {service}...")

        # Check if service log directory exists
        if not service_dir.exists():
            print(f"  ❌ Log directory missing: {service_dir}")
            all_good = False
            continue

        # Check for expected log files
        for log_file in log_files:
            log_path = service_dir / log_file
            if log_path.exists():
                size = log_path.stat().st_size
                if size > 0:
                    print(f"  ✅ {log_file} exists ({size} bytes)")
                else:
                    print(f"  ⚠️  {log_file} exists but is empty")
            else:
                print(f"  ❌ {log_file} missing")
                all_good = False

        print()

    return all_good


def test_traefik_access_logs():
    """Test if Traefik is logging HTTP requests."""
    print("🌐 Testing Traefik access logging...\n")

    # Make a test request to trigger access log
    try:
        # Try to access the auth service discovery endpoint (no auth required)
        result = subprocess.run(
            [
                "curl",
                "-s",
                "-o",
                "/dev/null",
                "-w",
                "%{http_code}",
                "http://localhost/.well-known/oauth-authorization-server",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            print("  ✅ Made test request to Traefik")
        else:
            print("  ⚠️  Test request failed")
    except Exception as e:
        print(f"  ❌ Error making test request: {e}")

    # Wait a moment for logs to be written
    time.sleep(2)

    # Check if access log has new entries
    access_log = Path("/home/atrawog/mcp-oauth-gateway/logs/traefik/access.log")
    if access_log.exists():
        # Get last few lines
        try:
            with open(access_log) as f:
                lines = f.readlines()
                if lines:
                    print(f"  ✅ Access log has {len(lines)} entries")
                    print("  📝 Latest entry preview:")
                    latest = lines[-1].strip()
                    if len(latest) > 100:
                        print(f"     {latest[:100]}...")
                    else:
                        print(f"     {latest}")
                else:
                    print("  ⚠️  Access log exists but is empty")
        except Exception as e:
            print(f"  ❌ Error reading access log: {e}")
    else:
        print("  ❌ Access log not found")

    print()


def check_log_permissions():
    """Check if log files have proper permissions."""
    print("🔐 Checking log file permissions...\n")

    logs_dir = Path("/home/atrawog/mcp-oauth-gateway/logs")

    for service_dir in logs_dir.iterdir():
        if service_dir.is_dir():
            for log_file in service_dir.glob("*.log"):
                stat = log_file.stat()
                mode = oct(stat.st_mode)[-3:]
                print(f"  {log_file.relative_to(logs_dir)}: {mode}")

    print()


def main():
    """Run all logging tests."""
    print("🧪 MCP OAuth Gateway Logging Configuration Test\n")
    print("=" * 50)
    print()

    # Check if services are running
    print("🐳 Checking if services are running...")
    result = subprocess.run(
        ["docker", "ps", "--format", "table {{.Names}}\t{{.Status}}"], check=False, capture_output=True, text=True
    )

    if result.returncode == 0:
        print(result.stdout)
    else:
        print("❌ Failed to check Docker services")
        return

    print("\n" + "=" * 50 + "\n")

    # Run tests
    logs_ok = check_service_logs()
    test_traefik_access_logs()
    check_log_permissions()

    # Summary
    print("=" * 50)
    if logs_ok:
        print("✅ All services have logging configured correctly!")
        print("\n📊 Next steps:")
        print("  - Monitor logs: just logs-files")
        print("  - View stats: just logs-stats")
        print("  - Setup rotation: just logs-rotation-setup")
    else:
        print("❌ Some services are missing log configuration")
        print("\n🔧 Troubleshooting:")
        print("  - Restart services: just restart")
        print("  - Check service logs: just logs <service-name>")
        print("  - Verify volumes: docker compose config | grep logs")


if __name__ == "__main__":
    main()
