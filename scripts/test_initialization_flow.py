#!/usr/bin/env python3
"""Test the initialization and notifications flow directly."""

import httpx
import json
import os

# Get token from .env
with open('.env') as f:
    for line in f:
        if line.startswith('MCP_CLIENT_ACCESS_TOKEN='):
            token = line.strip().split('=', 1)[1]
            break

# Get MCP Everything URL from environment
mcp_everything_enabled = os.getenv('MCP_EVERYTHING_TESTS_ENABLED', 'false').lower() == 'true'
mcp_everything_urls = os.getenv('MCP_EVERYTHING_URLS', '').split(',') if os.getenv('MCP_EVERYTHING_URLS') else []

if not mcp_everything_enabled:
    print("MCP Everything tests are disabled. Set MCP_EVERYTHING_TESTS_ENABLED=true to enable.")
    exit(0)

if not mcp_everything_urls:
    print("MCP_EVERYTHING_URLS environment variable not set")
    exit(1)

url = mcp_everything_urls[0]

# Step 1: Initialize
print("=== Step 1: Initialize ===")
init_request = {
    'jsonrpc': '2.0',
    'method': 'initialize',
    'params': {
        'protocolVersion': '2025-06-18',
        'capabilities': {},
        'clientInfo': {'name': 'test-init', 'version': '1.0'}
    },
    'id': 1
}

headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json',
    'Accept': 'application/json, text/event-stream',
    'MCP-Protocol-Version': '2025-06-18'
}

response = httpx.post(url, json=init_request, headers=headers, verify=False)
print(f'Status: {response.status_code}')
print(f'Headers: {dict(response.headers)}')
print(f'Response: {response.text}')

# Get session ID
session_id = response.headers.get('mcp-session-id')
print(f'\nSession ID: {session_id}')

# Step 2: Send notifications/initialized
print("\n=== Step 2: Send notifications/initialized ===")
notif_request = {
    'jsonrpc': '2.0',
    'method': 'notifications/initialized'
}

notif_headers = headers.copy()
if session_id:
    notif_headers['Mcp-Session-Id'] = session_id

response = httpx.post(url, json=notif_request, headers=notif_headers, verify=False)
print(f'Status: {response.status_code}')
print(f'Headers: {dict(response.headers)}')
print(f'Response: {response.text}')

# Step 3: Try tools/list
print("\n=== Step 3: Try tools/list ===")
tools_request = {
    'jsonrpc': '2.0',
    'method': 'tools/list',
    'params': {},
    'id': 2
}

tools_headers = headers.copy()
if session_id:
    tools_headers['Mcp-Session-Id'] = session_id

response = httpx.post(url, json=tools_request, headers=tools_headers, verify=False)
print(f'Status: {response.status_code}')
print(f'Response: {response.text}')