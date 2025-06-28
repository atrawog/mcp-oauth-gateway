"""Pydantic models for OAuth 2.1 and RFC 7591 compliance"""

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


# OAuth Client Registration Model (RFC 7591)
class ClientRegistration(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    redirect_uris: Optional[list[str]] = None
    client_name: Optional[str] = None
    client_uri: Optional[str] = None
    logo_uri: Optional[str] = None
    scope: Optional[str] = None
    contacts: Optional[list[str]] = None
    tos_uri: Optional[str] = None
    policy_uri: Optional[str] = None
    jwks_uri: Optional[str] = None
    jwks: Optional[dict[str, Any]] = None
    software_id: Optional[str] = None
    software_version: Optional[str] = None


# Token Response Model
class TokenResponse(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    refresh_token: Optional[str] = None
    scope: Optional[str] = None


# Error Response Model (RFC 6749)
class ErrorResponse(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    error: str
    error_description: Optional[str] = None
    error_uri: Optional[str] = None
