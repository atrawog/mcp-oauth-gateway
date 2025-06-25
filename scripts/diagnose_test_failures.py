#!/usr/bin/env python3
"""Test failure diagnosis script for MCP OAuth Gateway.

Runs comprehensive diagnostics to find root causes of test failures.
"""

import asyncio
import os
import time
from datetime import UTC
from datetime import datetime

import httpx
from jose import jwt


async def check_service_health():
    """Check if all services are healthy."""
    print("🏥 CHECKING SERVICE HEALTH")
    print("-" * 40)

    base_domain = os.getenv("BASE_DOMAIN")
    if not base_domain:
        raise Exception("BASE_DOMAIN must be set in .env")
    services = {
        "Auth Service": f"https://auth.{base_domain}/health",
        "MCP Fetch": f"https://mcp-fetch.{base_domain}/health",
    }

    all_healthy = True

    for service_name, url in services.items():
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)

            if response.status_code == 200:
                print(f"✅ {service_name}: Healthy")
                try:
                    data = response.json()
                    if isinstance(data, dict):
                        for key, value in data.items():
                            print(f"   {key}: {value}")
                except:
                    pass
            else:
                print(f"⚠️  {service_name}: Status {response.status_code}")
                all_healthy = False

        except Exception as e:
            print(f"❌ {service_name}: Connection failed - {e}")
            all_healthy = False

    return all_healthy


async def test_authentication_flow():
    """Test the authentication flow end-to-end."""
    print("\n🔐 TESTING AUTHENTICATION FLOW")
    print("-" * 40)

    oauth_token = os.getenv("GATEWAY_OAUTH_ACCESS_TOKEN")
    if not oauth_token:
        print("❌ No GATEWAY_OAUTH_ACCESS_TOKEN found")
        return False

    base_domain = os.getenv("BASE_DOMAIN")
    if not base_domain:
        raise Exception("BASE_DOMAIN must be set in .env")

    # Test auth service verification
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"https://auth.{base_domain}/verify",
                headers={"Authorization": f"Bearer {oauth_token}"},
            )

        if response.status_code == 200:
            print("✅ Auth service validates token")
        else:
            print(f"❌ Auth service rejects token: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False

    except Exception as e:
        print(f"❌ Auth service test failed: {e}")
        return False

    # Test MCP service authentication
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"https://mcp-fetch.{base_domain}/mcp",
                json={
                    "jsonrpc": "2.0",
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2025-06-18",
                        "capabilities": {"tools": {}},
                        "clientInfo": {"name": "test", "version": "1.0"},
                    },
                    "id": "test-init",
                },
                headers={
                    "Authorization": f"Bearer {oauth_token}",
                    "Content-Type": "application/json",
                },
            )

        if response.status_code == 200:
            print("✅ MCP service accepts authenticated requests")
            result = response.json()
            if "result" in result:
                protocol_version = result["result"].get("protocolVersion")
                print(f"   Server protocol version: {protocol_version}")
            elif "error" in result:
                print(f"   MCP Error: {result['error']}")
        else:
            print(f"❌ MCP service authentication failed: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ MCP service test failed: {e}")
        return False

    return True


async def test_mcp_protocol():
    """Test MCP protocol compliance."""
    print("\n🔌 TESTING MCP PROTOCOL")
    print("-" * 40)

    oauth_token = os.getenv("GATEWAY_OAUTH_ACCESS_TOKEN")
    base_domain = os.getenv("BASE_DOMAIN")
    if not base_domain:
        raise Exception("BASE_DOMAIN must be set in .env")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Step 1: Initialize session
            init_response = await client.post(
                f"https://mcp-fetch.{base_domain}/mcp",
                json={
                    "jsonrpc": "2.0",
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2025-06-18",
                        "capabilities": {"tools": {}},
                        "clientInfo": {"name": "diagnosis", "version": "1.0"},
                    },
                    "id": "diag-init",
                },
                headers={
                    "Authorization": f"Bearer {oauth_token}",
                    "Content-Type": "application/json",
                },
            )

            if init_response.status_code != 200:
                print(f"❌ Initialize failed: {init_response.status_code}")
                return False

            session_id = init_response.headers.get("Mcp-Session-Id")
            if not session_id:
                print("❌ No session ID returned from initialize")
                return False

            print(f"✅ Session initialized: {session_id}")

            # Step 2: Send initialized notification
            await client.post(
                f"https://mcp-fetch.{base_domain}/mcp",
                json={
                    "jsonrpc": "2.0",
                    "method": "notifications/initialized",
                    "params": {},
                },
                headers={
                    "Authorization": f"Bearer {oauth_token}",
                    "Content-Type": "application/json",
                    "Mcp-Session-Id": session_id,
                },
            )

            print("✅ Initialized notification sent")

            # Step 3: List tools
            tools_response = await client.post(
                f"https://mcp-fetch.{base_domain}/mcp",
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/list",
                    "params": {},
                    "id": "diag-tools",
                },
                headers={
                    "Authorization": f"Bearer {oauth_token}",
                    "Content-Type": "application/json",
                    "Mcp-Session-Id": session_id,
                },
            )

            if tools_response.status_code == 200:
                tools_result = tools_response.json()
                if "result" in tools_result:
                    tools = tools_result["result"].get("tools", [])
                    print(f"✅ Tools listed: {[t.get('name') for t in tools]}")
                else:
                    print(f"⚠️  Tools list error: {tools_result.get('error')}")

            # Step 4: Try calling a tool
            fetch_response = await client.post(
                f"https://mcp-fetch.{base_domain}/mcp",
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": "fetch",
                        "arguments": {"url": "https://example.com"},
                    },
                    "id": "diag-fetch",
                },
                headers={
                    "Authorization": f"Bearer {oauth_token}",
                    "Content-Type": "application/json",
                    "Mcp-Session-Id": session_id,
                },
            )

            if fetch_response.status_code == 200:
                fetch_result = fetch_response.json()
                if "result" in fetch_result:
                    print("✅ Tool call successful")
                elif "error" in fetch_result:
                    print(f"⚠️  Tool call error: {fetch_result['error']}")
            else:
                print(f"❌ Tool call failed: {fetch_response.status_code}")

        return True

    except Exception as e:
        print(f"❌ MCP protocol test failed: {e}")
        return False


