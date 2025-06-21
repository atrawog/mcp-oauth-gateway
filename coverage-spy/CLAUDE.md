# 🔥 CLAUDE.md - The Coverage-Spy Divine Scripture! ⚡

**🕵️ Behold! The Sacred Coverage Interceptor - Divine Metrics Without Contamination! 🕵️**

**⚡ This is Coverage-Spy - The Holy Sidecar Pattern for Production Coverage Glory! ⚡**

## 🔱 The Sacred Purpose - Divine Coverage Without Code Pollution!

**Coverage-Spy is the blessed pattern for measuring REAL production code coverage!**

This sacred technique channels these divine powers:
- **Zero Code Modification** - Production containers remain pure and untouched!
- **Sidecar Pattern Glory** - Parallel containers for measurement isolation!
- **Python Site Customization** - sitecustomize.py divine interception!
- **Real Service Testing** - Measure actual production behavior!
- **Clean Separation** - Coverage code never touches production!

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

### The Divine sitecustomize.py
```python
"""
Sacred coverage interceptor - loaded automatically by Python!
This file is placed in the Python path to enable coverage.
"""

import os
import sys
import atexit

# Only activate if COVERAGE_ENABLE is set
if os.environ.get('COVERAGE_ENABLE') == 'true':
    try:
        import coverage
        
        # Configure coverage with divine settings
        cov = coverage.Coverage(
            data_file='/coverage/.coverage',
            source=['/app'],
            omit=[
                '*/tests/*',
                '*/test_*',
                '*/__pycache__/*',
                '*/site-packages/*'
            ]
        )
        
        # Start coverage measurement
        cov.start()
        
        # Register cleanup on exit
        def save_coverage():
            cov.stop()
            cov.save()
            print("Coverage data saved to /coverage/.coverage")
            
        atexit.register(save_coverage)
        
    except ImportError:
        # Coverage not installed - fail silently
        pass
```

**⚡ Automatically loaded by Python on interpreter startup! ⚡**

## 🐳 The Docker Implementation - Parallel Container Pattern!

### Dockerfile.coverage - The Sidecar Vessel
```dockerfile
# Start from the same base as production
FROM python:3.11-slim AS base

# Install dependencies including coverage
RUN pixi add coverage pytest-cov

# Copy application code
COPY . /app
WORKDIR /app

# CRITICAL: Add coverage-spy to Python path
ENV PYTHONPATH="/coverage-spy:$PYTHONPATH"
COPY coverage-spy/sitecustomize.py /coverage-spy/

# Enable coverage collection
ENV COVERAGE_ENABLE=true

# Mount point for coverage data
VOLUME /coverage

# Same command as production
CMD ["python", "-m", "your_app"]
```

### docker-compose.coverage.yml - The Orchestration
```yaml
services:
  auth-coverage:
    build:
      context: ./auth
      dockerfile: Dockerfile.coverage
    environment:
      - COVERAGE_ENABLE=true
      - COVERAGE_FILE=/coverage/.coverage.auth
    volumes:
      - ./coverage-data:/coverage
    # All other settings same as production
    
  mcp-fetch-coverage:
    build:
      context: ./mcp-fetch  
      dockerfile: Dockerfile.coverage
    environment:
      - COVERAGE_ENABLE=true
      - COVERAGE_FILE=/coverage/.coverage.mcp-fetch
    volumes:
      - ./coverage-data:/coverage
```

**⚡ Each service gets its own coverage sidecar! ⚡**

## 🔧 The Sacred Configuration - Environment Control!

### Coverage Control Variables
```bash
# Enable/disable coverage collection
COVERAGE_ENABLE=true|false

# Coverage data file location
COVERAGE_FILE=/coverage/.coverage

# Source directories to measure
COVERAGE_SOURCE=/app

# Patterns to omit from coverage
COVERAGE_OMIT=*/tests/*,*/migrations/*
```

### The Coverage Configuration (.coveragerc)
```ini
[run]
source = /app
omit = 
    */tests/*
    */migrations/*
    */__pycache__/*
    */site-packages/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:

[html]
directory = /coverage/htmlcov
```

## 🚀 Using the Coverage-Spy Pattern!

### 1. Enable Coverage Testing
```bash
# Start coverage sidecars
just up-coverage

# Run your test suite
just test-with-coverage

# Stop and collect data
just down-coverage
```

### 2. Generate Reports
```bash
# Combine coverage data
just coverage-combine

# Generate HTML report
just coverage-html

# View results
open htmlcov/index.html
```

### 3. Extract Metrics
```bash
# Generate JSON summary
just coverage-json

# Parse and analyze
just analyze-coverage
```

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

### Example Test Run
```bash
# Start everything with coverage
docker-compose -f docker-compose.yml \
              -f docker-compose.coverage.yml \
              up -d

# Wait for services
just ensure-services-ready

# Run comprehensive tests
just test-all

# Collect coverage data
docker-compose down
just coverage-report
```

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

## 📊 Advanced Patterns - Divine Coverage Mastery!

### Parallel Coverage Collection
```python
# In sitecustomize.py for parallel safety
cov = coverage.Coverage(
    data_file=f'/coverage/.coverage.{os.getpid()}',
    parallel=True
)
```

### Dynamic Coverage Control
```python
# Toggle coverage at runtime
if os.environ.get('COVERAGE_PAUSE'):
    cov.stop()
else:
    cov.start()
```

### Coverage Webhooks
```python
# Send coverage data on completion
def upload_coverage():
    cov.stop()
    cov.save()
    
    # Upload to coverage service
    requests.post('http://coverage-server/upload', 
                  files={'coverage': open('.coverage', 'rb')})
```

## 🎯 The Divine Mission - Coverage-Spy Purpose!

**What Coverage-Spy MUST Do:**
- Measure production code coverage accurately!
- Maintain complete separation from production!
- Work with any Python application seamlessly!
- Provide actionable coverage metrics!
- Support parallel test execution!

**What Coverage-Spy MUST NOT Do:**
- Modify production code or images!
- Impact production performance!
- Require code changes for measurement!
- Store sensitive data in reports!
- Break existing functionality!

**⚡ Pure measurement without contamination! ⚡**

## 🔱 Why This Pattern is Divine!

### The Problem with Traditional Coverage
- Requires code modification!
- Mixes test code with production!
- Can't measure real deployments!
- Impacts performance always!

### The Coverage-Spy Solution  
- Zero production changes!
- Parallel measurement containers!
- Real deployment testing!
- Optional performance impact!

**⚡ The ONLY way to measure production truthfully! ⚡**

## 📜 Integration with CI/CD - Automated Divine Metrics!

### GitHub Actions Example
```yaml
- name: Start services with coverage
  run: |
    docker-compose -f docker-compose.yml \
                   -f docker-compose.coverage.yml \
                   up -d

- name: Run integration tests
  run: just test-integration

- name: Collect coverage data
  run: |
    docker-compose down
    just coverage-combine
    just coverage-xml

- name: Upload to Codecov
  uses: codecov/codecov-action@v3
  with:
    file: ./coverage.xml
```

## 🛠️ Debugging Coverage Issues!

```bash
# Verify sitecustomize loading
docker exec service-coverage python -c "import sys; print(sys.path)"

# Check coverage is active
docker exec service-coverage python -c "import coverage; print(coverage.__version__)"

# View coverage data
docker exec service-coverage coverage report

# Debug data file location
docker exec service-coverage ls -la /coverage/

# Monitor coverage in real-time
docker exec service-coverage coverage run --help
```

---

**🔥 May your coverage be complete, your production pure, and your metrics forever truthful! ⚡**