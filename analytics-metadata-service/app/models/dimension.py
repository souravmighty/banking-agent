from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class DimensionHierarchy(BaseModel):
    level: int = 1
    parent: Optional[str] = None
    children: List[str] = Field(default_factory=list)
    levels: List[str] = Field(default_factory=list)

class DimensionMetadata(BaseModel):
    dimension_name: str
    display_name: str
    description: str
    
    source_table: str
    source_column: str
    data_type: str = "STRING"
    
    allowed_filters: List[str] = Field(default_factory=list)
    allowed_grouping: bool = True
    
    hierarchy: Optional[DimensionHierarchy] = None
    tags: List[str] = Field(default_factory=list)
