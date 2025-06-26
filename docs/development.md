# Development

This section covers development practices, guidelines, and procedures for contributing to the MCP OAuth Gateway.

## Development Topics

```{toctree}
:maxdepth: 2

development/guidelines
development/testing-approach
development/project-structure
development/adding-services
```

## Getting Started

### Development Setup

1. Clone the repository
2. Set up your development environment with `just setup`
3. Install dependencies: `pixi install`
4. Start development services: `just dev`

### Development Workflow

```bash
# Start development environment
just dev

# Run tests during development
just test-watch

# Lint and format code
just lint

# Build documentation locally
just docs-build
```

## Key Principles

### No Mocking Policy

All tests must use real services:
- Real Docker containers
- Actual API calls
- True integration testing
- No mocks, stubs, or fakes

### Tool Trinity

Always use the blessed tools:
- **just** - All commands through justfile
- **pixi** - Python package management
- **docker-compose** - Service orchestration

### Project Structure

Follow the sacred structure:
- Services in separate directories
- Tests in `./tests/`
- Scripts in `./scripts/`
- Documentation in `./docs/`

## Contributing

1. Follow the [Development Guidelines](development/guidelines.md)
2. Write tests for all changes
3. Update documentation as needed
4. Submit pull requests with clear descriptions

## Testing

See [Testing Approach](development/testing-approach.md) for detailed testing guidelines.
