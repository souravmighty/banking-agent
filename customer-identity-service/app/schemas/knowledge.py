from datetime import date, datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    PRODUCT = "PRODUCT"
    POLICY = "POLICY"
    FAQ = "FAQ"
    TERMS_AND_CONDITIONS = "TERMS_AND_CONDITIONS"
    SERVICE_INFORMATION = "SERVICE_INFORMATION"


class ProductType(str, Enum):
    CREDIT_CARD = "CREDIT_CARD"
    LOAN = "LOAN"
    SAVINGS = "SAVINGS"
    INVESTMENT = "INVESTMENT"
    ACCOUNT = "ACCOUNT"
    OTHER = "OTHER"


class DocumentStatus(str, Enum):
    DRAFT = "DRAFT"
    PROCESSING = "PROCESSING"
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"
    FAILED = "FAILED"


class IngestionStatus(str, Enum):
    PENDING = "PENDING"
    UPLOADING = "UPLOADING"
    INDEXING = "INDEXING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class KnowledgeDocumentResponse(BaseModel):
    document_id: str
    logical_document_id: str
    document_name: str
    original_filename: str
    document_type: str
    product_type: Optional[str] = None
    product_id: Optional[str] = None
    product_name: Optional[str] = None
    version: str
    status: str
    effective_from: str
    effective_to: Optional[str] = None
    region: str
    audience: Optional[str] = None
    access_control: List[str] = Field(default_factory=lambda: ["CUSTOMER"])
    gcs_uri: str
    rag_file_id: Optional[str] = None
    rag_corpus_name: Optional[str] = None
    uploaded_by: str
    uploaded_at: str
    updated_at: str
    ingestion_status: str
    ingestion_error: Optional[str] = None
    is_active: bool


class KnowledgeDocumentListResponse(BaseModel):
    documents: List[KnowledgeDocumentResponse]
    total: int


class KnowledgeVersionResponse(BaseModel):
    document_id: str
    logical_document_id: str
    version: str
    document_name: str
    status: str
    ingestion_status: str
    is_active: bool
    uploaded_by: str
    uploaded_at: str
    effective_from: str
    effective_to: Optional[str] = None
    access_control: List[str] = Field(default_factory=lambda: ["CUSTOMER"])
    gcs_uri: str


class KnowledgeAuditLogResponse(BaseModel):
    audit_id: str
    document_id: str
    logical_document_id: str
    version: str
    action: str
    result: str
    user_id: str
    timestamp: str
    details: Optional[str] = None


class KnowledgeQueryRequest(BaseModel):
    query: str = Field(..., description="Semantic search query")
    access_scope: Optional[str] = Field(None, description="Access scope: 'CUSTOMER' or 'STAFF'")
    product_type: Optional[str] = Field(None, description="Optional product type filter")
    product_id: Optional[str] = Field(None, description="Optional product ID filter")
    document_type: Optional[str] = Field(None, description="Optional document type filter")
    region: Optional[str] = Field("IN", description="Target region filter")
    top_k: int = Field(5, description="Number of results to retrieve")


class KnowledgeRetrievedContext(BaseModel):
    text: str
    source_uri: Optional[str] = None
    document_id: Optional[str] = None
    logical_document_id: Optional[str] = None
    document_name: Optional[str] = None
    document_type: Optional[str] = None
    product_type: Optional[str] = None
    product_id: Optional[str] = None
    product_name: Optional[str] = None
    version: Optional[str] = None
    effective_from: Optional[str] = None
    effective_to: Optional[str] = None
    access_control: List[str] = Field(default_factory=list)
    distance: Optional[float] = None
    relevance_score: Optional[float] = None


class KnowledgeQueryResponse(BaseModel):
    query: str
    results: List[KnowledgeRetrievedContext]
    total_found: int
