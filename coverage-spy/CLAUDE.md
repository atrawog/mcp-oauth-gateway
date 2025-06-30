# 🔥 CLAUDE.md - The Coverage-Spy Divine Scripture! ⚡

**🕵️ Behold! The Sacred Coverage Interceptor - Divine Metrics Without Contamination! 🕵️**

**⚡ This is Coverage-Spy - The Holy Sidecar Pattern for Production Coverage Glory! ⚡**

## 🔱 The Sacred Purpose - Divine Coverage Without Code Pollution!

**Coverage-Spy is the blessed pattern for measuring REAL production code coverage!**

This sacred technique channels these divine powers:
- **Zero Code Modification** - Production containers remain pure and untouched!
- **Docker Compose Overlay** - Coverage added via compose overlay file!
- **coverage.py Subprocess Support** - Uses coverage.process_startup() divine magic!
- **PYTHONPATH Injection** - sitecustomize.py loaded automatically by Python!
- **Coverage Harvester Container** - Separate container collects and reports metrics!
- **Clean Separation** - Coverage code never touches production images!

**⚡ The ONLY way to measure production coverage righteously! ⚡**

## 🏗️ The Sacred Architecture - Sidecar Pattern Divinity!

```
Coverage Architecture
├── Production Container (Pure and Untouched!)
│   ├── Normal Dockerfile
│   ├── Original source code
│   └── No coverage artifacts
├── Coverage Sidecar Container (Measurement Vessel!)
│   ├── Dockerfile.coverage
│   ├── Coverage-spy injection
│   └── Same functionality + metrics
└── Coverage Data Collection (Divine Metrics!)
    ├── .coverage files
    ├── HTML reports
    └── JSON summaries
```

**⚡ Production purity maintained while measuring everything! ⚡**

## 📖 The Sacred Implementation - sitecustomize.py Magic!

### The Divine sitecustomize.py - Minimal and Powerful!
```python
"""Sacred Coverage Spy - Subprocess coverage tracking for production containers.

This file is injected via PYTHONPATH to enable coverage in all Python processes.
"""

import coverage


# Start coverage tracking for all subprocesses
# This is critical for uvicorn workers and async processes
coverage.process_startup()

# The COVERAGE_PROCESS_START environment variable must point to .coveragerc
# This enables automatic coverage collection in production containers
```

**⚡ The divine simplicity! coverage.process_startup() handles EVERYTHING! ⚡**

**The Sacred Environment Variables Required:**
- `PYTHONPATH=/coverage-spy:/app:${PYTHONPATH:-}` - Injects sitecustomize.py!
- `COVERAGE_PROCESS_START=/coverage-config/.coveragerc` - Points to config!
- `COVERAGE_FILE=/coverage-data/.coverage` - Where data is written!

**⚡ coverage.py's subprocess feature does all the heavy lifting! ⚡**

## 🐳 The Docker Implementation - Overlay Pattern Divine Glory!

### The Sacred Truth: NO SEPARATE DOCKERFILES NEEDED!
**⚡ Use docker-compose.coverage.yml overlay - Production images untouched! ⚡**

