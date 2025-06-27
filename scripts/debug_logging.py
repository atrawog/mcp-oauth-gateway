#!/usr/bin/env python3
"""Debug logging configuration issues."""

import logging
import os
import sys


# Set LOG_FILE environment variable
os.environ["LOG_FILE"] = "/tmp/test_log.log"

# Import the server module to trigger logging config
sys.path.insert(0, "/app")

# Get logger and test it
logger = logging.getLogger("mcp_oauth_dynamicclient")
logger.info("Test log message from debug script")

# Check if file was created
if os.path.exists("/tmp/test_log.log"):
    print("✅ Log file created successfully")
    with open("/tmp/test_log.log") as f:
        print("Log contents:", f.read())
else:
    print("❌ Log file not created")

# Check logging handlers
print("\nActive logging handlers:")
for handler in logging.root.handlers:
    print(f"  - {type(handler).__name__}: {handler}")
