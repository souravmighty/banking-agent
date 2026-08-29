import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv, find_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load .env from mcp-server directory and current/parent directories
_MCP_DIR = Path(__file__).resolve().parent.parent
load_dotenv(_MCP_DIR / ".env")
load_dotenv(Path(__file__).resolve().parent / ".env")
load_dotenv(find_dotenv(usecwd=True))


class TransactionServerSettings(BaseSettings):
    # Server Info
    PROJECT_NAME: str = "BankPilot Transaction MCP Server"
    VERSION: str = "1.0.0"
    MCP_HOST: str = "0.0.0.0"
    MCP_PORT: int = 8080

    # Google Cloud & BigQuery
    GOOGLE_CLOUD_PROJECT: str = "banking-agent-rag-mcp"
    GOOGLE_CLOUD_LOCATION: str = "us-central1"
    BIGQUERY_DATASET: str = "banking_data"
    CUSTOMER_IDENTITY_DATASET: str = "customer_identity"

    # Transaction Security & Limit Policies
    DEFAULT_TRANSACTION_THRESHOLD: float = 5000.0
    MAX_TRANSACTION_LIMIT: float = 100000.0
    OTP_EXPIRY_SECONDS: int = 300  # 5 minutes
    OTP_MAX_ATTEMPTS: int = 3

    # Resend Email Integration
    RESEND_API_KEY: Optional[str] = None
    EMAIL_FROM: str = "BankPilot <security@contact.souravmaiti.dev>"
    ADMIN_EMAIL: Optional[str] = "souravmaiti1997@gmail.com"

    # Identity Service URL
    IDENTITY_SERVICE_URL: str = "http://localhost:8001"

    # Logging
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )


settings = TransactionServerSettings()
