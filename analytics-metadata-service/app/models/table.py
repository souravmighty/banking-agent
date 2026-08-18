from enum import Enum
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from app.models.column import ColumnMetadata, SensitivityLevel

class ObjectType(str, Enum):
    TABLE = "TABLE"
    VIEW = "VIEW"
    MATERIALIZED_VIEW = "MATERIALIZED_VIEW"

class SCDType(str, Enum):
    NONE = "NONE"
    SCD_TYPE_1 = "SCD_TYPE_1"
    SCD_TYPE_2 = "SCD_TYPE_2"
    OTHER = "OTHER"

class TableMetadata(BaseModel):
    project_id: str
    dataset_name: str
    table_name: str
    
    object_type: ObjectType = ObjectType.TABLE
    
    description: Optional[str] = None
    
    business_domain: Optional[str] = None
    business_entity: Optional[str] = None
    business_purpose: Optional[str] = None
    
    grain: Optional[str] = None
    
    scd_type: SCDType = SCDType.NONE
    
    natural_key: List[str] = Field(default_factory=list)
    primary_key: List[str] = Field(default_factory=list)
    
    preferred_analytics_source: bool = False
    allowed_for_analytics: bool = True
    allowed_for_nl2sql: bool = True
    allowed_for_visualization: bool = True
    
    sensitivity_level: Optional[SensitivityLevel] = SensitivityLevel.INTERNAL
    data_owner: Optional[str] = None
    
    partitioning: Optional[Dict[str, Any]] = None
    clustering_columns: List[str] = Field(default_factory=list)
    
    effective_from_column: Optional[str] = None
    effective_to_column: Optional[str] = None
    current_flag_column: Optional[str] = None
    
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None
    
    tags: List[str] = Field(default_factory=list)
    columns: List[ColumnMetadata] = Field(default_factory=list)

    @property
    def full_table_id(self) -> str:
        return f"{self.project_id}.{self.dataset_name}.{self.table_name}"
