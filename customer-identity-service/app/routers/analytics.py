import uuid
from fastapi import APIRouter, Depends, Query, Request
from typing import Dict, Any
from app.schemas.responses import AnalyticsMetadataResponse
from app.services.analytics_metadata_service import AnalyticsMetadataService
from app.dependencies import require_bank_staff, get_analytics_metadata_service
from app.utils.logger import logger

router = APIRouter(tags=["analytics"])


@router.get("/analytics-metadata", response_model=AnalyticsMetadataResponse)
async def get_analytics_metadata(
    request: Request,
    refresh: bool = Query(False, description="Force refresh analytics metadata cache from BigQuery"),
    user_info: Dict[str, Any] = Depends(require_bank_staff),
    analytics_service: AnalyticsMetadataService = Depends(get_analytics_metadata_service)
):
    request_id = str(uuid.uuid4())
    user_identifier = user_info.get("email") or user_info.get("uid") or "unknown_staff"
    user_role = user_info.get("user_role", "BANK_STAFF")

    if refresh:
        analytics_service.invalidate_cache()

    try:
        metadata_response = analytics_service.get_analytics_metadata()
        
        # Calculate object counts for structured audit log
        table_count = 0
        view_count = 0
        for ds in metadata_response.datasets.values():
            if ds.tables:
                table_count += len(ds.tables)
            if ds.views:
                view_count += len(ds.views)

        log_data = {
            "endpoint": "/analytics-metadata",
            "request_id": request_id,
            "user_identifier": user_identifier,
            "user_role": user_role,
            "success": True,
            "objects_returned": table_count + view_count,
            "table_count": table_count,
            "view_count": view_count
        }
        logger.info("Analytics metadata requested successfully", extra=log_data)
        return metadata_response

    except Exception as e:
        logger.error(
            f"Error serving analytics metadata: {str(e)}",
            extra={
                "endpoint": "/analytics-metadata",
                "request_id": request_id,
                "user_identifier": user_identifier,
                "user_role": user_role,
                "success": False,
                "error": str(e)
            }
        )
        raise e
