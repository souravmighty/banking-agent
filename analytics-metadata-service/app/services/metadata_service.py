from typing import List, Optional
from app.repositories.metadata_repository import MetadataRepository
from app.models.table import TableMetadata
from app.models.metric import MetricMetadata
from app.models.dimension import DimensionMetadata
from app.models.relationship import TableRelationship
from app.models.business_term import BusinessTerm

class MetadataService:
    """
    CRUD and detail retrieval operations for individual metadata assets.
    """
    def __init__(self, repository: MetadataRepository):
        self.repository = repository

    def list_tables(self) -> List[TableMetadata]:
        return self.repository.get_all_tables()

    def get_table(self, table_name: str) -> Optional[TableMetadata]:
        return self.repository.get_table(table_name)

    def list_metrics(self) -> List[MetricMetadata]:
        return self.repository.get_all_metrics()

    def get_metric(self, metric_name: str) -> Optional[MetricMetadata]:
        return self.repository.get_metric(metric_name)

    def list_dimensions(self) -> List[DimensionMetadata]:
        return self.repository.get_all_dimensions()

    def get_dimension(self, dimension_name: str) -> Optional[DimensionMetadata]:
        return self.repository.get_dimension(dimension_name)

    def list_relationships(self) -> List[TableRelationship]:
        return self.repository.get_all_relationships()

    def list_business_terms(self) -> List[BusinessTerm]:
        return self.repository.get_all_business_terms()
