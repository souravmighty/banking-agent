import os
import sys
import uuid
from google.cloud import bigquery
from google.oauth2 import service_account
from dotenv import load_dotenv

# Base directory setup
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(BASE_DIR, '.env'))

KEY_PATH = os.path.join(BASE_DIR, 'keys/tf-sa-key.json')


def get_bigquery_client(project_id: str) -> bigquery.Client:
    """Initializes BigQuery client with service account if available, else default."""
    if os.path.exists(KEY_PATH):
        credentials = service_account.Credentials.from_service_account_file(KEY_PATH)
        return bigquery.Client(project=project_id, credentials=credentials)
    return bigquery.Client(project=project_id)


def ensure_demo_tables_exist(client: bigquery.Client, project_id: str, identity_dataset_id: str):
    """Ensures customer_identity dataset and demo_customers table exist."""
    dataset_ref = f"{project_id}.{identity_dataset_id}"
    dataset = bigquery.Dataset(dataset_ref)
    dataset.location = "us-central1"
    client.create_dataset(dataset, exists_ok=True)
    print(f"✓ Dataset '{identity_dataset_id}' verified.")

    demo_customers_ref = f"{dataset_ref}.demo_customers"
    schema = [
        bigquery.SchemaField("demo_customer_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("customer_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("original_name", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("original_email", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("demo_name", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("demo_email", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("firebase_uid", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("status", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("allocated_at", "TIMESTAMP", mode="NULLABLE"),
        bigquery.SchemaField("expires_at", "TIMESTAMP", mode="NULLABLE"),
        bigquery.SchemaField("released_at", "TIMESTAMP", mode="NULLABLE"),
        bigquery.SchemaField("allocated_by", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("remarks", "STRING", mode="NULLABLE"),
    ]
    table = bigquery.Table(demo_customers_ref, schema=schema)
    try:
        client.get_table(demo_customers_ref)
        print(f"✓ Table '{demo_customers_ref}' already exists.")
    except Exception:
        client.create_table(table)
        print(f"✓ Table '{demo_customers_ref}' created successfully.")


def fetch_top_20_customers(client: bigquery.Client, project_id: str, data_dataset_id: str):
    """
    Ranks active bank customers based on total balance, fixed deposits,
    product holdings, debit volume, and transaction frequency.
    """
    ranking_query = f"""
    WITH customer_balances AS (
      SELECT customer_id, SUM(balance) as total_balance, COUNT(account_number) as num_accounts
      FROM `{project_id}.{data_dataset_id}.accounts`
      WHERE is_current = TRUE AND account_status = "ACTIVE"
      GROUP BY customer_id
    ),
    customer_fds AS (
      SELECT customer_id, SUM(current_value) as fd_balance, COUNT(fd_account_number) as num_fds
      FROM `{project_id}.{data_dataset_id}.fixed_deposits`
      WHERE status = "ACTIVE"
      GROUP BY customer_id
    ),
    customer_cc AS (
      SELECT customer_id, COUNT(card_account_number) as num_cc
      FROM `{project_id}.{data_dataset_id}.credit_cards`
      WHERE is_current = TRUE AND status = "ACTIVE"
      GROUP BY customer_id
    ),
    customer_loans AS (
      SELECT customer_id, COUNT(loan_account_number) as num_loans
      FROM `{project_id}.{data_dataset_id}.loans`
      WHERE status = "ACTIVE"
      GROUP BY customer_id
    ),
    customer_tx AS (
      SELECT a.customer_id, 
             COUNT(t.transaction_id) as tx_volume, 
             SUM(CASE WHEN t.direction = "DEBIT" THEN t.amount ELSE 0 END) as total_debit
      FROM `{project_id}.{data_dataset_id}.transactions` t
      JOIN `{project_id}.{data_dataset_id}.accounts` a ON t.account_number = a.account_number
      WHERE a.is_current = TRUE
      GROUP BY a.customer_id
    )
    SELECT 
      CAST(c.customer_id AS STRING) as customer_id,
      c.name,
      c.email,
      c.customer_segment,
      COALESCE(cb.total_balance, 0) as total_balance,
      COALESCE(cf.fd_balance, 0) as fd_balance,
      (COALESCE(cb.num_accounts, 0) + COALESCE(cf.num_fds, 0) + COALESCE(cc.num_cc, 0) + COALESCE(cl.num_loans, 0)) as total_products,
      (
        0.35 * COALESCE(cb.total_balance, 0) +
        0.15 * COALESCE(cf.fd_balance, 0) +
        0.10 * (COALESCE(cb.num_accounts, 0) + COALESCE(cf.num_fds, 0) + COALESCE(cc.num_cc, 0) + COALESCE(cl.num_loans, 0)) +
        0.10 * (COALESCE(tx.total_debit, 0) / 6.0) +
        0.10 * COALESCE(tx.tx_volume, 0)
      ) as wealth_score
    FROM `{project_id}.{data_dataset_id}.customers` c
    LEFT JOIN customer_balances cb ON c.customer_id = cb.customer_id
    LEFT JOIN customer_fds cf ON c.customer_id = cf.customer_id
    LEFT JOIN customer_cc cc ON c.customer_id = cc.customer_id
    LEFT JOIN customer_loans cl ON c.customer_id = cl.customer_id
    LEFT JOIN customer_tx tx ON c.customer_id = tx.customer_id
    WHERE c.is_current = TRUE AND c.customer_status = "ACTIVE"
    ORDER BY wealth_score DESC
    LIMIT 20
    """
    results = list(client.query(ranking_query).result())
    return results


def sync_demo_customers(project_id: str, data_dataset_id: str = "banking_data", identity_dataset_id: str = "customer_identity"):
    client = get_bigquery_client(project_id)
    ensure_demo_tables_exist(client, project_id, identity_dataset_id)

    demo_customers_ref = f"{project_id}.{identity_dataset_id}.demo_customers"
    
    print(f"\nFetching top 20 ranked customers from {project_id}.{data_dataset_id}...")
    top_20 = fetch_top_20_customers(client, project_id, data_dataset_id)
    
    if not top_20:
        print("❌ Error: No active customers found in banking_data.customers.")
        sys.exit(1)

    print(f"\n{'#':<3} {'Customer ID':<18} {'Name':<24} {'Email':<32} {'Segment':<10} {'Balance (INR)':<15} {'Products':<8} {'Wealth Score':<12}")
    print("-" * 130)
    for idx, c in enumerate(top_20, 1):
        print(f"{idx:<3} {c.customer_id:<18} {c.name:<24} {c.email:<32} {c.customer_segment:<10} {c.total_balance:<15.2f} {c.total_products:<8} {c.wealth_score:<12.2f}")

    # Truncate / delete existing rows from demo_customers table
    print(f"\nClearing old records from {demo_customers_ref}...")
    client.query(f"DELETE FROM `{demo_customers_ref}` WHERE TRUE").result()

    # Construct batch DML insert for top 20 demo customers
    values_clauses = []
    query_parameters = []
    
    for i, r in enumerate(top_20):
        demo_id = f"demo-{uuid.uuid4().hex[:8]}"
        cust_id = str(r.customer_id)
        name = r.name
        email = r.email
        
        values_clauses.append(f"(@demo_id_{i}, @cust_id_{i}, @name_{i}, @email_{i}, 'AVAILABLE')")
        query_parameters.extend([
            bigquery.ScalarQueryParameter(f"demo_id_{i}", "STRING", demo_id),
            bigquery.ScalarQueryParameter(f"cust_id_{i}", "STRING", cust_id),
            bigquery.ScalarQueryParameter(f"name_{i}", "STRING", name),
            bigquery.ScalarQueryParameter(f"email_{i}", "STRING", email),
        ])

    insert_query = f"""
        INSERT INTO `{demo_customers_ref}` (
            demo_customer_id, customer_id, original_name, original_email, status
        ) VALUES {", ".join(values_clauses)}
    """
    job_config = bigquery.QueryJobConfig(query_parameters=query_parameters)
    client.query(insert_query, job_config=job_config).result()

    print(f"\n✓ Successfully populated {len(top_20)} top customers into {demo_customers_ref}!")
    print("All demo accounts are set to status 'AVAILABLE' with exact matching names and emails.")


if __name__ == "__main__":
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "banking-agent-rag-mcp")
    data_dataset_id = os.getenv("BQ_DATASET_ID", "banking_data")
    identity_dataset_id = "customer_identity"
    
    print(f"============================================================")
    print(f"Syncing Demo Customers Pool for Project: {project_id}")
    print(f"Data Source Dataset:     {data_dataset_id}")
    print(f"Identity Target Dataset: {identity_dataset_id}")
    print(f"============================================================")
    
    sync_demo_customers(project_id, data_dataset_id, identity_dataset_id)
