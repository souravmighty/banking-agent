import os
import sys

# Ensure we can import app
sys.path.append(os.getcwd())

from google.cloud import bigquery
from app.config import settings

def setup_demo_requests():
    client = bigquery.Client(project=settings.GOOGLE_CLOUD_PROJECT)
    dataset_id = f"{settings.GOOGLE_CLOUD_PROJECT}.customer_identity"
    
    # 1. Create demo_requests table
    demo_requests_ref = f"{dataset_id}.demo_requests"
    schema = [
        bigquery.SchemaField("request_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("name", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("email", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("company", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("role", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("linkedin", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("purpose", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("status", "STRING", mode="REQUIRED"), # PENDING, APPROVED, ALLOCATED, REJECTED, EXPIRED
        bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("updated_at", "TIMESTAMP", mode="NULLABLE"),
        bigquery.SchemaField("approved_by", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("remarks", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("customer_id", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("expires_at", "TIMESTAMP", mode="NULLABLE"),
    ]
    
    table = bigquery.Table(demo_requests_ref, schema=schema)
    try:
        client.get_table(demo_requests_ref)
        print("Table demo_requests already exists.")
    except Exception:
        table = client.create_table(table)
        print("Table demo_requests created successfully.")

    # 2. Update demo_customer_audit table schema to include request_id
    audit_ref = f"{dataset_id}.demo_customer_audit"
    try:
        audit_table = client.get_table(audit_ref)
        # Check if request_id column exists
        has_req_id = any(field.name == "request_id" for field in audit_table.schema)
        if not has_req_id:
            print("Adding request_id column to demo_customer_audit table...")
            original_schema = list(audit_table.schema)
            original_schema.append(bigquery.SchemaField("request_id", "STRING", mode="NULLABLE"))
            audit_table.schema = original_schema
            client.update_table(audit_table, ["schema"])
            print("Successfully added request_id column to demo_customer_audit.")
        else:
            print("demo_customer_audit already has request_id column.")
    except Exception as e:
        print(f"Error checking/updating demo_customer_audit: {e}")

if __name__ == "__main__":
    setup_demo_requests()
