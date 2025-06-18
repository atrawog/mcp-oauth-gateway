"""
Sacred Auth Service - The OAuth Oracle
Following OAuth 2.1 and RFC 7591 divine specifications
"""
import os
import time
import secrets
import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from urllib.parse import urlparse, parse_qs, urlencode

from fastapi import FastAPI, Request, HTTPException, Form, Query, Response, Depends
from fastapi.responses import JSONResponse, RedirectResponse, HTMLResponse
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
import httpx
import redis.asyncio as redis
from jose import jwt, JWTError
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend


# Sacred Configuration
class Settings(BaseSettings):
    # GitHub OAuth
    github_client_id: str
    github_client_secret: str
    
    # JWT Configuration
    jwt_secret: str
    jwt_algorithm: str = "HS256"  # Will upgrade to RS256 in next iteration
    
    # Domain Configuration
    base_domain: str
    
    # Redis Configuration
    redis_url: str
    redis_password: Optional[str] = None  # Optional for backward compatibility
    
    # Token Lifetimes
    access_token_lifetime: int = 86400  # 24 hours
    refresh_token_lifetime: int = 2592000  # 30 days
    session_timeout: int = 3600  # 1 hour
    
    # Access Control
    allowed_github_users: str = ""  # Comma-separated list
    
    # MCP Protocol Version
    mcp_protocol_version: str = "2025-03-26"
    
    class Config:
        env_file = ".env"


settings = Settings()

# Initialize FastAPI
app = FastAPI(title="MCP OAuth Gateway - Auth Service")

# Redis connection pool
redis_pool: Optional[redis.Redis] = None


# OAuth Client Registration Model (RFC 7591)
class ClientRegistration(BaseModel):
    redirect_uris: list[str]
    client_name: Optional[str] = None
    client_uri: Optional[str] = None
    logo_uri: Optional[str] = None
    scope: Optional[str] = None
    contacts: Optional[list[str]] = None
    tos_uri: Optional[str] = None
    policy_uri: Optional[str] = None
    jwks_uri: Optional[str] = None
    jwks: Optional[Dict[str, Any]] = None
    software_id: Optional[str] = None
    software_version: Optional[str] = None


# Token Response Model
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    refresh_token: Optional[str] = None
    scope: Optional[str] = None


# Error Response Model (RFC 6749)
class ErrorResponse(BaseModel):
    error: str
    error_description: Optional[str] = None
    error_uri: Optional[str] = None


# Redis connection management
async def get_redis() -> redis.Redis:
    return redis_pool


@app.on_event("startup")
async def startup():
    global redis_pool
    redis_pool = redis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True
    )
    # Test connection
    await redis_pool.ping()
    print("✓ Redis connection established")


@app.on_event("shutdown")
async def shutdown():
    if redis_pool:
        await redis_pool.close()


# Health check endpoint
@app.get("/health")
async def health_check():
    """Divine health check - verifies all systems are blessed"""
    try:
        # Check Redis
        await redis_pool.ping()
        return {"status": "healthy", "service": "auth"}
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
        )


# .well-known/oauth-authorization-server endpoint (RFC 8414)
@app.get("/.well-known/oauth-authorization-server")
async def oauth_metadata():
    """Server metadata shrine - reveals our OAuth capabilities"""
    base_url = f"https://auth.{settings.base_domain}"
    return {
        "issuer": base_url,
        "authorization_endpoint": f"{base_url}/authorize",
        "token_endpoint": f"{base_url}/token",
        "registration_endpoint": f"{base_url}/register",
        "jwks_uri": f"{base_url}/jwks",
        "response_types_supported": ["code"],
        "subject_types_supported": ["public"],
        "id_token_signing_alg_values_supported": ["HS256", "RS256"],
        "scopes_supported": ["openid", "profile", "email"],
        "token_endpoint_auth_methods_supported": ["client_secret_post", "client_secret_basic"],
        "claims_supported": ["sub", "name", "email", "preferred_username"],
        "code_challenge_methods_supported": ["S256", "plain"],
        "grant_types_supported": ["authorization_code", "refresh_token"],
        "revocation_endpoint": f"{base_url}/revoke",
        "introspection_endpoint": f"{base_url}/introspect"
    }