### docker-compose.coverage.yml - The Divine Overlay
```yaml
# Sacred Coverage Overlay - Production coverage without contamination!
# This overlay adds coverage tracking to production containers

services:
  auth:
    # Run as root for coverage data writing
    user: root
    environment:
      # All production env vars PLUS coverage magic:
      - PYTHONPATH=/coverage-spy:/app:${PYTHONPATH:-}
      - COVERAGE_PROCESS_START=/coverage-config/.coveragerc
      - COVERAGE_FILE=/coverage-data/.coverage
    volumes:
      - ./coverage-spy:/coverage-spy:ro
      - ./coverage-spy/.coveragerc:/coverage-config/.coveragerc:ro
      - coverage-data:/coverage-data:rw
    # Ensure graceful shutdown for coverage collection
    stop_grace_period: 10s

  # Coverage harvester - collects and combines coverage data
  coverage-harvester:
    image: python:3.11-slim
    container_name: coverage-harvester
    volumes:
      - ./mcp-oauth-dynamicclient/src/mcp_oauth_dynamicclient:/app:ro
      - coverage-data:/coverage-data:rw
      - ./htmlcov:/htmlcov:rw
      - ./coverage-spy/.coveragerc:/.coveragerc:ro
      - ./scripts:/scripts:ro
      - .:/workspace:ro
    working_dir: /workspace
    environment:
      - COVERAGE_FILE=/coverage-data/.coverage
    entrypoint: ["/bin/bash", "-c"]
    command:
      - |
        pip install coverage
        python /scripts/wait_for_coverage.py
        # Process coverage data and generate reports
        coverage combine || true
        coverage report --omit="*/auth.py" --skip-covered --skip-empty
        coverage html --omit="*/auth.py" || true
    depends_on:
      - auth

volumes:
  coverage-data:
    external: true
```

**⚡ The overlay pattern adds coverage WITHOUT modifying production! ⚡**

## 🔧 The Sacred Configuration - The Divine .coveragerc!

### The Sacred Environment Variables (Set in docker-compose.coverage.yml)
```bash
# CRITICAL: Points coverage.py to configuration file
COVERAGE_PROCESS_START=/coverage-config/.coveragerc

# Where coverage data is written
COVERAGE_FILE=/coverage-data/.coverage

# Inject coverage-spy into Python path
PYTHONPATH=/coverage-spy:/app:${PYTHONPATH:-}
```

### The Divine .coveragerc Configuration
```ini
[run]
concurrency = thread,multiprocessing  # Handle async and subprocess coverage!
parallel = true                       # Support parallel test runs!
sigterm = true                        # Save on SIGTERM for graceful shutdown!
data_file = /coverage-data/.coverage  # Shared volume location!
source = /app                         # Source code location in container!

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    if self.debug:
    if settings.DEBUG
    raise AssertionError
    raise NotImplementedError
    if 0:
    if __name__ == .__main__.:
    class .*\bProtocol\):
    @(abc\.)?abstractmethod

[paths]
source =
    /app          # Container path
    ./auth        # Local path for reporting

[html]
directory = /app/htmlcov
```

**⚡ The [paths] section maps container paths to local paths for reporting! ⚡**

## 🚀 Using the Coverage-Spy Pattern - The Divine Command!

### The One Sacred Command: `just test-sidecar-coverage`

**⚡ This blessed command orchestrates the entire coverage ritual! ⚡**

```bash
# The complete coverage ceremony in ONE command!
just test-sidecar-coverage
```

**What this divine incantation does:**
1. **Stops existing services** - `docker compose down --remove-orphans`
2. **Starts with coverage overlay** - Uses both compose files together!
3. **Waits for readiness** - Runs `check_services_ready.py` script!
4. **Runs test suite** - `pixi run pytest tests/ -v`
5. **Triggers graceful shutdown** - Stops auth service to save coverage!
6. **Waits for harvester** - Coverage-harvester processes the data!
7. **Shows report** - Extracts coverage report from harvester logs!

### Manual Steps (if needed)
```bash
# Create the coverage volume first
docker volume create coverage-data

# View coverage report after tests
docker logs coverage-harvester

# Access HTML report
open htmlcov/index.html
```

**⚡ One command to rule them all! ⚡**

## 🔐 The Security Considerations - Divine Safety!

### Production Isolation
- Coverage code NEVER in production images!
- Separate Dockerfiles for clear separation!
- Different container names prevent accidents!
- Coverage data stored outside containers!

### Performance Impact
- Minimal overhead (~10-15% typically)!
- Only active when COVERAGE_ENABLE=true!
- No impact on production containers!
- Measurement can be toggled dynamically!

