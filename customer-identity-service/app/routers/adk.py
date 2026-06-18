from fastapi import APIRouter, Depends
from app.schemas.responses import ADKContextResponse
from app.services.customer_service import CustomerService
from app.services.view_service import ViewService
from app.dependencies import get_customer_service, get_view_service, get_current_user
from typing import Dict, Any

router = APIRouter(prefix="/adk", tags=["adk"])

@router.get("/context", response_model=ADKContextResponse)
async def get_adk_context(
    decoded_token: Dict[str, Any] = Depends(get_current_user),
    customer_service: CustomerService = Depends(get_customer_service),
    view_service: ViewService = Depends(get_view_service)
):
    uid = decoded_token["uid"]
    customer = customer_service.get_customer_by_uid(uid)
    customer_id = customer["customer_id"]
    
    # Create or update views and get their IDs
    view_names = view_service.create_authorized_views(customer_id)
    
    # Get rich metadata for the authorized views
    views_metadata = view_service.get_authorized_views_metadata(view_names)
    
    # Get authorized account details (including all types)
    authorized_accounts = customer_service.get_authorized_accounts(customer_id)
    
    return {
        "customer_id": customer_id,
        "customer": customer,
        "authorized_views": views_metadata,
        "authorized_accounts": authorized_accounts
    }