# Dynamic Client Registration endpoint (RFC 7591)
@app.post("/register", status_code=201)
async def register_client(
    registration: ClientRegistration,
    redis_client: redis.Redis = Depends(get_redis)
):
    """The Divine Registration Portal - RFC 7591 compliant"""
    
    # Validate redirect URIs
    if not registration.redirect_uris:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "invalid_client_metadata",
                "error_description": "redirect_uris is required"
            }
        )
    
    # Generate client credentials
    client_id = f"client_{secrets.token_urlsafe(16)}"
    client_secret = secrets.token_urlsafe(32)
    
    # Store client in Redis (eternal storage)
    client_data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "client_secret_expires_at": 0,  # Never expires
        "redirect_uris": json.dumps(registration.redirect_uris),
        "client_name": registration.client_name or "Unnamed Client",
        "scope": registration.scope or "openid profile email",
        "created_at": int(time.time())
    }
    
    # Store with sacred key pattern
    await redis_client.hset(f"oauth:client:{client_id}", mapping=client_data)
    
    # Return registration response
    response = {
        "client_id": client_id,
        "client_secret": client_secret,
        "client_secret_expires_at": 0,
        "redirect_uris": registration.redirect_uris,
        "client_name": registration.client_name,
        "scope": registration.scope,
        "client_id_issued_at": client_data["created_at"]
    }
    
    # Echo back all registered metadata
    for field in ["client_uri", "logo_uri", "contacts", "tos_uri", "policy_uri"]:
        value = getattr(registration, field, None)
        if value is not None:
            response[field] = value
    
    return response


# Authorization endpoint
@app.get("/authorize")
async def authorize(
    client_id: str = Query(...),
    redirect_uri: str = Query(...),
    response_type: str = Query(...),
    scope: str = Query("openid profile email"),
    state: str = Query(...),
    code_challenge: Optional[str] = Query(None),
    code_challenge_method: Optional[str] = Query("S256"),
    redis_client: redis.Redis = Depends(get_redis)
):
    """Portal to authentication realm - initiates GitHub OAuth flow"""
    
    # Validate client_id
    client_data = await redis_client.hgetall(f"oauth:client:{client_id}")
    if not client_data:
        # RFC 6749 - MUST NOT redirect on invalid client_id
        raise HTTPException(
            status_code=400,
            detail={
                "error": "invalid_client",
                "error_description": "Unknown client"
            }
        )
    
    # Validate redirect_uri
    allowed_uris = json.loads(client_data.get("redirect_uris", "[]"))
    if redirect_uri not in allowed_uris:
        # RFC 6749 - MUST NOT redirect on invalid redirect_uri
        raise HTTPException(
            status_code=400,
            detail={
                "error": "invalid_redirect_uri",
                "error_description": "Redirect URI not registered"
            }
        )
    
    # Validate response_type
    if response_type != "code":
        return RedirectResponse(
            url=f"{redirect_uri}?error=unsupported_response_type&state={state}"
        )
    
    # Store authorization request state
    auth_state = secrets.token_urlsafe(32)
    auth_data = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": scope,
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": code_challenge_method
    }
    
    # Store with 5 minute TTL
    await redis_client.setex(
        f"oauth:state:{auth_state}",
        300,
        json.dumps(auth_data)
    )
    
    # Redirect to GitHub OAuth
    github_params = {
        "client_id": settings.github_client_id,
        "redirect_uri": f"https://auth.{settings.base_domain}/callback",
        "scope": "user:email",
        "state": auth_state
    }
    
    github_url = f"https://github.com/login/oauth/authorize?{urlencode(github_params)}"
    return RedirectResponse(url=github_url)


