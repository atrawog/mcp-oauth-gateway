# Client Name Update List

## Tests that need updating to follow "TEST <test_function_name>" pattern

### /home/atrawog/AI/atrawog/mcp-oauth-gateway/tests/test_mcp_client_oauth.py

1. **test_dynamic_client_registration** (line 37)
   - Current: `client_name = f"mcp-client-oauth-{secrets.token_urlsafe(8)}"`
   - Should be: `client_name = "TEST test_dynamic_client_registration"`

2. **test_client_registration_with_auth_token** (line 71)
   - Current: `client_name = f"mcp-auth-client-{secrets.token_urlsafe(8)}"`
   - Should be: `client_name = "TEST test_client_registration_with_auth_token"`

3. **test_authorization_code_flow_initiation** (line 103)
   - Current: `client_name = f"mcp-flow-test-{secrets.token_urlsafe(8)}"`
   - Should be: `client_name = "TEST test_authorization_code_flow_initiation"`

4. **test_pkce_flow_for_cli_clients** (line 143)
   - Current: `"client_name": "MCP CLI Client"`
   - Should be: `"client_name": "TEST test_pkce_flow_for_cli_clients"`

5. **test_token_refresh_flow** (line 186)
   - Current: `"client_name": "Refresh Test Client"`
   - Should be: `"client_name": "TEST test_token_refresh_flow"`

6. **test_token_introspection** (line 264)
   - Current: `"client_name": "Introspection Test Client"`
   - Should be: `"client_name": "TEST test_token_introspection"`

7. **test_credential_format** (line 304)
   - Current: `"client_name": "Storage Test Client"`
   - Should be: `"client_name": "TEST test_credential_format"`

8. **test_client_reregistration** (line 418)
   - Current: `client_name = "Persistent MCP Client"`
   - Should be: `client_name = "TEST test_client_reregistration"`

### /home/atrawog/AI/atrawog/mcp-oauth-gateway/tests/test_mcp_oauth_dynamicclient.py

9. **test_dynamic_client_registration_rfc7591** (line 78)
   - Current: `client_name = f"test-client-{secrets.token_urlsafe(8)}"`
   - Should be: `client_name = "TEST test_dynamic_client_registration_rfc7591"`

10. **test_client_registration_validation** (line 136)
    - Current: `json={"client_name": "Invalid Client"}`
    - Should be: `json={"client_name": "TEST test_client_registration_validation"}`

11. **test_authorization_endpoint_with_registered_client** (line 183)
    - Current: `client_name = f"auth-test-client-{secrets.token_urlsafe(8)}"`
    - Should be: `client_name = "TEST test_authorization_endpoint_with_registered_client"`

12. **test_redis_integration** (line 249)
    - Current: `client_name = f"redis-test-{secrets.token_urlsafe(8)}"`
    - Should be: `client_name = "TEST test_redis_integration"`

13. **test_pkce_support** (line 293)
    - Current: `"client_name": "PKCE Test Client"`
    - Should be: `"client_name": "TEST test_pkce_support"`

14. **test_concurrent_client_registrations** (line 353)
    - Current: `"client_name": f"Concurrent Client {index}"`
    - Should be: `"client_name": f"TEST test_concurrent_client_registrations {index}"`

15. **test_invalid_grant_types** (line 400)
    - Current: `"client_name": "Grant Type Test Client"`
    - Should be: `"client_name": "TEST test_invalid_grant_types"`

16. **test_full_oauth_flow_with_mcp_client** (line 439)
    - Current: `client_name = f"mcp-integration-{secrets.token_urlsafe(8)}"`
    - Should be: `client_name = "TEST test_full_oauth_flow_with_mcp_client"`

17. **test_auth_service_handles_invalid_tokens** (line 464)
    - Current: `"client_name": "Invalid Token Client"`
    - Should be: `"client_name": "TEST test_auth_service_handles_invalid_tokens"`

### /home/atrawog/AI/atrawog/mcp-oauth-gateway/tests/test_auth_error_paths.py

18. **test_registration_empty_redirect_uris** (line 80)
    - Current: `"client_name": "Test Client"`
    - Should be: `"client_name": "TEST test_registration_empty_redirect_uris"`

19. **test_create_token_with_user_tracking** (line 283)
    - Current: `"client_name": "User Tracking Test Client"`
    - Should be: `"client_name": "TEST test_create_token_with_user_tracking"`

### /home/atrawog/AI/atrawog/mcp-oauth-gateway/tests/test_coverage_gaps_specific.py

20. **test_registration_with_invalid_data** (line 70)
    - Current: `"client_name": TEST_CLIENT_NAME` (where TEST_CLIENT_NAME = "Test Client")
    - Should be: `"client_name": "TEST test_registration_with_invalid_data"`

### /home/atrawog/AI/atrawog/mcp-oauth-gateway/tests/test_registration_security.py

