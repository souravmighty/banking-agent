from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from app.models.table import TableMetadata
from app.models.metric import MetricMetadata
from app.models.dimension import DimensionMetadata
from app.models.relationship import TableRelationship
from app.models.query_guidance import QueryGuidanceRule

class ContextRequest(BaseModel):
    tables: List[str] = Field(default_factory=list)
    metrics: List[str] = Field(default_factory=list)
    dimensions: List[str] = Field(default_factory=list)
    include: List[str] = Field(
        default_factory=lambda: [
            "columns",
            "relationships",
            "scd",
            "query_guidance",
            "sensitivity"
        ]
    )
    exclude_pii: bool = True

class ContextResponse(BaseModel):
    tables: List[TableMetadata] = Field(default_factory=list)
    metrics: List[MetricMetadata] = Field(default_factory=list)
    dimensions: List[DimensionMetadata] = Field(default_factory=list)
    relationships: List[TableRelationship] = Field(default_factory=list)
    query_guidance: List[QueryGuidanceRule] = Field(default_factory=list)
    scd_guidance: Dict[str, Any] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)
    validation: Dict[str, Any] = Field(default_factory=dict)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class NL2SQLContextRequest(BaseModel):
    question: Optional[str] = None
    selected_tables: List[str] = Field(default_factory=list)
    selected_metrics: List[str] = Field(default_factory=list)
    selected_dimensions: List[str] = Field(default_factory=list)
    strict_governance: bool = True

class NL2SQLContextResponse(BaseModel):
    question: Optional[str] = None
    tables: List[Dict[str, Any]] = Field(default_factory=list)
    metrics: List[Dict[str, Any]] = Field(default_factory=list)
    dimensions: List[Dict[str, Any]] = Field(default_factory=list)
    join_guidance: List[Dict[str, Any]] = Field(default_factory=list)
    scd_guidance: List[Dict[str, Any]] = Field(default_factory=list)
    query_rules: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    governance_notes: List[str] = Field(default_factory=list)
    prompt_context_str: str = ""
    validation_passed: bool = True
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
