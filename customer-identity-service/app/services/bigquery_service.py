from google.cloud import bigquery
from app.config import settings
from typing import List, Dict, Any, Optional

class BigQueryService:
    def __init__(self):
        self.client = bigquery.Client(project=settings.GOOGLE_CLOUD_PROJECT)

    def execute_query(self, query: str, job_config: bigquery.QueryJobConfig = None) -> List[Dict[str, Any]]:
        query_job = self.client.query(query, job_config=job_config)
        results = query_job.result()
        return [dict(row) for row in results]

    def create_or_replace_view(self, view_id: str, source_query: str):
        view = bigquery.Table(view_id)
        view.view_query = source_query
        self.client.delete_table(view_id, not_found_ok=True)
        self.client.create_table(view)

    def create_or_replace_view_with_metadata(self, view_id: str, source_query: str, description: str, schema: List[bigquery.SchemaField]):
        """
        Creates or replaces a BigQuery view with customized table descriptions and column field descriptions.
        """
        # Double escape single quotes for string literals in BigQuery SQL
        def escape_string(val: str) -> str:
            if not val:
                return ""
            return val.replace("\\", "\\\\").replace("'", "\\'")

        # Build column options
        cols_sql = []
        for field in schema:
            desc = escape_string(field.description or "")
            cols_sql.append(f"`{field.name}` OPTIONS(description='{desc}')")

        columns_clause = ",\n  ".join(cols_sql)
        escaped_desc = escape_string(description or "")

        ddl = f"""
        CREATE OR REPLACE VIEW `{view_id}`
        (
          {columns_clause}
        )
        OPTIONS(
          description='{escaped_desc}'
        )
        AS
        {source_query}
        """
        
        try:
            query_job = self.client.query(ddl)
            query_job.result()
        except Exception as e:
            # Fallback to create the view without schema if schema is rejected in specific configurations
            view_fallback = bigquery.Table(view_id)
            view_fallback.view_query = source_query
            view_fallback.description = description
            self.client.delete_table(view_id, not_found_ok=True)
            self.client.create_table(view_fallback)

    def get_table_schema(self, dataset_id: str, table_id: str) -> List[Dict[str, Any]]:
        query = f"""
            SELECT column_name, data_type, is_nullable
            FROM `{settings.GOOGLE_CLOUD_PROJECT}.{dataset_id}.INFORMATION_SCHEMA.COLUMNS`
            WHERE table_name = @table_id
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("table_id", "STRING", table_id)
            ]
        )
        return self.execute_query(query, job_config=job_config)

    def get_table_metadata(self, dataset_id: str, table_id: str) -> Dict[str, Any]:
        """
        Retrieves table metadata using BigQuery metadata APIs and INFORMATION_SCHEMA.
        Gets table description, field descriptions, column types, and nullable information.
        """
        table_ref = f"{settings.GOOGLE_CLOUD_PROJECT}.{dataset_id}.{table_id}"
        table_description = ""
        fields = []

        # 1. Retrieve table description from BigQuery table metadata API
        try:
            table = self.client.get_table(table_ref)
            table_description = table.description or ""
        except Exception as e:
            pass

        # 2. Retrieve column metadata (name, type, is_nullable, description) from INFORMATION_SCHEMA.COLUMNS and COLUMN_FIELD_PATHS
        try:
            query = f"""
                SELECT 
                  c.column_name, 
                  c.data_type, 
                  c.is_nullable, 
                  p.description
                FROM `{settings.GOOGLE_CLOUD_PROJECT}.{dataset_id}.INFORMATION_SCHEMA.COLUMNS` c
                LEFT JOIN `{settings.GOOGLE_CLOUD_PROJECT}.{dataset_id}.INFORMATION_SCHEMA.COLUMN_FIELD_PATHS` p
                  ON c.table_name = p.table_name AND c.column_name = p.column_name AND c.column_name = p.field_path
                WHERE c.table_name = @table_id
            """
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("table_id", "STRING", table_id)
                ]
            )
            columns_info = self.execute_query(query, job_config=job_config)
            
            if columns_info:
                for col in columns_info:
                    mode = "NULLABLE"
                    if col["is_nullable"] == "NO":
                        mode = "REQUIRED"
                    if "ARRAY" in str(col["data_type"]).upper():
                        mode = "REPEATED"
                    fields.append({
                        "name": col["column_name"],
                        "type": col["data_type"],
                        "description": col.get("description") or "",
                        "is_nullable": col["is_nullable"] == "YES",
                        "mode": mode
                    })
            else:
                # Fallback to Table schema object if INFORMATION_SCHEMA didn't yield columns
                try:
                    table = self.client.get_table(table_ref)
                    for field in table.schema:
                        fields.append({
                            "name": field.name,
                            "type": field.field_type,
                            "description": field.description or "",
                            "is_nullable": field.is_nullable,
                            "mode": field.mode or "NULLABLE"
                        })
                except Exception:
                    pass
        except Exception as e:
            # Final fallback if query fails
            try:
                table = self.client.get_table(table_ref)
                for field in table.schema:
                    fields.append({
                        "name": field.name,
                        "type": field.field_type,
                        "description": field.description or "",
                        "is_nullable": field.is_nullable,
                        "mode": field.mode or "NULLABLE"
                    })
            except Exception:
                pass

        return {
            "table_description": table_description,
            "fields": fields
        }
