from fastapi import APIRouter, Depends, HTTPException, status
from app.dependencies import get_current_customer_id, get_bq_service
from app.services.bigquery_service import BigQueryService
from app.services.dashboard_service import DashboardService
from typing import Dict, Any, List

router = APIRouter(tags=["dashboard"])

def get_dashboard_service(bq: BigQueryService = Depends(get_bq_service)) -> DashboardService:
    return DashboardService(bq)

@router.get("/dashboard", response_model=Dict[str, Any])
async def get_dashboard(
    customer_id: int = Depends(get_current_customer_id),
    service: DashboardService = Depends(get_dashboard_service)
):
    try:
        return service.get_aggregated_dashboard(customer_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch dashboard data: {str(e)}"
        )

@router.get("/customer/profile", response_model=Dict[str, Any])
async def get_profile(
    customer_id: int = Depends(get_current_customer_id),
    service: DashboardService = Depends(get_dashboard_service)
):
    profile = service.get_customer_profile(customer_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer profile not found."
        )
    return dict(profile)

@router.get("/accounts", response_model=List[Dict[str, Any]])
async def get_accounts(
    customer_id: int = Depends(get_current_customer_id),
    service: DashboardService = Depends(get_dashboard_service)
):
    try:
        return service.get_accounts(customer_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch accounts: {str(e)}"
        )

@router.get("/cards", response_model=List[Dict[str, Any]])
async def get_cards(
    customer_id: int = Depends(get_current_customer_id),
    service: DashboardService = Depends(get_dashboard_service)
):
    try:
        return service.get_cards(customer_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch credit cards: {str(e)}"
        )

@router.get("/loans", response_model=List[Dict[str, Any]])
async def get_loans(
    customer_id: int = Depends(get_current_customer_id),
    service: DashboardService = Depends(get_dashboard_service)
):
    try:
        return service.get_loans(customer_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch loans: {str(e)}"
        )

@router.get("/investments", response_model=List[Dict[str, Any]])
async def get_investments(
    customer_id: int = Depends(get_current_customer_id),
    service: DashboardService = Depends(get_dashboard_service)
):
    try:
        return service.get_investments(customer_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch investments: {str(e)}"
        )

@router.get("/transactions", response_model=List[Dict[str, Any]])
async def get_transactions(
    customer_id: int = Depends(get_current_customer_id),
    service: DashboardService = Depends(get_dashboard_service)
):
    try:
        return service.get_transactions(customer_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch transactions: {str(e)}"
        )
