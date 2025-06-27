#!/usr/bin/env bash
# Setup log rotation for MCP OAuth Gateway services

set -euo pipefail

PROJECT_ROOT="/home/atrawog/mcp-oauth-gateway"
LOGROTATE_CONF="$PROJECT_ROOT/logrotate.conf"

echo "🔄 Setting up log rotation for MCP OAuth Gateway..."

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then
    echo "⚠️  This script should be run with sudo to set up system-wide log rotation"
    echo "   Run: sudo $0"
    exit 1
fi

# Create logs directory structure if not exists
echo "📁 Creating log directories..."
mkdir -p "$PROJECT_ROOT/logs"/{traefik,auth,mcp-{fetch,fetchs,filesystem,memory,everything,time,tmux,playwright,sequentialthinking,echo-stateful,echo-stateless}}

# Set proper permissions
chmod -R 755 "$PROJECT_ROOT/logs"

# Copy logrotate config to system location
echo "📝 Installing logrotate configuration..."
cp "$LOGROTATE_CONF" /etc/logrotate.d/mcp-oauth-gateway

# Test logrotate configuration
echo "🧪 Testing logrotate configuration..."
logrotate -d /etc/logrotate.d/mcp-oauth-gateway

echo "✅ Log rotation setup complete!"
echo ""
echo "📊 Log rotation will run daily and keep 7 days of compressed logs"
echo "📍 Logs location: $PROJECT_ROOT/logs/"
echo ""
echo "🔧 Manual commands:"
echo "   - Force rotation: sudo logrotate -f /etc/logrotate.d/mcp-oauth-gateway"
echo "   - Test config: sudo logrotate -d /etc/logrotate.d/mcp-oauth-gateway"
