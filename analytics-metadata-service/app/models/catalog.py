from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field

class CompactTableCatalogEntry(BaseModel):
    table: str
    dataset: str
    description: Optional[str] = None
    business_domain: Optional[str] = None
    business_entity: Optional[str] = None
    grain: Optional[str] = None
    preferred_analytics_source: bool = False
    key_metrics: List[str] = Field(default_factory=list)
    key_dimensions: List[str] = Field(default_factory=list)
    related_tables: List[str] = Field(default_factory=list)
    scd_type: str = "NONE"
    sensitivity_level: Optional[str] = "INTERNAL"
    allowed_for_analytics: bool = True
    allowed_for_nl2sql: bool = True

class CompactMetricCatalogEntry(BaseModel):
    metric: str
    display_name: Optional[str] = None
    description: str
    business_definition: Optional[str] = None
    source_tables: List[str] = Field(default_factory=list)
    allowed_dimensions: List[str] = Field(default_factory=list)
    default_aggregation: str = "SUM"
    unit: Optional[str] = None

class CompactDimensionCatalogEntry(BaseModel):
    dimension: str
    description: str
    source: str
    hierarchy: Optional[List[str]] = None

class CompactCatalogResponse(BaseModel):
    tables: List[CompactTableCatalogEntry] = Field(default_factory=list)
    metrics: List[CompactMetricCatalogEntry] = Field(default_factory=list)
    dimensions: List[CompactDimensionCatalogEntry] = Field(default_factory=list)
    version: str = "1.0.0"
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
