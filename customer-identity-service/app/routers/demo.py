from fastapi import APIRouter, Depends, Query, Path
from pydantic import BaseModel, EmailStr
from typing import Dict, Any, List, Optional
from app.services.demo_service import DemoService
from app.dependencies import get_demo_service, get_current_user
from app.config import settings
from app.utils.exceptions import UnauthorizedException

router = APIRouter(prefix="/demo", tags=["demo"])

# --- Schemas ---

class DemoRequestCreateInput(BaseModel):
    name: str
    email: EmailStr
    company: Optional[str] = None
    role: Optional[str] = None
    linkedin: Optional[str] = None
    purpose: Optional[str] = None

class DemoRequestDetailsResponse(BaseModel):
    request_id: str
    name: str
    email: EmailStr
    company: Optional[str] = None
    role: Optional[str] = None
    linkedin: Optional[str] = None
    purpose: Optional[str] = None
    status: str
    created_at: str
    updated_at: Optional[str] = None
    approved_by: Optional[str] = None
    remarks: Optional[str] = None
    customer_id: Optional[str] = None
    expires_at: Optional[str] = None

class DemoRequestOutput(BaseModel):
    customer_id: int
    expires_at: str
    status: str
    message: Optional[str] = None

class DemoReleaseInput(BaseModel):
    customer_id: str

class DemoReleaseOutput(BaseModel):
    customer_id: int
    status: str
    released_at: str
    deleted_views_count: int

class DemoStatusOutput(BaseModel):
    demo_customer_id: str
    customer_id: int
    original_name: str
    original_email: str
    demo_name: Optional[str] = None
    demo_email: Optional[str] = None
    firebase_uid: Optional[str] = None
    status: str
    allocated_at: Optional[str] = None
    expires_at: Optional[str] = None
    released_at: Optional[str] = None
    allocated_by: Optional[str] = None
    remarks: Optional[str] = None

class DemoRejectInput(BaseModel):
    remarks: Optional[str] = None

class DashboardSummaryResponse(BaseModel):
    pending_requests: int
    allocated_customers: int
    available_customers: int
    expired_today: int

# --- Helper ---

def verify_admin_user(decoded_token: Dict[str, Any], bq_service: Optional[Any] = None) -> None:
    admin_emails = [email.strip().lower() for email in settings.ADMIN_EMAILS.split(",") if email.strip()]
    user_email = decoded_token.get("email", "").lower()
    
    # 1. Quick static lookup (Fast, no DB call)
    is_admin = user_email in admin_emails or user_email.endswith("@bankpilot.dev") or user_email.endswith("@bankpilot.com")
    
    # 2. Dynamic BigQuery table lookup fallback
    if not is_admin:
        try:
            from app.services.bigquery_service import BigQueryService
            from google.cloud import bigquery
            bq = bq_service or BigQueryService()
            table_ref = f"{settings.GOOGLE_CLOUD_PROJECT}.customer_identity.bank_staff"
            query = f"SELECT 1 FROM `{table_ref}` WHERE LOWER(email) = @email"
            job_config = bigquery.QueryJobConfig(
                query_parameters=[bigquery.ScalarQueryParameter("email", "STRING", user_email)]
            )
            results = bq.execute_query(query, job_config=job_config)
            if results:
                is_admin = True
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Error querying bank_staff BigQuery table: {e}")
            
    if not is_admin:
        raise UnauthorizedException(detail="Only administrators are allowed to access this endpoint.")

# --- Endpoints ---

# 1. Public endpoint to request a demo (No authentication required)
@router.post("/request", response_model=DemoRequestDetailsResponse)
async def request_demo(
    payload: DemoRequestCreateInput,
    demo_service: DemoService = Depends(get_demo_service)
):
    # Perform input validation for linkedIn URL format if provided
    if payload.linkedin:
        li = payload.linkedin.lower()
        if not ("linkedin.com/" in li or "linkedin.cn/" in li):
            from app.utils.exceptions import CustomerIdentityException
            raise CustomerIdentityException(
                status_code=400,
                detail="LinkedIn profile must be a valid LinkedIn URL."
            )
            
    return demo_service.submit_demo_request(
        name=payload.name,
        email=payload.email,
        company=payload.company,
        role=payload.role,
        linkedin=payload.linkedin,
        purpose=payload.purpose
    )

