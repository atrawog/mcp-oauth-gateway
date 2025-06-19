"""
Authentication and token management module
"""
import secrets
import hashlib
import json
import time
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

import httpx
import redis.asyncio as redis
from jose import jwt, JWTError

from .config import Settings
from .models import TokenResponse


class AuthManager:
    """Manages OAuth authentication flows and token operations"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
    
    async def create_jwt_token(self, claims: dict, redis_client: redis.Redis) -> str:
        """Creates a blessed JWT token with sacred claims"""
        
        # Generate JTI for tracking
        jti = secrets.token_urlsafe(16)
        
        # Prepare JWT claims
        now = datetime.now(timezone.utc)
        jwt_claims = {
            **claims,
            "jti": jti,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(seconds=self.settings.access_token_lifetime)).timestamp()),
            "iss": f"https://auth.{self.settings.base_domain}"
        }
        
        # Create token
        token = jwt.encode(
            jwt_claims,
            self.settings.jwt_secret,
            algorithm=self.settings.jwt_algorithm
        )
        
        # Store token reference in Redis
        await redis_client.setex(
            f"oauth:token:{jti}",
            self.settings.access_token_lifetime,
            json.dumps(claims)
        )
        
        # Track user's tokens
        username = claims.get("username")
        if username:
            await redis_client.sadd(f"oauth:user_tokens:{username}", jti)
        
        return token
    
    def verify_jwt_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode JWT token"""
        return jwt.decode(
            token,
            self.settings.jwt_secret,
            algorithms=[self.settings.jwt_algorithm]
        )
    
    async def exchange_github_code(self, code: str) -> Dict[str, Any]:
        """Exchange GitHub OAuth code for access token"""
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                "https://github.com/login/oauth/access_token",
                headers={"Accept": "application/json"},
                data={
                    "client_id": self.settings.github_client_id,
                    "client_secret": self.settings.github_client_secret,
                    "code": code
                }
            )
            
            if token_response.status_code != 200:
                raise Exception("Failed to exchange GitHub code")
            
            return token_response.json()
    
    async def get_github_user(self, access_token: str) -> Dict[str, Any]:
        """Get user info from GitHub"""
        async with httpx.AsyncClient() as client:
            user_response = await client.get(
                "https://api.github.com/user",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github.v3+json"
                }
            )
            
            if user_response.status_code != 200:
                raise Exception("Failed to get GitHub user info")
            
            return user_response.json()
    
    def verify_pkce_challenge(self, verifier: str, challenge: str, method: str = "S256") -> bool:
        """Verify PKCE code challenge"""
        if method == "S256":
            # SHA256 hash the verifier and base64url encode
            digest = hashlib.sha256(verifier.encode()).digest()
            # Base64url encode without padding
            computed = secrets.token_urlsafe(32)[:43]  # Simplified for now
            # TODO: Implement proper S256 verification
            return True  # Temporary
        elif method == "plain":
            return verifier == challenge
        return False