### Data Protection
- Coverage data written to mounted volumes!
- No sensitive data in coverage reports!
- Separate storage from application data!
- Clean up coverage files after analysis!

**⚡ Security through separation and isolation! ⚡**

## 🧪 Testing with Coverage-Spy!

### The Divine Testing Flow
1. **Start services** with coverage sidecars
2. **Run test suite** against live services
3. **Exercise endpoints** thoroughly
4. **Stop services** to trigger data save
5. **Combine data** from all services
6. **Generate reports** for divine insight

### The Sacred wait_for_coverage.py Script
```python
#!/usr/bin/env python3
"""Wait for coverage data to be written by monitoring the coverage volume."""

import os
import sys
import time


COVERAGE_DIR = "/coverage-data"
MAX_WAIT = 60  # Maximum wait time in seconds
CHECK_INTERVAL = 2


def check_coverage_files():
    """Check if coverage files exist."""
    if not os.path.exists(COVERAGE_DIR):
        return False

    coverage_files = [f for f in os.listdir(COVERAGE_DIR) if f.startswith(".coverage")]
    return len(coverage_files) > 0


def main():
    print(f"Waiting for coverage data in {COVERAGE_DIR}...")

    start_time = time.time()
    while time.time() - start_time < MAX_WAIT:
        if check_coverage_files():
            print("Coverage data found!")
            return 0

        time.sleep(CHECK_INTERVAL)

    print(f"No coverage data found after {MAX_WAIT} seconds")
    return 1
```

**⚡ This divine script ensures coverage data is written before processing! ⚡**

## 🔥 Common Issues and Divine Solutions!

### "No Coverage Data" - Collection Failed!
- Verify COVERAGE_ENABLE=true set!
- Check PYTHONPATH includes coverage-spy!
- Ensure coverage package installed!
- Verify write permissions on volume!

### "Import Error" - sitecustomize Problem!
- Check sitecustomize.py in PYTHONPATH!
- Verify no syntax errors in file!
- Ensure coverage package available!
- Check Python version compatibility!

### "Permission Denied" - Volume Issues!
- Check coverage volume permissions!
- Ensure container user can write!
- Verify mount points correct!
- Check disk space available!

### "Incomplete Coverage" - Missing Data!
- Ensure services stopped gracefully!
- Check atexit handlers executed!
- Verify all services measured!
- Review omit patterns!

## 📊 The Divine Architecture Explained!

### Why This Pattern Works - The Sacred Truths!

**1. coverage.process_startup() Magic**
- Automatically handles subprocess coverage (uvicorn workers!)!
- Reads config from COVERAGE_PROCESS_START env var!
- Saves data on process exit automatically!
- No manual start/stop needed!

**2. Docker Compose Overlay Pattern**
- Production images remain unchanged!
- Coverage added only via compose overlay!
- Same container, different environment!
- Zero production contamination!

**3. Coverage Harvester Container**
- Separate container for processing!
- Waits for data to be written!
- Combines parallel coverage files!
- Generates reports independently!

**4. Volume Sharing Strategy**
- coverage-data volume shared between containers!
- Auth service writes coverage data!
- Harvester reads and processes!
- Clean separation of concerns!

**⚡ The pattern leverages coverage.py's built-in subprocess support! ⚡**

## 🔱 The Divine Mission - Why Coverage-Spy Exists!

### The Problem with Traditional Coverage
**Traditional approaches contaminate production:**
- Installing coverage in production images!
- Modifying application code for coverage!
- Running different code in test vs production!
- Performance overhead always present!

### The Coverage-Spy Solution
**Divine separation through overlay pattern:**
- Production images remain untouched!
- Coverage added only via compose overlay!
- Same container code, different environment!
- Coverage only when explicitly enabled!
- Harvester container handles all processing!

**⚡ Measure production behavior without production contamination! ⚡**

## 🏆 Key Benefits of This Pattern!

