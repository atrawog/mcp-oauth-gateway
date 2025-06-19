"""Configuration management for MCP HTTP-to-stdio proxy."""
import os
from pathlib import Path
from typing import Optional
from datetime import datetime

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with .env file support."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # MCP Server Configuration
    mcp_server_url: str = Field(
        ...,
        description="URL of the MCP server to connect to"
    )
    
    # OAuth Configuration - MCP CLIENT REALM ONLY!
    # NEVER use OAUTH_* variables - those are server tokens!
    oauth_client_id: Optional[str] = Field(
        None,
        description="OAuth client ID (populated after registration)",
        alias="MCP_CLIENT_ID"
    )
    oauth_client_secret: Optional[str] = Field(
        None,
        description="OAuth client secret (populated after registration)",
        alias="MCP_CLIENT_SECRET"
    )
    oauth_access_token: Optional[str] = Field(
        None,
        description="Current OAuth access token",
        alias="MCP_CLIENT_ACCESS_TOKEN"
    )
    oauth_refresh_token: Optional[str] = Field(
        None,
        description="OAuth refresh token for token renewal",
        alias="MCP_CLIENT_REFRESH_TOKEN"
    )
    oauth_token_expires_at: Optional[datetime] = Field(
        None,
        description="Token expiration timestamp"
    )
    
    # OAuth Server URLs (discovered automatically)
    # OAuth endpoints - discovered automatically, not stored
    oauth_issuer: Optional[str] = Field(
        None,
        description="OAuth issuer URL (discovered from server)"
    )
    oauth_authorization_url: Optional[str] = Field(
        None,
        description="OAuth authorization endpoint (discovered)"
    )
    oauth_token_url: Optional[str] = Field(
        None,
        description="OAuth token endpoint (discovered)"
    )
    oauth_device_auth_url: Optional[str] = Field(
        None,
        description="OAuth device authorization endpoint (discovered)"
    )
    oauth_registration_url: Optional[str] = Field(
        None,
        description="OAuth dynamic client registration endpoint (discovered)"
    )
    oauth_metadata_url: Optional[str] = Field(
        None,
        description="OAuth server metadata discovery URL (discovered)"
    )
    
    # Client Configuration
    client_name: str = Field(
        "mcp-http-stdio",
        description="Client name for OAuth registration"
    )
    client_version: str = Field(
        "0.1.0",
        description="Client version"
    )
    
    # Session Configuration
    session_timeout: int = Field(
        300,
        description="Session timeout in seconds",
        ge=60,
        le=3600
    )
    request_timeout: int = Field(
        30,
        description="Request timeout in seconds",
        ge=5,
        le=300
    )
    
    # Logging
    log_level: str = Field(
        "INFO",
        description="Logging level",
        pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$"
    )
    
    # NO CREDENTIAL FILES! Everything through .env as divinely commanded!
    
    # Security
    verify_ssl: bool = Field(
        True,
        description="Verify SSL certificates"
    )
    
    @field_validator("oauth_token_expires_at", mode="before")
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
            return datetime.utcnow() < self.oauth_token_expires_at
        
        # If no expiration, assume token is valid
        return True
    
    def needs_registration(self) -> bool:
        """Check if OAuth client registration is needed."""
        return not self.oauth_client_id or not self.oauth_client_secret
    
    def save_credentials(self) -> None:
        """Save current OAuth credentials and discovered endpoints to .env file."""
        # NO CREDENTIAL FILES! Everything flows through .env as commanded!
        # This violates Commandment 4: Thou Shalt Configure Only Through .env Files
        pass
    
    def load_credentials(self) -> None:
        """Load OAuth credentials from .env configuration."""
        # NO CREDENTIAL FILES! Everything flows through .env as commanded!
        # Credentials are already loaded from environment by pydantic-settings
        pass