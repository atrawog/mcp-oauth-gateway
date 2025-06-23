"""Sacred Coverage Spy - Subprocess coverage tracking for production containers
This file is injected via PYTHONPATH to enable coverage in all Python processes.
"""
import coverage


# Start coverage tracking for all subprocesses
# This is critical for uvicorn workers and async processes
coverage.process_startup()

# The COVERAGE_PROCESS_START environment variable must point to .coveragerc
# This enables automatic coverage collection in production containers
