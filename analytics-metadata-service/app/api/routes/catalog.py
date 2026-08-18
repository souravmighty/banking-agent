from fastapi import APIRouter, Depends, Query
from typing import Optional
from app.core.security import require_read_access
from app.api.dependencies import get_catalog_service
from app.services.catalog_service import CatalogService
from app.models.catalog import CompactCatalogResponse

router = APIRouter(prefix="/metadata", tags=["Compact Catalog"])

@router.get("/catalog", response_model=CompactCatalogResponse)
def get_compact_semantic_catalog(
    domain: Optional[str] = Query(None, description="Filter compact catalog by business domain (e.g. CUSTOMER, TRANSACTIONS, CARDS)"),
    catalog_service: CatalogService = Depends(get_catalog_service),
    _role: str = Depends(require_read_access),
):
    """
    Returns Layer A compact semantic catalog containing table summaries, grain, key metrics,
    dimensions, SCD flags, and relationships. Designed specifically for LLM Analytics Planner context.
    """
    return catalog_service.get_compact_catalog(domain=domain)