# Callback endpoint
@app.get("/callback")
async def oauth_callback(
    code: str = Query(...),
    state: str = Query(...),
    redis_client: redis.Redis = Depends(get_redis)
):
    """The blessed return path - handles GitHub OAuth callback"""
    
    # Retrieve authorization state
    auth_data_str = await redis_client.get(f"oauth:state:{state}")
    if not auth_data_str:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "invalid_request",
                "error_description": "Invalid or expired state"
            }
        )
    
    auth_data = json.loads(auth_data_str)
    
    # Exchange GitHub code for token
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://github.com/login/oauth/access_token",
            headers={"Accept": "application/json"},
            data={
                "client_id": settings.github_client_id,
                "client_secret": settings.github_client_secret,
                "code": code
            }
        )
        
        if token_response.status_code != 200:
            return RedirectResponse(
                url=f"{auth_data['redirect_uri']}?error=server_error&state={auth_data['state']}"
            )
        
        github_token = token_response.json()
        
        # Get user info from GitHub
        user_response = await client.get(
            "https://api.github.com/user",
            headers={
                "Authorization": f"Bearer {github_token['access_token']}",
                "Accept": "application/vnd.github.v3+json"
            }
        )
        
        if user_response.status_code != 200:
            return RedirectResponse(
                url=f"{auth_data['redirect_uri']}?error=server_error&state={auth_data['state']}"
            )
        
        user_info = user_response.json()
    
    # Check if user is allowed
    allowed_users = settings.allowed_github_users.split(",") if settings.allowed_github_users else []
    if allowed_users and user_info["login"] not in allowed_users:
        return RedirectResponse(
            url=f"{auth_data['redirect_uri']}?error=access_denied&state={auth_data['state']}"
        )
    
    # Generate authorization code
    auth_code = secrets.token_urlsafe(32)
    
    # Store authorization code with user info
    code_data = {
        **auth_data,
        "user_id": str(user_info["id"]),
        "username": user_info["login"],
        "email": user_info.get("email", ""),
        "name": user_info.get("name", "")
    }
    
    # Store with 1 year TTL (per CLAUDE.md)
    await redis_client.setex(
        f"oauth:code:{auth_code}",
        31536000,
        json.dumps(code_data)
    )
    
    # Clean up state
    await redis_client.delete(f"oauth:state:{state}")
    
    # Redirect back to client
    redirect_params = {
        "code": auth_code,
        "state": auth_data["state"]
    }
    
    return RedirectResponse(
        url=f"{auth_data['redirect_uri']}?{urlencode(redirect_params)}"
    )


