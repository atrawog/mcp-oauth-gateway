"""OAuth 2.1 and RFC 7591 compliant routes with Authlib ResourceProtector
Using Authlib's security framework instead of custom implementations
"""

import json
import logging
import secrets
import time
from typing import Optional
from urllib.parse import urlencode

import redis.asyncio as redis
from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse

from .async_resource_protector import create_async_resource_protector
from .auth_authlib import AuthManager
from .config import Settings
from .models import ClientRegistration, TokenResponse
from .rfc7592 import DynamicClientConfigurationEndpoint

# Set up logging
logger = logging.getLogger(__name__)


def create_oauth_router(settings: Settings, redis_manager, auth_manager: AuthManager) -> APIRouter:
    """Create OAuth router with all endpoints using Authlib ResourceProtector"""
    router = APIRouter()

    # Create AsyncResourceProtector instance - defer Redis client access until runtime
    require_oauth = None

    async def get_redis() -> redis.Redis:
        """Dependency to get Redis client"""
        return redis_manager.client

    # Custom dependency that uses AsyncResourceProtector
    async def verify_bearer_token(request: Request):
        """Verify bearer token using Authlib ResourceProtector"""
        # Create resource protector lazily to ensure Redis is initialized
        nonlocal require_oauth
        if require_oauth is None:
            require_oauth = create_async_resource_protector(
                settings,
                redis_manager.client,
                auth_manager.key_manager,
            )
        # AsyncResourceProtector handles all validation and error raising
        token = await require_oauth.validate_request(request)
        return token

    async def verify_github_user_auth(request: Request, token=Depends(verify_bearer_token)) -> str:
        """Dependency to verify GitHub user authentication for admin operations"""
        # Token is already validated by ResourceProtector
        username = token.get("username")

        if not username:
            raise HTTPException(
                status_code=403,
                detail={"error": "access_denied", "error_description": "No username in token"},
            )

        # Check if user is in allowed list
        allowed_users = (
            settings.allowed_github_users.split(",") if settings.allowed_github_users else []
        )
        # If ALLOWED_GITHUB_USERS is set to '*', allow any authenticated GitHub user
        if allowed_users and "*" not in allowed_users and username not in allowed_users:
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "access_denied",
                    "error_description": f"User '{username}' not authorized for client registration",  # TODO: Break long line
                },
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
            "introspection_endpoint": f"{base_url}/introspect",
            "service_documentation": f"{base_url}/docs",
            "op_policy_uri": f"{base_url}/policy",
            "op_tos_uri": f"{base_url}/terms",
        }

    # JWKS endpoint for RS256 public key distribution
    @router.get("/jwks")
    async def jwks():
        """JSON Web Key Set endpoint - distributes the divine RS256 public key!"""
        jwk = auth_manager.key_manager.get_jwk()
        return {"keys": [jwk]}

    # Dynamic Client Registration endpoint (RFC 7591) - PUBLIC ACCESS
    @router.post("/register", status_code=201)
    async def register_client(
        registration: ClientRegistration,
        redis_client: redis.Redis = Depends(get_redis),
    ):
        """The Divine Registration Portal - RFC 7591 compliant - PUBLIC ACCESS"""
        # Validate redirect URIs - RFC 7591 compliance
        if not registration.redirect_uris:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "invalid_client_metadata",
                    "error_description": "redirect_uris is required",
                },
            )

        # Validate each redirect URI
        for uri in registration.redirect_uris:
            if not uri or not isinstance(uri, str):
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "invalid_redirect_uri",
                        "error_description": "Invalid redirect URI format",
                    },
                )

            # RFC 7591 - Must be HTTPS (except localhost)
            if uri.startswith("http://"):
                if not any(
                    uri.startswith(f"http://{host}")
                    for host in ["localhost", "127.0.0.1", "[::1]"]  # TODO: Break long line
                ):
                    raise HTTPException(
                        status_code=400,
                        detail={
                            "error": "invalid_redirect_uri",
                            "error_description": "HTTP redirect URIs are only allowed for localhost",
                        },
                    )
            elif not uri.startswith("https://") and ":" not in uri:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "invalid_redirect_uri",
                        "error_description": "Redirect URI must use HTTPS or be an app-specific URI",
                    },
                )

        # Generate client credentials
        credentials = auth_manager.generate_client_credentials()
        client_id = credentials["client_id"]
        client_secret = credentials["client_secret"]

        # Calculate client expiration time
        created_at = int(time.time())
        expires_at = 0 if settings.client_lifetime == 0 else created_at + settings.client_lifetime

        # Generate registration access token for RFC 7592 management
        registration_access_token = f"reg-{secrets.token_urlsafe(32)}"

        # Store client in Redis
        client_data = {
            "client_id": client_id,
            "client_secret": client_secret,
            "client_secret_expires_at": expires_at,
            "client_id_issued_at": created_at,
            "redirect_uris": json.dumps(registration.redirect_uris),
            "client_name": registration.client_name or "Unnamed Client",
            "scope": registration.scope or "openid profile email",
            "created_at": created_at,
            "response_types": json.dumps(["code"]),
            "grant_types": json.dumps(["authorization_code", "refresh_token"]),
            "registration_access_token": registration_access_token,
        }

        # Store with expiration matching client lifetime
        if settings.client_lifetime > 0:
            await redis_client.setex(
                f"oauth:client:{client_id}",
                settings.client_lifetime,
                json.dumps(client_data),  # TODO: Break long line
            )
        else:
            await redis_client.set(f"oauth:client:{client_id}", json.dumps(client_data))

        # Return registration response per RFC 7591
        response = {
            "client_id": client_id,
            "client_secret": client_secret,
            "client_secret_expires_at": expires_at,
            "client_id_issued_at": created_at,
            "redirect_uris": registration.redirect_uris,
            "client_name": registration.client_name,
            "scope": registration.scope,
            "registration_access_token": registration_access_token,
            "registration_client_uri": f"https://auth.{settings.base_domain}/register/{client_id}",  # TODO: Break long line
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
        redis_client: redis.Redis = Depends(get_redis),
    ):
        """Portal to authentication realm - initiates GitHub OAuth flow"""
        # Validate client
        client = await auth_manager.get_client(client_id, redis_client)
        if not client:
            # RFC 6749 - MUST NOT redirect on invalid client_id
            return HTMLResponse(
                status_code=400,
                content=f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>OAuth Client Registration Error</title>
                    <style>
                        body {{
                            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                            padding: 40px;
                            max-width: 600px;
                            margin: 0 auto;
                            background-color: #f5f5f5;
                        }}
                        .error-container {{
                            background: white;
                            padding: 30px;
                            border-radius: 10px;
                            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                        }}
                        h1 {{ color: #d73502; }}
                        .error-code {{
                            font-family: monospace;
                            background: #f0f0f0;
                            padding: 2px 6px;
                            border-radius: 3px;
                        }}
                        .client-id {{
                            word-break: break-all;
                            font-family: monospace;
                            font-size: 0.9em;
                        }}
                    </style>
                </head>
                <body>
                    <div class="error-container">
                        <h1>⚠️ OAuth Client Registration Invalid</h1>
                        <p>The application attempting to connect has an invalid or expired client registration.</p>

                        <p><strong>Technical Details:</strong></p>
                        <ul>
                            <li>Error: <span class="error-code">invalid_client</span></li>
                            <li>Client ID: <span class="client-id">{client_id}</span></li>
                        </ul>

                        <p style="margin-top: 30px; color: #666; font-size: 0.9em;">
                            For developers: The client should POST to
                            <code>https://auth.{settings.base_domain}/register</code>
                            to obtain new credentials.
                        </p>
                    </div>
                </body>
                </html>
                """,
            )

        # Validate redirect_uri
        if not client.check_redirect_uri(redirect_uri):
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "invalid_redirect_uri",
                    "error_description": "Redirect URI not registered",
                },
            )

        # Validate response_type
        if not client.check_response_type(response_type):
            return RedirectResponse(
                url=f"{redirect_uri}?error=unsupported_response_type&state={state}",
            )

        # Validate PKCE method
        if code_challenge and code_challenge_method != "S256":
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "invalid_request",
                    "error_description": "Only S256 PKCE method is supported",
                },
            )

        # Store authorization request state
        auth_state = secrets.token_urlsafe(32)
        auth_data = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": scope,
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": code_challenge_method,
        }

        await redis_client.setex(
            f"oauth:state:{auth_state}",
            300,
            json.dumps(auth_data),
        )  # TODO: Break long line
        logger.info(
            f"Created OAuth state: {auth_state} for client: {client_id}, original state: {state}",
        )

        # Redirect to GitHub OAuth
        github_params = {
            "client_id": settings.github_client_id,
            "redirect_uri": f"https://auth.{settings.base_domain}/callback",
            "scope": "user:email",
            "state": auth_state,
        }

        github_url = f"https://github.com/login/oauth/authorize?{urlencode(github_params)}"  # TODO: Break long line
        return RedirectResponse(
            url=github_url,
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0",
            },
        )

    # Callback endpoint
    @router.get("/callback")
    async def oauth_callback(
        code: str = Query(...),
        state: str = Query(...),
        redis_client: redis.Redis = Depends(get_redis),
    ):
        """The blessed return path - handles GitHub OAuth callback"""
        # Retrieve authorization state
        logger.info(
            f"Callback received with state: {state}, code: {code[:8]}..." if code else "no code",
        )
        auth_data_str = await redis_client.get(f"oauth:state:{state}")
        if not auth_data_str:
            logger.warning(f"State not found in Redis: {state}")
            # Check if any similar states exist (for debugging)
            all_states = await redis_client.keys("oauth:state:*")
            logger.debug(f"Current states in Redis: {len(all_states)} total")

            # Redirect to user-friendly error page instead of returning JSON
            return RedirectResponse(
                url=f"/error?{urlencode({'error': 'invalid_request', 'error_description': 'Invalid or expired state. This usually happens when you take longer than 5 minutes to complete the authentication, or when you refresh an old authentication page.'})}",
                status_code=302,
                headers={
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache",
                    "Expires": "0",
                },
            )

        auth_data = json.loads(auth_data_str)
        logger.info(
            f"State validated successfully: {state}, client_id: {auth_data.get('client_id')}",
        )

        # Exchange GitHub code
        user_info = await auth_manager.exchange_github_code(code)

        if not user_info:
            return RedirectResponse(
                url=f"{auth_data['redirect_uri']}?error=server_error&state={auth_data['state']}",  # TODO: Break long line
            )

        # Check if user is allowed
        allowed_users = (
            settings.allowed_github_users.split(",") if settings.allowed_github_users else []
        )
        # If ALLOWED_GITHUB_USERS is set to '*', allow any authenticated GitHub user
        if allowed_users and "*" not in allowed_users and user_info["login"] not in allowed_users:
            return RedirectResponse(
                url=f"{auth_data['redirect_uri']}?error=access_denied&state={auth_data['state']}",  # TODO: Break long line
            )

        # Generate authorization code
        auth_code = secrets.token_urlsafe(32)

        # Store authorization code with user info
        code_data = {
            **auth_data,
            "user_id": str(user_info["id"]),
            "username": user_info["login"],
            "email": user_info.get("email", ""),
            "name": user_info.get("name", ""),
        }

        await redis_client.setex(
            f"oauth:code:{auth_code}",
            31536000,
            json.dumps(code_data),
        )  # TODO: Break long line

        # Clean up state
        await redis_client.delete(f"oauth:state:{state}")
        logger.info(f"Cleaned up state after successful auth: {state}")

        # Handle out-of-band redirect URI
        if auth_data["redirect_uri"] == "urn:ietf:wg:oauth:2.0:oob":
            return RedirectResponse(
                url=f"https://auth.{settings.base_domain}/success?code={auth_code}&state={auth_data['state']}",  # TODO: Break long line
                headers={
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache",
                    "Expires": "0",
                },
            )

        # Normal redirect
        redirect_params = {"code": auth_code, "state": auth_data["state"]}

        return RedirectResponse(
            url=f"{auth_data['redirect_uri']}?{urlencode(redirect_params)}",  # TODO: Break long line
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0",
            },
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
        redis_client: redis.Redis = Depends(get_redis),
    ):
        """The transmutation chamber - exchanges codes for tokens"""
        # Validate client
        client = await auth_manager.get_client(client_id, redis_client)
        if not client:
            raise HTTPException(
                status_code=401,
                detail={
                    "error": "invalid_client",
                    "error_description": "Client authentication failed",
                },
                headers={"WWW-Authenticate": "Basic"},
            )

        # Validate client secret
        if client_secret and not client.check_client_secret(client_secret):
            raise HTTPException(
                status_code=401,
                detail={
                    "error": "invalid_client",
                    "error_description": "Invalid client credentials",
                },
                headers={"WWW-Authenticate": "Basic"},
            )

        # Validate grant type
        if not client.check_grant_type(grant_type):
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "unsupported_grant_type",
                    "error_description": f"Grant type '{grant_type}' is not supported",
                },
            )

        if grant_type == "authorization_code":
            if not code:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "invalid_request",
                        "error_description": "Missing authorization code",
                    },
                )

            # Retrieve authorization code
            code_data_str = await redis_client.get(f"oauth:code:{code}")
            if not code_data_str:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "invalid_grant",
                        "error_description": "Invalid or expired authorization code",
                    },
                )

            code_data = json.loads(code_data_str)

            # Validate redirect_uri
            if redirect_uri != code_data["redirect_uri"]:
                raise HTTPException(
                    status_code=400,
                    detail={"error": "invalid_grant", "error_description": "Redirect URI mismatch"},
                )

            # Validate PKCE
            if code_data.get("code_challenge"):
                if not code_verifier:
                    raise HTTPException(
                        status_code=400,
                        detail={
                            "error": "invalid_grant",
                            "error_description": "PKCE code_verifier required",
                        },
                    )

                if not auth_manager.verify_pkce_challenge(
                    code_verifier,
                    code_data["code_challenge"],
                    code_data["code_challenge_method"],
                ):
                    raise HTTPException(
                        status_code=400,
                        detail={
                            "error": "invalid_grant",
                            "error_description": "PKCE verification failed",
                        },
                    )

            # Generate tokens
            access_token = await auth_manager.create_jwt_token(
                {
                    "sub": code_data["user_id"],
                    "username": code_data["username"],
                    "email": code_data["email"],
                    "name": code_data["name"],
                    "scope": code_data["scope"],
                    "client_id": client_id,
                },
                redis_client,
            )

            refresh_token_value = await auth_manager.create_refresh_token(
                {
                    "user_id": code_data["user_id"],
                    "username": code_data["username"],
                    "client_id": client_id,
                    "scope": code_data["scope"],
                },
                redis_client,
            )

            # Delete used authorization code
            await redis_client.delete(f"oauth:code:{code}")

            return TokenResponse(
                access_token=access_token,
                expires_in=settings.access_token_lifetime,
                refresh_token=refresh_token_value,
                scope=code_data["scope"],
            )

        elif grant_type == "refresh_token":
            if not refresh_token:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "invalid_request",
                        "error_description": "Missing refresh token",
                    },
                )

            # Retrieve refresh token data
            refresh_data_str = await redis_client.get(f"oauth:refresh:{refresh_token}")
            if not refresh_data_str:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "invalid_grant",
                        "error_description": "Invalid or expired refresh token",
                    },
                )

            refresh_data = json.loads(refresh_data_str)

            # Generate new access token
            access_token = await auth_manager.create_jwt_token(
                {
                    "sub": refresh_data["user_id"],
                    "username": refresh_data["username"],
                    "scope": refresh_data["scope"],
                    "client_id": client_id,
                },
                redis_client,
            )

            return TokenResponse(
                access_token=access_token,
                expires_in=settings.access_token_lifetime,
                scope=refresh_data["scope"],
            )

        else:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "unsupported_grant_type",
                    "error_description": f"Grant type '{grant_type}' not supported",
                },
            )

    # ForwardAuth verification endpoint - Using ResourceProtector
    @router.get("/verify")
    @router.post("/verify")
    async def verify_token(request: Request, token=Depends(verify_bearer_token)):
        """Token examination oracle - validates Bearer tokens for Traefik"""
        # Token is already validated by ResourceProtector
        # Return success with user info headers
        return Response(
            status_code=200,
            headers={
                "X-User-Id": str(token.get("sub", "")),
                "X-User-Name": token.get("username", ""),
                "X-Auth-Token": request.headers.get("Authorization", "").replace("Bearer ", ""),
            },
        )

    # Token revocation endpoint (RFC 7009)
    @router.post("/revoke")
    async def revoke_token(
        token: str = Form(...),
        token_type_hint: Optional[str] = Form(None),
        client_id: str = Form(...),
        client_secret: Optional[str] = Form(None),
        redis_client: redis.Redis = Depends(get_redis),
    ):
        """Token banishment altar - revokes tokens"""
        # Validate client
        client = await auth_manager.get_client(client_id, redis_client)
        if not client:
            # RFC 7009 - invalid client should still return 200
            return Response(status_code=200)

        if client_secret and not client.check_client_secret(client_secret):
            return Response(status_code=200)

        # Revoke token
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
        redis_client: redis.Redis = Depends(get_redis),
    ):
        """Token examination oracle - RFC 7662 compliant"""
        # Validate client
        client = await auth_manager.get_client(client_id, redis_client)
        if not client or (client_secret and not client.check_client_secret(client_secret)):
            return {"active": False}

        # Introspect token
        introspection_result = await auth_manager.introspect_token(token, redis_client)

        return introspection_result

    # OAuth error page
    @router.get("/error")
    async def oauth_error_page(
        error: str = Query(...),
        error_description: Optional[str] = Query(None),
    ):
        """User-friendly error page for OAuth flow failures"""
        return HTMLResponse(
            content=f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>OAuth Error</title>
                <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
                <meta http-equiv="Pragma" content="no-cache">
                <meta http-equiv="Expires" content="0">
            </head>
            <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; padding: 40px; max-width: 600px; margin: 0 auto;">
                <div style="background: #fef2f2; border: 1px solid #fecaca; border-radius: 8px; padding: 20px; margin-bottom: 20px;">
                    <h1 style="color: #dc2626; margin: 0 0 10px 0;">❌ OAuth Authentication Failed</h1>
                    <p style="font-size: 18px; margin: 0;"><strong>Error:</strong> {error}</p>
                    <p style="margin: 10px 0 0 0;"><strong>Details:</strong> {error_description or "No additional details available"}</p>
                </div>

                <div style="background: #f3f4f6; border-radius: 8px; padding: 20px; margin-bottom: 20px;">
                    <h2 style="margin: 0 0 10px 0;">What happened?</h2>
                    <p style="margin: 0;">{"Your authentication session expired. OAuth state tokens are valid for only 5 minutes for security reasons." if "expired state" in (error_description or "").lower() else "The OAuth authentication process encountered an error."}</p>
                </div>

                <div style="background: #dbeafe; border: 1px solid #93c5fd; border-radius: 8px; padding: 20px;">
                    <h2 style="color: #1d4ed8; margin: 0 0 10px 0;">How to fix this:</h2>
                    <ol style="margin: 10px 0; padding-left: 20px;">
                        <li><strong>Close this browser tab</strong></li>
                        <li><strong>Close any other OAuth tabs</strong> from previous attempts</li>
                        <li><strong>Run the command again:</strong> <code style="background: #f3f4f6; padding: 2px 4px; border-radius: 3px;">just generate-github-token</code></li>
                        <li><strong>Complete the flow quickly</strong> (within 5 minutes)</li>
                    </ol>
                    <p style="margin: 10px 0 0 0; font-size: 14px; color: #4b5563;">
                        <strong>Tip:</strong> If you see multiple browser tabs open, close all but the newest one to avoid confusion.
                    </p>
                </div>

                <p style="text-align: center; margin-top: 30px; color: #6b7280;">
                    This page prevents caching. You can safely close this tab.
                </p>
            </body>
            </html>
            """,
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0",
            },
        )

    # OAuth success page
    @router.get("/success")
    async def oauth_success(
        code: Optional[str] = Query(None),
        state: Optional[str] = Query(None),
        error: Optional[str] = Query(None),
        error_description: Optional[str] = Query(None),
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
                    <p><strong>Description:</strong> {error_description or "No description provided"}</p>
                    <p>You can close this window.</p>
                </body>
                </html>
                """,
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
                """,
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
            """,
        )

    # RFC 7592 - Dynamic Client Registration Management Protocol
    @router.get("/register/{client_id}")
    async def get_client_registration(
        client_id: str,
        request: Request,
        redis_client: redis.Redis = Depends(get_redis),
    ):
        """Get client registration information - RFC 7592 compliant"""
        config_endpoint = DynamicClientConfigurationEndpoint(settings, redis_client)

        try:
            client = await config_endpoint.authenticate_client(request, client_id)
        except ValueError as e:
            raise HTTPException(status_code=404, detail="Client not found") from e

        if not client:
            auth_header = request.headers.get("Authorization", "")
            if not auth_header:
                raise HTTPException(
                    status_code=401,
                    detail="Missing authentication",
                    headers={"WWW-Authenticate": 'Bearer realm="auth"'},
                )
            elif not auth_header.startswith("Bearer "):
                raise HTTPException(
                    status_code=401,
                    detail="Invalid authentication method",
                    headers={"WWW-Authenticate": 'Bearer realm="auth"'},
                )
            else:
                raise HTTPException(
                    status_code=403,
                    detail="Invalid or expired registration access token",
                )

        if not await config_endpoint.check_permission(client, request):
            raise HTTPException(status_code=403, detail="Insufficient permissions")

        return config_endpoint.generate_client_configuration_response(client)

    @router.put("/register/{client_id}")
    async def update_client_registration(
        client_id: str,
        request: Request,
        client_metadata: dict,
        redis_client: redis.Redis = Depends(get_redis),
    ):
        """Update client registration - RFC 7592 compliant"""
        config_endpoint = DynamicClientConfigurationEndpoint(settings, redis_client)

        try:
            client = await config_endpoint.authenticate_client(request, client_id)
        except ValueError as e:
            raise HTTPException(status_code=404, detail="Client not found") from e

        if not client:
            auth_header = request.headers.get("Authorization", "")
            if not auth_header:
                raise HTTPException(
                    status_code=401,
                    detail="Missing authentication",
                    headers={"WWW-Authenticate": 'Bearer realm="auth"'},
                )
            elif not auth_header.startswith("Bearer "):
                raise HTTPException(
                    status_code=401,
                    detail="Invalid authentication method",
                    headers={"WWW-Authenticate": 'Bearer realm="auth"'},
                )
            else:
                raise HTTPException(
                    status_code=403,
                    detail="Invalid or expired registration access token",
                )

        if not await config_endpoint.check_permission(client, request):
            raise HTTPException(status_code=403, detail="Insufficient permissions")

        # Validate redirect_uris if provided
        if "redirect_uris" in client_metadata:
            if not client_metadata["redirect_uris"]:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "invalid_client_metadata",
                        "error_description": "redirect_uris cannot be empty",
                    },
                )

            for uri in client_metadata["redirect_uris"]:
                if not uri or not isinstance(uri, str):
                    raise HTTPException(
                        status_code=400,
                        detail={
                            "error": "invalid_redirect_uri",
                            "error_description": "Invalid redirect URI format",
                        },
                    )

                if uri.startswith("http://"):
                    if not any(
                        uri.startswith(f"http://{host}")
                        for host in ["localhost", "127.0.0.1", "[::1]"]
                    ):
                        raise HTTPException(
                            status_code=400,
                            detail={
                                "error": "invalid_redirect_uri",
                                "error_description": "HTTP redirect URIs are only allowed for localhost",
                            },
                        )
                elif not uri.startswith("https://") and ":" not in uri:
                    raise HTTPException(
                        status_code=400,
                        detail={
                            "error": "invalid_redirect_uri",
                            "error_description": "Redirect URI must use HTTPS or be an app-specific URI",
                        },
                    )

        try:
            updated_client = await config_endpoint.update_client(client, client_metadata)
            return config_endpoint.generate_client_configuration_response(updated_client)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e)) from e

    @router.delete("/register/{client_id}")
    async def delete_client_registration(
        client_id: str,
        request: Request,
        redis_client: redis.Redis = Depends(get_redis),
    ):
        """Delete client registration - RFC 7592 compliant"""
        config_endpoint = DynamicClientConfigurationEndpoint(settings, redis_client)

        try:
            client = await config_endpoint.authenticate_client(request, client_id)
        except ValueError as e:
            raise HTTPException(status_code=404, detail="Client not found") from e

        if not client:
            auth_header = request.headers.get("Authorization", "")
            if not auth_header:
                raise HTTPException(
                    status_code=401,
                    detail="Missing authentication",
                    headers={"WWW-Authenticate": 'Bearer realm="auth"'},
                )
            elif not auth_header.startswith("Bearer "):
                raise HTTPException(
                    status_code=401,
                    detail="Invalid authentication method",
                    headers={"WWW-Authenticate": 'Bearer realm="auth"'},
                )
            else:
                raise HTTPException(
                    status_code=403,
                    detail="Invalid or expired registration access token",
                )

        if not await config_endpoint.check_permission(client, request):
            raise HTTPException(status_code=403, detail="Insufficient permissions")

        await config_endpoint.delete_client(client)
        return Response(status_code=204)

    return router
