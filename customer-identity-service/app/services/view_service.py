from google.cloud import bigquery
from app.services.bigquery_service import BigQueryService
from app.config import settings
from typing import List, Dict, Any

def map_to_source_table(view_name_or_id: str) -> str:
    table_id = view_name_or_id.split('.')[-1] if '.' in view_name_or_id else view_name_or_id
    if "customer_v" in table_id or "customers" in table_id:
        return "customers"
    elif "accounts_v" in table_id or "accounts" in table_id:
        return "accounts"
    elif "transactions_v" in table_id or "transactions" in table_id:
        return "transactions"
    elif "credit_cards" in table_id:
        return "credit_cards"
    elif "loans" in table_id:
        return "loans"
    elif "fixed_deposits" in table_id:
        return "fixed_deposits"
    elif "beneficiaries" in table_id:
        return "beneficiaries"
    elif "customer_identity_mapping" in table_id:
        return "customer_identity_mapping"
    elif "credit_scores" in table_id:
        return "credit_scores"
    return table_id

def get_scd_metadata(table_id: str) -> Dict[str, Any]:
    base_table = map_to_source_table(table_id)
    is_scd = base_table in ["customers", "accounts", "credit_cards"]
    return {
        "is_scd_type_2": is_scd,
        "scd_columns": ["eff_start_ts", "eff_end_ts", "is_current", "record_version"] if is_scd else []
    }

class ViewService:
    def __init__(self, bq_service: BigQueryService):
        self.bq = bq_service
        self.source_dataset = f"{settings.GOOGLE_CLOUD_PROJECT}.{settings.BIGQUERY_DATASET}"
        self.target_dataset = f"{settings.GOOGLE_CLOUD_PROJECT}.{settings.BIGQUERY_VIEWS_DATASET}"

    def create_view_with_metadata(self, view_id: str, source_query: str, source_table_id: str):
        """
        Creates a BigQuery view with metadata (description and schema field descriptions) 
        cloned directly from the base source table.
        """
        source_metadata = self.bq.get_table_metadata(settings.BIGQUERY_DATASET, source_table_id)
        
        schema = []
        for field in source_metadata["fields"]:
            schema.append(bigquery.SchemaField(
                name=field["name"],
                field_type=field["type"],
                mode="NULLABLE" if field.get("is_nullable", True) else "REQUIRED",
                description=field["description"]
            ))
            
        self.bq.create_or_replace_view_with_metadata(
            view_id=view_id,
            source_query=source_query,
            description=source_metadata["table_description"],
            schema=schema
        )

    def create_authorized_views(self, customer_id: int):
        # View for customer profile
        customer_view_id = f"{self.target_dataset}.customer_{customer_id}_customer_v"
        customer_query = f"SELECT * FROM `{self.source_dataset}.customers` WHERE customer_id = {customer_id}"
        self.create_view_with_metadata(customer_view_id, customer_query, "customers")

        # View for customer accounts
        accounts_view_id = f"{self.target_dataset}.customer_{customer_id}_accounts_v"
        accounts_query = f"SELECT * FROM `{self.source_dataset}.accounts` WHERE customer_id = {customer_id}"
        self.create_view_with_metadata(accounts_view_id, accounts_query, "accounts")

        # View for customer transactions
        transactions_view_id = f"{self.target_dataset}.customer_{customer_id}_transactions_v"
        transactions_query = f"SELECT * FROM `{self.source_dataset}.transactions` WHERE account_number IN (SELECT account_number FROM `{self.source_dataset}.accounts` WHERE customer_id = {customer_id})"
        self.create_view_with_metadata(transactions_view_id, transactions_query, "transactions")
        
        return [customer_view_id, accounts_view_id, transactions_view_id]

    def get_view_schemas(self, view_names: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        schemas = {}
        for full_name in view_names:
            parts = full_name.split('.')
            dataset_id = parts[1]
            table_id = parts[2]
            schemas[full_name] = self.bq.get_table_schema(dataset_id, table_id)
        return schemas

    def get_authorized_views_metadata(self, view_names: List[str]) -> List[Dict[str, Any]]:
        """
        Retrieves table/view descriptions, field descriptions, types, nullability,
        and SCD metadata using both BigQuery Table APIs and INFORMATION_SCHEMA.
        """
        views_metadata = []
        for full_name in view_names:
            parts = full_name.split('.')
            if len(parts) == 3:
                dataset_id = parts[1]
                table_id = parts[2]
            else:
                dataset_id = settings.BIGQUERY_VIEWS_DATASET
                table_id = parts[-1]

            view_name = f"{dataset_id}.{table_id}"
            
            # 1. Map the view to its base source table
            source_table = map_to_source_table(table_id)

            # 2. Retrieve view metadata
            view_metadata = self.bq.get_table_metadata(dataset_id, table_id)
            
            # 3. Retrieve base source table metadata (contains rich table & field descriptions)
            source_metadata = self.bq.get_table_metadata(settings.BIGQUERY_DATASET, source_table)

            # 4. Create lookup dict for source field descriptions and modes
            source_field_desc = {
                field["name"].lower(): field["description"] 
                for field in source_metadata["fields"]
            }
            source_field_modes = {
                field["name"].lower(): field.get("mode") or "NULLABLE" 
                for field in source_metadata["fields"]
            }

            # 5. Fallback for table description
            table_desc = view_metadata["table_description"] or source_metadata["table_description"] or ""

            # 6. Determine SCD status and fields
            scd_meta = get_scd_metadata(source_table)

            # Determine AI usage guidance
            ai_usage_guidance = ""
            if scd_meta["is_scd_type_2"]:
                ai_usage_guidance = "Use is_current = TRUE unless historical analysis is requested."
            else:
                ai_usage_guidance = "Query records directly."

            # 7. Extract and merge view fields (enriching view field desc & mode with source table if blank!)
            fields_list = []
            
            # Use view columns if retrieved, otherwise fall back to source table columns
            target_fields = view_metadata["fields"] if view_metadata["fields"] else source_metadata["fields"]
            
            for field in target_fields:
                field_name = field["name"]
                desc = field.get("description") or source_field_desc.get(field_name.lower()) or ""
                mode = source_field_modes.get(field_name.lower()) or field.get("mode") or "NULLABLE"
                fields_list.append({
                    "name": field_name,
                    "type": field["type"],
                    "description": desc,
                    "mode": mode
                })

            views_metadata.append({
                "view_name": view_name,
                "table_description": table_desc,
                "ai_usage_guidance": ai_usage_guidance,
                "is_scd_type_2": scd_meta["is_scd_type_2"],
                "scd_columns": scd_meta["scd_columns"],
                "fields": fields_list
            })
            
        return views_metadata
