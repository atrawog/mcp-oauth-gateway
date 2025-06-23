#!/usr/bin/env python3
"""Debug JWT private key."""

import base64
import os


key_b64 = os.getenv("JWT_PRIVATE_KEY_B64")
if key_b64:
    decoded = base64.b64decode(key_b64)
    # Write to a file to inspect
    with open("/tmp/test_key.pem", "wb") as f:
        f.write(decoded)
    print("Key written to /tmp/test_key.pem")

    # Try to check with openssl
    import subprocess

    result = subprocess.run(
        ["openssl", "rsa", "-in", "/tmp/test_key.pem", "-check"],
        check=False,
        capture_output=True,
        text=True,
    )
    print("OpenSSL check stdout:", result.stdout)
    print("OpenSSL check stderr:", result.stderr)
    print("Return code:", result.returncode)
