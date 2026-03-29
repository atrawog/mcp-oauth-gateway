# MCP Echo Server Refactoring Plan

## Overview

This document outlines the plan to refactor the MCP Echo Server implementations (stateful and stateless) to eliminate ~400+ lines of code duplication by extracting common functionality into a shared base class.

## Current State

### Duplication Analysis

The stateful and stateless echo servers share significant code:

| Method | Similarity | Lines Each | Status |
|--------|-----------|------------|--------|
| `_handle_post_request()` | 100% identical | 22 | Extract to base |
| `_validate_post_headers()` | 100% identical | 37 | Extract to base |
| `_error_response()` | 100% identical | 7 | Extract to base |
| `_sse_response_stream()` | 100% identical | 9 | Extract to base |
| `_sse_error_stream()` | 100% identical | 5 | Extract to base |
| `run()` | 99.7% identical | 59 | Extract to base |
| `handle_mcp_request()` | 93.8% similar | 121 | Template method |
| `_handle_bearer_decode()` | 94.1% similar | 112 | Template method |

**Total Duplicated Lines**: ~372 lines that should be shared

### Key Differences Between Implementations

The stateful and stateless servers differ in:

1. **Session Handling**:
   - Stateful: Tracks `mcp-session-id` header
   - Stateless: No session tracking

2. **Logging Identifiers**:
   - Stateful: "MCP-ECHO STATEFUL REQUEST/RESPONSE"
   - Stateless: "MCP-ECHO STATELESS REQUEST/RESPONSE"

3. **Request Type**:
   - Stateful: `"type": "mcp_echo_stateful_request"`
   - Stateless: `"type": "mcp_echo_stateless_request"`

4. **Capabilities**:
   - Stateful: `resources.listChanged = True`
   - Stateless: `resources.listChanged = False`

## Refactoring Strategy

### Phase 1: Foundation (COMPLETED)

**Status**: ✅ Base class created at `mcp-echo-base/src/mcp_echo_base/server_base.py`

Created `MCPEchoServerBase` abstract base class with:

1. **100% Identical Methods** (Concrete implementations):
   - `_handle_post_request()` - POST request handling with validation
   - `_validate_post_headers()` - Content-Type and Accept header validation
   - `_error_response()` - JSON-RPC error response formatting
   - `_sse_response_stream()` - SSE streaming for single response
   - `_sse_error_stream()` - SSE streaming for errors
   - `run()` - Server startup and configuration

2. **Template Methods** (Common structure, customizable parts):
   - `handle_mcp_request()` - Main request handler with subclass hooks
   - `_get_common_headers()` - Extract common Traefik headers
   - `_get_base_request_data()` - Build base request data structure
   - `_handle_options_request()` - OPTIONS request handling
   - `_handle_get_request()` - GET request (SSE) handling

3. **Abstract Methods** (Must be implemented by subclasses):
   - `get_server_type()` - Return "stateless" or "stateful"
   - `get_supported_versions()` - Return list of protocol versions
   - `get_additional_headers()` - Return subclass-specific headers
   - `get_additional_request_data()` - Return subclass-specific request data
   - `handle_initialize()` - Handle initialize request
   - `_log_request()` - Log with subclass-specific format

### Phase 2: Integration (IN PROGRESS)

#### Step 1: Create Package Structure

```bash
cd ~/code/ISInternal/mcp-oauth-gateway
mkdir -p mcp-echo-base/src/mcp_echo_base
mkdir -p mcp-echo-base/tests
touch mcp-echo-base/src/mcp_echo_base/__init__.py
touch mcp-echo-base/pyproject.toml
touch mcp-echo-base/README.md
```

#### Step 2: Update Stateless Server

File: `mcp-echo-streamablehttp-server-stateless/src/mcp_echo_streamablehttp_server_stateless/server.py`

```python
from mcp_echo_base.server_base import MCPEchoServerBase

class MCPEchoServerStateless(MCPEchoServerBase):
    """Stateless MCP Echo Server implementation."""

    def get_server_type(self) -> str:
        return "stateless"

    def get_supported_versions(self) -> list[str]:
        return ["2025-06-18", "2024-11-05"]

    def get_additional_headers(self) -> dict[str, str]:
        # Stateless doesn't track additional headers beyond common ones
        return {}

    def get_additional_request_data(self, traefik_headers: dict[str, Any]) -> dict[str, Any]:
        # No additional fields for stateless
        return {}

    def _log_request(self, request: Request, traefik_headers: dict[str, Any]):
        logger.info(
            "MCP-ECHO STATELESS REQUEST - Method: %s | Path: %s | "
            "Real-IP: %s | Forwarded-For: %s | Host: %s | User: %s",
            request.method,
            str(request.url.path),
            traefik_headers.get("x-real-ip", "unknown"),
            traefik_headers.get("x-forwarded-for", "unknown"),
            traefik_headers.get("host", "unknown"),
            traefik_headers.get("x-user-name", "unknown"),
        )

    async def handle_initialize(self, arguments: dict[str, Any], request_id: Any) -> dict[str, Any]:
        # Stateless initialize implementation
        # ... existing code ...
```

