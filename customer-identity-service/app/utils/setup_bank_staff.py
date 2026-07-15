import os
import sys
from datetime import datetime, timezone

# Ensure we can import app
sys.path.append(os.getcwd())

from google.cloud import bigquery
from app.config import settings

def setup_bank_staff():
    client = bigquery.Client(project=settings.GOOGLE_CLOUD_PROJECT)
    dataset_id = f"{settings.GOOGLE_CLOUD_PROJECT}.customer_identity"
    
    # Define table reference
    table_ref = f"{dataset_id}.bank_staff"
    
    schema = [
        bigquery.SchemaField("email", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("name", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("role", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("added_at", "TIMESTAMP", mode="REQUIRED"),
    ]
    
    table = bigquery.Table(table_ref, schema=schema)
    
    # 1. Create Table
    try:
        client.get_table(table_ref)
        print("Table bank_staff already exists.")
    except Exception:
        table = client.create_table(table)
        print("Table bank_staff created successfully in BigQuery.")

    # 2. Seed default admin emails if not already present
    default_admins = [
        {"email": "souravmaiti1997@gmail.com", "name": "Sourav Maiti", "role": "OPERATIONS"},
        {"email": "souravmaiti1997@googlemail.com", "name": "Sourav Maiti", "role": "OPERATIONS"}
    ]
    
    # Query to check existing emails
    try:
        query = f"SELECT email FROM `{table_ref}`"
        results = [row["email"].lower() for row in client.query(query).result()]
        
        to_insert = [admin for admin in default_admins if admin["email"].lower() not in results]
        
        if to_insert:
            print(f"Seeding {len(to_insert)} default admins into bank_staff table...")
            
            # Formulate the standard DML insert query
            # (We use DML to avoid streaming buffer update limitations)
            now_iso = datetime.now(timezone.utc).isoformat()
            
            values_str = ", ".join([
                f"('{admin['email']}', '{admin['name']}', '{admin['role']}', TIMESTAMP('{now_iso}'))"
                for admin in to_insert
            ])
            
            insert_query = f"INSERT INTO `{table_ref}` (email, name, role, added_at) VALUES {values_str}"
            client.query(insert_query).result()
            print("Successfully seeded default staff accounts!")
        else:
            print("Default staff accounts are already seeded.")
            
    except Exception as e:
        print(f"Error seeding bank_staff table: {e}")

if __name__ == "__main__":
    setup_bank_staff()
