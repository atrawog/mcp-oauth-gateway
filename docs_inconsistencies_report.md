# Documentation Inconsistencies Report

## Executive Summary

This report identifies inconsistencies between the documentation files and the actual codebase/README.md. The analysis covers environment variable naming, non-existent `just` commands, formatting issues, and contradictory information.

## 1. Environment Variable Naming Inconsistencies

### ❌ INCORRECT: `ENABLE_MCP_*` pattern
**Files affected:**
- `docs/deployment/production.md` (line 156-157)

**Issue:** Documentation mentions `ENABLE_METRICS=true` and `ENABLE_TRACING=true` which don't exist in `.env.example`

**Correct pattern:** `MCP_*_ENABLED` (e.g., `MCP_FETCH_ENABLED=true`)

**Evidence from `.env.example`:**
```bash
MCP_ECHO_STATEFUL_ENABLED=false
MCP_ECHO_STATELESS_ENABLED=true
MCP_FETCH_ENABLED=false
MCP_FILESYSTEM_ENABLED=false
# etc.
```

## 2. Non-existent `just` Commands

### Commands mentioned in documentation but NOT found in justfile:

| Command | File | Line | Status |
|---------|------|------|--------|
| `just generate-all-secrets` | Multiple files | - | ❌ Does not exist |
| `just wait-healthy` | `docs/deployment/production.md` | 228 | ❌ Does not exist |
| `just health-check-all` | `docs/deployment/production.md` | 234 | ❌ Does not exist |
| `just oauth-backup` | `docs/services/auth.md` | 354 | ❌ Does not exist |
| `just oauth-purge-expired` | `docs/services/auth.md` | 358 | ❌ Does not exist |
| `just oauth-list-registrations` | `docs/services/auth.md` | 362 | ❌ Does not exist |
| `just oauth-stats` | `docs/services/auth.md` | 366 | ❌ Does not exist |
| `just monitoring-up` | `docs/deployment/production.md` | 406 | ❌ Does not exist |

### Actual commands available:
- `just check-health` (not `health-check-all`)
- `just generate-jwt-secret`, `just generate-rsa-keys`, `just generate-redis-password` (not `generate-all-secrets`)

## 3. Configuration Variable Inconsistencies

### In `docs/deployment/production.md`:
- **Line 145**: `JWT_EXPIRY=3600` - This variable is not referenced in README.md or `.env.example`
- **Line 156-157**: `ENABLE_METRICS=true`, `ENABLE_TRACING=true` - These don't exist
- **Line 148-149**: Traefik-specific variables not consistent with main configuration

### Rate Limiting Variables:
Documentation mentions:
- `RATE_LIMIT_AVERAGE=50`
- `RATE_LIMIT_BURST=100`
- `OAUTH_RATE_LIMIT_REGISTER=5/hour`
- `OAUTH_RATE_LIMIT_TOKEN=60/hour`

These are not found in `.env.example` or README.md

## 4. Formatting Inconsistencies

### Documentation uses different formatting patterns than README.md:
- README.md uses clear architecture diagrams with box-drawing characters
- Some documentation files use simplified formatting
- Inconsistent use of emoji indicators (🔥, ⚡, etc.)

## 5. Contradictory Information

### Token Lifetimes:
- **README.md** (line 481): States "CLIENT_LIFETIME=7776000 # Client registration: 90 days"
- **docs/deployment/production.md** (line 134): States "CLIENT_LIFETIME=2592000 # 30 days for production"

### Service Management:
- Documentation mentions various service management commands that don't exist
- Actual pattern is simpler: `just up`, `just down`, `just restart [service]`

## 6. Missing Context

### Documentation references features not in README.md:
1. **Monitoring stack** (Prometheus, Grafana, Loki) - extensive documentation but not mentioned in README.md
2. **Rate limiting** configuration - detailed in docs but not in main configuration
3. **Security headers** configuration - mentioned in production docs but not in README.md

## 7. Command Pattern Inconsistencies

### Documentation shows commands that don't follow the sacred pattern:
```bash
# Documentation shows:
just health-check-all
just wait-healthy

# Actual pattern:
just check-health
just check-services
```

## 8. Environment Variables Summary

### All mentioned environment variables extracted from documentation:

**From production.md:**
- COMPOSE_PROJECT_NAME
- DOMAIN (should be BASE_DOMAIN)
- ENVIRONMENT
- JWT_EXPIRY (not in .env.example)
- REDIS_SAVE_INTERVALS
- REDIS_APPENDONLY
- REDIS_MAXMEMORY
- REDIS_MAXMEMORY_POLICY
- TRAEFIK_LOG_LEVEL
- TRAEFIK_DASHBOARD
- RATE_LIMIT_AVERAGE (not in .env.example)
- RATE_LIMIT_BURST (not in .env.example)
- OAUTH_RATE_LIMIT_REGISTER (not in .env.example)
- OAUTH_RATE_LIMIT_TOKEN (not in .env.example)
- ENABLE_METRICS (should be removed)
- ENABLE_TRACING (should be removed)
- LOG_LEVEL

**From auth.md:**
- GATEWAY_RSA_PRIVATE_KEY
- GATEWAY_RSA_PUBLIC_KEY
- ACCESS_TOKEN_LIFETIME
- REFRESH_TOKEN_LIFETIME

## Recommendations

1. **Update all documentation** to use correct environment variable patterns (`MCP_*_ENABLED`)
2. **Remove references** to non-existent `just` commands
3. **Standardize** token lifetime recommendations
4. **Add missing variables** to `.env.example` or remove from documentation
5. **Align formatting** with README.md style
6. **Clarify** which features are aspirational vs. implemented
7. **Update command references** to match actual justfile commands
8. **Remove or implement** monitoring-related configurations

## Priority Fixes

### High Priority:
1. Fix all `ENABLE_MCP_*` references to `MCP_*_ENABLED`
2. Remove non-existent `just` command references
3. Correct CLIENT_LIFETIME inconsistency

### Medium Priority:
1. Add missing environment variables to `.env.example`
2. Update formatting to match README.md
3. Remove or document monitoring features properly

### Low Priority:
1. Minor formatting inconsistencies
2. Additional context clarifications
