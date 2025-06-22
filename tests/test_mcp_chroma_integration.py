"""
Comprehensive integration tests for MCP Chroma service.
Tests all vector database functionality including document management, semantic search, and embeddings.
"""
import pytest
import json
import os

from tests.test_constants import BASE_DOMAIN


@pytest.fixture(scope="class")
def base_domain():
    """Base domain for tests."""
    return BASE_DOMAIN


class TestMCPChromaIntegration:
    """Test MCP Chroma service integration with OAuth authentication."""
    
    @pytest.fixture(scope="class")
    def chroma_url(self, base_domain):
        return f"https://mcp-chroma.{base_domain}"
    
    def run_mcp_client_raw(self, url, token, method, params=None):
        """Run mcp-streamablehttp-client with raw MCP protocol."""
        import subprocess
        
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
        env["MCP_SERVER_URL"] = f"{url}/mcp"
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            env=env
        )
        
        if result.returncode != 0:
            pytest.fail(f"MCP client failed: {result.stderr}")
            
        # Parse JSON response - look for JSON in the output
        try:
            # Look for JSON response in the output
            output = result.stdout
            
            # Find all JSON objects in the output
            json_objects = []
            i = 0
            while i < len(output):
                if output[i] == '{':
                    # Found start of JSON, find the matching closing brace
                    brace_count = 0
                    json_start = i
                    json_end = i
                    
                    for j in range(i, len(output)):
                        if output[j] == '{':
                            brace_count += 1
                        elif output[j] == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                json_end = j + 1
                                break
                    
                    if brace_count == 0:
                        json_str = output[json_start:json_end]
                        try:
                            obj = json.loads(json_str)
                            # Only keep JSON-RPC responses
                            if "jsonrpc" in obj or "result" in obj or "error" in obj:
                                json_objects.append(obj)
                            i = json_end
                        except:
                            i += 1
                    else:
                        i += 1
                else:
                    i += 1
            
            if not json_objects:
                pytest.fail(f"No JSON-RPC response found in output: {output}")
            
            # Return the last JSON-RPC response
            return json_objects[-1]
            
        except Exception as e:
            pytest.fail(f"Failed to parse JSON response: {e}\nOutput: {result.stdout}")

    def test_chroma_service_health(self, chroma_url):
        """Test chroma service health endpoint."""
        import requests
        response = requests.get(f"{chroma_url}/health", timeout=10)
        assert response.status_code == 200
        
        health_data = response.json()
        assert health_data["status"] == "healthy"
        assert "active_sessions" in health_data
        assert health_data["server_command"] == "uv run chroma"

    def test_chroma_oauth_discovery(self, chroma_url):
        """Test OAuth discovery endpoint routing."""
        import requests
        response = requests.get(f"{chroma_url}/.well-known/oauth-authorization-server", timeout=10)
        assert response.status_code == 200
        
        oauth_config = response.json()
        assert oauth_config["issuer"]
        assert oauth_config["authorization_endpoint"]
        assert oauth_config["token_endpoint"]
        assert oauth_config["registration_endpoint"]

    def test_chroma_mcp_initialize(self, chroma_url, mcp_client_token, wait_for_services):
        """Test MCP protocol initialization."""
        response = self.run_mcp_client_raw(
            url=chroma_url,
            token=mcp_client_token,
            method="initialize",
            params={
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        )
        
        assert "result" in response
        result = response["result"]
        assert result["protocolVersion"] == "2024-11-05"
        assert "capabilities" in result
        assert "serverInfo" in result
        assert result["serverInfo"]["name"] == "chroma"

    def test_chroma_list_tools(self, chroma_url, mcp_client_token, wait_for_services):
        """Test listing available chroma tools."""
        response = self.run_mcp_client_raw(
            url=chroma_url,
            token=mcp_client_token,
            method="tools/list"
        )
        
        assert "result" in response
        tools = response["result"]["tools"]
        
        # Expected chroma tools
        expected_tools = {
            "create_document", "read_document", "update_document", 
            "delete_document", "list_documents", "search_similar"
        }
        
        tool_names = {tool["name"] for tool in tools}
        
        # Check that we have all expected tools
        assert expected_tools.issubset(tool_names), f"Missing tools. Expected: {expected_tools}, Got: {tool_names}"

    def test_chroma_create_document(self, chroma_url, mcp_client_token, wait_for_services):
        """Test creating a document in the vector database."""
        response = self.run_mcp_client_raw(
            url=chroma_url,
            token=mcp_client_token,
            method="tools/call",
            params={
                "name": "create_document",
                "arguments": {
                    "document_id": "test_doc_pytest",
                    "content": "Pytest is a powerful testing framework for Python that makes it easy to write simple and scalable test cases.",
                    "metadata": {
                        "category": "Testing",
                        "topic": "Python Testing",
                        "framework": "pytest"
                    }
                }
            }
        )
        
        assert "result" in response
        result = response["result"]
        assert "content" in result
        content = result["content"]
        assert isinstance(content, list)
        assert len(content) > 0
        assert "successfully" in content[0]["text"]

    def test_chroma_read_document(self, chroma_url, mcp_client_token, wait_for_services):
        """Test reading a document from the vector database."""
        # First create a document
        create_response = self.run_mcp_client_raw(
            url=chroma_url,
            token=mcp_client_token,
            method="tools/call",
            params={
                "name": "create_document",
                "arguments": {
                    "document_id": "test_read_doc",
                    "content": "Document for read testing",
                    "metadata": {"test": "read"}
                }
            }
        )
        
        assert "result" in create_response
        
        # Now read it back
        response = self.run_mcp_client_raw(
            url=chroma_url,
            token=mcp_client_token,
            method="tools/call",
            params={
                "name": "read_document",
                "arguments": {
                    "document_id": "test_read_doc"
                }
            }
        )
        
        assert "result" in response
        result = response["result"]
        assert "content" in result
        content = result["content"]
        assert isinstance(content, list)
        assert len(content) > 0
        assert "test_read_doc" in content[0]["text"]
        assert "Document for read testing" in content[0]["text"]

    def test_chroma_update_document(self, chroma_url, mcp_client_token, wait_for_services):
        """Test updating a document in the vector database."""
        # First create a document
        doc_id = "test_update_doc"
        create_response = self.run_mcp_client_raw(
            url=chroma_url,
            token=mcp_client_token,
            method="tools/call",
            params={
                "name": "create_document",
                "arguments": {
                    "document_id": doc_id,
                    "content": "Original content",
                    "metadata": {"version": "1"}
                }
            }
        )
        
        assert "result" in create_response
        
        # Update the document
        response = self.run_mcp_client_raw(
            url=chroma_url,
            token=mcp_client_token,
            method="tools/call",
            params={
                "name": "update_document",
                "arguments": {
                    "document_id": doc_id,
                    "content": "Updated content with more information",
                    "metadata": {"version": "2", "updated": "true"}
                }
            }
        )
        
        assert "result" in response
        result = response["result"]
        assert "content" in result
        assert "successfully" in result["content"][0]["text"]

    def test_chroma_list_documents(self, chroma_url, mcp_client_token, wait_for_services):
        """Test listing documents in the vector database."""
        response = self.run_mcp_client_raw(
            url=chroma_url,
            token=mcp_client_token,
            method="tools/call",
            params={
                "name": "list_documents",
                "arguments": {
                    "limit": 5
                }
            }
        )
        
        assert "result" in response
        result = response["result"]
        assert "content" in result
        content = result["content"]
        assert isinstance(content, list)
        assert len(content) > 0
        # Should show document listing
        assert "Documents" in content[0]["text"] or "ID:" in content[0]["text"]

    def test_chroma_search_similar(self, chroma_url, mcp_client_token, wait_for_services):
        """Test semantic similarity search."""
        # First ensure we have some documents
        for i in range(3):
            self.run_mcp_client_raw(
                url=chroma_url,
                token=mcp_client_token,
                method="tools/call",
                params={
                    "name": "create_document",
                    "arguments": {
                        "document_id": f"search_test_{i}",
                        "content": [
                            "Machine learning enables computers to learn from data",
                            "Deep learning uses neural networks with multiple layers",
                            "Natural language processing helps computers understand human language"
                        ][i],
                        "metadata": {"category": "AI", "index": i}
                    }
                }
            )
        
        # Now search for similar documents
        response = self.run_mcp_client_raw(
            url=chroma_url,
            token=mcp_client_token,
            method="tools/call",
            params={
                "name": "search_similar",
                "arguments": {
                    "query": "artificial neural networks and deep learning",
                    "num_results": 3
                }
            }
        )
        
        assert "result" in response
        result = response["result"]
        assert "content" in result
        content = result["content"]
        assert isinstance(content, list)
        assert len(content) > 0
        # Should show similar documents
        assert "Similar documents" in content[0]["text"] or "Document" in content[0]["text"]

    def test_chroma_delete_document(self, chroma_url, mcp_client_token, wait_for_services):
        """Test deleting a document from the vector database."""
        # First create a document
        doc_id = "test_delete_doc"
        create_response = self.run_mcp_client_raw(
            url=chroma_url,
            token=mcp_client_token,
            method="tools/call",
            params={
                "name": "create_document",
                "arguments": {
                    "document_id": doc_id,
                    "content": "Document to be deleted",
                    "metadata": {"temporary": "true"}
                }
            }
        )
        
        assert "result" in create_response
        
        # Delete the document
        response = self.run_mcp_client_raw(
            url=chroma_url,
            token=mcp_client_token,
            method="tools/call",
            params={
                "name": "delete_document",
                "arguments": {
                    "document_id": doc_id
                }
            }
        )
        
        assert "result" in response
        result = response["result"]
        assert "content" in result
        assert "successfully" in result["content"][0]["text"]
        
        # Verify it's gone by trying to read it
        read_response = self.run_mcp_client_raw(
            url=chroma_url,
            token=mcp_client_token,
            method="tools/call",
            params={
                "name": "read_document",
                "arguments": {
                    "document_id": doc_id
                }
            }
        )
        
        # Should either error or indicate document not found
        assert "result" in read_response or "error" in read_response

    def test_chroma_metadata_filter(self, chroma_url, mcp_client_token, wait_for_services):
        """Test searching with metadata filters."""
        # Create documents with specific metadata
        categories = ["Science", "Technology", "Mathematics"]
        for i, category in enumerate(categories):
            self.run_mcp_client_raw(
                url=chroma_url,
                token=mcp_client_token,
                method="tools/call",
                params={
                    "name": "create_document",
                    "arguments": {
                        "document_id": f"metadata_test_{i}",
                        "content": f"Document about {category.lower()} topics",
                        "metadata": {
                            "category": category,
                            "year": 2024,
                            "importance": i + 1
                        }
                    }
                }
            )
        
        # Search with metadata filter
        response = self.run_mcp_client_raw(
            url=chroma_url,
            token=mcp_client_token,
            method="tools/call",
            params={
                "name": "search_similar",
                "arguments": {
                    "query": "scientific knowledge",
                    "num_results": 5,
                    "metadata_filter": {
                        "category": "Science"
                    }
                }
            }
        )
        
        assert "result" in response
        result = response["result"]
        assert "content" in result

    def test_chroma_pagination(self, chroma_url, mcp_client_token, wait_for_services):
        """Test document listing pagination."""
        # Test with offset
        response = self.run_mcp_client_raw(
            url=chroma_url,
            token=mcp_client_token,
            method="tools/call",
            params={
                "name": "list_documents",
                "arguments": {
                    "limit": 2,
                    "offset": 1
                }
            }
        )
        
        assert "result" in response
        result = response["result"]
        assert "content" in result

    def test_chroma_protocol_version_compliance(self, chroma_url, mcp_client_token, wait_for_services):
        """Test MCP protocol version compliance."""
        # Test with correct protocol version
        response = self.run_mcp_client_raw(
            url=chroma_url,
            token=mcp_client_token,
            method="initialize",
            params={
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "version-test", "version": "1.0.0"}
            }
        )
        
        assert "result" in response
        result = response["result"]
        assert result["protocolVersion"] == "2024-11-05"

    def test_chroma_error_handling(self, chroma_url, mcp_client_token, wait_for_services):
        """Test error handling for invalid operations."""
        # Test invalid method
        response = self.run_mcp_client_raw(
            url=chroma_url,
            token=mcp_client_token,
            method="invalid/method"
        )
        
        assert "error" in response
        error = response["error"]
        assert error["code"] == -32601  # Method not found

    def test_chroma_authentication_required(self, chroma_url):
        """Test that MCP endpoint requires authentication."""
        import requests
        
        # Test without token
        response = requests.post(
            f"{chroma_url}/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/list"
            },
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 401
        assert "WWW-Authenticate" in response.headers

    def test_chroma_cleanup(self, chroma_url, mcp_client_token, wait_for_services):
        """Clean up test documents."""
        # List of test document IDs to clean up
        test_doc_ids = [
            "test_doc_pytest", "test_read_doc", "test_update_doc",
            "search_test_0", "search_test_1", "search_test_2",
            "metadata_test_0", "metadata_test_1", "metadata_test_2"
        ]
        
        for doc_id in test_doc_ids:
            response = self.run_mcp_client_raw(
                url=chroma_url,
                token=mcp_client_token,
                method="tools/call",
                params={
                    "name": "delete_document",
                    "arguments": {
                        "document_id": doc_id
                    }
                }
            )
            # Don't fail if document doesn't exist - it's cleanup