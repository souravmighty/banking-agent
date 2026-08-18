from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional, List
from pathlib import Path
import os

class Settings(BaseSettings):
    # API & Service Configuration
    PROJECT_NAME: str = "BankPilot Analytics Metadata Service"
    API_V1_STR: str = "/api/v1"
    SERVICE_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    
    # Google Cloud & BigQuery Configuration
    GOOGLE_CLOUD_PROJECT: str = "banking-agent-rag-mcp"
    GOOGLE_CLOUD_LOCATION: str = "us-central1"
    BIGQUERY_DATASET: str = "banking_data"
    BIGQUERY_ANALYTICS_DATASET: str = "analytics"
    BIGQUERY_METADATA_DATASET: str = "analytics_metadata"
    
    # Path to Google Service Account Key (optional if using ADC)
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = None
    
    # Metadata YAML repository path
    METADATA_DIR: str = Field(
        default_factory=lambda: str(
            Path(__file__).resolve().parent.parent.parent / "metadata"
        )
    )
    
    # Security & API Keys
    ADMIN_API_KEY: str = "bankpilot-admin-secret-key"
    ANALYTICS_COPILOT_API_KEY: str = "bankpilot-analytics-copilot-key"
    MOCK_AUTH_BYPASS: bool = True  # Allows local dev and testing without strict auth headers
    
    # Cache settings
    CACHE_TTL_SECONDS: int = 3600
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()
