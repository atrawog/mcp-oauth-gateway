#!/usr/bin/env python3
"""Analyze test performance from pytest output to identify slow tests."""

import re
import sys
from collections import defaultdict


def analyze_test_log(filename):
    """Analyze test log for performance issues."""
    # Track which tests appear to be integration/e2e tests
    integration_tests = []
    unit_tests = []

    # Track test patterns
    streaming_tests = []
    client_tests = []
    oauth_tests = []

    with open(filename) as f:
        content = f.read()

    # Find all test names
    test_pattern = r"tests/test_([^/]+)\.py::([^\s]+)"
    matches = re.findall(test_pattern, content)

    for module, test in matches:
        full_test = f"{module}::{test}"

        # Categorize tests
        if "integration" in module or "full" in module or "e2e" in module:
            integration_tests.append(full_test)
        else:
            unit_tests.append(full_test)

        if "streaming" in test.lower() or "sse" in module:
            streaming_tests.append(full_test)

        if "client" in module or "oauth" in module:
            client_tests.append(full_test)

        if "oauth" in module:
            oauth_tests.append(full_test)

    # Analyze test distribution
    print("=== Test Performance Analysis ===\n")

    print(f"Total tests found: {len(matches)}")
    print(f"Integration tests: {len(integration_tests)}")
    print(f"Unit tests: {len(unit_tests)}")
    print(f"Streaming tests: {len(streaming_tests)}")
    print(f"Client tests: {len(client_tests)}")
    print(f"OAuth tests: {len(oauth_tests)}")

    # Find tests that are likely slow based on their names
    likely_slow = []
    slow_patterns = [
        "streaming",
        "sse",
        "full",
        "integration",
        "e2e",
        "memory",
        "store",
        "retrieve",
        "playwright",
        "tmux",
        "everything",
        "complete",
        "workflow",
    ]

    for module, test in matches:
        full_test = f"{module}::{test}"
        if any(pattern in full_test.lower() for pattern in slow_patterns):
            likely_slow.append(full_test)

    print(f"\n=== Likely Slow Tests ({len(likely_slow)}) ===")
    print("These tests likely involve I/O, network calls, or complex operations:\n")

    # Group by module
    by_module = defaultdict(list)
    for test in likely_slow:
        module = test.split("::")[0]
        by_module[module].append(test)

    for module, tests in sorted(by_module.items()):
        print(f"\n{module}:")
        for test in tests[:5]:  # Show first 5 from each module
            print(f"  - {test}")
        if len(tests) > 5:
            print(f"  ... and {len(tests) - 5} more")

    # Recommendations
    print("\n=== Performance Recommendations ===\n")

    print("1. **Parallel Execution Issues:**")
    print("   - Some tests may have race conditions when accessing shared resources")
    print("   - Redis-based tests might conflict if they use the same keys")
    print("   - OAuth flow tests might conflict on client registrations\n")

    print("2. **Slow Test Categories:**")
    print("   - Streaming/SSE tests: Involve real-time data transfer")
    print("   - Integration tests: Full end-to-end flows with multiple services")
    print("   - Client tests: Spawn subprocesses and perform full OAuth flows")
    print("   - Memory/storage tests: Database operations\n")

    print("3. **Optimization Strategies:**")
    print("   - Mark slow tests with @pytest.mark.slow")
    print("   - Run slow tests separately from fast unit tests")
    print("   - Use test fixtures to share expensive setup")
    print("   - Mock external services where possible")
    print("   - Use pytest-xdist's --dist loadscope for test grouping")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        analyze_test_log(sys.argv[1])
    else:
        analyze_test_log("test-parallel-output.log")
