"""JWT test helper using Authlib instead of jose."""

import time
from typing import Any

from authlib.jose import jwt


def create_test_jwt(payload: dict[str, Any], secret: str, algorithm: str = "HS256") -> str:
    """Create a test JWT token using Authlib."""
    # Add standard claims if not present
    if "iat" not in payload:
        payload["iat"] = int(time.time())
    if "exp" not in payload:
        payload["exp"] = int(time.time()) + 3600  # 1 hour

    # Create header
    header = {"alg": algorithm}

    # Encode using Authlib
    token = jwt.encode(header, payload, secret)

    # Authlib returns bytes, convert to string
    return token.decode("utf-8") if isinstance(token, bytes) else token


# Alias for compatibility
encode = create_test_jwt
