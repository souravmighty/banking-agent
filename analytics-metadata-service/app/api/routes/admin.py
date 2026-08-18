from fastapi import APIRouter, Depends
from app.core.security import require_admin_access
from app.api.dependencies import get_metadata_sync_service, get_metadata_validator
from app.services.metadata_sync import MetadataSyncService
from app.services.metadata_validator import MetadataValidator
from app.models.sync import SyncRequest, SyncResponse, ValidationResult

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.post("/sync", response_model=SyncResponse)
def sync_metadata_from_bigquery(
    request: SyncRequest = SyncRequest(),
    sync_service: MetadataSyncService = Depends(get_metadata_sync_service),
    _role: str = Depends(require_admin_access),
):
    """
    Syncs live technical schema from BigQuery INFORMATION_SCHEMA,
    merges it into the curated metadata repository without overwriting business definitions,
    and runs full consistency validation.
    """
    return sync_service.sync(request)

@router.post("/validate", response_model=ValidationResult)
def validate_metadata_repository(
    validator: MetadataValidator = Depends(get_metadata_validator),
    _role: str = Depends(require_admin_access),
):
    """
    Validates complete consistency across tables, metrics, dimensions, relationships, and governance.
    """
    return validator.validate_entire_repository()
