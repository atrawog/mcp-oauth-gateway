# Package Documentation Standard

This document outlines the standardized documentation workflow for all packages in the MCP OAuth Gateway project.

## README Structure

All package README files should follow this consistent structure:

### 1. Title and Brief Description
- Package name as main heading
- One-line description of what the package does
- Clear value proposition

### 2. Overview Section
- Detailed explanation of the package's purpose
- Key features list
- Architecture context (where it fits in the system)

### 3. Installation Section

Every package README must include these installation methods:

#### Using pip
```bash
pip install package-name
```

#### Using pixi
```bash
pixi add --pypi package-name
```

#### Docker Deployment
```dockerfile
FROM python:3.11-slim

# Install the package
RUN pip install package-name

# Set environment variables
ENV VAR_NAME=value

# Expose the port (if applicable)
EXPOSE 3000

# Run the service
CMD ["python", "-m", "package_module_name"]
```

### 4. Quick Start Section
- Running locally with pip/pixi installation
- Running with Python module directly
- Docker Compose example (if applicable)
- Basic usage examples

### 5. Configuration Section
- Environment variables table
- Required vs optional settings
- Default values
- Example .env file

### 6. API/Usage Section
- Detailed API documentation (for servers)
- CLI commands (for tools)
- Code examples
- Common use cases

### 7. Architecture Section (if complex)
- System diagrams
- Component interactions
- Protocol details

### 8. Development Section
- Running tests
- Building locally
- Contributing guidelines

### 9. Troubleshooting Section
- Common issues and solutions
- Debug mode instructions
- FAQ

### 10. License Section

## Docker Compose Examples

For services that run in Docker, include a complete docker-compose.yml example:

```yaml
services:
  service-name:
    image: service-name:latest
    build:
      context: ./service-directory
    environment:
      - ENV_VAR=${ENV_VAR}
    ports:
      - "3000:3000"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 30s
      timeout: 5s
      retries: 3
```

## Installation Method Consistency

### Python Packages
- Always provide both `pip install` and `pixi add --pypi` commands
- Use `--pypi` flag for pixi to ensure PyPI packages are installed correctly
- Include the exact package name as published on PyPI

### Docker Images
- Use Python 3.11-slim as the base image for consistency
- Set environment variables for configuration
- Always bind to 0.0.0.0 for container networking
- Include EXPOSE directive for documentation

### Command Names
- Provide the installed command name (e.g., `mcp-echo-server`)
- Show the Python module alternative (e.g., `python -m mcp_echo_server`)
- Include examples with environment variable overrides

## Environment Variable Documentation

Use tables for clarity:

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `VAR_NAME` | What it does | Default value | Yes/No |

## Code Examples

- Use language-specific code blocks with syntax highlighting
- Include both simple and complex examples
- Show error handling where appropriate
- Add comments to explain non-obvious parts

## Health Check Examples

For services, always include the MCP protocol health check:

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:3000/mcp", "-X", "POST",
         "-H", "Content-Type: application/json",
         "-d", '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"healthcheck","version":"1.0"}},"id":1}']
  interval: 30s
  timeout: 5s
  retries: 3
```

## Cross-References

- Link to related services in the "Related Services" section
- Reference the main project documentation
- Include links to protocol specifications where relevant
