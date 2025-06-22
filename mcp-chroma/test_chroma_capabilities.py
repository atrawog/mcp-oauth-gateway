#!/usr/bin/env python3
"""
Comprehensive test suite for MCP Chroma service capabilities.

This script tests all the vector database functionality provided by the Chroma MCP server
including document management, semantic search, collection operations, and vector embeddings.
"""

import json
import time
import subprocess
import tempfile
import os
from typing import Dict, Any, List, Optional

class ChromaMCPTester:
    """Test suite for Chroma MCP server capabilities."""
    
    def __init__(self, server_url: str = "http://localhost:32773/mcp"):
        """Initialize the tester with server URL."""
        self.server_url = server_url
        self.test_results = []
        self.client_process = None
        
    def run_mcp_client_command(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Run an MCP command using mcp-streamablehttp-client.
        
        Args:
            method: The MCP method to call
            params: Parameters for the method
            
        Returns:
            Dict containing the response from the server
        """
        # Create the JSON-RPC request
        request = {
            "jsonrpc": "2.0",
            "id": int(time.time() * 1000),  # Use timestamp as ID
            "method": method
        }
        
        if params:
            request["params"] = params
            
        # Write request to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(request, f)
            request_file = f.name
            
        try:
            # Run mcp-streamablehttp-client
            cmd = [
                "pixi", "run", "python", "-m", "mcp_streamablehttp_client.cli",
                "--server-url", self.server_url,
                "--stdin-file", request_file,
                "--timeout", "30"
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                try:
                    response = json.loads(result.stdout.strip())
                    return response
                except json.JSONDecodeError:
                    return {"error": f"Invalid JSON response: {result.stdout}"}
            else:
                return {"error": f"Command failed: {result.stderr}"}
                
        except subprocess.TimeoutExpired:
            return {"error": "Command timed out"}
        except Exception as e:
            return {"error": f"Exception: {str(e)}"}
        finally:
            # Clean up temporary file
            try:
                os.unlink(request_file)
            except:
                pass
    
    def test_initialize(self) -> bool:
        """Test MCP server initialization."""
        print("🚀 Testing MCP initialization...")
        
        response = self.run_mcp_client_command(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "chroma-tester",
                    "version": "1.0.0"
                }
            }
        )
        
        if "error" in response:
            print(f"❌ Initialize failed: {response['error']}")
            return False
            
        if "result" in response and "serverInfo" in response["result"]:
            server_info = response["result"]["serverInfo"]
            print(f"✅ Initialized successfully: {server_info['name']} v{server_info['version']}")
            return True
        else:
            print(f"❌ Unexpected initialize response: {response}")
            return False
    
    def test_list_tools(self) -> bool:
        """Test listing available tools."""
        print("🔧 Testing tools list...")
        
        response = self.run_mcp_client_command("tools/list")
        
        if "error" in response:
            print(f"❌ List tools failed: {response['error']}")
            return False
            
        if "result" in response and "tools" in response["result"]:
            tools = response["result"]["tools"]
            print(f"✅ Found {len(tools)} tools:")
            for tool in tools:
                print(f"   - {tool['name']}: {tool.get('description', 'No description')}")
            return True
        else:
            print(f"❌ Unexpected tools response: {response}")
            return False
    
    def test_collection_management(self) -> bool:
        """Test collection creation, listing, and management."""
        print("📚 Testing collection management...")
        
        # Test create collection
        print("  Creating test collection...")
        response = self.run_mcp_client_command(
            "tools/call",
            {
                "name": "create_collection",
                "arguments": {
                    "name": "test_collection",
                    "metadata": {
                        "description": "Test collection for capability testing",
                        "created_by": "mcp-tester"
                    }
                }
            }
        )
        
        if "error" in response:
            print(f"    ❌ Create collection failed: {response['error']}")
            return False
        
        print("    ✅ Collection created successfully")
        
        # Test list collections
        print("  Listing collections...")
        response = self.run_mcp_client_command(
            "tools/call",
            {
                "name": "list_collections",
                "arguments": {}
            }
        )
        
        if "error" in response:
            print(f"    ❌ List collections failed: {response['error']}")
            return False
            
        if "result" in response:
            print(f"    ✅ Collections listed successfully")
            return True
        else:
            print(f"    ❌ Unexpected collections response: {response}")
            return False
    
    def test_document_operations(self) -> bool:
        """Test document add, get, update, and delete operations."""
        print("📄 Testing document operations...")
        
        # Test add document
        print("  Adding test document...")
        response = self.run_mcp_client_command(
            "tools/call",
            {
                "name": "add_document",
                "arguments": {
                    "collection_name": "test_collection",
                    "document_id": "doc_001",
                    "content": "Machine learning is a powerful subset of artificial intelligence that enables computers to learn and improve from experience without being explicitly programmed.",
                    "metadata": {
                        "category": "AI",
                        "topic": "Machine Learning",
                        "author": "Test Author",
                        "timestamp": "2024-01-15"
                    }
                }
            }
        )
        
        if "error" in response:
            print(f"    ❌ Add document failed: {response['error']}")
            return False
        
        print("    ✅ Document added successfully")
        
        # Test get document
        print("  Retrieving document...")
        response = self.run_mcp_client_command(
            "tools/call",
            {
                "name": "get_document",
                "arguments": {
                    "collection_name": "test_collection",
                    "document_id": "doc_001"
                }
            }
        )
        
        if "error" in response:
            print(f"    ❌ Get document failed: {response['error']}")
            return False
        
        print("    ✅ Document retrieved successfully")
        
        # Test update document
        print("  Updating document...")
        response = self.run_mcp_client_command(
            "tools/call",
            {
                "name": "update_document",
                "arguments": {
                    "collection_name": "test_collection",
                    "document_id": "doc_001",
                    "content": "Machine learning is a powerful subset of artificial intelligence that enables computers to learn and improve from experience without being explicitly programmed. It includes supervised, unsupervised, and reinforcement learning approaches.",
                    "metadata": {
                        "category": "AI",
                        "topic": "Machine Learning",
                        "author": "Test Author",
                        "timestamp": "2024-01-15",
                        "updated": "2024-01-20"
                    }
                }
            }
        )
        
        if "error" in response:
            print(f"    ❌ Update document failed: {response['error']}")
            return False
        
        print("    ✅ Document updated successfully")
        
        # Add a few more documents for testing
        documents = [
            {
                "id": "doc_002", 
                "content": "Deep learning is a specialized form of machine learning that uses neural networks with multiple layers to model and understand complex patterns in data.",
                "metadata": {"category": "AI", "topic": "Deep Learning", "author": "Test Author"}
            },
            {
                "id": "doc_003",
                "content": "Natural language processing (NLP) enables computers to understand, interpret, and generate human language in a meaningful way.",
                "metadata": {"category": "AI", "topic": "NLP", "author": "Test Author"}
            }
        ]
        
        for doc in documents:
            print(f"  Adding document {doc['id']}...")
            response = self.run_mcp_client_command(
                "tools/call",
                {
                    "name": "add_document",
                    "arguments": {
                        "collection_name": "test_collection",
                        "document_id": doc["id"],
                        "content": doc["content"],
                        "metadata": doc["metadata"]
                    }
                }
            )
            
            if "error" in response:
                print(f"    ❌ Add document {doc['id']} failed: {response['error']}")
                return False
        
        print("    ✅ Additional documents added successfully")
        return True
    
    def test_search_operations(self) -> bool:
        """Test various search operations."""
        print("🔍 Testing search operations...")
        
        # Test basic semantic search
        print("  Testing semantic search...")
        response = self.run_mcp_client_command(
            "tools/call",
            {
                "name": "search_documents",
                "arguments": {
                    "collection_name": "test_collection",
                    "query": "neural networks and artificial intelligence",
                    "n_results": 3,
                    "include_metadata": True
                }
            }
        )
        
        if "error" in response:
            print(f"    ❌ Semantic search failed: {response['error']}")
            return False
        
        print("    ✅ Semantic search completed successfully")
        
        # Test metadata filtering search
        print("  Testing metadata search...")
        response = self.run_mcp_client_command(
            "tools/call",
            {
                "name": "search_by_metadata",
                "arguments": {
                    "collection_name": "test_collection",
                    "metadata_filter": {
                        "category": "AI",
                        "topic": "Machine Learning"
                    },
                    "n_results": 5
                }
            }
        )
        
        if "error" in response:
            print(f"    ❌ Metadata search failed: {response['error']}")
            return False
        
        print("    ✅ Metadata search completed successfully")
        
        # Test find similar documents
        print("  Testing similarity search...")
        response = self.run_mcp_client_command(
            "tools/call",
            {
                "name": "find_similar",
                "arguments": {
                    "collection_name": "test_collection",
                    "document_id": "doc_001",
                    "n_results": 2
                }
            }
        )
        
        if "error" in response:
            print(f"    ❌ Similarity search failed: {response['error']}")
            return False
        
        print("    ✅ Similarity search completed successfully")
        return True
    
    def test_embedding_operations(self) -> bool:
        """Test embedding generation and comparison."""
        print("🧮 Testing embedding operations...")
        
        # Test generate embedding
        print("  Testing embedding generation...")
        response = self.run_mcp_client_command(
            "tools/call",
            {
                "name": "generate_embedding",
                "arguments": {
                    "text": "Machine learning and artificial intelligence technologies"
                }
            }
        )
        
        if "error" in response:
            print(f"    ❌ Generate embedding failed: {response['error']}")
            return False
        
        print("    ✅ Embedding generation completed successfully")
        
        # Test batch embedding
        print("  Testing batch embedding...")
        response = self.run_mcp_client_command(
            "tools/call",
            {
                "name": "batch_embed",
                "arguments": {
                    "texts": [
                        "Deep learning neural networks",
                        "Natural language processing",
                        "Computer vision algorithms"
                    ]
                }
            }
        )
        
        if "error" in response:
            print(f"    ❌ Batch embedding failed: {response['error']}")
            return False
        
        print("    ✅ Batch embedding completed successfully")
        return True
    
    def test_resources(self) -> bool:
        """Test resource access functionality."""
        print("📊 Testing resource access...")
        
        # Test list resources
        print("  Testing resource listing...")
        response = self.run_mcp_client_command("resources/list")
        
        if "error" in response:
            print(f"    ❌ List resources failed: {response['error']}")
            return False
        
        print("    ✅ Resources listed successfully")
        
        # Test read collection resource
        print("  Testing collection resource access...")
        response = self.run_mcp_client_command(
            "resources/read",
            {
                "uri": "chroma://collection/test_collection"
            }
        )
        
        if "error" in response:
            print(f"    ❌ Read collection resource failed: {response['error']}")
            return False
        
        print("    ✅ Collection resource accessed successfully")
        return True
    
    def test_cleanup(self) -> bool:
        """Clean up test data."""
        print("🧹 Cleaning up test data...")
        
        # Delete test documents
        print("  Deleting test documents...")
        for doc_id in ["doc_001", "doc_002", "doc_003"]:
            response = self.run_mcp_client_command(
                "tools/call",
                {
                    "name": "delete_document",
                    "arguments": {
                        "collection_name": "test_collection",
                        "document_id": doc_id
                    }
                }
            )
            
            if "error" in response:
                print(f"    ⚠️ Delete document {doc_id} failed: {response['error']}")
            else:
                print(f"    ✅ Document {doc_id} deleted")
        
        # Delete test collection
        print("  Deleting test collection...")
        response = self.run_mcp_client_command(
            "tools/call",
            {
                "name": "delete_collection",
                "arguments": {
                    "name": "test_collection"
                }
            }
        )
        
        if "error" in response:
            print(f"    ⚠️ Delete collection failed: {response['error']}")
            return False
        
        print("    ✅ Test collection deleted")
        return True
    
    def run_all_tests(self) -> Dict[str, bool]:
        """Run the complete test suite."""
        print("🧪 Starting Chroma MCP Capability Tests")
        print("=" * 50)
        
        test_methods = [
            ("Initialize", self.test_initialize),
            ("List Tools", self.test_list_tools),
            ("Collection Management", self.test_collection_management),
            ("Document Operations", self.test_document_operations),
            ("Search Operations", self.test_search_operations),
            ("Embedding Operations", self.test_embedding_operations),
            ("Resource Access", self.test_resources),
            ("Cleanup", self.test_cleanup)
        ]
        
        results = {}
        passed = 0
        total = len(test_methods)
        
        for test_name, test_method in test_methods:
            print(f"\n📋 Running: {test_name}")
            try:
                result = test_method()
                results[test_name] = result
                if result:
                    passed += 1
                    print(f"✅ {test_name}: PASSED")
                else:
                    print(f"❌ {test_name}: FAILED")
            except Exception as e:
                print(f"💥 {test_name}: ERROR - {str(e)}")
                results[test_name] = False
        
        print("\n" + "=" * 50)
        print(f"🏁 Test Results: {passed}/{total} tests passed")
        print("=" * 50)
        
        if passed == total:
            print("🎉 All tests passed! MCP Chroma service is fully functional!")
        else:
            print("⚠️ Some tests failed. Check the output above for details.")
        
        return results


def main():
    """Main function to run the test suite."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test MCP Chroma server capabilities")
    parser.add_argument(
        "--url", 
        default="http://localhost:32773/mcp",
        help="MCP server URL (default: http://localhost:32773/mcp)"
    )
    
    args = parser.parse_args()
    
    tester = ChromaMCPTester(args.url)
    results = tester.run_all_tests()
    
    # Exit with error code if any tests failed
    if not all(results.values()):
        exit(1)


if __name__ == "__main__":
    main()