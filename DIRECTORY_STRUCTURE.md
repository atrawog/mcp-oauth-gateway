# MCP OAuth Gateway - Directory Structure

This document provides a comprehensive overview of the repository's directory structure and organization.

## Repository Type: Monorepo with Git Submodules

This is a **monorepo** that uses **Git submodules** for modular package management. Core packages are maintained as separate repositories and included as submodules.

---

## Top-Level Structure

```
/Users/alyshialedlie/code/is-internal/mcp-oauth-gateway/
├── .github/              # GitHub Actions workflows
├── auth/                 # OAuth authorization service (main auth component)
├── coverage-spy/         # Code coverage monitoring utility
├── docs/                 # Jupyter Book documentation
├── scripts/              # Utility and automation scripts (158 files)
├── tests/                # Comprehensive test suite (87 test files)
├── traefik/              # Reverse proxy configuration
│
├── mcp-oauth-dynamicclient/          # [SUBMODULE] OAuth 2.0 server (RFC 7591/7592)
├── mcp-streamablehttp-proxy/         # [SUBMODULE] Stdio → HTTP/SSE wrapper
├── mcp-streamablehttp-client/        # [SUBMODULE] HTTP/SSE → stdio wrapper
├── mcp-fetch-streamablehttp-server/  # [SUBMODULE] Native fetch server
├── mcp-echo-streamablehttp-server-stateful/   # [SUBMODULE] Echo diagnostic (stateful)
├── mcp-echo-streamablehttp-server-stateless/  # [SUBMODULE] Echo diagnostic (stateless)
│
├── mcp-echo-base/        # Shared base class for echo servers (Template Method pattern)
├── mcp-echo-stateful/    # Docker config for stateful echo
├── mcp-echo-stateless/   # Docker config for stateless echo
├── mcp-everything/       # Test server with all features
├── mcp-fetch/            # Web content fetching (stdio proxy)
├── mcp-fetchs/           # Fetch service (s suffix variant)
├── mcp-filesystem/       # File system access (sandboxed)
├── mcp-memory/           # Persistent memory/knowledge graph
├── mcp-playwright/       # Browser automation
├── mcp-sequentialthinking/  # Structured problem solving
├── mcp-time/             # Time and timezone operations
├── mcp-tmux/             # Terminal multiplexer integration
│
├── .env.example          # Example environment configuration
├── .gitignore            # Git ignore rules
├── .gitmodules           # Git submodule configuration (6 submodules)
├── .pre-commit-config.yaml  # Pre-commit hooks
├── CLAUDE.md             # Claude Code AI assistant guidance
├── coverage.json         # Code coverage report
├── docker-compose.yml    # Main Docker Compose configuration
├── docker-compose.coverage.yml  # Coverage testing compose file
├── justfile              # Command runner (44KB of automation)
├── LICENSE               # Project license
├── logrotate.conf        # Log rotation configuration
├── mcp-oauth-gateway.code-workspace  # VS Code workspace
├── mcp-template.docker-compose.yml   # Template for new services
├── pixi.lock             # Pixi dependency lock file (474KB)
├── pixi.toml             # Pixi package manager config
├── pytest.ini            # Pytest configuration
├── README.md             # Main project documentation (38KB)
├── ruff.toml             # Ruff linter configuration
└── utils.py              # Shared utility functions
```

---

## Component Categories

### 1. Core Infrastructure (Main Repository)

| Directory | Purpose | Type |
|-----------|---------|------|
| `auth/` | OAuth 2.1 authorization server | Service |
| `traefik/` | Reverse proxy, routing, TLS termination | Infrastructure |
| `docs/` | Jupyter Book documentation | Documentation |
| `tests/` | Comprehensive test suite (87 files) | Testing |
| `scripts/` | Automation utilities (158 files) | Utilities |
| `coverage-spy/` | Code coverage monitoring | Testing |

### 2. Git Submodules (External Repositories)

**Published Python packages maintained as separate repos:**

| Submodule | PyPI Package | Purpose |
|-----------|-------------|---------|
| `mcp-oauth-dynamicclient/` | mcp-oauth-dynamicclient | RFC 7591/7592 OAuth server |
| `mcp-streamablehttp-proxy/` | mcp-streamablehttp-proxy | Stdio → HTTP/SSE bridge |
| `mcp-streamablehttp-client/` | mcp-streamablehttp-client | HTTP/SSE → stdio client |
| `mcp-fetch-streamablehttp-server/` | mcp-fetch-streamablehttp-server | Native Python fetch server |
| `mcp-echo-streamablehttp-server-stateful/` | mcp-echo-streamablehttp-server-stateful | Diagnostic echo (stateful) |
| `mcp-echo-streamablehttp-server-stateless/` | mcp-echo-streamablehttp-server-stateless | Diagnostic echo (stateless) |

**How to identify:** Each has its own `.git/` directory and is listed in `.gitmodules`.

### 3. MCP Service Directories (Docker Configurations)

**These are NOT submodules** - they contain Docker/service configs only:

