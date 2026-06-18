from fastapi import APIRouter, Depends
from app.schemas.responses import CustomerMeResponse
from app.services.customer_service import CustomerService
from app.dependencies import get_customer_service, get_current_user
from typing import Dict, Any

router = APIRouter(prefix="/auth", tags=["auth"])

@router.get("/me", response_model=CustomerMeResponse)
async def get_me(
    decoded_token: Dict[str, Any] = Depends(get_current_user),
    customer_service: CustomerService = Depends(get_customer_service)
):
    uid = decoded_token["uid"]
    customer = customer_service.get_customer_by_uid(uid)
    return {
        "customer_id": customer["customer_id"],
        "name": customer["name"],
        "email": customer["email"],
        "kyc_status": customer["kyc_status"]
    }
