from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # API Configuration
    PROJECT_NAME: str = "Customer Identity Service"
    API_V1_STR: str = "/api/v1"
    
    # Google Cloud Configuration
    GOOGLE_CLOUD_PROJECT: str
    BIGQUERY_DATASET: str = "banking_data"
    BIGQUERY_VIEWS_DATASET: str = "customer_views"
    
    # Firebase Configuration
    FIREBASE_SERVICE_ACCOUNT_PATH: Optional[str] = None
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")

settings = Settings()
