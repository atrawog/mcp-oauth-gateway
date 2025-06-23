#!/usr/bin/env python3
"""Debug script to verify coverage configuration in the auth container."""
import os
import sys


print("=== Coverage Debug Information ===")
print(f"Python executable: {sys.executable}")
print(f"Python version: {sys.version}")
print(f"PYTHONPATH: {os.environ.get('PYTHONPATH', 'Not set')}")
print(f"COVERAGE_PROCESS_START: {os.environ.get('COVERAGE_PROCESS_START', 'Not set')}")
print(f"COVERAGE_FILE: {os.environ.get('COVERAGE_FILE', 'Not set')}")

# Check if sitecustomize can be imported
try:
    import sitecustomize
    print("✓ sitecustomize module found and imported")
except ImportError as e:
    print(f"✗ Failed to import sitecustomize: {e}")

# Check if coverage is available
try:
    import coverage
    print(f"✓ Coverage version: {coverage.__version__}")
except ImportError:
    print("✗ Coverage module not found")

# Check if coverage config exists
config_path = os.environ.get('COVERAGE_PROCESS_START', '')
if config_path and os.path.exists(config_path):
    print(f"✓ Coverage config found at: {config_path}")
    with open(config_path) as f:
        print("Config contents:")
        print(f.read())
else:
    print(f"✗ Coverage config not found at: {config_path}")

# Check coverage data directory
coverage_dir = "/coverage-data"
if os.path.exists(coverage_dir):
    print(f"✓ Coverage data directory exists: {coverage_dir}")
    print(f"  Contents: {os.listdir(coverage_dir)}")
else:
    print(f"✗ Coverage data directory not found: {coverage_dir}")