**Lines Removed**: ~200 lines
**Lines Added**: ~50 lines (subclass implementations)
**Net Savings**: ~150 lines

#### Step 3: Update Stateful Server

File: `mcp-echo-streamablehttp-server-stateful/src/mcp_echo_streamablehttp_server_stateful/server.py`

```python
from mcp_echo_base.server_base import MCPEchoServerBase

class MCPEchoServerStateful(MCPEchoServerBase):
    """Stateful MCP Echo Server implementation with session management."""

    def __init__(self, debug: bool = False, supported_versions: list[str] | None = None,
                 session_timeout: int = 300):
        super().__init__(debug, supported_versions)
        self.session_timeout = session_timeout
        self._sessions: dict[str, dict[str, Any]] = {}

    def get_server_type(self) -> str:
        return "stateful"

    def get_supported_versions(self) -> list[str]:
        return ["2025-06-18", "2024-11-05"]

    def get_additional_headers(self) -> dict[str, str]:
        return {"mcp-session-id": "mcp-session-id"}

    def get_additional_request_data(self, traefik_headers: dict[str, Any]) -> dict[str, Any]:
        return {"session_id": traefik_headers.get("mcp-session-id", "none")}

    def _log_request(self, request: Request, traefik_headers: dict[str, Any]):
        logger.info(
            "MCP-ECHO STATEFUL REQUEST - Method: %s | Path: %s | "
            "Real-IP: %s | Forwarded-For: %s | User: %s | Session: %s",
            request.method,
            str(request.url.path),
            traefik_headers.get("x-real-ip", "unknown"),
            traefik_headers.get("x-forwarded-for", "unknown"),
            traefik_headers.get("x-user-name", "unknown"),
            traefik_headers.get("mcp-session-id", "none"),
        )

    async def handle_initialize(self, arguments: dict[str, Any], request_id: Any) -> dict[str, Any]:
        # Stateful initialize with session management
        # ... existing code ...
```

**Lines Removed**: ~200 lines
**Lines Added**: ~60 lines (subclass implementations + session logic)
**Net Savings**: ~140 lines

#### Step 4: Update Dependencies

Add to both server `pyproject.toml`:

```toml
[project]
dependencies = [
    "mcp-echo-base",
    # ... existing dependencies
]
```

### Phase 3: Testing (CRITICAL)

#### Unit Tests

Create `mcp-echo-base/tests/test_server_base.py`:

```python
import pytest
from mcp_echo_base.server_base import MCPEchoServerBase

class TestMCPEchoServerBase:
    """Test base class functionality."""

    def test_error_response_format(self):
        """Test JSON-RPC error response format."""
        # Test implementation

    def test_validate_post_headers_valid(self):
        """Test header validation with valid headers."""
        # Test implementation

    def test_validate_post_headers_invalid_content_type(self):
        """Test header validation rejects invalid Content-Type."""
        # Test implementation
```

#### Integration Tests

Test both servers:

```bash
# Start stateless server
cd mcp-echo-streamablehttp-server-stateless
python -m mcp_echo_streamablehttp_server_stateless.server --debug

# Test in another terminal
curl -X POST http://localhost:3000/ \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{"jsonrpc":"2.0","method":"initialize","params":{},"id":1}'

# Start stateful server
cd mcp-echo-streamablehttp-server-stateful
python -m mcp_echo_streamablehttp_server_stateful.server --debug

# Test session handling
curl -X POST http://localhost:3001/ \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "mcp-session-id: test-session-123" \
  -d '{"jsonrpc":"2.0","method":"initialize","params":{},"id":1}'
```

#### Regression Tests

1. Test all MCP methods (initialize, tools/list, prompts/list, resources/list)
2. Test SSE streaming (GET requests)
3. Test OPTIONS requests (capabilities)
4. Test error handling (invalid Content-Type, invalid JSON, etc.)
5. Test session management (stateful only)
6. Test Traefik header forwarding
7. Test debug logging

### Phase 4: Deployment

1. **Backup Current Implementations**:
   ```bash
   git tag backup-before-echo-refactor
   ```

2. **Deploy Stateless First** (lower risk):
   - Deploy to staging
   - Run integration tests
   - Monitor for 24 hours
   - Deploy to production

3. **Deploy Stateful** (after stateless is stable):
   - Deploy to staging
   - Run session-specific tests
   - Monitor for 24 hours
   - Deploy to production

## Risk Assessment

| Risk | Severity | Mitigation |
|------|----------|------------|
| Breaking changes in stateless | HIGH | Deploy stateless first, extensive testing |
| Session bugs in stateful | HIGH | Comprehensive session testing, gradual rollout |
| Performance regression | MEDIUM | Load testing, monitoring |
| Import path issues | LOW | Verify imports in all environments |

## Estimated Effort