# Token endpoint
@app.post("/token")
async def token_exchange(
    grant_type: str = Form(...),
    code: Optional[str] = Form(None),
    redirect_uri: Optional[str] = Form(None),
    client_id: str = Form(...),
    client_secret: Optional[str] = Form(None),
    code_verifier: Optional[str] = Form(None),
    refresh_token: Optional[str] = Form(None),
    redis_client: redis.Redis = Depends(get_redis)
):
    """The transmutation chamber - exchanges codes for tokens"""
    
    # Validate client
    client_data = await redis_client.hgetall(f"oauth:client:{client_id}")
    if not client_data:
        raise HTTPException(
            status_code=401,
            detail={
                "error": "invalid_client",
                "error_description": "Unknown client"
            },
            headers={"WWW-Authenticate": "Basic"}
        )
    
    # Validate client secret (if provided)
    if client_secret and client_secret != client_data.get("client_secret"):
        raise HTTPException(
            status_code=401,
            detail={
                "error": "invalid_client",
                "error_description": "Invalid client credentials"
            },
            headers={"WWW-Authenticate": "Basic"}
        )
    
    if grant_type == "authorization_code":
        if not code:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "invalid_request",
                    "error_description": "Missing authorization code"
                }
            )
        
        # Retrieve authorization code
        code_data_str = await redis_client.get(f"oauth:code:{code}")
        if not code_data_str:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "invalid_grant",
                    "error_description": "Invalid or expired authorization code"
                }
            )
        
        code_data = json.loads(code_data_str)
        
        # Validate redirect_uri
        if redirect_uri != code_data["redirect_uri"]:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "invalid_grant",
                    "error_description": "Redirect URI mismatch"
                }
            )
        
        # Validate PKCE if present
        if code_data.get("code_challenge"):
            if not code_verifier:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "invalid_grant",
                        "error_description": "PKCE code_verifier required"
                    }
                )
            
            # Verify challenge
            if code_data["code_challenge_method"] == "S256":
                challenge = hashlib.sha256(code_verifier.encode()).digest()
                challenge_b64 = secrets.token_urlsafe(32)[:43]  # Simplified for now
                # TODO: Implement proper S256 verification
            
        # Generate tokens
        access_token = await create_jwt_token(
            {
                "sub": code_data["user_id"],
                "username": code_data["username"],
                "email": code_data["email"],
                "name": code_data["name"],
                "scope": code_data["scope"],
                "client_id": client_id
            },
            redis_client
        )
        
        refresh_token_value = secrets.token_urlsafe(32)
        
        # Store refresh token
        await redis_client.setex(
            f"oauth:refresh:{refresh_token_value}",
            settings.refresh_token_lifetime,
            json.dumps({
                "user_id": code_data["user_id"],
                "username": code_data["username"],
                "client_id": client_id,
                "scope": code_data["scope"]
            })
        )
        
        # Delete used authorization code
        await redis_client.delete(f"oauth:code:{code}")
        
        return TokenResponse(
            access_token=access_token,
            expires_in=settings.access_token_lifetime,
            refresh_token=refresh_token_value,
            scope=code_data["scope"]
        )
    
    elif grant_type == "refresh_token":
        if not refresh_token:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "invalid_request",
                    "error_description": "Missing refresh token"
                }
            )
        
        # Retrieve refresh token data
        refresh_data_str = await redis_client.get(f"oauth:refresh:{refresh_token}")
        if not refresh_data_str:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "invalid_grant",
                    "error_description": "Invalid or expired refresh token"
                }
            )
        
        refresh_data = json.loads(refresh_data_str)
        
        # Generate new access token
        access_token = await create_jwt_token(
            {
                "sub": refresh_data["user_id"],
                "username": refresh_data["username"],
                "scope": refresh_data["scope"],
                "client_id": client_id
            },
            redis_client
        )
        
        return TokenResponse(
            access_token=access_token,
            expires_in=settings.access_token_lifetime,
            scope=refresh_data["scope"]
        )
    
    else:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "unsupported_grant_type",
                "error_description": f"Grant type '{grant_type}' not supported"
            }
        )


# ForwardAuth verification endpoint
@app.get("/verify")
@app.post("/verify")
async def verify_token(
    request: Request,
    redis_client: redis.Redis = Depends(get_redis)
):
    """Token examination oracle - validates Bearer tokens for Traefik"""
    
    # Extract token from Authorization header
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail={
                "error": "invalid_request",
                "error_description": "Missing or invalid Authorization header"
            },
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    token = auth_header[7:]  # Remove "Bearer " prefix
    
    try:
        # Decode and verify JWT
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm]
        )
        
        # Check if token is revoked
        jti = payload.get("jti")
        if jti:
            token_data = await redis_client.get(f"oauth:token:{jti}")
            if not token_data:
                raise HTTPException(
                    status_code=401,
                    detail={
                        "error": "invalid_token",
                        "error_description": "Token revoked or not found"
                    },
                    headers={"WWW-Authenticate": "Bearer"}
                )
        
        # Return success with user info headers
        return Response(
            status_code=200,
            headers={
                "X-User-Id": str(payload.get("sub", "")),
                "X-User-Name": payload.get("username", ""),
                "X-Auth-Token": token
            }
        )
        
    except JWTError as e:
        raise HTTPException(
            status_code=401,
            detail={
                "error": "invalid_token",
                "error_description": str(e)
            },
            headers={"WWW-Authenticate": "Bearer"}
        )


