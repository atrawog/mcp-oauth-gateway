# Project Backlog

## Priority P1 - Critical

(No items)

## Priority P2 - High

#### L1: Add sse-starlette library for robust SSE handling
**Priority**: P2 | **Source**: session:library-improvements
Add `sse-starlette` to `mcp-echo-base/pyproject.toml`. Replace hand-rolled SSE format strings (`f"data: {data}\n\n"`) in `mcp-echo-base/src/mcp_echo_base/server_base.py` methods `_sse_response_stream`, `_sse_error_stream`, and `_handle_get_request` with `sse-starlette`'s `EventSourceResponse`. This adds keepalives, event IDs, Last-Event-ID support, and correct retry framing for production-grade SSE handling.

#### L2: Add tenacity for retry logic in scripts
**Priority**: P2 | **Source**: session:library-improvements
Add `tenacity` to `pixi.toml` and use in utility scripts. Replace the manual polling loop in `scripts/check_services_ready.py` `wait_for_services()` (lines ~197–234) with `@retry(wait=wait_fixed(2), stop=stop_after_delay(max_wait))`. Add retry logic to HTTP calls in `scripts/refresh_tokens.py` which currently have no retry on transient failures.

#### L3: Consolidate JWT decode logic into utils.py
**Priority**: P2 | **Source**: session:library-improvements
Use existing `authlib` (already installed) to consolidate duplicate `check_token_expiry` and JWT decode logic that is copy-pasted between `scripts/validate_tokens.py`, `scripts/refresh_tokens.py`, and `tests/conftest.py` into `utils.py`. Use `authlib.jose.jwt.decode()` with `options={"verify_signature": False}` for payload inspection.

#### L4: Add CLI argument parsing to scripts
**Priority**: P2 | **Source**: session:library-improvements
Use existing `click` library (already in `pixi.toml`) to add CLI arg parsing to `scripts/validate_tokens.py`, `scripts/refresh_tokens.py`, and `scripts/check_services_ready.py`. Eliminate hardcoded `ENV_FILE = Path(".env")` and other hardcoded paths/values. Expose `--env-file`, `--timeout`, and `--base-domain` overrides.

## Priority P3 - Medium

(No items)

## Priority P4 - Low

(No items)