# 2. Staff/Admin endpoint to list all demo requests
@router.get("/requests", response_model=List[DemoRequestDetailsResponse])
async def list_demo_requests(
    decoded_token: Dict[str, Any] = Depends(get_current_user),
    demo_service: DemoService = Depends(get_demo_service)
):
    verify_admin_user(decoded_token)
    return demo_service.get_all_demo_requests()

# 3. Staff/Admin endpoint to get a single demo request
@router.get("/requests/{requestId}", response_model=DemoRequestDetailsResponse)
async def get_demo_request(
    requestId: str = Path(..., description="The ID of the demo request"),
    decoded_token: Dict[str, Any] = Depends(get_current_user),
    demo_service: DemoService = Depends(get_demo_service)
):
    verify_admin_user(decoded_token)
    from app.utils.exceptions import CustomerIdentityException
    req = demo_service.get_demo_request_by_id(requestId)
    if not req:
        raise CustomerIdentityException(status_code=404, detail="Demo request not found.")
    return req

# 4. Staff/Admin endpoint to get dashboard summary card metrics
@router.get("/summary", response_model=DashboardSummaryResponse)
async def get_summary_metrics(
    decoded_token: Dict[str, Any] = Depends(get_current_user),
    demo_service: DemoService = Depends(get_demo_service)
):
    verify_admin_user(decoded_token)
    return demo_service.get_dashboard_summary()

# 5. Staff/Admin endpoint to approve a demo request
@router.post("/approve/{requestId}", response_model=DemoRequestOutput)
async def approve_request(
    requestId: str = Path(..., description="The ID of the demo request to approve"),
    decoded_token: Dict[str, Any] = Depends(get_current_user),
    demo_service: DemoService = Depends(get_demo_service)
):
    verify_admin_user(decoded_token)
    approved_by = decoded_token.get("email", "Admin")
    return demo_service.approve_demo_request(requestId, approved_by=approved_by)

# 6. Staff/Admin endpoint to reject a demo request
@router.post("/reject/{requestId}")
async def reject_request(
    requestId: str = Path(..., description="The ID of the demo request to reject"),
    payload: Optional[DemoRejectInput] = None,
    decoded_token: Dict[str, Any] = Depends(get_current_user),
    demo_service: DemoService = Depends(get_demo_service)
):
    verify_admin_user(decoded_token)
    rejected_by = decoded_token.get("email", "Admin")
    remarks = payload.remarks if payload else None
    return demo_service.reject_demo_request(requestId, rejected_by=rejected_by, remarks=remarks)

# 7. Staff/Admin endpoint to release a demo customer (path param)
@router.post("/release/{customerId}", response_model=DemoReleaseOutput)
async def release_demo_path(
    customerId: str = Path(..., description="The customer ID to release"),
    decoded_token: Dict[str, Any] = Depends(get_current_user),
    demo_service: DemoService = Depends(get_demo_service)
):
    verify_admin_user(decoded_token)
    return demo_service.release_demo_customer(
        customer_id=customerId,
        performed_by=decoded_token.get("email", "Admin")
    )

# 8. Keep old release endpoint for compatibility
@router.post("/release", response_model=DemoReleaseOutput)
async def release_demo_payload(
    payload: DemoReleaseInput,
    decoded_token: Dict[str, Any] = Depends(get_current_user),
    demo_service: DemoService = Depends(get_demo_service)
):
    verify_admin_user(decoded_token)
    return demo_service.release_demo_customer(
        customer_id=payload.customer_id,
        performed_by=decoded_token.get("email", "Admin")
    )

# 9. Get demo allocation status for a single email
@router.get("/status/{email}", response_model=DemoStatusOutput)
async def get_demo_status(
    email: str,
    decoded_token: Dict[str, Any] = Depends(get_current_user),
    demo_service: DemoService = Depends(get_demo_service)
):
    # Any authenticated user can check demo status for any email
    return demo_service.get_demo_status(email)

# 10. List all allocated demo customers
@router.get("/customers", response_model=List[DemoStatusOutput])
async def list_demo_customers(
    decoded_token: Dict[str, Any] = Depends(get_current_user),
    demo_service: DemoService = Depends(get_demo_service)
):
    verify_admin_user(decoded_token)
    return demo_service.get_all_demo_customers()

# 11. Run automatic expiries
@router.post("/release-expired", response_model=List[int])
async def release_expired(
    decoded_token: Dict[str, Any] = Depends(get_current_user),
    demo_service: DemoService = Depends(get_demo_service)
):
    verify_admin_user(decoded_token)
    return demo_service.release_expired_customers()
