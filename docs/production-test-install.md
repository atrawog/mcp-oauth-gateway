# Production Install with Full Test Verification

**🧪 Deploy MCP OAuth Gateway and verify every component with the divine test suite!**

This guide extends the [Quick Production Install](quick-install.md) with comprehensive testing to verify your production deployment.

## Prerequisites

- Completed [Quick Production Install](quick-install.md)
- All services running and healthy
- Valid domain with SSL certificates

## Step 1: Enable All MCP Services for Testing

Edit your `.env` to enable all services for comprehensive testing:

```bash
# Enable ALL MCP services for full test coverage
MCP_EVERYTHING_ENABLED=true
MCP_FETCH_ENABLED=true
MCP_FILESYSTEM_ENABLED=true
MCP_MEMORY_ENABLED=true
MCP_PLAYWRIGHT_ENABLED=true
MCP_SEQUENTIALTHINKING_ENABLED=true
MCP_TIME_ENABLED=true
MCP_TMUX_ENABLED=true
MCP_FETCHS_ENABLED=true
MCP_ECHO_STATEFUL_ENABLED=true
MCP_ECHO_STATELESS_ENABLED=true
```

## Step 2: Rebuild and Restart with All Services

```bash
# Rebuild all services
just rebuild

# Restart to load new configuration
just down
just up

# Ensure all services are ready
just check-health
```

## Step 3: Run Pre-Test Health Checks

```bash
# Comprehensive health check
just check-health

# Check SSL certificates for all subdomains
just check-ssl

# View service status
just status
```

## Step 4: Execute Full Test Suite

### Run All Tests
```bash
# Run complete test suite with coverage
just test-sidecar-coverage

# View test results
cat reports/test-results.txt
```

### Run Specific Test Categories

```bash
# OAuth flow tests
just test tests/test_oauth_flows.py -v

# MCP protocol tests
just test tests/test_mcp_protocol.py -v

# Security tests
just test tests/test_security.py -v

# Integration tests
just test tests/test_integration.py -v
```

### Parallel Test Execution
```bash
# Run tests in parallel for faster results
just test-parallel

# Run with specific worker count
just test-n 8
```

## Step 5: Verify OAuth Functionality

```bash
# Test dynamic client registration
just test tests/test_oauth_register.py::test_rfc7591_compliance -v

# Test PKCE flow
just test tests/test_oauth_flows.py::test_pkce_required -v

# Test token lifecycle
just test tests/test_oauth_tokens.py -v
```

## Step 6: Verify MCP Service Integration

```bash
# Test each MCP service individually
just test tests/test_mcp_services.py::test_mcp_fetch -v
just test tests/test_mcp_services.py::test_mcp_filesystem -v
just test tests/test_mcp_services.py::test_mcp_memory -v

# Test MCP protocol compliance
just test tests/test_mcp_protocol.py::test_streamablehttp_transport -v
```

## Step 7: Load Testing (Optional)

```bash
# Run load tests to verify production readiness
just test tests/test_load.py -v

# Check performance metrics
just test tests/test_performance.py -v
```

## Step 8: Security Verification

```bash
# Run security test suite
just test tests/test_security.py -v

# Verify authentication enforcement
just test tests/test_auth_enforcement.py -v

# Test CORS and origin validation
just test tests/test_cors.py -v
```

## Step 9: View Test Coverage Report

```bash
# Coverage reports are generated automatically by test-sidecar-coverage
# View coverage report
python -m http.server -d htmlcov 8080
# Browse to http://localhost:8080

# Alternative: Check coverage statistics
cat reports/coverage.txt
```

## Step 10: Clean Test Data

```bash
# Remove test-generated OAuth registrations
just test-cleanup

# Verify cleanup
just oauth-list-registrations
```

## Test Results Interpretation

### Expected Results
- ✅ All tests should pass (100% success rate)
- ✅ Coverage should be >80% for critical components
- ✅ No security vulnerabilities detected
- ✅ All MCP services responding correctly
- ✅ OAuth flows working end-to-end

### Common Test Failures and Solutions

**Service Not Ready**
```bash
# Ensure services are fully initialized
just check-health
just test
```

**SSL Certificate Issues**
```bash
# Verify certificates
just check-ssl
# Certificates may take time to provision
sleep 60 && just test
```

**OAuth Token Issues**
```bash
# Regenerate tokens
just generate-github-token
just mcp-client-token
```

## Continuous Verification

Set up automated testing:

```bash
# Add to crontab for daily verification
0 2 * * * cd /path/to/mcp-oauth-gateway && just test-sidecar-coverage

# Check latest test results
ls -la reports/
cat reports/test-results.txt
```

## Production Verification Checklist

- [ ] All services health checks passing
- [ ] SSL certificates valid for all subdomains
- [ ] OAuth endpoints accessible
- [ ] MCP services responding to protocol requests
- [ ] Test suite 100% passing
- [ ] Coverage meets requirements
- [ ] Load tests acceptable performance
- [ ] Security tests all passing
- [ ] Backup/restore procedures tested

## Next Steps

- Review test coverage reports in `htmlcov/`
- Configure backup automation per [Production Deployment](deployment/production.md)
- Review logs for any warnings: `just logs --since 1h`

**⚡ Remember: A tested production system is a trusted production system!**
