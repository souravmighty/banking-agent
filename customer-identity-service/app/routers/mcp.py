from fastapi import APIRouter, Depends
from app.schemas.responses import MCPContextResponse
from app.services.customer_service import CustomerService
from app.dependencies import get_customer_service, get_current_user
from typing import Dict, Any, List

router = APIRouter(prefix="/mcp", tags=["mcp"])

@router.get("/customer-context", response_model=MCPContextResponse)
async def get_mcp_context(
    decoded_token: Dict[str, Any] = Depends(get_current_user),
    customer_service: CustomerService = Depends(get_customer_service)
):
    uid = decoded_token["uid"]
    customer = customer_service.get_customer_by_uid(uid)
    customer_id = customer["customer_id"]
    
    # Get authorized account details (including all types)
    authorized_accounts = customer_service.get_authorized_accounts(customer_id)
    
    # Get beneficiary details
    beneficiary_details = customer_service.get_beneficiary_details(customer_id)
    
    return {
        "customer_id": customer_id,
        "authorized_accounts": authorized_accounts,
        "beneficiary_details": beneficiary_details,
        "kyc_status": customer["kyc_status"]
    }
