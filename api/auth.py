from __future__ import annotations

import os
from fastapi import Header, HTTPException, Security
from fastapi.security import APIKeyHeader

# API Key header name that clients will use
API_KEY_HEADER = "X-API-Key"

# Get API key from environment variable
# Clients must send this exact key in the X-API-Key header
API_KEY = os.getenv("API_KEY") or os.getenv("VEE_CHATBOT_API_KEY")

# Security scheme for FastAPI
api_key_header = APIKeyHeader(name=API_KEY_HEADER, auto_error=False)


def verify_api_key(api_key: str | None = Security(api_key_header)) -> str:
    """
    Verify API key from request header.
    
    Args:
        api_key: The API key from the X-API-Key header
        
    Returns:
        The verified API key
        
    Raises:
        HTTPException: If API key is missing or invalid
    """
    # If no API key is configured, allow all requests (development mode)
    # This is useful for local testing without authentication
    if not API_KEY:
        return "dev"
    
    # Check if API key is provided and matches
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing API key. Please provide a valid X-API-Key header.",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    if api_key != API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key. Please provide a valid X-API-Key header.",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    return api_key

