from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import dashboard

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Microservice providing aggregated and granular customer financial data from BigQuery views.",
    version="1.0.0",
)

# Enable CORS for frontend and other microservices
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for strict environments if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(dashboard.router, prefix=settings.API_V1_STR)

@app.get("/health")
@app.get("/")
def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "project": settings.GOOGLE_CLOUD_PROJECT,
    }
