from typing import List, Optional
from datetime import datetime, timezone
from app.core.config import settings
from app.core.logging import logger
from app.repositories.bigquery_schema_repository import BigQuerySchemaRepository
from app.repositories.metadata_repository import MetadataRepository
from app.services.metadata_validator import MetadataValidator
from app.models.sync import SyncRequest, SyncResponse, ValidationResult

class MetadataSyncService:
    """
    Orchestrates synchronization from BigQuery technical metadata,
    merging with curated YAML, running validation, and updating cache/storage.
    """
    def __init__(
        self,
        bq_repo: BigQuerySchemaRepository,
        metadata_repo: MetadataRepository,
        validator: MetadataValidator,
    ):
        self.bq_repo = bq_repo
        self.metadata_repo = metadata_repo
        self.validator = validator

    def sync(self, request: SyncRequest) -> SyncResponse:
        project_id = request.project_id or settings.GOOGLE_CLOUD_PROJECT
        datasets = request.dataset_ids or [settings.BIGQUERY_DATASET, settings.BIGQUERY_ANALYTICS_DATASET]

        if request.force_refresh:
            self.metadata_repo.load_curated_metadata()

        discovered_count = 0
        all_discovered = []
        for dataset_id in datasets:
            disc_tables = self.bq_repo.discover_tables(dataset_id=dataset_id, project_id=project_id)
            discovered_count += len(disc_tables)
            all_discovered.extend(disc_tables)

        # Merge discovered technical metadata into curated catalog
        merged_count = self.metadata_repo.merge_technical_metadata(all_discovered)

        # Run complete validation
        validation_summary = self.validator.validate_entire_repository()

        logger.info(
            f"Metadata sync complete. Discovered {discovered_count} tables, "
            f"merged {merged_count} tables. Repository valid: {validation_summary.valid}"
        )

        return SyncResponse(
            status="SUCCESS",
            tables_discovered=discovered_count,
            tables_curated=len(self.metadata_repo.get_all_tables()),
            metrics_synced=len(self.metadata_repo.get_all_metrics()),
            dimensions_synced=len(self.metadata_repo.get_all_dimensions()),
            relationships_synced=len(self.metadata_repo.get_all_relationships()),
            validation_summary=validation_summary,
            persisted_to_storage=request.persist_to_bigquery,
            synced_at=datetime.now(timezone.utc),
        )
