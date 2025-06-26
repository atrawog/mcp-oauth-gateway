#!/usr/bin/env python3
"""Update tests to use unique client names for parallel execution."""

import re
from pathlib import Path


def update_test_file(filepath, test_name_in_string=None):
    """Update a test file to use unique_client_name fixture."""
    content = filepath.read_text()

    # Check if the test function already has unique_client_name parameter
    test_functions = re.findall(r"(?:async )?def (test_\w+)\([^)]*\):", content)

    for func_name in test_functions:
        # Find the function definition
        func_pattern = rf"((?:async )?def {func_name}\()([^)]*)\):"
        match = re.search(func_pattern, content)

        if match and test_name_in_string and func_name in test_name_in_string:
            params = match.group(2)

            # Add unique_client_name if not present
            if "unique_client_name" not in params:
                new_params = params + ", unique_client_name" if params.strip() else "unique_client_name"
                content = content.replace(match.group(0), f"{match.group(1)}{new_params}):")

            # Replace hardcoded client names with fixture
            content = re.sub(rf'"TEST {func_name}"', "unique_client_name", content)
            content = re.sub(rf"'TEST {func_name}'", "unique_client_name", content)

    # Update client_name in JSON objects
    content = re.sub(r'"client_name":\s*"TEST [^"]*"', '"client_name": unique_client_name', content)

    filepath.write_text(content)
    print(f"✅ Updated {filepath}")