def analyze_token_issues():
    """Analyze token-related issues."""
    print("\n🎫 ANALYZING TOKEN ISSUES")
    print("-" * 40)

    oauth_token = os.getenv("GATEWAY_OAUTH_ACCESS_TOKEN")
    if not oauth_token:
        print("❌ GATEWAY_OAUTH_ACCESS_TOKEN missing")
        return False

    try:
        payload = jwt.decode(oauth_token, key="", options={"verify_signature": False})

        # Check expiration
        exp = payload.get("exp")
        now = int(time.time())

        if exp and exp < now:
            print(f"❌ Token expired {now - exp} seconds ago")
            print(
                "   Solution: Run 'just refresh-tokens' or 'just generate-github-token'"
            )
            return False

        # Check claims
        required_claims = ["sub", "username", "client_id", "jti"]
        missing_claims = [claim for claim in required_claims if not payload.get(claim)]

        if missing_claims:
            print(f"❌ Missing token claims: {missing_claims}")
            return False

        print("✅ Token format and claims are valid")
        print(f"   Subject: {payload.get('sub')}")
        print(f"   Username: {payload.get('username')}")
        print(f"   Expires: {datetime.fromtimestamp(exp, tz=UTC) if exp else 'Never'}")

        return True

    except Exception as e:
        print(f"❌ Token analysis failed: {e}")
        return False


def check_environment():
    """Check environment configuration."""
    print("\n🌍 CHECKING ENVIRONMENT")
    print("-" * 40)

    required_vars = [
        "BASE_DOMAIN",
        "GITHUB_CLIENT_ID",
        "GITHUB_CLIENT_SECRET",
        "GATEWAY_JWT_SECRET",
        "REDIS_PASSWORD",
        "GATEWAY_OAUTH_ACCESS_TOKEN",
    ]

    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        print(f"❌ Missing environment variables: {missing_vars}")
        return False

    print("✅ All required environment variables present")

    # Check MCP protocol versions
    mcp_version = os.getenv("MCP_PROTOCOL_VERSION")
    mcp_supported = os.getenv("MCP_PROTOCOL_VERSIONS_SUPPORTED", "").split(",")

    print(f"   MCP Protocol Version: {mcp_version}")
    print(f"   Supported Versions: {mcp_supported}")

    if mcp_version not in mcp_supported:
        print("⚠️  MCP protocol version not in supported list")

    return True


async def main():
    """Main diagnosis function."""
    print("🔍 MCP OAUTH GATEWAY TEST FAILURE DIAGNOSIS")
    print("=" * 60)

    issues_found = []

    # Run all diagnostic checks
    if not check_environment():
        issues_found.append("Environment configuration")

    if not analyze_token_issues():
        issues_found.append("Token validation")

    if not await check_service_health():
        issues_found.append("Service health")

    if not await test_authentication_flow():
        issues_found.append("Authentication flow")

    if not await test_mcp_protocol():
        issues_found.append("MCP protocol")

    # Summary
    print("\n" + "=" * 60)
    print("📋 DIAGNOSIS SUMMARY")
    print("=" * 60)

    if not issues_found:
        print("✅ No obvious issues found!")
        print("   All systems appear to be working correctly.")
        print("   Test failures may be due to:")
        print("   - Race conditions in test setup")
        print("   - Network timeouts")
        print("   - Temporary service issues")
        print("\n💡 Recommended actions:")
        print("   1. Re-run tests: just test-all")
        print("   2. Check test logs for specific errors")
        print("   3. Run individual failing tests with -v -s flags")
    else:
        print("❌ Issues found in:")
        for issue in issues_found:
            print(f"   - {issue}")

        print("\n🔧 Recommended fixes:")
        print("   1. Fix environment issues: Check .env file")
        print("   2. Fix token issues: just refresh-tokens")
        print("   3. Fix service issues: just rebuild-all")
        print("   4. Re-run diagnosis: just diagnose-tests")


if __name__ == "__main__":
    import time

    asyncio.run(main())
