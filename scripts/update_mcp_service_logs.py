#!/usr/bin/env python3
"""Update all MCP service docker-compose.yml files to add logging volumes."""

import re
from pathlib import Path


def update_docker_compose(file_path):
    """Add logging volume to a docker-compose.yml file."""
    service_name = file_path.parent.name
    print(f"Updating {service_name}...")

    with open(file_path) as f:
        content = f.read()

    # Check if volumes already configured
    if "../logs/" in content:
        print("  - Already has logging volume configured")
        return False

    # Find the environment section and add volumes after it
    # Look for the pattern where environment section ends and before labels/depends_on/healthcheck
    pattern = r"(environment:.*?)\n(\s+)(labels:|depends_on:|healthcheck:)"

    def add_volumes(match):
        env_section = match.group(1)
        indent = match.group(2)
        next_section = match.group(3)

        # Get the indentation of environment variables (should be 2 spaces more than 'environment:')
        env_var_indent = "      "  # 6 spaces for service properties

        volumes_section = (
            f"{env_section}\n{indent}volumes:\n{env_var_indent}- ../logs/{service_name}:/logs\n{indent}{next_section}"
        )
        return volumes_section

    # If no environment section, add volumes before labels
    if not re.search(pattern, content, re.DOTALL):
        # Try to add before labels if no environment section
        pattern = r"(\n)(\s+)(labels:)"

        def add_volumes_no_env(match):
            newline = match.group(1)
            indent = match.group(2)
            labels = match.group(3)
            return f"{newline}{indent}volumes:\n{indent}  - ../logs/{service_name}:/logs\n{indent}{labels}"

        updated_content = re.sub(pattern, add_volumes_no_env, content)
    else:
        updated_content = re.sub(pattern, add_volumes, content, flags=re.DOTALL)

    # Add LOG_FILE environment variable if there's an environment section
    if "environment:" in updated_content:
        # Find the last environment variable and add LOG_FILE after it
        env_pattern = r"(environment:.*?)(\n\s+)([a-zA-Z])"

        def add_log_file_env(match):
            env_section = match.group(1)
            # Find all environment variables
            env_lines = env_section.split("\n")
            # Insert LOG_FILE after the environment: line
            for i, line in enumerate(env_lines):
                if "environment:" in line:
                    # Insert after this line
                    env_lines.insert(i + 1, "      - LOG_FILE=/logs/server.log")
                    break
            return "\n".join(env_lines) + match.group(2) + match.group(3)

        updated_content = re.sub(env_pattern, add_log_file_env, updated_content, flags=re.DOTALL)

    if updated_content != content:
        with open(file_path, "w") as f:
            f.write(updated_content)
        print("  - Added logging volume mount")
        return True
    print("  - No changes needed")
    return False


def main():
    """Update all MCP service docker-compose files."""
    project_root = Path("/home/atrawog/mcp-oauth-gateway")

    # Find all mcp-*/docker-compose.yml files
    mcp_services = list(project_root.glob("mcp-*/docker-compose.yml"))
    # Exclude the oauth client and streamablehttp client
    print(f"Found {len(mcp_services)} total MCP services")
    mcp_services = [
        s for s in mcp_services if "mcp-oauth-dynamicclient" not in str(s) and "mcp-streamablehttp-client" not in str(s)
    ]

    print(f"Found {len(mcp_services)} MCP service docker-compose files to update\n")

    updated_count = 0
    for service_file in sorted(mcp_services):
        if update_docker_compose(service_file):
            updated_count += 1
        print()

    print(f"Updated {updated_count} services with logging configuration")


if __name__ == "__main__":
    main()
