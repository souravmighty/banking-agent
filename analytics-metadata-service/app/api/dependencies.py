from functools import lru_cache
from app.repositories.bigquery_schema_repository import BigQuerySchemaRepository
from app.repositories.metadata_repository import MetadataRepository
from app.services.catalog_service import CatalogService
from app.services.metadata_service import MetadataService
from app.services.metadata_validator import MetadataValidator
from app.services.context_builder import ContextBuilder
from app.services.metadata_search import MetadataSearchService
from app.services.metadata_sync import MetadataSyncService

# Singleton repository instances
_bq_repo = BigQuerySchemaRepository()
_metadata_repo = MetadataRepository()
_validator = MetadataValidator(_metadata_repo)
_catalog_service = CatalogService(_metadata_repo)
_metadata_service = MetadataService(_metadata_repo)
_context_builder = ContextBuilder(_metadata_repo, _validator)
_search_service = MetadataSearchService(_metadata_repo)
_sync_service = MetadataSyncService(_bq_repo, _metadata_repo, _validator)

def get_metadata_repository() -> MetadataRepository:
    return _metadata_repo

def get_bq_schema_repository() -> BigQuerySchemaRepository:
    return _bq_repo

def get_catalog_service() -> CatalogService:
    return _catalog_service

def get_metadata_service() -> MetadataService:
    return _metadata_service

def get_metadata_validator() -> MetadataValidator:
    return _validator

def get_context_builder() -> ContextBuilder:
    return _context_builder

def get_metadata_search_service() -> MetadataSearchService:
    return _search_service

def get_metadata_sync_service() -> MetadataSyncService:
    return _sync_service
