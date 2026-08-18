from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field

class RuleType(str, Enum):
    GRAIN_WARNING = "GRAIN_WARNING"
    SCD2_FILTER = "SCD2_FILTER"
    PREFERRED_SOURCE = "PREFERRED_SOURCE"
    AGGREGATION_RULE = "AGGREGATION_RULE"
    TEMPORAL_GUIDANCE = "TEMPORAL_GUIDANCE"
    GENERAL = "GENERAL"

class QueryGuidanceRule(BaseModel):
    id: str
    title: str
    target_tables: List[str] = Field(default_factory=list)
    target_metrics: List[str] = Field(default_factory=list)
    rule_type: RuleType = RuleType.GENERAL
    rule_text: str
    sql_snippet: Optional[str] = None
