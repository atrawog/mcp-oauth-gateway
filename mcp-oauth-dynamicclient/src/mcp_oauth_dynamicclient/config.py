"""Configuration module for MCP OAuth Dynamic Client"""

from typing import Optional

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Sacred Configuration following the divine laws"""

    # GitHub OAuth
    github_client_id: str
    github_client_secret: str

    # JWT Configuration
    jwt_secret: str
    jwt_algorithm: str  # NO DEFAULTS!
    jwt_private_key_b64: Optional[str] = None  # Base64 encoded RSA private key for RS256

    # Domain Configuration
    base_domain: str

    # Redis Configuration
    redis_url: str
    redis_password: Optional[str]  # NO DEFAULTS!

    # Token Lifetimes - NO DEFAULTS, MUST BE IN .env!
    access_token_lifetime: int
    refresh_token_lifetime: int
    session_timeout: int
    client_lifetime: int  # 0 = never expires

    # Access Control
    allowed_github_users: str  # NO DEFAULTS! Comma-separated list

    # MCP Protocol Version
    mcp_protocol_version: str  # NO DEFAULTS!

    model_config = ConfigDict(
        env_file=".env",
        extra="ignore",  # Allow extra fields from environment
    )
