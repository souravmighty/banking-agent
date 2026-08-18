from typing import Optional, List
from pydantic import BaseModel, Field

class BusinessTerm(BaseModel):
    term: str
    mapped_metric: Optional[str] = None
    mapped_dimension: Optional[str] = None
    mapped_table: Optional[str] = None
    definition: str
    synonyms: List[str] = Field(default_factory=list)
