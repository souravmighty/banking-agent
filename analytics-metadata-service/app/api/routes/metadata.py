from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from app.core.security import require_read_access
from app.api.dependencies import get_metadata_service, get_context_builder
from app.services.metadata_service import MetadataService
from app.services.context_builder import ContextBuilder
from app.models.table import TableMetadata
from app.models.dimension import DimensionMetadata
from app.models.relationship import TableRelationship
from app.models.business_term import BusinessTerm
from app.models.query_guidance import QueryGuidanceRule
from app.models.context import (
    ContextRequest,
    ContextResponse,
    NL2SQLContextRequest,
    NL2SQLContextResponse,
)

router = APIRouter(prefix="/metadata", tags=["Detailed Metadata & Context"])

@router.post("/context", response_model=ContextResponse)
def get_detailed_context(
    request: ContextRequest,
    context_builder: ContextBuilder = Depends(get_context_builder),
    _role: str = Depends(require_read_access),
):
    """
    Returns Layer B detailed metadata for selected tables, metrics, and dimensions only.
    Includes columns, data types, PK/FK, SCD rules, relationships, join warnings, and governance.
    """
    return context_builder.build_context(request)

@router.post("/nl2sql-context", response_model=NL2SQLContextResponse)
def get_nl2sql_context(
    request: NL2SQLContextRequest,
    context_builder: ContextBuilder = Depends(get_context_builder),
    _role: str = Depends(require_read_access),
):
    """
    Returns a compact, LLM-ready prompt context containing schema, metric formulas, join rules,
    grain explanations, SCD2 temporal queries, and PII exclusion notes.
    """
    return context_builder.build_nl2sql_context(request)

@router.get("/tables", response_model=List[TableMetadata])
def list_tables(
    metadata_service: MetadataService = Depends(get_metadata_service),
    _role: str = Depends(require_read_access),
):
    """Lists all registered tables with complete column schemas and metadata."""
    return metadata_service.list_tables()

@router.get("/tables/{table_name}", response_model=TableMetadata)
def get_table_details(
    table_name: str,
    metadata_service: MetadataService = Depends(get_metadata_service),
    _role: str = Depends(require_read_access),
):
    """Retrieves detailed schema and configuration for a single table."""
    table = metadata_service.get_table(table_name)
    if not table:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Table '{table_name}' not found.",
        )
    return table

@router.get("/dimensions", response_model=List[DimensionMetadata])
def list_dimensions(
    metadata_service: MetadataService = Depends(get_metadata_service),
    _role: str = Depends(require_read_access),
):
    """Lists all analytical dimensions and hierarchies."""
    return metadata_service.list_dimensions()

@router.get("/dimensions/{dimension_name}", response_model=DimensionMetadata)
def get_dimension_details(
    dimension_name: str,
    metadata_service: MetadataService = Depends(get_metadata_service),
    _role: str = Depends(require_read_access),
):
    """Retrieves definition for a specific dimension."""
    dimension = metadata_service.get_dimension(dimension_name)
    if not dimension:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dimension '{dimension_name}' not found.",
        )
    return dimension

@router.get("/relationships", response_model=List[TableRelationship])
def list_relationships(
    metadata_service: MetadataService = Depends(get_metadata_service),
    _role: str = Depends(require_read_access),
):
    """Lists all table relationships, join keys, and join warnings."""
    return metadata_service.list_relationships()

@router.get("/business-terms", response_model=List[BusinessTerm])
def list_business_terms(
    metadata_service: MetadataService = Depends(get_metadata_service),
    _role: str = Depends(require_read_access),
):
    """Lists business vocabulary mapping natural language terms to metrics and dimensions."""
    return metadata_service.list_business_terms()

@router.get("/query-guidance", response_model=List[QueryGuidanceRule])
def list_query_guidance(
    metadata_service: MetadataService = Depends(get_metadata_service),
    _role: str = Depends(require_read_access),
):
    """Lists all query guidance, SCD2, partitioning, and aggregation rules."""
    return metadata_service.repository.get_all_query_guidance()
