#!/bin/bash
# Run MCP OAuth flow and save credentials to .env

# Load environment
source .env

# Set MCP server URL
export MCP_SERVER_URL="https://mcp-fetch.${BASE_DOMAIN}/mcp"

# Run the OAuth flow and capture output
echo "Running OAuth flow..."
OUTPUT=$(script -q -c ".pixi/envs/default/bin/python -m mcp_streamablehttp_client.cli --token --server-url \"$MCP_SERVER_URL\"" /dev/null)

# Display the output
echo "$OUTPUT"

# Extract and save environment variables
echo "$OUTPUT" | grep "^export MCP_CLIENT_" | while read -r line; do
    # Extract key and value
    if [[ $line =~ ^export\ ([^=]+)=(.+)$ ]]; then
        KEY="${BASH_REMATCH[1]}"
        VALUE="${BASH_REMATCH[2]}"

        # Save to .env
        if grep -q "^$KEY=" .env 2>/dev/null; then
            # Update existing
            sed -i "s|^$KEY=.*|$KEY=$VALUE|" .env
        else
            # Add new
            echo "$KEY=$VALUE" >> .env
        fi
        echo "✅ Saved $KEY to .env"
    fi
done
