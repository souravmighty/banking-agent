from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class SearchResultType(str, Enum):
    TABLE = "TABLE"
    COLUMN = "COLUMN"
    METRIC = "METRIC"
    DIMENSION = "DIMENSION"
    BUSINESS_TERM = "BUSINESS_TERM"

class SearchResultItem(BaseModel):
    item_type: SearchResultType
    name: str
    display_name: Optional[str] = None
    description: str
    parent_table: Optional[str] = None
    score: float = 1.0
    matched_field: str
    matched_text: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class SearchRequest(BaseModel):
    query: str
    top_k: int = 10
    types: Optional[List[SearchResultType]] = None

class SearchResponse(BaseModel):
    query: str
    total_results: int
    results: List[SearchResultItem] = Field(default_factory=list)
