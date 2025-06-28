#!/usr/bin/env python3
"""Generate Traefik middlewares.yml from template with environment variables."""

import os
import sys
from pathlib import Path


def generate_cors_origins_yaml(origins_str: str) -> tuple[str, str]:
    """Generate YAML list for CORS origins and determine credentials setting.

    Returns:
        tuple: (yaml_list, allow_credentials)

    """
    if not origins_str:
        # No CORS origins specified
        return '          - "http://localhost"', "false"

    # Handle wildcard case
    if origins_str.strip() == "*":
        return '          - "*"', "false"

    # Split comma-separated origins
    origins = [origin.strip() for origin in origins_str.split(",") if origin.strip()]

    if not origins:
        return '          - "http://localhost"', "false"

    # Format as YAML list
    yaml_lines = []
    for origin in origins:
        yaml_lines.append(f'          - "{origin}"')

    return "\n".join(yaml_lines), "true"


def main():
    """Generate middlewares.yml from template."""
    # Get environment variables
    cors_origins = os.getenv("MCP_CORS_ORIGINS", "")
    base_domain = os.getenv("BASE_DOMAIN", "localhost")

    # Determine script location
    script_dir = Path(__file__).parent.parent
    template_path = script_dir / "traefik" / "dynamic" / "middlewares.yml.template"
    output_path = script_dir / "traefik" / "dynamic" / "middlewares.yml"

    # Check template exists
    if not template_path.exists():
        print(f"Error: Template not found at {template_path}", file=sys.stderr)
        sys.exit(1)

    # Read template
    template_content = template_path.read_text()

    # Generate CORS origins YAML
    cors_yaml, allow_credentials = generate_cors_origins_yaml(cors_origins)

    # Replace placeholders
    content = template_content.replace("${CORS_ORIGINS_YAML}", cors_yaml)
    content = content.replace("${CORS_ALLOW_CREDENTIALS}", allow_credentials)
    content = content.replace("${BASE_DOMAIN}", base_domain)

    # Write output
    output_path.write_text(content)
    print(f"Generated {output_path}")

    # Log configuration
    print(f"CORS Origins: {cors_origins or 'none'}")
    print(f"Allow Credentials: {allow_credentials}")
    print(f"Base Domain: {base_domain}")


if __name__ == "__main__":
    main()
