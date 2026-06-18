from google.cloud import bigquery
from google.oauth2 import service_account
from google.cloud.exceptions import NotFound
import os
from dotenv import load_dotenv
import sys

# Load the .env file
load_dotenv()

# Data directory path
DATA_DIR = '../../data'

def upload_csv_to_bigquery(project_id, dataset_id, table_id, csv_file):
    """Upload CSV file to BigQuery table"""
    
    KEY_PATH = "../../keys/tf-sa-key.json"

    # Create credentials from the file
    credentials = service_account.Credentials.from_service_account_file(KEY_PATH)
    client = bigquery.Client(project=project_id, credentials=credentials)
    
    table_ref = f"{project_id}.{dataset_id}.{table_id}"
    
    # Configure the load job
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,
        autodetect=False,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )
    
    print(f"Uploading {csv_file} to {table_ref}...")
    
    with open(csv_file, "rb") as source_file:
        load_job = client.load_table_from_file(
            source_file,
            table_ref,
            job_config=job_config
        )
    
    # Wait for the job to complete
    load_job.result()
    
    # Get table info
    table = client.get_table(table_ref)
    print(f"✓ Loaded {table.num_rows} rows into {table_ref}")

def main():
    # Configuration
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    dataset_id = os.getenv("DATASET_ID", "banking_data")

    if not project_id:
        print("Error: GOOGLE_CLOUD_PROJECT environment variable not set")
        print("Usage: export GOOGLE_CLOUD_PROJECT=your-project-id")
        sys.exit(1)
    
    # Tables to upload (with paths relative to data directory)
    tables = {
        'customers': f'{DATA_DIR}/customers.csv',
        'customer_identity_mapping': f'{DATA_DIR}/customer_identity_mapping.csv',
        'accounts': f'{DATA_DIR}/accounts.csv',
        'credit_cards': f'{DATA_DIR}/credit_cards.csv',
        'beneficiaries': f'{DATA_DIR}/beneficiaries.csv',
        'loans': f'{DATA_DIR}/loans.csv',
        'fixed_deposits': f'{DATA_DIR}/fixed_deposits.csv',
        'transactions': f'{DATA_DIR}/transactions.csv',
        'credit_scores': f'{DATA_DIR}/credit_scores.csv'
    }
    
    # Check if data directory exists
    if not os.path.exists(DATA_DIR):
        print(f"Error: Data directory '{DATA_DIR}' not found")
        print("Please run the data generation script first: python generate_data.py")
        sys.exit(1)
    
    # Check if all CSV files exist
    missing_files = [f for f in tables.values() if not os.path.exists(f)]
    if missing_files:
        print(f"Error: Missing CSV files: {missing_files}")
        print("Please run the data generation script first: python generate_data.py")
        sys.exit(1)
    
    # Upload each table
    print(f"\nUploading data to {project_id}.{dataset_id}")
    print("=" * 60)
    
    for table_id, csv_file in tables.items():
        try:
            upload_csv_to_bigquery(project_id, dataset_id, table_id, csv_file)
        except Exception as e:
            print(f"✗ Error uploading {csv_file}: {str(e)}")
            continue
    
    print("\n" + "=" * 60)
    print("Upload complete!")
    print(f"\nView your data at:")
    print(f"https://console.cloud.google.com/bigquery?project={project_id}&d={dataset_id}&page=dataset")

if __name__ == "__main__":
    main()