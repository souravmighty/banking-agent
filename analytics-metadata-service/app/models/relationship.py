from enum import Enum
from typing import Optional
from pydantic import BaseModel

class RelationshipType(str, Enum):
    ONE_TO_ONE = "ONE_TO_ONE"
    ONE_TO_MANY = "ONE_TO_MANY"
    MANY_TO_ONE = "MANY_TO_ONE"
    MANY_TO_MANY = "MANY_TO_MANY"

class TableRelationship(BaseModel):
    left_table: str
    left_column: str
    
    right_table: str
    right_column: str
    
    relationship_type: RelationshipType = RelationshipType.ONE_TO_MANY
    business_description: str
    
    allowed_for_analytics: bool = True
    join_warning: Optional[str] = None
    join_sql_template: Optional[str] = None
