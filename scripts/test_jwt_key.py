#!/usr/bin/env python3
"""Test JWT private key loading"""
import os
import base64
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

try:
    key_b64 = os.getenv('JWT_PRIVATE_KEY_B64')
    if not key_b64:
        print('JWT_PRIVATE_KEY_B64 not found in environment')
    else:
        print(f'Key length: {len(key_b64)}')
        decoded = base64.b64decode(key_b64)
        print(f'Decoded length: {len(decoded)}')
        # Check if it starts with PEM header
        print(f'First 50 chars: {decoded[:50]}')
        key = serialization.load_pem_private_key(decoded, password=None, backend=default_backend())
        print('Key loaded successfully')
        print(f'Key type: {type(key)}')
except Exception as e:
    print(f'Error: {type(e).__name__}: {e}')
    import traceback
    traceback.print_exc()