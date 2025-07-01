# 🔥 MCP Echo StreamableHTTP Server - Stateful Edition Divine Documentation ⚡

**⚡ THE DIVINE STATEFUL ECHO SERVER - VS CODE COMPATIBLE SESSION MANAGEMENT! ⚡**

## Sacred Purpose

**🔥 Behold! The stateful echo server that maintains divine session continuity! ⚡**

This blessed implementation provides:
- **Session Management** - Persistent state across multiple requests!
- **Message Queuing** - Divine message buffering for async clients!
- **VS Code Integration** - Perfect compatibility with stateful clients!
- **11 Debug Tools** - Including stateful tools like replayLastEcho!
- **Full MCP Compliance** - Protocol 2025-06-18 with session support!

## The Divine Architecture

### 🏗️ Session Management - The Sacred State Keeper!

**⚡ The SessionManager class - Divine memory across requests! ⚡**

```python
SessionManager:
  - sessions: dict[str, dict[str, Any]]  # Active sessions storage!
  - message_queues: dict[str, deque]     # Per-session message queues!
  - session_timeout: int = 3600          # 1 hour default lifetime!
  - Background cleanup task              # Expired session reaper!
```

**Session Lifecycle:**
1. **Creation** - New UUID4 session ID on first initialize
2. **Activity** - Updated last_activity on each request
3. **Storage** - Client info, protocol version, custom state
4. **Cleanup** - Automatic expiration after timeout
5. **Death** - Session and queue removal

### 🌊 StreamableHTTP Transport - Stateful Glory!

**⚡ Two divine endpoints for stateful communication! ⚡**

**POST /mcp - The Command Gateway:**
- Accepts JSON-RPC 2.0 requests
- Creates sessions on initialize
- Returns Mcp-Session-Id header
- Queues messages for SSE clients

**GET /mcp - The Message Poller:**
- Requires Mcp-Session-Id header
- Returns queued messages as SSE stream
- Keep-alive pings when queue empty
- Maintains session activity

### 🔧 The 11 Sacred Debug Tools

**⚡ Each tool blessed with divine debugging powers! ⚡**

1. **echo** - Echo with session context prefix!
   - Stores message in session for replay
   - Shows session ID and client name

2. **replayLastEcho** - THE STATEFUL EXCLUSIVE!
   - Retrieves last echo from session memory
   - Requires valid session to function
   - Proves stateful implementation!

3. **printHeader** - Categorized header display!
   - Traefik headers
   - Authentication headers
   - Regular headers
   - Alphabetical listing

4. **bearerDecode** - JWT token analysis!
   - Header and payload decoding
   - Time claim calculations
   - Custom claim extraction
   - No signature verification

5. **authContext** - OAuth context display!
   - Bearer token presence
   - OAuth header extraction
   - User identification

6. **requestTiming** - Performance metrics!
   - Request elapsed time
   - Performance indicators
   - Session age tracking

7. **corsAnalysis** - CORS configuration!
   - Notes Traefik handles CORS
   - Origin header detection

8. **environmentDump** - Config display!
   - MCP configuration vars
   - Secret redaction option
   - Session timeout display

9. **healthProbe** - Deep health check!
   - Service status
   - Active session count
   - Session statistics

10. **sessionInfo** - Session statistics!
    - Current session details
    - All active sessions list
    - Server statistics
    - Queue status

11. **whoIStheGOAT** - Excellence analyzer!
    - Extracts user from JWT/headers
    - AI-powered analysis
    - Session-aware results

## Configuration Commandments

**⚡ Environment variables control divine behavior! ⚡**

```bash
MCP_ECHO_HOST=0.0.0.0                    # Bind to all interfaces
MCP_ECHO_PORT=3000                       # Divine port number
MCP_ECHO_DEBUG=true                      # Enable sacred logging
MCP_SESSION_TIMEOUT=3600                 # Session lifetime seconds
MCP_PROTOCOL_VERSION=2025-06-18          # Protocol compliance
MCP_PROTOCOL_VERSIONS_SUPPORTED=2025-06-18,2025-03-26,2024-11-05  # Multi-version support
```

## Divine Docker Integration

**🐳 Container deployment with divine isolation! ⚡**

```yaml
healthcheck:
  test: Protocol-compliant initialization handshake
  interval: 30s
  timeout: 5s
  retries: 3
```

**The health check performs actual MCP protocol validation!**

## Sacred Session Features

### Message Queuing - Async Client Support!

**⚡ Per-session message queues with overflow protection! ⚡**

- MAX_MESSAGE_QUEUE_SIZE = 100
- FIFO queue with automatic overflow handling
- GET /mcp drains queue completely
- SSE format for streaming delivery

### Session Context - Stateful Memory!

**⚡ Sessions store divine context! ⚡**

```python
session = {
    "created_at": time.time(),
    "last_activity": time.time(),
    "initialized": bool,
    "protocol_version": str,
    "client_info": dict,
    "last_echo_message": str,  # Custom state example!
}
```

### Background Cleanup - Memory Guardian!

**⚡ Automatic expired session removal! ⚡**

- Runs every 60 seconds
- Removes sessions older than timeout
- Clears associated message queues
- Prevents memory leaks

## VS Code Integration Excellence

**🎨 Perfect compatibility with VS Code MCP client! ⚡**

1. **Session Persistence** - Maintains state across requests
2. **Message Buffering** - Handles async communication
3. **SSE Support** - Streaming responses for real-time updates
4. **Protocol Compliance** - Full 2025-06-18 specification

## The Divine Truth

**⚡ This is the ONLY stateful MCP echo server in the gateway! ⚡**

All other echo servers are stateless! This implementation proves:
- Session management capabilities
- Message queuing architecture
- Stateful tool implementation
- VS Code compatibility patterns

**May your sessions persist, your queues never overflow, and your state remain consistent! ⚡**
