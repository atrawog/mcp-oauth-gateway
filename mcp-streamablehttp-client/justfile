set dotenv-load := true

# Default recipe - show help
default:
    @just --list

# Install package in development mode
install:
    pip install -e ".[dev]"

# Run tests
test:
    pytest tests/ -v

# Run tests with coverage
test-coverage:
    pytest tests/ -v --cov=mcp_http_stdio --cov-report=html --cov-report=term

# Run linting
lint:
    ruff check src/ tests/
    mypy src/

# Format code
format:
    ruff format src/ tests/

# Build Docker image
docker-build:
    docker-compose build

# Run in Docker (interactive for OAuth setup)
docker-run:
    docker-compose run --rm mcp-http-stdio

# Test authentication
test-auth:
    mcp-http-stdio --test-auth

# Check and refresh tokens
check-tokens:
    mcp-http-stdio --token

# Reset authentication
reset-auth:
    mcp-http-stdio --reset-auth

# Test fetch command
test-fetch:
    mcp-http-stdio --command "fetch https://httpbin.org/json"

# Test with custom URL
test-fetch-url URL:
    mcp-http-stdio -c "fetch {{URL}}"

# List available tools
list-tools:
    mcp-http-stdio --command "tools/list"

# Run command examples
run-examples:
    ./examples/command_examples.sh

# Run with debug logging
debug:
    mcp-http-stdio --log-level DEBUG

# Clean up build artifacts
clean:
    rm -rf build/ dist/ *.egg-info
    find . -type d -name __pycache__ -exec rm -rf {} +
    find . -type f -name "*.pyc" -delete

# Build package
build: clean
    python -m build

# Upload to PyPI (test)
upload-test: build
    python -m twine upload --repository testpypi dist/*

# Upload to PyPI (production)
upload: build
    python -m twine upload dist/*