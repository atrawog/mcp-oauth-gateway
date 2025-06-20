# Test Cleanup Guide - CLAUDE.md Compliant

## Sacred Test Naming Pattern

All tests MUST use the pattern `"TEST <actual_test_name>"` for client_name to enable automatic cleanup.

Replace `<actual_test_name>` with the actual name of your test function!

## The Divine Commands

```bash
# Show all test registrations (dry run)
just test-cleanup-show

# Preview what would be deleted
just test-cleanup

# Actually delete all test data (use with caution!)
just test-cleanup-execute
```

## Example Test Pattern

```python
# ❌ OLD WAY - No consistent pattern
async def test_oauth_flow(self):
    registration_data = {
        "client_name": "OAuth Test Client",  # Hard to identify as test data
        "redirect_uris": ["http://localhost:8080/callback"]
    }

# ✅ NEW WAY - Use actual test function name!
async def test_oauth_flow(self):
    registration_data = {
        "client_name": "TEST test_oauth_flow",  # Actual test name after "TEST "
        "redirect_uris": ["http://localhost:8080/callback"]
    }

# ✅ Another example with different test
async def test_client_registration(self):
    registration_data = {
        "client_name": "TEST test_client_registration",  # Matches function name
        "redirect_uris": ["http://localhost:8080/callback"]
    }
```

## Real Test Naming Examples

Based on actual test function names:

- `test_oauth_flow()` → `"TEST test_oauth_flow"`
- `test_registration_security()` → `"TEST test_registration_security"`
- `test_mcp_integration()` → `"TEST test_mcp_integration"`
- `test_claude_client_flow()` → `"TEST test_claude_client_flow"`
- `test_refresh_token_rotation()` → `"TEST test_refresh_token_rotation"`

## Important Notes

1. **Pattern is case-sensitive**: Must start with `"TEST "` (with space)
2. **Cleanup is aggressive**: Deletes the registration AND all associated tokens
3. **Use unique test names**: Helps identify which test created what data
4. **Run cleanup after test sessions**: Keeps Redis pure for next run

## Integration with CI/CD

Add to your test pipeline:

```yaml
# After running tests
- name: Cleanup test data
  run: just test-cleanup-execute
```

This ensures test data doesn't accumulate in your Redis instance!