- **Phase 1 (Foundation)**: ✅ Complete (1 hour)
- **Phase 2 (Integration)**: 2-3 hours
- **Phase 3 (Testing)**: 2-3 hours
- **Phase 4 (Deployment)**: 1-2 hours
- **Total**: 6-9 hours

## Success Criteria

1. ✅ Base class created with all common functionality
2. Both servers inherit from base class
3. All tests passing (unit + integration)
4. No regression in functionality
5. Code duplication reduced by 75%+
6. Documentation updated
7. Both servers deployed successfully

## Next Steps

1. Review this plan with team
2. Schedule refactoring sprint
3. Create mcp-echo-base package
4. Implement Phase 2 (Integration)
5. Execute Phase 3 (Testing)
6. Deploy Phase 4 (Deployment)

## References

- Duplication Analysis: See Python duplication report (114 groups, 6074 duplicated lines)
- Base Class: `mcp-echo-base/src/mcp_echo_base/server_base.py`
- Current Stateless: `mcp-echo-streamablehttp-server-stateless/src/.../server.py`
- Current Stateful: `mcp-echo-streamablehttp-server-stateful/src/.../server.py`

## Progress Update

### Completed (Phase 1 & Phase 2 Partial)

1. ✅ **Base Class Created** (Phase 1)
   - Location: `mcp-echo-base/src/mcp_echo_base/server_base.py`
   - Package structure: `pyproject.toml`, `__init__.py`, `README.md`
   - All common methods extracted
   - Template methods implemented
   - Abstract methods defined

2. ✅ **Stateless Server Refactored** (Phase 2 - Step 2)
   - Original: 1,278 lines
   - Refactored: 1,019 lines
   - **Reduction: 259 lines (20.3%)**
   - Backup: `server_original_backup.py`
   - Dependencies updated: Added `mcp-echo-base` to `pyproject.toml`
   - Import cleaned: Removed `sys.path` manipulation
   - Syntax validated: ✓ Passes `py_compile`

3. ⏳ **Stateful Server** (Phase 2 - Step 3) - READY TO IMPLEMENT
   - Pattern established with stateless refactoring (20.3% reduction achieved)
   - Stateful server analysis:
     - Original: 1,415 lines
     - SessionManager class: 102 lines (unique to stateful, keep as-is)
     - Expected duplicate code: ~250-270 lines (similar to stateless)
     - Expected refactored size: ~1,145-1,165 lines
     - **Expected reduction: ~250-270 lines (17-19%)**

   - Implementation steps:
     1. Import `MCPEchoServerBase`
     2. Inherit from base class
     3. Keep `SessionManager` class (lines 39-141)
     4. Implement abstract methods with session awareness:
        - `get_server_type()` → "stateful"
        - `get_supported_versions()` → ["2025-06-18"]
        - `get_additional_headers()` → `{"mcp-session-id": "mcp-session-id"}`
        - `get_additional_request_data()` → `{"session_id": traefik_headers.get("mcp-session-id", "none")}`
        - `_log_request()` → Include session ID
        - `handle_initialize()` → Session creation/management (returns tuple)
     5. Keep session-specific methods:
        - `_handle_get_request()` - polls session messages
        - Session-aware tool handlers
     6. Update `_handle_jsonrpc_request()` signature (returns tuple)
     7. Add dependency to pyproject.toml
     8. Backup and replace

   - Complexity notes:
     - Stateful has additional session management logic not present in stateless
     - Methods return tuples (response, session_id) instead of just response
     - GET requests used for session message polling (different from stateless)
     - Session lifecycle managed through SessionManager

### Stateful Server - Ready to Complete

**Preparation Complete**:
1. ✅ Dependencies updated (`mcp-echo-base` added to pyproject.toml)
2. ✅ Original backed up (`server_original_backup.py`)
3. ✅ Detailed implementation guide created (`REFACTORING_NEXT_STEPS.md`)
4. ✅ Pattern proven with stateless (20.3% reduction achieved)

**Implementation Ready**:
- All steps documented in `mcp-echo-streamablehttp-server-stateful/REFACTORING_NEXT_STEPS.md`
- Expected reduction: ~250-270 lines (17-19%)
- Key differences from stateless documented
- Testing steps provided

### Next Steps

1. **Complete Stateful Refactoring** (Follow REFACTORING_NEXT_STEPS.md)
   - Estimated time: 1-2 hours
   - Expected result: ~250-270 line reduction
   - Total project savings: ~500-530 lines

2. **Install Dependencies** in proper environment
   ```bash
   cd mcp-echo-base && pip install -e .
   cd ../mcp-echo-streamablehttp-server-stateless && pip install -e .
   cd ../mcp-echo-streamablehttp-server-stateful && pip install -e .
   ```

3. **Run Integration Tests** (Phase 3)
   - Test stateless server functionality
   - Test stateful server with session management
   - Test all 9+ diagnostic tools
   - Regression testing

4. **Deploy** (Phase 4)
   - Stateless first (lower risk)
   - Monitor 24 hours
   - Stateful second
   - Monitor 24 hours
