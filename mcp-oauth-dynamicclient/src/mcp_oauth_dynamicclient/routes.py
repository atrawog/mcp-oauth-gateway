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
from authlib.jose.errors import JoseError

from .config import Settings
from .models import ClientRegistration, TokenResponse, ErrorResponse
from .auth_authlib import AuthManager, OAuth2Client


def create_oauth_router(settings: Settings, redis_manager, auth_manager: AuthManager) -> APIRouter:
    """Create OAuth router with all endpoints"""
    
    router = APIRouter()
    
    async def get_redis() -> redis.Redis:
        """Dependency to get Redis client"""
        return redis_manager.client
    
    async def verify_github_user_auth(request: Request) -> str:
        """Dependency to verify GitHub user authentication for admin operations"""
        # Check if user has valid session from GitHub OAuth
        auth_header = request.headers.get("Authorization", "")
        
        if not auth_header.startswith("Bearer "):
            # No auth - initiate GitHub OAuth flow
            raise HTTPException(
                status_code=401,
                detail={
                    "error": "authorization_required",
                    "error_description": "GitHub authentication required for client registration",
                    "authorization_endpoint": f"https://auth.{settings.base_domain}/authorize"
                },
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        token = auth_header[7:]  # Remove "Bearer " prefix
        
        # Verify token and get user info
        payload = await auth_manager.verify_jwt_token(token, redis_manager.client)
        
        if not payload:
            raise HTTPException(
                status_code=401,
                detail={
                    "error": "invalid_token",
                    "error_description": "Invalid or expired token"
                },
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Check if user is in allowed list
        username = payload.get("username")
        if not username:
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "access_denied",
                    "error_description": "No username in token"
                }
            )
        
        allowed_users = settings.allowed_github_users.split(",") if settings.allowed_github_users else []
        if allowed_users and username not in allowed_users:
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "access_denied",
                    "error_description": f"User '{username}' not authorized for client registration"
                }
            )
        
        return username
    
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
            "code_challenge_methods_supported": ["S256"],
            "grant_types_supported": ["authorization_code", "refresh_token"],
            "revocation_endpoint": f"{base_url}/revoke",
            "introspection_endpoint": f"{base_url}/introspect"
        }
    
    # Dynamic Client Registration endpoint (RFC 7591) - GITHUB USER PROTECTED
    @router.post("/register", status_code=201)
    async def register_client(
        registration: ClientRegistration,
        redis_client: redis.Redis = Depends(get_redis),
        github_username: str = Depends(verify_github_user_auth)
    ):
        """The Divine Registration Portal - RFC 7591 compliant - GITHUB USER PROTECTED"""
        
        # Validate redirect URIs
        if not registration.redirect_uris:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "invalid_client_metadata",
                    "error_description": "redirect_uris is required"
                }
            )
        
        # Generate client credentials using Authlib patterns
        credentials = auth_manager.generate_client_credentials()
        client_id = credentials["client_id"]
        client_secret = credentials["client_secret"]
        
        # Store client in Redis (eternal storage)
        client_data = {
            "client_id": client_id,
            "client_secret": client_secret,
            "client_secret_expires_at": credentials["client_secret_expires_at"],
            "redirect_uris": json.dumps(registration.redirect_uris),
            "client_name": registration.client_name or "Unnamed Client",
            "scope": registration.scope or "openid profile email",
            "created_at": int(time.time()),
            "response_types": json.dumps(["code"]),
            "grant_types": json.dumps(["authorization_code", "refresh_token"])
        }
        
        # Store with sacred key pattern
        await redis_client.set(f"oauth:client:{client_id}", json.dumps(client_data))
        
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
        
        # Validate client using Authlib OAuth2Client
        client = await auth_manager.get_client(client_id, redis_client)
        if not client:
            # RFC 6749 - MUST NOT redirect on invalid client_id
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "invalid_client",
                    "error_description": "Unknown client"
                }
            )
        
        # Validate redirect_uri using Authlib client
        if not client.check_redirect_uri(redirect_uri):
            # RFC 6749 - MUST NOT redirect on invalid redirect_uri
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "invalid_redirect_uri",
                    "error_description": "Redirect URI not registered"
                }
            )
        
        # Validate response_type using Authlib client
        if not client.check_response_type(response_type):
            return RedirectResponse(
                url=f"{redirect_uri}?error=unsupported_response_type&state={state}"
            )
        
        # Validate PKCE method - only S256 is blessed by CLAUDE.md
        if code_challenge and code_challenge_method != "S256":
            # Plain method is FORBIDDEN per sacred commandments!
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "invalid_request",
                    "error_description": "Only S256 PKCE method is supported. Plain method is deprecated per CLAUDE.md sacred laws!"
                }
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
        
        # Exchange GitHub code using Authlib
        user_info = await auth_manager.exchange_github_code(code)
        
        if not user_info:
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
        
        # Validate client using Authlib OAuth2Client
        client = await auth_manager.get_client(client_id, redis_client)
        if not client:
            raise HTTPException(
                status_code=401,
                detail={
                    "error": "invalid_client",
                    "error_description": "Unknown client"
                },
                headers={"WWW-Authenticate": "Basic"}
            )
        
        # Validate client secret using Authlib
        if client_secret and not client.check_client_secret(client_secret):
            raise HTTPException(
                status_code=401,
                detail={
                    "error": "invalid_client",
                    "error_description": "Invalid client credentials"
                },
                headers={"WWW-Authenticate": "Basic"}
            )
        
        # Validate grant type using Authlib
        if not client.check_grant_type(grant_type):
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "unsupported_grant_type",
                    "error_description": f"Grant type '{grant_type}' is not supported"
                }
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
            
            # Create refresh token using Authlib
            refresh_token_value = await auth_manager.create_refresh_token(
                {
                    "user_id": code_data["user_id"],
                    "username": code_data["username"],
                    "client_id": client_id,
                    "scope": code_data["scope"]
                },
                redis_client
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
        
        # Verify token using Authlib
        payload = await auth_manager.verify_jwt_token(token, redis_client)
        
        if not payload:
            raise HTTPException(
                status_code=401,
                detail={
                    "error": "invalid_token",
                    "error_description": "Token invalid, expired, or revoked"
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
        
    # Token revocation endpoint (RFC 7009)
    @router.post("/revoke")
    async def revoke_token(
        token: str = Form(...),
        token_type_hint: Optional[str] = Form(None),
        client_id: str = Form(...),
        client_secret: Optional[str] = Form(None),
        redis_client: redis.Redis = Depends(get_redis)
    ):
        """Token banishment altar - revokes tokens using Authlib"""
        
        # Validate client using Authlib OAuth2Client
        client = await auth_manager.get_client(client_id, redis_client)
        if not client:
            # RFC 7009 - invalid client should still return 200
            return Response(status_code=200)
        
        if client_secret and not client.check_client_secret(client_secret):
            return Response(status_code=200)
        
        # Revoke token using Authlib
        await auth_manager.revoke_token(token, redis_client)
        
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
        """Token examination oracle - uses Authlib for RFC 7662 compliance"""
        
        # Validate client using Authlib OAuth2Client
        client = await auth_manager.get_client(client_id, redis_client)
        if not client or (client_secret and not client.check_client_secret(client_secret)):
            return {"active": False}
        
        # Introspect token using Authlib
        introspection_result = await auth_manager.introspect_token(token, redis_client)
        
        return introspection_result
    
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