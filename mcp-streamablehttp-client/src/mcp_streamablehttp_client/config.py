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
    
    # OAuth Configuration (all discovered automatically)
    oauth_client_id: Optional[str] = Field(
        None,
        description="OAuth client ID (populated after registration)"
    )
    oauth_client_secret: Optional[str] = Field(
        None,
        description="OAuth client secret (populated after registration)"
    )
    oauth_access_token: Optional[str] = Field(
        None,
        description="Current OAuth access token"
    )
    oauth_refresh_token: Optional[str] = Field(
        None,
        description="OAuth refresh token for token renewal"
    )
    oauth_token_expires_at: Optional[datetime] = Field(
        None,
        description="Token expiration timestamp"
    )
    
    # OAuth Server URLs (discovered automatically)
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
    
    # Storage
    credential_storage_path: Path = Field(
        Path.home() / ".mcp" / "credentials.json",
        description="Path to store OAuth credentials"
    )
    
    # Security
    verify_ssl: bool = Field(
        True,
        description="Verify SSL certificates"
    )
    
    @field_validator("credential_storage_path", mode="before")
    def expand_path(cls, v):
        """Expand ~ and environment variables in paths."""
        if isinstance(v, str):
            v = os.path.expanduser(os.path.expandvars(v))
        return Path(v)
    
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
        """Save current OAuth credentials and discovered endpoints to storage."""
        import json
        
        # Ensure directory exists
        self.credential_storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        credentials = {
            # OAuth credentials
            "oauth_client_id": self.oauth_client_id,
            "oauth_client_secret": self.oauth_client_secret,
            "oauth_access_token": self.oauth_access_token,
            "oauth_refresh_token": self.oauth_refresh_token,
            "oauth_token_expires_at": self.oauth_token_expires_at.isoformat() if self.oauth_token_expires_at else None,
            # Discovered endpoints (cache for offline use)
            "oauth_issuer": self.oauth_issuer,
            "oauth_authorization_url": self.oauth_authorization_url,
            "oauth_token_url": self.oauth_token_url,
            "oauth_device_auth_url": self.oauth_device_auth_url,
            "oauth_registration_url": self.oauth_registration_url,
            "oauth_metadata_url": self.oauth_metadata_url,
        }
        
        with open(self.credential_storage_path, "w") as f:
            json.dump(credentials, f, indent=2)
        
        # Set restrictive permissions (owner read/write only)
        os.chmod(self.credential_storage_path, 0o600)
    
    def load_credentials(self) -> None:
        """Load OAuth credentials from storage if they exist."""
        import json
        
        if not self.credential_storage_path.exists():
            return
        
        try:
            with open(self.credential_storage_path, "r") as f:
                credentials = json.load(f)
            
            # Update settings with loaded credentials
            for key, value in credentials.items():
                if hasattr(self, key) and value is not None:
                    setattr(self, key, value)
        except Exception:
            # Ignore errors loading credentials
            pass