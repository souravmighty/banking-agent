from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # API Configuration
    PROJECT_NAME: str = "Customer Identity Service"
    API_V1_STR: str = "/api/v1"
    
    # Google Cloud Configuration
    GOOGLE_CLOUD_PROJECT: str
    BIGQUERY_DATASET: str = "banking_data"
    BIGQUERY_ANALYTICS_DATASET: str = "analytics"
    BIGQUERY_VIEWS_DATASET: str = "customer_views"

    # Analytics Metadata Configuration & Allowlist
    ANALYTICS_ALLOWED_TABLES: str = "customers,accounts,transactions,credit_cards,loans,fixed_deposits,credit_scores"
    ANALYTICS_ALLOWED_VIEWS: str = "analytics_customer_360,analytics_customer_acquisition,analytics_transactions,analytics_products,analytics_balances"
    ANALYTICS_METADATA_CACHE_TTL_SECONDS: int = 3600
    
    # Firebase Configuration
    FIREBASE_SERVICE_ACCOUNT_PATH: Optional[str] = None
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # Admin Emails for Demo Operations (comma-separated)
    ADMIN_EMAILS: str = "souravmaiti1997@gmail.com"
    ADMIN_EMAIL: Optional[str] = None
    
    # Resend Configuration
    RESEND_API_KEY: Optional[str] = None
    EMAIL_FROM: str = "BankPilot <security@contact.souravmaiti.dev>"
    
    # Optional SMTP Configuration for email notifications
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: Optional[str] = None
    SMTP_FROM_NAME: str = "BankPilot"
    
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")

settings = Settings()