21. **test_register_endpoint_is_public** (line 54)
    - Current: `"client_name": "Public Registration Test Client"`
    - Should be: `"client_name": "TEST test_register_endpoint_is_public"`

22. **test_anyone_can_register_with_auth** (line 87)
    - Current: `"client_name": "Test App for Security Verification"`
    - Should be: `"client_name": "TEST test_anyone_can_register_with_auth"`

23. **test_registered_client_cannot_get_token_without_github_auth** (line 121)
    - Current: `"client_name": "Security Test Client"`
    - Should be: `"client_name": "TEST test_registered_client_cannot_get_token_without_github_auth"`

24. **test_authorization_requires_github_login** (line 160)
    - Current: `"client_name": "Auth Flow Test Client"`
    - Should be: `"client_name": "TEST test_authorization_requires_github_login"`

25. **test_oauth_flow_checks_allowed_users** (line 212)
    - Current: `"client_name": "User Restriction Test"`
    - Should be: `"client_name": "TEST test_oauth_flow_checks_allowed_users"`

26. **test_token_exchange_without_valid_code** (line 290)
    - Current: `"client_name": "Invalid Code Test"`
    - Should be: `"client_name": "TEST test_token_exchange_without_valid_code"`

### /home/atrawog/AI/atrawog/mcp-oauth-gateway/tests/test_mcp_fetch_complete.py

27. **test_mcp_fetch_actually_fetches_content** (line 26)
    - Current: `"client_name": f"{TEST_CLIENT_NAME} - Complete Flow Test"` (where TEST_CLIENT_NAME = "MCP Fetch Test Client")
    - Should be: `"client_name": "TEST test_mcp_fetch_actually_fetches_content"`

### /home/atrawog/AI/atrawog/mcp-oauth-gateway/tests/test_register_security.py

28. **test_register_is_public_endpoint** (line 18)
    - Current: `"client_name": "Test Client"`
    - Should be: `"client_name": "TEST test_register_is_public_endpoint"`

29. **test_register_ignores_authorization_headers** (line 43)
    - Current: `"client_name": "Test Client with Auth Header"`
    - Should be: `"client_name": "TEST test_register_ignores_authorization_headers"`

30. **test_security_enforced_at_authorization_stage** (line 67)
    - Current: `"client_name": "Security Test Client"`
    - Should be: `"client_name": "TEST test_security_enforced_at_authorization_stage"`

31. **test_register_with_valid_token_still_succeeds** (line 104)
    - Current: `"client_name": "Client With Valid Token"`
    - Should be: `"client_name": "TEST test_register_with_valid_token_still_succeeds"`

32. **test_token_endpoint_requires_authentication** (line 134)
    - Current: `"client_name": "Token Security Test Client"`
    - Should be: `"client_name": "TEST test_token_endpoint_requires_authentication"`

33. **test_multiple_clients_can_register_publicly** (line 167)
    - Current: `"client_name": f"Public Test Client {i}"`
    - Should be: `"client_name": f"TEST test_multiple_clients_can_register_publicly {i}"`

34. **test_anyone_can_register_multiple_clients** (line 202)
    - Current: `"client_name": "Bootstrap Test App 1"` (and others)
    - Should be: `"client_name": "TEST test_anyone_can_register_multiple_clients 1"` (etc.)

### /home/atrawog/AI/atrawog/mcp-oauth-gateway/tests/test_coverage_gaps.py

35. **test_client_registration_missing_redirect_uris** (line 36)
    - Current: `"client_name": "Test Client Without URIs"`
    - Should be: `"client_name": "TEST test_client_registration_missing_redirect_uris"`

### /home/atrawog/AI/atrawog/mcp-oauth-gateway/tests/test_sacred_seals_compliance.py

36. **test_dual_realms_architecture** (line 116)
    - Current: `"client_name": "Claude.ai MCP Client"`
    - Should be: `"client_name": "TEST test_dual_realms_architecture"`

### /home/atrawog/AI/atrawog/mcp-oauth-gateway/tests/test_oauth_flow.py

37. **test_client_registration_rfc7591** (line 37)
    - Current: `"client_name": "RFC 7591 Test Client"`
    - Should be: `"client_name": "TEST test_client_registration_rfc7591"`

### /home/atrawog/AI/atrawog/mcp-oauth-gateway/tests/test_additional_coverage.py

38. **test_token_endpoint_missing_client_credentials** (line 60)
    - Current: `"client_name": TEST_CLIENT_NAME` (where TEST_CLIENT_NAME = "Test Client")
    - Should be: `"client_name": "TEST test_token_endpoint_missing_client_credentials"`

## Summary

Total number of tests that need updating: **38**

All these tests should have their `client_name` values updated to follow the pattern `"TEST <test_function_name>"` to ensure unique and identifiable client names in the test suite.