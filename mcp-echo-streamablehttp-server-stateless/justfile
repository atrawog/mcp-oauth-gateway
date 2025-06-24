set dotenv-load := true
set positional-arguments := true

# Default recipe - show available commands
default:
    @just --list

# Install the package in development mode
install:
    pixi run pip install -e .

# Run the server
run *args:
    pixi run mcp-echo-streamablehttp-server-stateless {{args}}

# Run the server with debug logging
debug:
    pixi run mcp-echo-streamablehttp-server-stateless --debug

# Run the test script
test:
    pixi run python test_server.py

# Run the example client
example:
    pixi run python example_client.py

# Build Docker image
build:
    cd .. && docker-compose -f mcp-echo/docker-compose.yml build

# Run with docker-compose
up:
    cd .. && docker-compose -f mcp-echo/docker-compose.yml up -d

# Stop docker-compose
down:
    cd .. && docker-compose -f mcp-echo/docker-compose.yml down

# View logs
logs:
    cd .. && docker-compose -f mcp-echo/docker-compose.yml logs -f

# Clean up build artifacts
clean:
    rm -rf build/ dist/ *.egg-info/
    find . -type d -name __pycache__ -exec rm -rf {} + || true
    find . -type f -name "*.pyc" -delete

# Format code
format:
    pixi run black src/ test_server.py example_client.py
    pixi run isort src/ test_server.py example_client.py

# Lint code
lint:
    pixi run flake8 src/ test_server.py example_client.py
    pixi run mypy src/ test_server.py example_client.py

# Run server and test in sequence
test-integration:
    #!/usr/bin/env bash
    set -e
    echo "Starting server in background..."
    pixi run mcp-echo-streamablehttp-server-stateless &
    SERVER_PID=$!
    sleep 2
    echo "Running tests..."
    pixi run python test_server.py
    TEST_RESULT=$?
    echo "Stopping server..."
    kill $SERVER_PID
    exit $TEST_RESULT