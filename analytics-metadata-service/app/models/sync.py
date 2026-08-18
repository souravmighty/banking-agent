from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field

class ValidationIssue(BaseModel):
    severity: str  # ERROR / WARNING / INFO
    entity_type: str  # TABLE / METRIC / DIMENSION / RELATIONSHIP / GOVERNANCE
    entity_name: str
    message: str

class ValidationResult(BaseModel):
    valid: bool
    total_tables: int = 0
    total_metrics: int = 0
    total_dimensions: int = 0
    total_relationships: int = 0
    errors: List[ValidationIssue] = Field(default_factory=list)
    warnings: List[ValidationIssue] = Field(default_factory=list)
    validated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SyncRequest(BaseModel):
    project_id: Optional[str] = None
    dataset_ids: Optional[List[str]] = None
    persist_to_bigquery: bool = False
    force_refresh: bool = False

class SyncResponse(BaseModel):
    status: str
    tables_discovered: int
    tables_curated: int
    metrics_synced: int
    dimensions_synced: int
    relationships_synced: int
    validation_summary: ValidationResult
    persisted_to_storage: bool
    synced_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