| Directory | Protocol Version | Description |
|-----------|------------------|-------------|
| `mcp-echo-base/` | N/A | Shared base class (Template Method pattern) |
| `mcp-echo-stateful/` | 2025-06-18 | Docker config for stateful echo |
| `mcp-echo-stateless/` | 2025-06-18 | Docker config for stateless echo |
| `mcp-everything/` | 2025-06-18 | Test server with all features |
| `mcp-fetch/` | 2025-03-26 | Web content fetching (stdio wrapper) |
| `mcp-fetchs/` | 2025-06-18 | Fetch service variant |
| `mcp-filesystem/` | 2025-03-26 | Sandboxed file system access |
| `mcp-memory/` | 2024-11-05 | Knowledge graph/memory |
| `mcp-playwright/` | 2025-06-18 | Browser automation |
| `mcp-sequentialthinking/` | 2024-11-05 | Problem solving framework |
| `mcp-time/` | 2025-03-26 | Time/timezone operations |
| `mcp-tmux/` | 2025-06-18 | Terminal multiplexer |

---

## Directory Deep Dive

### `/auth/` - OAuth Authorization Service

Contains the main OAuth 2.1 implementation:
- `Dockerfile` - Service container image
- `Dockerfile.coverage` - Coverage testing image
- `docker-compose.yml` - Service orchestration
- `CLAUDE.md` - Service-specific AI guidance

**Implementation:** Uses `mcp-oauth-dynamicclient` package (submodule).

### `/traefik/` - Reverse Proxy

Traefik configuration for routing, TLS, and authentication:
- Dynamic routing rules
- Let's Encrypt TLS certificates
- ForwardAuth middleware for OAuth
- Service discovery via Docker labels

### `/docs/` - Documentation

Jupyter Book documentation with:
- Architecture diagrams
- API documentation
- Service guides
- Justfile command reference

**Build:** `just docs-build`, **Serve:** `just docs-serve`

### `/tests/` - Test Suite

87 comprehensive test files covering:
- OAuth flows (authorization code, device flow, PKCE)
- MCP protocol compliance
- Service integration tests
- Security validation (RFC compliance)
- Error handling and edge cases

**Run:** `just test` or `just test-parallel`

### `/scripts/` - Automation Scripts

158 utility scripts for:
- Service management
- OAuth token generation
- Testing utilities
- Deployment automation
- Debugging tools

### Submodule Directories

Each submodule contains:
- `src/` - Python source code
- `pyproject.toml` - Package configuration
- `README.md` - Package documentation
- `.git/` - Own Git repository
- `LICENSE` - Package license

**Development Pattern:**
1. Work inside submodule directory
2. Commit changes to submodule repo
3. Update parent repo to reference new commit
4. Push both repos

---

## File Organization Best Practices

### ✅ What's Been Done

1. **Removed redundant files:**
   - Deleted 46 `repomix-output.xml` files (~3.6MB)
   - Cleaned up all `__pycache__/` directories
   - Removed all `.pyc` compiled Python files

2. **Ensured .gitignore coverage:**
   - `repomix-output.xml` is ignored (line 113)
   - `__pycache__/` is ignored (line 21)
   - All Python artifacts are excluded

3. **Directory structure is clean:**
   - Git submodules properly configured
   - Service directories logically organized
   - No orphaned or duplicate files

### ⚠️ Important Notes

1. **DO NOT delete CLAUDE.md files** - These provide AI assistant guidance per directory
2. **Submodules have their own .git/** - This is normal and required
3. **Service directories are NOT submodules** - They contain only Docker configs
4. **utils.py in root** - Shared utility module, should stay at root level

---

## Working with Submodules

### Clone with submodules:
```bash
git clone --recurse-submodules https://github.com/atrawog/mcp-oauth-gateway.git
```

### Initialize submodules after clone:
```bash
git submodule update --init --recursive
```

### Update all submodules to latest:
```bash
git submodule update --remote --recursive
```

### Work on a submodule:
```bash
cd mcp-oauth-dynamicclient/
# Make changes
git add .
git commit -m "Update OAuth implementation"
git push origin main

# Return to parent repo
cd ..
git add mcp-oauth-dynamicclient
git commit -m "Update submodule reference"
git push
```

---

## Environment Configuration

All configuration via `.env` file (copy from `.env.example`):

### Required variables:
- `BASE_DOMAIN` - Your public domain
- `ACME_EMAIL` - Email for Let's Encrypt
- `GITHUB_CLIENT_ID` / `GITHUB_CLIENT_SECRET` - GitHub OAuth app
- `REDIS_PASSWORD` - Redis security
- `GATEWAY_JWT_SECRET` - JWT signing key

### Service enablement:
- `MCP_*_ENABLED=true/false` - Enable/disable individual services

---

## Package Manager: Pixi

This project uses **pixi** (not pip/poetry/uv):
- `pixi.toml` - Dependency configuration
- `pixi.lock` - Locked dependency versions
- `.pixi/` - Local environment (git-ignored)

**Install dependencies:** `pixi install`

---

## Summary Statistics

- **Total MCP services:** 19 directories
- **Git submodules:** 6 packages
- **Test files:** 87
- **Utility scripts:** 158
- **Main justfile:** 44KB (comprehensive automation)
- **Documentation:** Jupyter Book with multiple sections

---

## Quick Reference

| Task | Command |
|------|---------|
| Start all services | `just up` |
| Stop all services | `just down` |
| Run tests | `just test` |
| Run tests in parallel | `just test-parallel` |
| View logs | `just logs [service]` |
| Build docs | `just docs-build` |
| Check health | `just ensure-services-ready` |
| Generate secrets | `just generate-all-secrets` |

For complete command reference, see `justfile` or run `just --list`.

---

**Last Updated:** 2026-03-28
**Repository:** https://github.com/atrawog/mcp-oauth-gateway
