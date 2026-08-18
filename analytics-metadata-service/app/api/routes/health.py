from fastapi import APIRouter
from app.core.config import settings

router = APIRouter(tags=["Health"])

@router.get("/health")
@router.get("/")
def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.SERVICE_VERSION,
        "project": settings.GOOGLE_CLOUD_PROJECT,
        "environment": settings.ENVIRONMENT,
    }
