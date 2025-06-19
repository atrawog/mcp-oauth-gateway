"""
OAuth 2.1 and RFC 7591 compliant routes
"""
import secrets
import json
import time
from typing import Optional
from urllib.parse import urlencode

from fastapi import APIRouter, Request, HTTPException, Form, Query, Response, Depends
from fastapi.responses import JSONResponse, RedirectResponse, HTMLResponse
import redis.asyncio as redis
from jose import JWTError, jwt

from .config import Settings
from .models import ClientRegistration, TokenResponse, ErrorResponse
from .auth import AuthManager


def create_oauth_router(settings: Settings, redis_manager, auth_manager: AuthManager) -> APIRouter:
    """Create OAuth router with all endpoints"""
    
    router = APIRouter()
    
    async def get_redis() -> redis.Redis:
        """Dependency to get Redis client"""
        return redis_manager.client
    
    # .well-known/oauth-authorization-server endpoint (RFC 8414)
    @router.get("/.well-known/oauth-authorization-server")
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
    @router.post("/register", status_code=201)
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
    @router.get("/authorize")
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
    @router.get("/callback")
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
        
        try:
            # Exchange GitHub code for token
            github_token = await auth_manager.exchange_github_code(code)
            
            # Get user info from GitHub
            user_info = await auth_manager.get_github_user(github_token['access_token'])
            
        except Exception as e:
            return RedirectResponse(
                url=f"{auth_data['redirect_uri']}?error=server_error&state={auth_data['state']}"
            )
        
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
    @router.post("/token")
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
                if not auth_manager.verify_pkce_challenge(
                    code_verifier,
                    code_data["code_challenge"],
                    code_data["code_challenge_method"]
                ):
                    raise HTTPException(
                        status_code=400,
                        detail={
                            "error": "invalid_grant",
                            "error_description": "PKCE verification failed"
                        }
                    )
            
            # Generate tokens
            access_token = await auth_manager.create_jwt_token(
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
            access_token = await auth_manager.create_jwt_token(
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
    @router.get("/verify")
    @router.post("/verify")
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
            payload = auth_manager.verify_jwt_token(token)
            
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
    
    # Token revocation endpoint (RFC 7009)
    @router.post("/revoke")
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
    @router.post("/introspect")
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
            payload = auth_manager.verify_jwt_token(token)
            
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
    
    # OAuth success page for token generation
    @router.get("/success")
    async def oauth_success(
        code: Optional[str] = Query(None),
        state: Optional[str] = Query(None),
        error: Optional[str] = Query(None),
        error_description: Optional[str] = Query(None)
    ):
        """OAuth success page for displaying authorization codes"""
        if error:
            return HTMLResponse(
                content=f"""
                <!DOCTYPE html>
                <html>
                <head><title>OAuth Error</title></head>
                <body style="font-family: Arial; padding: 20px; text-align: center;">
                    <h1>❌ OAuth Error</h1>
                    <p><strong>Error:</strong> {error}</p>
                    <p><strong>Description:</strong> {error_description or 'No description provided'}</p>
                    <p>You can close this window.</p>
                </body>
                </html>
                """
            )
        
        if code:
            return HTMLResponse(
                content=f"""
                <!DOCTYPE html>
                <html>
                <head><title>OAuth Success</title></head>
                <body style="font-family: Arial; padding: 20px; text-align: center;">
                    <h1>✅ OAuth Success!</h1>
                    <p>Authorization code received successfully.</p>
                    <div style="background: #f5f5f5; padding: 10px; margin: 20px; border-radius: 5px; font-family: monospace;">
                        <strong>Authorization Code:</strong><br>
                        {code}
                    </div>
                    <p><em>Copy the code above for token generation.</em></p>
                    <p>You can close this window.</p>
                </body>
                </html>
                """
            )
        
        return HTMLResponse(
            content="""
            <!DOCTYPE html>
            <html>
            <head><title>OAuth Flow</title></head>
            <body style="font-family: Arial; padding: 20px; text-align: center;">
                <h1>⏳ OAuth Flow</h1>
                <p>No authorization code received yet.</p>
                <p>You can close this window.</p>
            </body>
            </html>
            """
        )
    
    return router