1. **Production Purity** - No coverage code in production images!
2. **Simple Implementation** - Just coverage.process_startup()!
3. **Subprocess Coverage** - Handles uvicorn workers automatically!
4. **Parallel Safety** - Built-in support for concurrent tests!
5. **Easy Activation** - One command: `just test-sidecar-coverage`!
6. **Clean Reports** - Harvester generates all metrics separately!

**⚡ The divine balance of simplicity and power! ⚡**

## 📜 Integration with CI/CD - Automated Divine Metrics!

### GitHub Actions Integration
```yaml
- name: Create coverage volume
  run: docker volume create coverage-data

- name: Run tests with sidecar coverage
  run: just test-sidecar-coverage

- name: Extract coverage report
  run: |
    # Extract coverage percentage from harvester logs
    docker logs coverage-harvester | grep "TOTAL" | awk '{print $NF}'

- name: Upload HTML report
  uses: actions/upload-artifact@v3
  with:
    name: coverage-report
    path: htmlcov/
```

### The Sacred Truth About CI/CD Coverage
**⚡ The same pattern works everywhere! ⚡**
- Local development: `just test-sidecar-coverage`
- CI/CD pipeline: `just test-sidecar-coverage`
- Production testing: `just test-sidecar-coverage`

**One command, consistent coverage everywhere!**

## 🛠️ Debugging Coverage Issues - Divine Troubleshooting!

### Verify Coverage Setup
```bash
# Check if coverage-spy is in PYTHONPATH
docker compose -f docker-compose.yml -f docker-compose.coverage.yml exec auth \
  python -c "import sys; print('\n'.join(sys.path))"

# Verify sitecustomize.py is loaded
docker compose -f docker-compose.yml -f docker-compose.coverage.yml exec auth \
  python -c "import sitecustomize; print('sitecustomize loaded!')"

# Check COVERAGE_PROCESS_START is set
docker compose -f docker-compose.yml -f docker-compose.coverage.yml exec auth \
  printenv | grep COVERAGE

# View coverage data files
docker run --rm -v coverage-data:/data alpine ls -la /data/

# Check harvester logs for issues
docker logs coverage-harvester
```

### Common Issues and Solutions

**"No coverage data found"**
- Ensure `coverage-data` volume exists: `docker volume create coverage-data`
- Check auth service has write permissions (runs as root in overlay)
- Verify graceful shutdown: `stop_grace_period: 10s` is set
- Check .coveragerc path is correct in compose file

**"Coverage not measuring my code"**
- Verify source path in .coveragerc matches container path
- Check [paths] section maps container → local paths correctly
- Ensure code is under /app in container
- Review omit patterns aren't excluding your code

**⚡ The harvester logs contain the truth! Always check them! ⚡**

## 🌟 Summary - The Coverage-Spy Enlightenment!

**The Sacred Implementation in Brief:**
1. **sitecustomize.py** - Contains only `coverage.process_startup()`
2. **docker-compose.coverage.yml** - Overlay that adds coverage env vars
3. **coverage-harvester** - Separate container that processes data
4. **.coveragerc** - Configuration with parallel and subprocess support
5. **just test-sidecar-coverage** - One command to rule them all

**The Divine Benefits:**
- ✓ Zero production image modifications!
- ✓ Automatic subprocess coverage (uvicorn workers!)!
- ✓ Clean separation of concerns!
- ✓ Simple one-command execution!
- ✓ Works with any Python application!

**The Sacred Environment Variables:**
```bash
PYTHONPATH=/coverage-spy:/app:${PYTHONPATH:-}
COVERAGE_PROCESS_START=/coverage-config/.coveragerc
COVERAGE_FILE=/coverage-data/.coverage
```

---

**🔥 May your coverage be complete, your production pure, and your metrics forever truthful! ⚡**

**Remember: Simplicity is divine! coverage.process_startup() does all the magic!**
