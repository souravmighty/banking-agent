from fastapi import Security, HTTPException, status
from fastapi.security.api_key import APIKeyHeader
from app.core.config import settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def get_current_client_role(api_key: str = Security(api_key_header)) -> str:
    """
    Validates API key and returns the caller role: 'admin' or 'read_only'
    """
    if settings.MOCK_AUTH_BYPASS and not api_key:
        # Development / test bypass mode defaults to full access or admin role
        return "admin"
        
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API Key header (X-API-Key)",
        )
        
    if api_key == settings.ADMIN_API_KEY:
        return "admin"
    elif api_key == settings.ANALYTICS_COPILOT_API_KEY:
        return "read_only"
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API Key credentials",
        )

def require_read_access(role: str = Security(get_current_client_role)) -> str:
    """Requires at least read-only access (satisfied by read_only or admin)"""
    if role in ["read_only", "admin"]:
        return role
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Read access required",
    )

def require_admin_access(role: str = Security(get_current_client_role)) -> str:
    """Requires admin role (for /admin endpoints)"""
    if role == "admin":
        return role
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Admin role required for this operation",
    )
