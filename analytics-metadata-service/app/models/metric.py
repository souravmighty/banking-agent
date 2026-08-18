from typing import Optional, List
from pydantic import BaseModel, Field

class MetricMetadata(BaseModel):
    metric_name: str
    display_name: str
    
    description: str
    business_definition: str
    
    sql_expression: Optional[str] = None
    
    default_aggregation: str = "SUM"
    data_type: str = "FLOAT"
    unit: Optional[str] = None
    
    source_tables: List[str] = Field(default_factory=list)
    
    allowed_dimensions: List[str] = Field(default_factory=list)
    allowed_filters: List[str] = Field(default_factory=list)
    
    is_ratio: bool = False
    
    numerator_metric: Optional[str] = None
    denominator_metric: Optional[str] = None
    
    calculation_notes: Optional[str] = None
    
    tags: List[str] = Field(default_factory=list)
