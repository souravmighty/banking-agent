from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.core.security import require_read_access
from app.api.dependencies import get_metadata_service
from app.services.metadata_service import MetadataService
from app.models.metric import MetricMetadata

router = APIRouter(prefix="/metadata/metrics", tags=["Metrics"])

@router.get("", response_model=List[MetricMetadata])
def list_metrics(
    metadata_service: MetadataService = Depends(get_metadata_service),
    _role: str = Depends(require_read_access),
):
    """Lists all curated analytical metrics and calculations."""
    return metadata_service.list_metrics()

@router.get("/{metric_name}", response_model=MetricMetadata)
def get_metric_details(
    metric_name: str,
    metadata_service: MetadataService = Depends(get_metadata_service),
    _role: str = Depends(require_read_access),
):
    """Retrieves business definition, formula, source tables, and allowed dimensions for a metric."""
    metric = metadata_service.get_metric(metric_name)
    if not metric:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Metric '{metric_name}' not found.",
        )
    return metric
