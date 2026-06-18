from fastapi import APIRouter, Depends
from app.schemas.requests import EmailCheckRequest
from app.schemas.responses import EmailCheckResponse, LinkUserResponse
from app.services.authorization_service import AuthorizationService
from app.dependencies import get_authorization_service, get_current_user
from typing import Dict, Any

router = APIRouter(prefix="/registration", tags=["registration"])

@router.post("/check-email", response_model=EmailCheckResponse)
async def check_email(
    request: EmailCheckRequest,
    auth_service: AuthorizationService = Depends(get_authorization_service)
):
    return auth_service.check_email_availability(request.email)

@router.post("/link-user", response_model=LinkUserResponse)
async def link_user(
    decoded_token: Dict[str, Any] = Depends(get_current_user),
    auth_service: AuthorizationService = Depends(get_authorization_service)
):
    return auth_service.link_firebase_user(decoded_token)
