"""Configuration management for MCP HTTP-to-stdio proxy."""

from datetime import UTC
from datetime import datetime

from pydantic import Field
from pydantic import field_validator
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with .env file support."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore")

    # MCP Server Configuration
    mcp_server_url: str = Field(..., description="URL of the MCP server to connect to")

    # OAuth Configuration - MCP CLIENT REALM ONLY!
    # NEVER use OAUTH_* variables - those are server tokens!
    oauth_client_id: str | None = Field(
        None,
        description="OAuth client ID (populated after registration)",
        alias="MCP_CLIENT_ID",
    )
    oauth_client_secret: str | None = Field(
        None,
        description="OAuth client secret (populated after registration)",
        alias="MCP_CLIENT_SECRET",
    )
    oauth_access_token: str | None = Field(
        None,
        description="Current OAuth access token",
        alias="MCP_CLIENT_ACCESS_TOKEN",
    )
    oauth_refresh_token: str | None = Field(
        None,
        description="OAuth refresh token for token renewal",
        alias="MCP_CLIENT_REFRESH_TOKEN",
    )
    oauth_token_expires_at: datetime | None = Field(None, description="Token expiration timestamp")

    # OAuth Server URLs (discovered automatically)
    # OAuth endpoints - discovered automatically, not stored
    oauth_issuer: str | None = Field(None, description="OAuth issuer URL (discovered from server)")
    oauth_authorization_url: str | None = Field(None, description="OAuth authorization endpoint (discovered)")
    oauth_token_url: str | None = Field(None, description="OAuth token endpoint (discovered)")
    oauth_device_auth_url: str | None = Field(None, description="OAuth device authorization endpoint (discovered)")
    oauth_registration_url: str | None = Field(
        None,
        description="OAuth dynamic client registration endpoint (discovered)",
    )
    oauth_metadata_url: str | None = Field(None, description="OAuth server metadata discovery URL (discovered)")

    # RFC 7592 Management Fields
    registration_access_token: str | None = Field(
        None,
        description="Bearer token for managing client registration (RFC 7592)",
        alias="MCP_CLIENT_REGISTRATION_TOKEN",
    )
    registration_client_uri: str | None = Field(
        None,
        description="URI for managing this client registration (RFC 7592)",
        alias="MCP_CLIENT_REGISTRATION_URI",
    )

    # Client Configuration
    client_name: str = Field("mcp-http-stdio", description="Client name for OAuth registration")
    client_version: str = Field("0.1.0", description="Client version")

    # Session Configuration
    session_timeout: int = Field(300, description="Session timeout in seconds", ge=60, le=3600)
    request_timeout: int = Field(30, description="Request timeout in seconds", ge=5, le=300)

    # Logging
    log_level: str = Field(
        "INFO",
        description="Logging level",
        pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$",
    )

    # NO CREDENTIAL FILES! Everything through .env as divinely commanded!

    # Security
    verify_ssl: bool = Field(True, description="Verify SSL certificates")

    @field_validator("oauth_token_expires_at", mode="before")
    @classmethod
    def parse_datetime(cls, v):
        """Parse datetime from ISO string if needed."""
        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v)
            except ValueError:
                return None
        return v

    def has_valid_credentials(self) -> bool:
        """Check if we have valid OAuth credentials."""
        if not self.oauth_access_token:
            return False

        if self.oauth_token_expires_at:
            # Check if token is expired
            return datetime.now(UTC) < self.oauth_token_expires_at

        # If no expiration, assume token is valid
        return True

    def needs_registration(self) -> bool:
        """Check if OAuth client registration is needed."""
        return not self.oauth_client_id or not self.oauth_client_secret

    # NO CREDENTIAL FILES! Everything flows through .env as commanded by CLAUDE.md!
    # Credentials are automatically loaded from environment by pydantic-settings
    # MCP_CLIENT_* environment variables are the ONLY source of truth!
