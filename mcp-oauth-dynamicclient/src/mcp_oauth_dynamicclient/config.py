"""
Configuration module for MCP OAuth Dynamic Client
"""
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Sacred Configuration following the divine laws"""
    
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
    mcp_protocol_version: str = "2025-06-18"
    
    class Config:
        env_file = ".env"