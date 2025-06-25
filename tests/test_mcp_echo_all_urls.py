"""Test MCP Echo service across all configured URLs (echo, echo-a through echo-z).

This test file follows CLAUDE.md Sacred Commandments:
- NO MOCKING - Tests against real deployed mcp-echo service
- Tests ALL URLs configured in MCP_ECHO_URLS
- Ensures each hostname works correctly with OAuth authentication
"""

import pytest
import httpx


class TestMCPEchoAllUrls:
    """Test that all echo hostnames are properly configured and working."""

    def _parse_sse_response(self, sse_text: str) -> dict:
        """Parse SSE response to extract JSON data."""
        for line in sse_text.strip().split('\n'):
            if line.startswith('data: '):
                data_str = line[6:]  # Remove 'data: ' prefix
                if data_str and data_str != '[DONE]':
                    import json
                    return json.loads(data_str)
        raise ValueError("No valid data found in SSE response")

    @pytest.mark.asyncio
    async def test_all_echo_urls_accessible(
        self, http_client: httpx.AsyncClient, mcp_echo_urls: list, gateway_auth_headers: dict
    ):
        """Test that all echo URLs (echo, echo-a through echo-z) are accessible."""
        results = {}
        
        for url in mcp_echo_urls:
            # Test basic authentication requirement
            response = await http_client.post(
                url,
                json={
                    "jsonrpc": "2.0",
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2025-06-18",
                        "capabilities": {},
                        "clientInfo": {"name": "test-all-urls", "version": "1.0.0"}
                    },
                    "id": 1
                }
            )
            
            # Should require authentication
            assert response.status_code == 401, f"{url} should require authentication"
            
            # Test with authentication
            response = await http_client.post(
                url,
                json={
                    "jsonrpc": "2.0",
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2025-06-18",
                        "capabilities": {},
                        "clientInfo": {"name": "test-all-urls", "version": "1.0.0"}
                    },
                    "id": 1
                },
                headers={
                    **gateway_auth_headers,
                    "Accept": "application/json, text/event-stream",
                    "Content-Type": "application/json",
                    "MCP-Protocol-Version": "2025-06-18"
                }
            )
            
            assert response.status_code == 200, f"{url} should accept authenticated requests"
            
            # Parse and verify response
            data = self._parse_sse_response(response.text)
            assert data["jsonrpc"] == "2.0"
            assert data["id"] == 1
            assert "result" in data
            assert data["result"]["protocolVersion"] == "2025-06-18"
            
            # Extract hostname from URL for results
            hostname = url.split("//")[1].split("/")[0]
            results[hostname] = "✅ Working"
            
        # Print summary
        print(f"\n{'='*60}")
        print("MCP Echo URL Test Results:")
        print(f"{'='*60}")
        for hostname, status in sorted(results.items()):
            print(f"{hostname}: {status}")
        print(f"{'='*60}")
        print(f"Total URLs tested: {len(results)}")
        print(f"All URLs working: {'✅ Yes' if all('✅' in s for s in results.values()) else '❌ No'}")
        
        # Verify we tested all expected URLs
        assert len(results) == len(mcp_echo_urls), f"Expected to test {len(mcp_echo_urls)} URLs, but tested {len(results)}"
        
        # Verify we have echo plus echo-a through echo-z (27 total)
        expected_count = 27  # echo + 26 letters
        assert len(results) == expected_count, f"Expected {expected_count} URLs (echo + echo-a through echo-z), but found {len(results)}"

    @pytest.mark.asyncio
    async def test_echo_tool_on_random_urls(
        self, http_client: httpx.AsyncClient, mcp_echo_urls: list, gateway_auth_headers: dict
    ):
        """Test echo tool functionality on a random sample of URLs."""
        import random
        
        # Test on 5 random URLs to avoid excessive testing
        sample_urls = random.sample(mcp_echo_urls, min(5, len(mcp_echo_urls)))
        
        for url in sample_urls:
            # Initialize session
            init_response = await http_client.post(
                url,
                json={
                    "jsonrpc": "2.0",
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2025-06-18",
                        "capabilities": {},
                        "clientInfo": {"name": "test-echo-tool", "version": "1.0.0"}
                    },
                    "id": 1
                },
                headers={
                    **gateway_auth_headers,
                    "Accept": "application/json, text/event-stream",
                    "Content-Type": "application/json",
                    "MCP-Protocol-Version": "2025-06-18"
                }
            )
            
            assert init_response.status_code == 200
            
            # Call echo tool
            echo_response = await http_client.post(
                url,
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": "echo",
                        "arguments": {
                            "message": f"Testing {url}"
                        }
                    },
                    "id": 2
                },
                headers={
                    **gateway_auth_headers,
                    "Accept": "application/json, text/event-stream",
                    "Content-Type": "application/json",
                    "MCP-Protocol-Version": "2025-06-18"
                }
            )
            
            assert echo_response.status_code == 200
            
            # Verify echo response
            data = self._parse_sse_response(echo_response.text)
            assert data["jsonrpc"] == "2.0"
            assert data["id"] == 2
            assert "result" in data
            assert data["result"]["content"][0]["type"] == "text"
            assert f"Testing {url}" in data["result"]["content"][0]["text"]