# Helper function to create JWT tokens
async def create_jwt_token(claims: dict, redis_client: redis.Redis) -> str:
    """Creates a blessed JWT token with sacred claims"""
    
    # Generate JTI for tracking
    jti = secrets.token_urlsafe(16)
    
    # Prepare JWT claims
    now = datetime.now(timezone.utc)
    jwt_claims = {
        **claims,
        "jti": jti,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=settings.access_token_lifetime)).timestamp()),
        "iss": f"https://auth.{settings.base_domain}"
    }
    
    # Create token
    token = jwt.encode(
        jwt_claims,
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm
    )
    
    # Store token reference in Redis
    await redis_client.setex(
        f"oauth:token:{jti}",
        settings.access_token_lifetime,
        json.dumps(claims)
    )
    
    # Track user's tokens
    username = claims.get("username")
    if username:
        await redis_client.sadd(f"oauth:user_tokens:{username}", jti)
    
    return token


# Token revocation endpoint (RFC 7009)
@app.post("/revoke")
async def revoke_token(
    token: str = Form(...),
    token_type_hint: Optional[str] = Form(None),
    client_id: str = Form(...),
    client_secret: Optional[str] = Form(None),
    redis_client: redis.Redis = Depends(get_redis)
):
    """Token banishment altar - revokes tokens"""
    
    # Validate client
    client_data = await redis_client.hgetall(f"oauth:client:{client_id}")
    if not client_data:
        # RFC 7009 - invalid client should still return 200
        return Response(status_code=200)
    
    if client_secret and client_secret != client_data.get("client_secret"):
        return Response(status_code=200)
    
    # Try to decode as JWT first
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            options={"verify_exp": False}  # Allow expired tokens to be revoked
        )
        
        jti = payload.get("jti")
        if jti:
            await redis_client.delete(f"oauth:token:{jti}")
            
            # Remove from user's token set
            username = payload.get("username")
            if username:
                await redis_client.srem(f"oauth:user_tokens:{username}", jti)
    
    except JWTError:
        # Might be a refresh token
        await redis_client.delete(f"oauth:refresh:{token}")
    
    # Always return 200 (RFC 7009)
    return Response(status_code=200)


# Token introspection endpoint (RFC 7662)
@app.post("/introspect")
async def introspect_token(
    token: str = Form(...),
    token_type_hint: Optional[str] = Form(None),
    client_id: str = Form(...),
    client_secret: Optional[str] = Form(None),
    redis_client: redis.Redis = Depends(get_redis)
):
    """Token examination oracle - reveals token properties"""
    
    # Validate client
    client_data = await redis_client.hgetall(f"oauth:client:{client_id}")
    if not client_data or (client_secret and client_secret != client_data.get("client_secret")):
        return {"active": False}
    
    try:
        # Try to decode as JWT
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm]
        )
        
        # Check if token exists in Redis
        jti = payload.get("jti")
        if jti:
            token_exists = await redis_client.exists(f"oauth:token:{jti}")
            if not token_exists:
                return {"active": False}
        
        return {
            "active": True,
            "scope": payload.get("scope", ""),
            "client_id": payload.get("client_id"),
            "username": payload.get("username"),
            "exp": payload.get("exp"),
            "iat": payload.get("iat"),
            "sub": payload.get("sub"),
            "jti": jti
        }
        
    except JWTError:
        # Might be a refresh token
        refresh_data_str = await redis_client.get(f"oauth:refresh:{token}")
        if refresh_data_str:
            refresh_data = json.loads(refresh_data_str)
            return {
                "active": True,
                "scope": refresh_data.get("scope", ""),
                "client_id": refresh_data.get("client_id"),
                "username": refresh_data.get("username"),
                "token_type": "refresh_token"
            }
    
    return {"active": False}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)