#!/usr/bin/env python3
"""
Wait for coverage data to be written by monitoring the coverage volume
"""
import os
import time
import sys

COVERAGE_DIR = "/coverage-data"
MAX_WAIT = 60  # Maximum wait time in seconds
CHECK_INTERVAL = 2

def check_coverage_files():
    """Check if coverage files exist"""
    if not os.path.exists(COVERAGE_DIR):
        return False
    
    coverage_files = [f for f in os.listdir(COVERAGE_DIR) if f.startswith('.coverage')]
    return len(coverage_files) > 0

def main():
    print(f"Waiting for coverage data in {COVERAGE_DIR}...")
    
    start_time = time.time()
    while time.time() - start_time < MAX_WAIT:
        if check_coverage_files():
            print("Coverage data found!")
            # List the files
            files = os.listdir(COVERAGE_DIR)
            print(f"Files in {COVERAGE_DIR}: {files}")
            return 0
        
        time.sleep(CHECK_INTERVAL)
    
    print(f"No coverage data found after {MAX_WAIT} seconds")
    print(f"Contents of {COVERAGE_DIR}:")
    try:
        files = os.listdir(COVERAGE_DIR)
        print(files if files else "Directory is empty")
    except Exception as e:
        print(f"Error listing directory: {e}")
    
    return 1

if __name__ == "__main__":
    sys.exit(main())