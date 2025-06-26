#!/usr/bin/env python
"""Debug script to check what URLs the tests are using."""

import os
import sys
from pathlib import Path


# Add parent directory to path to import test helpers
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.test_constants import BASE_DOMAIN
from tests.test_constants import MCP_FETCH_URL
from tests.test_constants import MCP_FETCH_URLS
from tests.test_constants import MCP_TESTING_URL


print(f"BASE_DOMAIN: {BASE_DOMAIN}")
print(f"MCP_TESTING_URL: {MCP_TESTING_URL}")
print(f"MCP_FETCH_URL: {MCP_FETCH_URL}")
print(f"MCP_FETCH_URLS: {MCP_FETCH_URLS}")

# Check what mcp_test_url fixture would return
testing_url = os.getenv("MCP_TESTING_URL")
url = testing_url.rstrip("/") if testing_url else MCP_FETCH_URL

print(f"\nmcp_test_url fixture would return: {url}")
print(f"But the actual MCP endpoint is at: {url}/mcp")
