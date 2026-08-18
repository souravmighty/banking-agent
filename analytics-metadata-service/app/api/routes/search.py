from fastapi import APIRouter, Depends
from app.core.security import require_read_access
from app.api.dependencies import get_metadata_search_service
from app.services.metadata_search import MetadataSearchService
from app.models.search import SearchRequest, SearchResponse

router = APIRouter(prefix="/metadata", tags=["Search"])

@router.post("/search", response_model=SearchResponse)
def search_metadata(
    request: SearchRequest,
    search_service: MetadataSearchService = Depends(get_metadata_search_service),
    _role: str = Depends(require_read_access),
):
    """
    Search across table names/descriptions, column names/descriptions,
    metrics, dimensions, and business terms/synonyms.
    """
    return search_service.search(request)
