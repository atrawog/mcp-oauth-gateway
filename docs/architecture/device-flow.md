# GitHub Device Flow (RFC 8628)

The MCP OAuth Gateway implements GitHub Device Flow for scenarios where browser-based authentication is not practical or possible.

## What is Device Flow?

Device Flow is an OAuth 2.0 extension ([RFC 8628](https://datatracker.ietf.org/doc/html/rfc8628)) designed for devices that either:
- Lack a browser (CLI tools, IoT devices)
- Have limited input capabilities
- Cannot receive redirect callbacks

Instead of redirecting to an authorization server, the device displays a code that users manually enter on another device.

## When the Gateway Uses Device Flow

The gateway uses GitHub Device Flow in **two specific scenarios**:

### 1. Gateway Self-Authentication

When the gateway itself needs a GitHub Personal Access Token (PAT):

```bash
just generate-github-token
```

**Purpose**: Obtain a GitHub PAT for the gateway's own operations
**Stored as**: `GITHUB_PAT` in `.env`
**Used for**: GitHub API calls by the gateway

### 2. MCP Client Authentication

When MCP clients need OAuth tokens without browser access:

```bash
just mcp-client-token
```

**Purpose**: Generate OAuth tokens for MCP clients (like CLI tools)
**Stored as**: `MCP_CLIENT_ACCESS_TOKEN` in `.env`
**Used by**: `mcp-streamablehttp-client` and similar tools

## How Device Flow Works

### Step-by-Step Process

1. **Device Code Request**
   ```
   POST https://github.com/login/device/code
   Content: client_id=GITHUB_CLIENT_ID&scope=user:email
   ```

2. **User Code Display**
   ```
   Gateway shows:
   ┌─────────────────────────────────────┐
   │ Visit: https://github.com/login/device │
   │ Enter code: ABCD-1234              │
   └─────────────────────────────────────┘
   ```

3. **User Authorization**
   - User visits the URL on any device with a browser
   - Enters the provided code
   - Authorizes the application

4. **Token Polling**
   ```
   POST https://github.com/login/oauth/access_token
   Content: client_id=...&device_code=...&grant_type=urn:ietf:params:oauth:grant-type:device_code
   ```
   - Gateway polls every 5-15 seconds
   - Continues until authorized or timeout

5. **Token Receipt**
   - GitHub returns access token upon authorization
   - Gateway stores token in `.env`

### Implementation Details

From `scripts/generate_oauth_token.py`:

```python
async def github_device_flow() -> str:
    # 1. Request device code
    response = await client.post(
        "https://github.com/login/device/code",
        data={"client_id": github_client_id, "scope": "user:email"}
    )

    # 2. Display code to user
    print(f"Visit: {device_data['verification_uri']}")
    print(f"Enter code: {device_data['user_code']}")

    # 3. Poll for authorization
    while True:
        poll_response = await client.post(
            "https://github.com/login/oauth/access_token",
            data={
                "client_id": github_client_id,
                "device_code": device_data["device_code"],
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code"
            }
        )
        if "access_token" in poll_response:
            return poll_response["access_token"]
```

## Device Flow vs Browser Flow

| Aspect | Device Flow | Browser Flow |
|--------|-------------|--------------|
| **User Experience** | Manual code entry | Automatic redirect |
| **Browser Required** | No (on device) | Yes |
| **Use Cases** | CLI tools, setup scripts | Web apps, Claude.ai |
| **Implementation** | Polling-based | Callback-based |
| **Security** | Code expires quickly | State parameter protection |
| **Gateway Usage** | Setup & CLI tools | End-user authentication |

## Security Considerations

### Device Flow Security

1. **Short-lived codes**: User codes expire in 15 minutes
2. **Rate limiting**: Polling intervals enforced
3. **Code complexity**: 8-character alphanumeric codes
4. **No URL exposure**: No redirect URIs in play

### Best Practices

1. **Clear instructions**: Display verification URL prominently
2. **Auto-open browser**: Attempt to open the URL automatically
3. **Timeout handling**: Stop polling after reasonable time
4. **Error messages**: Clear feedback on authorization status

## Error Handling

Common device flow errors:

| Error | Meaning | Action |
|-------|---------|--------|
| `authorization_pending` | User hasn't authorized yet | Continue polling |
| `slow_down` | Polling too fast | Increase interval |
| `expired_token` | Code expired | Request new code |
| `access_denied` | User declined | Stop polling |

## Configuration

Device flow behavior can be configured:

```env
# Polling interval (seconds)
DEVICE_FLOW_INTERVAL=5

# Maximum polling duration (seconds)
DEVICE_FLOW_TIMEOUT=900

# Auto-open browser
DEVICE_FLOW_AUTO_BROWSER=true
```

## Related Documentation

- [OAuth Flow Overview](oauth-flow.md) - Complete OAuth architecture
- [Token Management](../usage/token-management.md) - Managing generated tokens
- [GitHub OAuth Setup](../installation/github-oauth.md) - GitHub app configuration
