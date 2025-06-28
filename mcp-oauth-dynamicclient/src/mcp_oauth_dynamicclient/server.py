"""Main server module for MCP OAuth Dynamic Client"""

import json
import logging

# Configure logging
import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse

from .auth_authlib import AuthManager
from .config import Settings
from .redis_client import RedisManager
from .routes import create_oauth_router

log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
log_level = os.environ.get("LOG_LEVEL", "INFO")

# Configure logging handlers
handlers = []
# Always log to console
handlers.append(logging.StreamHandler())

# Add file handler if LOG_FILE is specified
log_file = os.environ.get("LOG_FILE")
if log_file:
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    file_handler = logging.FileHandler(log_file)
    handlers.append(file_handler)

logging.basicConfig(level=getattr(logging, log_level), format=log_format, handlers=handlers)


def _is_browser_request(request: Request) -> bool:
    """Check if request is from a browser based on Accept header."""
    accept_header = request.headers.get("Accept", "")
    return "text/html" in accept_header and "application/json" not in accept_header


def _generate_gateway_error_html(error_description: str) -> str:
    """Generate a human-friendly HTML error page for the MCP OAuth Gateway."""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>MCP OAuth Gateway - Authentication Required</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                padding: 40px;
                max-width: 800px;
                margin: 0 auto;
                background-color: #f5f5f5;
                line-height: 1.6;
            }}
            .container {{
                background: white;
                padding: 40px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            h1 {{
                color: #2563eb;
                margin-top: 0;
            }}
            h2 {{
                color: #1e40af;
                margin-top: 30px;
            }}
            .welcome {{
                font-size: 1.1em;
                color: #374151;
                margin: 20px 0;
            }}
            .error-box {{
                background: #fef2f2;
                border: 1px solid #fecaca;
                border-radius: 6px;
                padding: 16px;
                margin: 20px 0;
            }}
            .error-message {{
                color: #dc2626;
                font-weight: 600;
            }}
            code {{
                font-family: 'Monaco', 'Consolas', monospace;
                background: #f3f4f6;
                padding: 2px 6px;
                border-radius: 3px;
                font-size: 0.9em;
            }}
            .protocol-info {{
                background: #ecfdf5;
                border: 1px solid #a7f3d0;
                border-radius: 6px;
                padding: 16px;
                margin: 20px 0;
            }}
            .feature-list {{
                background: #f0f9ff;
                border: 1px solid #bae6fd;
                border-radius: 6px;
                padding: 20px;
                margin: 20px 0;
            }}
            .feature-list ul {{
                margin: 10px 0;
                padding-left: 20px;
            }}
            .feature-list li {{
                margin: 8px 0;
            }}
            .docs-link {{
                display: inline-block;
                background: #2563eb;
                color: white;
                padding: 12px 24px;
                border-radius: 6px;
                text-decoration: none;
                margin: 10px 10px 10px 0;
                font-weight: 600;
            }}
            .docs-link:hover {{
                background: #1d4ed8;
            }}
            .spec-link {{
                display: inline-block;
                background: #059669;
                color: white;
                padding: 12px 24px;
                border-radius: 6px;
                text-decoration: none;
                margin: 10px 10px 10px 0;
                font-weight: 600;
            }}
            .spec-link:hover {{
                background: #047857;
            }}
            .claude-link:hover {{
                background: #7c3aed;
            }}
            .tech-note {{
                background: #f9fafb;
                border: 1px solid #e5e7eb;
                border-radius: 6px;
                padding: 16px;
                margin-top: 30px;
                font-size: 0.9em;
                color: #6b7280;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔐 Welcome to the MCP OAuth Gateway!</h1>

            <p class="welcome">
                You've reached the MCP OAuth Gateway - your secure entry point to Model Context Protocol services.
                This gateway protects and manages access to MCP servers, ensuring only authorized clients can connect.
            </p>

            <div class="error-box">
                <div class="error-message">Authentication Required</div>
                <p>{error_description}</p>
            </div>

            <h2>What This Gateway Does</h2>
            <p>
                This MCP OAuth Gateway acts as a security layer between AI applications and MCP servers.
                It implements OAuth 2.1 authentication to ensure that only authorized clients can access the powerful
                capabilities provided by MCP services.
            </p>

            <div class="protocol-info">
                <strong>🚀 MCP Protocol Implementation</strong>
                <p style="margin: 8px 0 0 0;">
                    This gateway implements <strong>MCP Protocol Version 2025-06-18</strong>, the latest specification
                    for Model Context Protocol communication between AI assistants and external tools.
                </p>
            </div>

            <div class="claude-info" style="background: #f3e8ff; border: 1px solid #c084fc; border-radius: 6px; padding: 16px; margin: 20px 0;">
                <strong>🤖 Claude.ai Integration</strong>
                <p style="margin: 8px 0 0 0;">
                    This gateway can be used as a <strong>Custom Integration for Remote MCP</strong> in Claude.ai!
                    Simply add this gateway's URL when configuring custom integrations in Claude to access all
                    protected MCP services through a single secure endpoint.
                </p>
            </div>

            <div class="feature-list">
                <strong>Gateway Features:</strong>
                <ul>
                    <li><strong>OAuth 2.1 Compliance</strong> - Modern authentication with PKCE support</li>
                    <li><strong>Dynamic Client Registration</strong> - RFC 7591 compliant automatic client setup</li>
                    <li><strong>GitHub OAuth Integration</strong> - Secure user authentication via GitHub</li>
                    <li><strong>JWT Token Management</strong> - Cryptographically signed access tokens</li>
                    <li><strong>Multi-Service Support</strong> - Route to multiple MCP servers seamlessly</li>
                    <li><strong>Streamable HTTP Transport</strong> - Efficient protocol communication</li>
                </ul>
            </div>

            <div style="margin-top: 30px;">
                <a href="https://atrawog.github.io/mcp-oauth-gateway/" class="docs-link">
                    📚 Gateway Documentation
                </a>
                <a href="https://modelcontextprotocol.io/specification/2025-06-18" class="spec-link">
                    📖 MCP Specification
                </a>
                <a href="https://support.anthropic.com/en/articles/11175166-about-custom-integrations-using-remote-mcp" class="claude-link" style="display: inline-block; background: #8b5cf6; color: white; padding: 12px 24px; border-radius: 6px; text-decoration: none; margin: 10px 10px 10px 0; font-weight: 600;">
                    🤖 Claude Integration Guide
                </a>
            </div>

            <div class="tech-note">
                <strong>Why am I seeing this?</strong> Your request is missing the required <code>Authorization</code> header.
                This gateway requires Bearer token authentication for all MCP endpoints. Check the documentation
                above to learn how to obtain and use access tokens.
            </div>
        </div>
    </body>
    </html>
    """


def create_app(settings: Settings = None) -> FastAPI:
    """Create and configure the FastAPI application"""
    if settings is None:
        settings = Settings()

    # Initialize managers
    redis_manager = RedisManager(settings)
    auth_manager = AuthManager(settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Manage application lifecycle"""
        # Startup
        await redis_manager.initialize()
        yield
        # Shutdown
        await redis_manager.close()

    # Create FastAPI app
    app = FastAPI(
        title="MCP OAuth Gateway - Auth Service",
        description="Sacred Auth Service following OAuth 2.1 and RFC 7591 divine specifications",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Add custom exception handler for 401 errors
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Handle HTTP exceptions, returning HTML for browser requests on 401 errors"""
        if exc.status_code == 401 and _is_browser_request(request):
            # Extract error description from the exception detail
            error_description = "Authentication required"
            if isinstance(exc.detail, dict) and "error_description" in exc.detail:
                error_description = exc.detail["error_description"]

            return HTMLResponse(
                status_code=401,
                content=_generate_gateway_error_html(error_description),
                headers=exc.headers or {"WWW-Authenticate": "Bearer"},
            )

        # For non-browser requests or other status codes, return JSON
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.detail,
            headers=exc.headers,
        )

    # CORS is handled by Traefik middleware - no need to configure here
    # This ensures CORS headers are set in only one place as required

    # Add request logging middleware to capture Traefik forwarded headers
    @app.middleware("http")
    async def log_traefik_headers(request: Request, call_next):
        """Log Traefik forwarded headers and request details for security monitoring."""
        logger = logging.getLogger(__name__)
        start_time = time.time()

        # Extract Traefik forwarded headers
        traefik_headers = {
            "x-real-ip": request.headers.get("x-real-ip"),
            "x-forwarded-for": request.headers.get("x-forwarded-for"),
            "x-forwarded-host": request.headers.get("x-forwarded-host"),
            "x-forwarded-proto": request.headers.get("x-forwarded-proto"),
            "x-forwarded-port": request.headers.get("x-forwarded-port"),
            "x-forwarded-server": request.headers.get("x-forwarded-server"),
            "user-agent": request.headers.get("user-agent"),
            "host": request.headers.get("host"),
        }

        # Filter out None values
        traefik_headers = {k: v for k, v in traefik_headers.items() if v is not None}

        # Log request with Traefik headers
        request_data = {
            "type": "auth_request",
            "method": request.method,
            "path": str(request.url.path),
            "real_ip": traefik_headers.get("x-real-ip", "unknown"),
            "forwarded_for": traefik_headers.get("x-forwarded-for", "unknown"),
            "forwarded_host": traefik_headers.get("x-forwarded-host", "unknown"),
            "host": traefik_headers.get("host", "unknown"),
            "user_agent": traefik_headers.get("user-agent", "unknown"),
            "forwarded_proto": traefik_headers.get("x-forwarded-proto", "unknown"),
            "forwarded_port": traefik_headers.get("x-forwarded-port", "unknown"),
        }
        logger.info(
            "AUTH REQUEST - Method: %s | "
            "Path: %s | "
            "Real-IP: %s | "
            "Forwarded-For: %s | "
            "Host: %s | "
            "User-Agent: %s | "
            "JSON: %s",
            request.method,
            request.url.path,
            traefik_headers.get("x-real-ip", "unknown"),
            traefik_headers.get("x-forwarded-for", "unknown"),
            traefik_headers.get("x-forwarded-host", traefik_headers.get("host", "unknown")),
            traefik_headers.get("user-agent", "unknown"),
            json.dumps(request_data),
        )

        # Process the request
        response = await call_next(request)

        # Calculate response time
        process_time = time.time() - start_time

        # Log response with timing
        response_data = {
            "type": "auth_response",
            "status": response.status_code,
            "duration_seconds": round(process_time, 3),
            "path": str(request.url.path),
            "real_ip": traefik_headers.get("x-real-ip", "unknown"),
            "method": request.method,
        }
        logger.info(
            "AUTH RESPONSE - Status: %s | Time: %.3fs | Path: %s | Real-IP: %s | JSON: %s",
            response.status_code,
            process_time,
            request.url.path,
            traefik_headers.get("x-real-ip", "unknown"),
            json.dumps(response_data),
        )

        return response

    # Include OAuth routes with Authlib ResourceProtector for enhanced security
    oauth_router = create_oauth_router(settings, redis_manager, auth_manager)
    app.include_router(oauth_router)

    return app


# Create a default app instance for uvicorn
app = create_app()
