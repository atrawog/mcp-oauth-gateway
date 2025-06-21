#!/usr/bin/env python3
"""Test the Accept header requirement."""

import httpx
import os
import json

# Get token from .env
with open('.env') as f:
    for line in f:
        if line.startswith('MCP_CLIENT_ACCESS_TOKEN='):
            token = line.strip().split('=', 1)[1]
            break

url = 'https://mcp-everything.atradev.org/mcp'
data = {
    'jsonrpc': '2.0',
    'method': 'initialize',
    'params': {
        'protocolVersion': '2025-06-18',
        'capabilities': {},
        'clientInfo': {'name': 'test', 'version': '1.0'}
    },
    'id': 1
}

print("Testing WITHOUT Accept header:")
headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json',
    'MCP-Protocol-Version': '2025-06-18'
}
response = httpx.post(url, json=data, headers=headers, verify=False)
print(f'Status: {response.status_code}')
print(f'Response: {response.text[:200]}\n')

print("Testing WITH Accept header:")
headers['Accept'] = 'application/json, text/event-stream'
response = httpx.post(url, json=data, headers=headers, verify=False)
print(f'Status: {response.status_code}')
print(f'Content-Type: {response.headers.get("content-type")}')
print(f'Session ID: {response.headers.get("mcp-session-id")}')
print(f'Response: {response.text[:200]}')