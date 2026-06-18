import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.routers import registration, auth, adk, mcp
from app.config import settings
from app.utils.logger import logger
from app.utils.exceptions import CustomerIdentityException
import uuid

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging Middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    # Process request
    response = await call_next(request)
    
    process_time = time.time() - start_time
    
    # Structured log
    log_data = {
        "endpoint": request.url.path,
        "request_id": request_id,
        "execution_time": f"{process_time:.4f}s",
        "method": request.method,
        "status_code": response.status_code
    }
    
    # Try to get UID and Customer ID if they were attached to request state (optional)
    if hasattr(request.state, "firebase_uid"):
        log_data["firebase_uid"] = request.state.firebase_uid
    if hasattr(request.state, "customer_id"):
        log_data["customer_id"] = request.state.customer_id

    logger.info(f"Request processed", extra=log_data)
    
    return response

# Include Routers
app.include_router(registration.router, prefix=settings.API_V1_STR)
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(adk.router, prefix=settings.API_V1_STR)
app.include_router(mcp.router, prefix=settings.API_V1_STR)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": settings.PROJECT_NAME}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
