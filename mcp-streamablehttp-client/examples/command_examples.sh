#!/bin/bash
# MCP HTTP-to-stdio Command Examples
# These examples demonstrate the flexible command execution feature

echo "🚀 MCP HTTP-to-stdio Command Examples"
echo "===================================="

# Set your MCP server URL
export MCP_SERVER_URL="https://mcp-fetch.yourdomain.com/mcp"

echo ""
echo "📋 1. List available tools"
mcp-http-stdio --command "tools/list"

echo ""
echo "🌐 2. Test fetch tool with different URLs"
mcp-http-stdio -c "fetch https://httpbin.org/json"
mcp-http-stdio -c "fetch https://api.github.com/users/octocat"

echo ""
echo "🔍 3. Test search functionality (if available)"
mcp-http-stdio -c "search artificial intelligence"
mcp-http-stdio -c "search query=machine learning"

echo ""
echo "📁 4. File operations (if supported by server)"
mcp-http-stdio -c "read_file /etc/hostname"
mcp-http-stdio -c "read_file path=/tmp/test.txt"

echo ""
echo "⚙️ 5. Advanced parameter formats"

# JSON format (most flexible)
mcp-http-stdio -c 'fetch {"url": "https://httpbin.org/json", "timeout": 10}'

# Key=value format
mcp-http-stdio -c "fetch url=https://example.com timeout=5"

# Mixed parameters
mcp-http-stdio -c "search query='python tutorial' limit=10 sort=relevance"

echo ""
echo "🎯 6. Tool-specific examples"

# If your server has custom tools
mcp-http-stdio -c "analyze_code /path/to/file.py"
mcp-http-stdio -c "database_query SELECT * FROM users LIMIT 5"
mcp-http-stdio -c "generate_summary text='Long text to summarize...'"

echo ""
echo "✅ All examples completed!"
echo ""
echo "💡 Tips:"
echo "  • Use quotes around commands with spaces"
echo "  • JSON format: '{\"key\": \"value\"}'"
echo "  • Key=value format: 'key1=value1 key2=value2'"
echo "  • Simple format: 'toolname argument'"
echo "  • Check available tools first with 'tools/list'"
