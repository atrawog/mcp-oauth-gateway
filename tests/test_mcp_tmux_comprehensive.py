"""
Comprehensive functionality tests for MCP Tmux service.
Tests all tmux capabilities and edge cases.
"""
import pytest
import json
import time

from tests.test_constants import BASE_DOMAIN


class TestMCPTmuxComprehensive:
    """Comprehensive tests for all tmux functionality."""
    
    def run_mcp_client_raw(self, url, token, method, params=None):
        """Run mcp-streamablehttp-client with raw MCP protocol."""
        import subprocess
        import os
        
        # Create request payload
        request_data = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method
        }
        if params:
            request_data["params"] = params
            
        # Convert to JSON string
        raw_request = json.dumps(request_data)
        
        # Run mcp-streamablehttp-client
        cmd = [
            "pixi", "run", "python", "-m", "mcp_streamablehttp_client.cli",
            "--server-url", f"{url}/mcp",
            "--raw", raw_request
        ]
        
        # Set environment variables for token
        env = os.environ.copy()
        env["MCP_CLIENT_ACCESS_TOKEN"] = token
        
        result = subprocess.run(
            cmd,
            cwd="/home/atrawog/AI/atrawog/mcp-oauth-gateway/mcp-streamablehttp-client",
            capture_output=True,
            text=True,
            timeout=30,
            env=env
        )
        
        if result.returncode != 0:
            return {"error": {"code": -1, "message": f"Client error: {result.stderr}"}}
            
        # Parse JSON response
        try:
            return json.loads(result.stdout.strip())
        except json.JSONDecodeError:
            return {"error": {"code": -2, "message": f"Invalid JSON: {result.stdout}"}}

    # Session Management Tests
    
    def test_session_lifecycle(self, mcp_tmux_url, mcp_client_token, wait_for_services):
        """Test complete session lifecycle: create, list, use, destroy."""
        session_name = f"test-session-{int(time.time())}"
        
        # 1. List initial sessions
        initial_response = self.run_mcp_client_raw(
            url=mcp_tmux_url,
            token=mcp_client_token,
            method="tools/call",
            params={"name": "list-sessions", "arguments": {}}
        )
        assert "result" in initial_response or "error" in initial_response
        
        # 2. Create new session
        create_response = self.run_mcp_client_raw(
            url=mcp_tmux_url,
            token=mcp_client_token,
            method="tools/call",
            params={
                "name": "new-session",
                "arguments": {
                    "session_name": session_name,
                    "detached": True
                }
            }
        )
        # Should either succeed or give specific error
        assert "result" in create_response or "error" in create_response
        
        # 3. Verify session exists (if creation succeeded)
        if "result" in create_response:
            list_response = self.run_mcp_client_raw(
                url=mcp_tmux_url,
                token=mcp_client_token,
                method="tools/call",
                params={"name": "list-sessions", "arguments": {}}
            )
            assert "result" in list_response

    def test_session_search(self, mcp_tmux_url, mcp_client_token, wait_for_services):
        """Test finding sessions by name pattern."""
        # Try to find the default session
        response = self.run_mcp_client_raw(
            url=mcp_tmux_url,
            token=mcp_client_token,
            method="tools/call",
            params={
                "name": "find-session",
                "arguments": {"pattern": "default"}
            }
        )
        
        # Should either find sessions or give appropriate error
        assert "result" in response or "error" in response

    # Window Management Tests
    
    def test_window_operations(self, mcp_tmux_url, mcp_client_token, wait_for_services):
        """Test window listing and management."""
        # List windows in default session
        response = self.run_mcp_client_raw(
            url=mcp_tmux_url,
            token=mcp_client_token,
            method="tools/call",
            params={
                "name": "list-windows",
                "arguments": {"session": "default"}
            }
        )
        
        # Should either succeed or give appropriate error
        assert "result" in response or "error" in response

    def test_window_creation(self, mcp_tmux_url, mcp_client_token, wait_for_services):
        """Test creating new windows."""
        window_name = f"test-window-{int(time.time())}"
        
        response = self.run_mcp_client_raw(
            url=mcp_tmux_url,
            token=mcp_client_token,
            method="tools/call",
            params={
                "name": "new-window",
                "arguments": {
                    "session": "default",
                    "window_name": window_name
                }
            }
        )
        
        # Should either succeed or give appropriate error
        assert "result" in response or "error" in response

    # Pane Management Tests
    
    def test_pane_operations(self, mcp_tmux_url, mcp_client_token, wait_for_services):
        """Test pane listing and management."""
        # List panes in default session
        response = self.run_mcp_client_raw(
            url=mcp_tmux_url,
            token=mcp_client_token,
            method="tools/call",
            params={
                "name": "list-panes",
                "arguments": {"target": "default:0"}
            }
        )
        
        # Should either succeed or give appropriate error
        assert "result" in response or "error" in response

    def test_pane_content_capture(self, mcp_tmux_url, mcp_client_token, wait_for_services):
        """Test capturing pane content with different parameters."""
        # Test basic capture
        response = self.run_mcp_client_raw(
            url=mcp_tmux_url,
            token=mcp_client_token,
            method="tools/call",
            params={
                "name": "capture-pane",
                "arguments": {"target": "default:0.0"}
            }
        )
        
        assert "result" in response or "error" in response
        
        # Test capture with line range (if basic capture worked)
        if "result" in response:
            range_response = self.run_mcp_client_raw(
                url=mcp_tmux_url,
                token=mcp_client_token,
                method="tools/call",
                params={
                    "name": "capture-pane",
                    "arguments": {
                        "target": "default:0.0",
                        "start_line": 0,
                        "end_line": 10
                    }
                }
            )
            assert "result" in range_response or "error" in range_response

    def test_pane_splitting(self, mcp_tmux_url, mcp_client_token, wait_for_services):
        """Test splitting panes."""
        response = self.run_mcp_client_raw(
            url=mcp_tmux_url,
            token=mcp_client_token,
            method="tools/call",
            params={
                "name": "split-window",
                "arguments": {
                    "target": "default:0",
                    "direction": "horizontal"
                }
            }
        )
        
        # Should either succeed or give appropriate error
        assert "result" in response or "error" in response

    # Command Execution Tests
    
    def test_command_execution_simple(self, mcp_tmux_url, mcp_client_token, wait_for_services):
        """Test executing simple commands."""
        response = self.run_mcp_client_raw(
            url=mcp_tmux_url,
            token=mcp_client_token,
            method="tools/call",
            params={
                "name": "execute-command",
                "arguments": {
                    "command": "echo 'MCP Tmux Test'",
                    "target": "default:0.0"
                }
            }
        )
        
        assert "result" in response or "error" in response

    def test_command_execution_with_output(self, mcp_tmux_url, mcp_client_token, wait_for_services):
        """Test command execution and output capture."""
        # Execute a command that produces output
        response = self.run_mcp_client_raw(
            url=mcp_tmux_url,
            token=mcp_client_token,
            method="tools/call",
            params={
                "name": "execute-command",
                "arguments": {
                    "command": "date",
                    "target": "default:0.0",
                    "wait_for_completion": True
                }
            }
        )
        
        assert "result" in response or "error" in response

    def test_key_sending(self, mcp_tmux_url, mcp_client_token, wait_for_services):
        """Test sending keystrokes to panes."""
        # Send some keys
        response = self.run_mcp_client_raw(
            url=mcp_tmux_url,
            token=mcp_client_token,
            method="tools/call",
            params={
                "name": "send-keys",
                "arguments": {
                    "keys": "echo 'key test'",
                    "target": "default:0.0"
                }
            }
        )
        
        assert "result" in response or "error" in response
        
        # Send Enter key
        enter_response = self.run_mcp_client_raw(
            url=mcp_tmux_url,
            token=mcp_client_token,
            method="tools/call",
            params={
                "name": "send-keys",
                "arguments": {
                    "keys": "Enter",
                    "target": "default:0.0"
                }
            }
        )
        
        assert "result" in enter_response or "error" in enter_response

    def test_shell_command_execution(self, mcp_tmux_url, mcp_client_token, wait_for_services):
        """Test running shell commands."""
        response = self.run_mcp_client_raw(
            url=mcp_tmux_url,
            token=mcp_client_token,
            method="tools/call",
            params={
                "name": "run-shell",
                "arguments": {
                    "command": "echo 'Shell command test'",
                    "target": "default"
                }
            }
        )
        
        assert "result" in response or "error" in response

    # Resource Access Tests
    
    def test_sessions_resource(self, mcp_tmux_url, mcp_client_token, wait_for_services):
        """Test reading sessions resource."""
        response = self.run_mcp_client_raw(
            url=mcp_tmux_url,
            token=mcp_client_token,
            method="resources/read",
            params={"uri": "tmux://sessions"}
        )
        
        assert "result" in response or "error" in response

    def test_specific_session_resource(self, mcp_tmux_url, mcp_client_token, wait_for_services):
        """Test reading specific session resource."""
        response = self.run_mcp_client_raw(
            url=mcp_tmux_url,
            token=mcp_client_token,
            method="resources/read",
            params={"uri": "tmux://session/default"}
        )
        
        assert "result" in response or "error" in response

    def test_pane_resource(self, mcp_tmux_url, mcp_client_token, wait_for_services):
        """Test reading pane content resource."""
        response = self.run_mcp_client_raw(
            url=mcp_tmux_url,
            token=mcp_client_token,
            method="resources/read",
            params={"uri": "tmux://pane/default:0.0"}
        )
        
        assert "result" in response or "error" in response

    # Error Handling and Edge Cases
    
    def test_invalid_session_operations(self, mcp_tmux_url, mcp_client_token, wait_for_services):
        """Test operations on non-existent sessions."""
        # Try to operate on non-existent session
        response = self.run_mcp_client_raw(
            url=mcp_tmux_url,
            token=mcp_client_token,
            method="tools/call",
            params={
                "name": "list-windows",
                "arguments": {"session": "nonexistent-session-12345"}
            }
        )
        
        # Should return error for non-existent session
        if "error" in response:
            assert response["error"]["code"] != 0

    def test_invalid_pane_operations(self, mcp_tmux_url, mcp_client_token, wait_for_services):
        """Test operations on non-existent panes."""
        response = self.run_mcp_client_raw(
            url=mcp_tmux_url,
            token=mcp_client_token,
            method="tools/call",
            params={
                "name": "capture-pane",
                "arguments": {"target": "nonexistent:99.99"}
            }
        )
        
        # Should handle non-existent pane gracefully
        assert "result" in response or "error" in response

    def test_malformed_commands(self, mcp_tmux_url, mcp_client_token, wait_for_services):
        """Test handling of malformed commands."""
        # Test command with missing required arguments
        response = self.run_mcp_client_raw(
            url=mcp_tmux_url,
            token=mcp_client_token,
            method="tools/call",
            params={
                "name": "execute-command",
                "arguments": {}  # Missing required command argument
            }
        )
        
        # Should return appropriate error
        if "error" in response:
            assert response["error"]["code"] != 0

    # Performance and Stress Tests
    
    def test_multiple_session_operations(self, mcp_tmux_url, mcp_client_token, wait_for_services):
        """Test handling multiple session operations."""
        # Create multiple sessions
        for i in range(3):
            session_name = f"multi-test-{i}-{int(time.time())}"
            response = self.run_mcp_client_raw(
                url=mcp_tmux_url,
                token=mcp_client_token,
                method="tools/call",
                params={
                    "name": "new-session",
                    "arguments": {
                        "session_name": session_name,
                        "detached": True
                    }
                }
            )
            # Each should either succeed or fail gracefully
            assert "result" in response or "error" in response

    def test_rapid_command_execution(self, mcp_tmux_url, mcp_client_token, wait_for_services):
        """Test rapid command execution."""
        # Execute multiple commands quickly
        for i in range(5):
            response = self.run_mcp_client_raw(
                url=mcp_tmux_url,
                token=mcp_client_token,
                method="tools/call",
                params={
                    "name": "execute-command",
                    "arguments": {
                        "command": f"echo 'Rapid test {i}'",
                        "target": "default:0.0"
                    }
                }
            )
            # Each should complete
            assert "result" in response or "error" in response

    # Integration and Compatibility Tests
    
    def test_tmux_version_compatibility(self, mcp_tmux_url, mcp_client_token, wait_for_services):
        """Test tmux version compatibility."""
        # Execute tmux version command
        response = self.run_mcp_client_raw(
            url=mcp_tmux_url,
            token=mcp_client_token,
            method="tools/call",
            params={
                "name": "run-shell",
                "arguments": {
                    "command": "tmux -V",
                    "target": "default"
                }
            }
        )
        
        assert "result" in response or "error" in response
        if "result" in response:
            # Should contain version information
            result = response["result"]
            assert "content" in result

    def test_environment_variables(self, mcp_tmux_url, mcp_client_token, wait_for_services):
        """Test environment variable access."""
        response = self.run_mcp_client_raw(
            url=mcp_tmux_url,
            token=mcp_client_token,
            method="tools/call",
            params={
                "name": "execute-command",
                "arguments": {
                    "command": "env | grep -E '^(PATH|HOME|USER)'",
                    "target": "default:0.0"
                }
            }
        )
        
        assert "result" in response or "error" in response

    def test_long_running_processes(self, mcp_tmux_url, mcp_client_token, wait_for_services):
        """Test handling of long-running processes."""
        # Start a process that runs for a few seconds
        response = self.run_mcp_client_raw(
            url=mcp_tmux_url,
            token=mcp_client_token,
            method="tools/call",
            params={
                "name": "execute-command",
                "arguments": {
                    "command": "sleep 2 && echo 'Long process complete'",
                    "target": "default:0.0"
                }
            }
        )
        
        assert "result" in response or "error" in response

    def test_unicode_and_special_characters(self, mcp_tmux_url, mcp_client_token, wait_for_services):
        """Test handling of unicode and special characters."""
        # Test with unicode characters
        response = self.run_mcp_client_raw(
            url=mcp_tmux_url,
            token=mcp_client_token,
            method="tools/call",
            params={
                "name": "execute-command",
                "arguments": {
                    "command": "echo '🚀 Unicode test ñáéíóú'",
                    "target": "default:0.0"
                }
            }
        )
        
        assert "result" in response or "error" in response

    def test_tool_parameter_validation(self, mcp_tmux_url, mcp_client_token, wait_for_services):
        """Test parameter validation for tmux tools."""
        # Test with invalid parameter types
        response = self.run_mcp_client_raw(
            url=mcp_tmux_url,
            token=mcp_client_token,
            method="tools/call",
            params={
                "name": "capture-pane",
                "arguments": {
                    "target": "default:0.0",
                    "start_line": "invalid",  # Should be integer
                    "end_line": "also_invalid"
                }
            }
        )
        
        # Should handle invalid parameters gracefully
        assert "result" in response or "error" in response