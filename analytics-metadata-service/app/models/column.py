from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field

class SemanticType(str, Enum):
    CUSTOMER_ID = "CUSTOMER_ID"
    ACCOUNT_ID = "ACCOUNT_ID"
    CARD_ID = "CARD_ID"
    LOAN_ID = "LOAN_ID"
    TRANSACTION_ID = "TRANSACTION_ID"
    
    DATE = "DATE"
    DATETIME = "DATETIME"
    TIMESTAMP = "TIMESTAMP"
    
    CURRENCY = "CURRENCY"
    PERCENTAGE = "PERCENTAGE"
    COUNT = "COUNT"
    RATIO = "RATIO"
    
    NAME = "NAME"
    EMAIL = "EMAIL"
    PHONE = "PHONE"
    ADDRESS = "ADDRESS"
    
    CATEGORY = "CATEGORY"
    SEGMENT = "SEGMENT"
    CHANNEL = "CHANNEL"
    REGION = "REGION"
    
    BOOLEAN = "BOOLEAN"
    STATUS = "STATUS"
    ENUM = "ENUM"
    FREE_TEXT = "FREE_TEXT"
    OTHER = "OTHER"

class SensitivityLevel(str, Enum):
    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    CONFIDENTIAL = "CONFIDENTIAL"
    RESTRICTED = "RESTRICTED"
    PII = "PII"
    FINANCIAL = "FINANCIAL"

class ColumnMetadata(BaseModel):
    column_name: str
    data_type: str = "STRING"
    nullable: bool = True
    ordinal_position: int = 0
    
    description: Optional[str] = None
    business_description: Optional[str] = None
    semantic_type: Optional[SemanticType] = None
    
    is_primary_key: bool = False
    is_foreign_key: bool = False
    references_table: Optional[str] = None
    references_column: Optional[str] = None
    
    is_metric: bool = False
    is_dimension: bool = False
    is_filterable: bool = True
    is_groupable: bool = False
    is_sortable: bool = True
    is_time_dimension: bool = False
    
    is_sensitive: bool = False
    sensitivity_level: Optional[SensitivityLevel] = SensitivityLevel.INTERNAL
    
    allowed_aggregations: List[str] = Field(default_factory=list)
    default_aggregation: Optional[str] = None
    
    example_values: Optional[List[str]] = None
    tags: List[str] = Field(default_factory=list)