# Apply updates to specific files
updates = [
    {
        "file": "test_auth_error_paths.py",
        "matches": ['"TEST test_registration_empty_redirect_uris"', '"TEST test_create_token_with_user_tracking"'],
        "description": "Uses hardcoded client name",
    },
    {
        "file": "test_auth_error_paths.py",
        "matches": [
            '"client_name": "TEST test_registration_empty_redirect_uris"',
            '"client_name": "TEST test_create_token_with_user_tracking"',
        ],
        "description": "Hardcoded client_name in JSON",
    },
    {
        "file": "test_mcp_ai_hostnames.py",
        "matches": ['"TEST test_hostname_connectivity_{hostname}"', '"TEST test_fetch_through_ai_hostname"'],
        "description": "Uses hardcoded client name",
    },
    {
        "file": "test_mcp_client_oauth.py",
        "matches": [
            '"TEST test_dynamic_client_registration"',
            '"TEST test_client_registration_with_auth_token"',
            '"TEST test_authorization_code_flow_initiation"',
            '"TEST test_pkce_flow_for_cli_clients"',
            '"TEST test_token_refresh_flow"',
            '"TEST test_token_introspection"',
            '"TEST test_credential_format"',
            '"TEST test_client_reregistration"',
        ],
        "description": "Uses hardcoded client name",
    },
    {
        "file": "test_mcp_client_oauth.py",
        "matches": [
            '"client_name": "TEST test_pkce_flow_for_cli_clients"',
            '"client_name": "TEST test_token_refresh_flow"',
            '"client_name": "TEST test_token_introspection"',
            '"client_name": "TEST test_credential_format"',
        ],
        "description": "Hardcoded client_name in JSON",
    },
    {"file": "test_mcp_client_oauth.py", "matches": ['"test-client"'], "description": "Uses fixed test-client name"},
    {"file": "test_mcp_client_proxy.py", "matches": ['"test-client"'], "description": "Uses fixed test-client name"},
    {
        "file": "test_mcp_echo_client_full.py",
        "matches": [
            '"test-client"',
            '"test-client"',
            '"test-client"',
            '"test-client"',
            '"test-client"',
            '"test-client"',
            '"test-client"',
            '"test-client"',
        ],
        "description": "Uses fixed test-client name",
    },
    {
        "file": "test_mcp_echo_integration.py",
        "matches": ['"test-client"', '"test-client"', '"test-client"'],
        "description": "Uses fixed test-client name",
    },
    {
        "file": "test_mcp_everything_client_full.py",
        "matches": [
            '"test-client"',
            '"test-client"',
            '"test-client"',
            '"test-client"',
            '"test-client"',
            '"test-client"',
            '"test-client"',
            '"test-client"',
            '"test-client"',
        ],
        "description": "Uses fixed test-client name",
    },
    {
        "file": "test_mcp_fetch_complete.py",
        "matches": ['"TEST test_mcp_fetch_actually_fetches_content"'],
        "description": "Uses hardcoded client name",
    },
    {
        "file": "test_mcp_fetch_complete.py",
        "matches": ['"client_name": "TEST test_mcp_fetch_actually_fetches_content"'],
        "description": "Hardcoded client_name in JSON",
    },
    {
        "file": "test_mcp_fetch_oauth_debug.py",
        "matches": ['"test-client"'],
        "description": "Uses fixed test-client name",
    },
    {
        "file": "test_mcp_fetchs_mcp_compliance.py",
        "matches": ['"test-client"'],
        "description": "Uses fixed test-client name",
    },
    {
        "file": "test_mcp_memory_integration.py",
        "matches": ['"test-client"', '"test-client"', '"test-client"'],
        "description": "Uses fixed test-client name",
    },
    {
        "file": "test_mcp_playwright_integration.py",
        "matches": ['"test-client"'],
        "description": "Uses fixed test-client name",
    },
    {
        "file": "test_mcp_proxy.py",
        "matches": ['"test-client"', '"test-client"', '"test-client"', '"test-client"', '"test-client"'],
        "description": "Uses fixed test-client name",
    },
    {
        "file": "test_mcp_proxy_fixed.py",
        "matches": ['"test-client"', '"test-client"'],
        "description": "Uses fixed test-client name",
    },
    {
        "file": "test_mcp_tmux_integration.py",
        "matches": ['"test-client"'],
        "description": "Uses fixed test-client name",
    },
    {
        "file": "test_pkce_s256_enforcement.py",
        "matches": ['"TEST test_pkce_plain_method_rejected"', '"TEST test_pkce_s256_proper_validation"'],
        "description": "Uses hardcoded client name",
    },
    {
        "file": "test_pkce_s256_enforcement.py",
        "matches": [
            '"client_name": "TEST test_pkce_plain_method_rejected"',
            '"client_name": "TEST test_pkce_s256_proper_validation"',
        ],
        "description": "Hardcoded client_name in JSON",
    },
    {
        "file": "test_register_security.py",
        "matches": [
            '"TEST test_register_is_public_endpoint"',
            '"TEST test_register_is_public_endpoint"',
            '"TEST test_register_ignores_authorization_headers"',
            '"TEST test_register_ignores_authorization_headers"',
            '"TEST test_security_enforced_at_authorization_stage"',
            '"TEST test_register_with_valid_token_still_succeeds"',
            '"TEST test_register_with_valid_token_still_succeeds"',
            '"TEST test_token_endpoint_requires_authentication"',
            '"TEST test_multiple_clients_can_register_publicly_{i}"',
            '"TEST test_multiple_clients_can_register_publicly_{i}"',
            '"TEST test_anyone_can_register_multiple_clients_1"',
            '"TEST test_anyone_can_register_multiple_clients_2"',
        ],
        "description": "Uses hardcoded client name",
    },
    {
        "file": "test_register_security.py",
        "matches": [
            '"client_name": "TEST test_register_is_public_endpoint"',
            '"client_name": "TEST test_register_ignores_authorization_headers"',
            '"client_name": "TEST test_security_enforced_at_authorization_stage"',
            '"client_name": "TEST test_register_with_valid_token_still_succeeds"',
            '"client_name": "TEST test_token_endpoint_requires_authentication"',
            '"client_name": "TEST test_anyone_can_register_multiple_clients_1"',
            '"client_name": "TEST test_anyone_can_register_multiple_clients_2"',
        ],
        "description": "Hardcoded client_name in JSON",
    },
    {
        "file": "test_rfc7592_compliance.py",
        "matches": [
            '"client_name": "TEST RFC 7592 GET Test Client"',
            '"client_name": "TEST Original Name"',
            '"client_name": "TEST Updated Name via RFC 7592"',
            '"client_name": "TEST Client to Delete"',
            '"client_name": "TEST Bearer Token Test"',
            '"client_name": "TEST Client 1"',
            '"client_name": "TEST Client 2"',
            '"client_name": "TEST Malformed Test Client"',
            '"client_name": "TEST Concurrent Test"',
            '"client_name": "TEST Lifetime Test Client"',
        ],
        "description": "Hardcoded client_name in JSON",
    },
    {
        "file": "test_rfc7592_security.py",
        "matches": [
            '"client_name": "TEST Bearer Rejection Test"',
            '"client_name": "TEST Edge Case Test"',
            '"client_name": "TEST Timing Test"',
            '"client_name": "TEST Rate Limit Test"',
            '"client_name": "TEST SQL Test Client"',
        ],
        "description": "Hardcoded client_name in JSON",
    },
    {
        "file": "test_rfc_compliance.py",
        "matches": [
            '"client_name": "TEST Test Client"',
            '"client_name": "TEST Test Client"',
            '"client_name": "TEST Test Client"',
        ],
        "description": "Hardcoded client_name in JSON",
    },
    {
        "file": "test_sacred_seals_compliance.py",
        "matches": ['"TEST test_redis_key_patterns_and_ttls"', '"TEST test_seal_of_dual_realms"'],
        "description": "Uses hardcoded client name",
    },
    {
        "file": "test_sacred_seals_compliance.py",
        "matches": [
            '"client_name": "TEST test_redis_key_patterns_and_ttls"',
            '"client_name": "TEST test_seal_of_dual_realms"',
        ],
        "description": "Hardcoded client_name in JSON",
    },
]

for update in updates:
    filepath = Path("tests") / update["file"]
    update_test_file(filepath, update.get("test_name"))
