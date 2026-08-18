import time
import uuid
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import logger
from app.api.routes import health, catalog, metadata, metrics, search, admin

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.SERVICE_VERSION,
    description=(
        "Production Analytics Metadata & Semantic Service for BankPilot Analytics Copilot. "
        "Provides governed schema discovery, compact semantic catalogs, metric formulas, "
        " Slowly Changing Dimension (SCD Type 2) guidance, join relationship modeling, and prompt context."
    ),
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request Timing & Structured Logging Middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = f"{duration:.4f}"
    
    # Avoid verbose logging for health check
    if request.url.path not in ["/health", "/"]:
        logger.info(
            f"{request.method} {request.url.path} completed in {duration:.4f}s with status {response.status_code}",
            extra={"request_id": request_id}
        )
    return response

# Include Routers
app.include_router(health.router)
app.include_router(catalog.router)
app.include_router(metadata.router)
app.include_router(metrics.router)
app.include_router(search.router)
app.include_router(admin.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8003, reload=True)
