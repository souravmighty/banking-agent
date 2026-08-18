import os
from typing import List, Dict, Optional, Any
from datetime import datetime
from google.cloud import bigquery
from google.oauth2 import service_account
from app.core.config import settings
from app.core.logging import logger
from app.models.table import TableMetadata, ObjectType, SCDType
from app.models.column import ColumnMetadata, SensitivityLevel

class BigQuerySchemaRepository:
    """
    Discovers technical metadata directly from BigQuery INFORMATION_SCHEMA
    and client API for datasets, tables, and columns.
    """
    def __init__(self, client: Optional[bigquery.Client] = None):
        self._client = client

    def _get_client(self) -> Optional[bigquery.Client]:
        if self._client:
            return self._client
        try:
            if settings.GOOGLE_APPLICATION_CREDENTIALS and os.path.exists(settings.GOOGLE_APPLICATION_CREDENTIALS):
                credentials = service_account.Credentials.from_service_account_file(
                    settings.GOOGLE_APPLICATION_CREDENTIALS
                )
                self._client = bigquery.Client(
                    project=settings.GOOGLE_CLOUD_PROJECT,
                    credentials=credentials,
                    location=settings.GOOGLE_CLOUD_LOCATION,
                )
            else:
                self._client = bigquery.Client(
                    project=settings.GOOGLE_CLOUD_PROJECT,
                    location=settings.GOOGLE_CLOUD_LOCATION,
                )
            return self._client
        except Exception as e:
            logger.warning(f"BigQuery client initialization failed or offline: {str(e)}")
            return None

    def discover_tables(self, dataset_id: str, project_id: Optional[str] = None) -> List[TableMetadata]:
        """
        Discovers tables and columns from BigQuery for a specified dataset.
        """
        project = project_id or settings.GOOGLE_CLOUD_PROJECT
        client = self._get_client()
        if not client:
            logger.info(f"BigQuery client not available. Returning empty discovery list for {dataset_id}.")
            return []

        discovered: List[TableMetadata] = []
        try:
            dataset_ref = f"{project}.{dataset_id}"
            tables = list(client.list_tables(dataset_ref))
            
            for table_item in tables:
                table_ref = f"{project}.{dataset_id}.{table_item.table_id}"
                try:
                    full_table = client.get_table(table_ref)
                    obj_type = ObjectType.VIEW if full_table.table_type == "VIEW" else ObjectType.TABLE
                    
                    columns: List[ColumnMetadata] = []
                    for idx, schema_field in enumerate(full_table.schema, start=1):
                        col = ColumnMetadata(
                            column_name=schema_field.name,
                            data_type=schema_field.field_type,
                            nullable=(schema_field.mode != "REQUIRED"),
                            ordinal_position=idx,
                            description=schema_field.description,
                        )
                        columns.append(col)
                        
                    partitioning_info = None
                    if full_table.time_partitioning:
                        partitioning_info = {
                            "type": full_table.time_partitioning.type_,
                            "field": full_table.time_partitioning.field,
                        }
                    
                    clustering_cols = list(full_table.clustering_fields or [])
                    
                    t_meta = TableMetadata(
                        project_id=project,
                        dataset_name=dataset_id,
                        table_name=full_table.table_id,
                        object_type=obj_type,
                        description=full_table.description,
                        partitioning=partitioning_info,
                        clustering_columns=clustering_cols,
                        created_at=full_table.created,
                        modified_at=full_table.modified,
                        columns=columns,
                    )
                    discovered.append(t_meta)
                except Exception as table_err:
                    logger.warning(f"Failed to inspect table {table_ref}: {str(table_err)}")
                    continue
        except Exception as e:
            logger.error(f"Error discovering tables in dataset {dataset_id}: {str(e)}")
            
        return discovered
