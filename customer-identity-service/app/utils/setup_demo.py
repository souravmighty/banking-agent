import os
from google.cloud import bigquery
from app.config import settings

def setup_demo_environment():
    client = bigquery.Client(project=settings.GOOGLE_CLOUD_PROJECT)
    
    # 1. Create dataset customer_identity
    dataset_id = f"{settings.GOOGLE_CLOUD_PROJECT}.customer_identity"
    dataset = bigquery.Dataset(dataset_id)
    dataset.location = "us-central1"
    dataset = client.create_dataset(dataset, exists_ok=True)
    print(f"Dataset customer_identity ready.")

    
    # 2. Create demo_customers table
    demo_customers_ref = f"{dataset_id}.demo_customers"
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
    # Check if table exists
    try:
        client.get_table(demo_customers_ref)
        print("Table demo_customers already exists.")
    except Exception:
        table = client.create_table(table)
        print("Table demo_customers created successfully.")

    # 3. Create demo_customer_audit table
    audit_ref = f"{dataset_id}.demo_customer_audit"
    audit_schema = [
        bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("action", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("customer_id", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("demo_email", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("firebase_uid", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("performed_by", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("remarks", "STRING", mode="NULLABLE"),
    ]
    audit_table = bigquery.Table(audit_ref, schema=audit_schema)
    try:
        client.get_table(audit_ref)
        print("Table demo_customer_audit already exists.")
    except Exception:
        audit_table = client.create_table(audit_table)
        print("Table demo_customer_audit created successfully.")

    # 4. Populate Top 20 customers
    # First, let's see if we already have populated rows
    q_check = f"SELECT COUNT(*) as cnt FROM `{demo_customers_ref}`"
    results = list(client.query(q_check).result())
    if results and results[0]["cnt"] > 0:
        print("demo_customers table is already populated.")
        return

    print("Populating Top 20 customers into demo_customers...")
    q_rank = f"""
    WITH customer_balances AS (
      SELECT customer_id, SUM(balance) as total_balance, COUNT(account_number) as num_accounts
      FROM `{settings.GOOGLE_CLOUD_PROJECT}.{settings.BIGQUERY_DATASET}.accounts`
      WHERE is_current = TRUE AND account_status = "ACTIVE"
      GROUP BY customer_id
    ),
    customer_fds AS (
      SELECT customer_id, SUM(current_value) as fd_balance, COUNT(fd_account_number) as num_fds
      FROM `{settings.GOOGLE_CLOUD_PROJECT}.{settings.BIGQUERY_DATASET}.fixed_deposits`
      WHERE status = "ACTIVE"
      GROUP BY customer_id
    ),
    customer_cc AS (
      SELECT customer_id, COUNT(card_account_number) as num_cc
      FROM `{settings.GOOGLE_CLOUD_PROJECT}.{settings.BIGQUERY_DATASET}.credit_cards`
      WHERE is_current = TRUE AND status = "ACTIVE"
      GROUP BY customer_id
    ),
    customer_loans AS (
      SELECT customer_id, COUNT(loan_account_number) as num_loans
      FROM `{settings.GOOGLE_CLOUD_PROJECT}.{settings.BIGQUERY_DATASET}.loans`
      WHERE status = "ACTIVE"
      GROUP BY customer_id
    ),
    customer_tx AS (
      SELECT a.customer_id, 
             COUNT(t.transaction_id) as tx_volume, 
             SUM(CASE WHEN t.direction = "DEBIT" THEN t.amount ELSE 0 END) as total_debit
      FROM `{settings.GOOGLE_CLOUD_PROJECT}.{settings.BIGQUERY_DATASET}.transactions` t
      JOIN `{settings.GOOGLE_CLOUD_PROJECT}.{settings.BIGQUERY_DATASET}.accounts` a ON t.account_number = a.account_number
      WHERE a.is_current = TRUE
      GROUP BY a.customer_id
    )
    SELECT 
      c.customer_id,
      c.name,
      c.email,
      (
        0.35 * COALESCE(cb.total_balance, 0) +
        0.15 * COALESCE(cf.fd_balance, 0) +
        0.10 * (COALESCE(cb.num_accounts, 0) + COALESCE(cf.num_fds, 0) + COALESCE(cc.num_cc, 0) + COALESCE(cl.num_loans, 0)) +
        0.10 * (COALESCE(tx.total_debit, 0) / 6.0) +
        0.10 * COALESCE(tx.tx_volume, 0)
      ) as wealth_score
    FROM `{settings.GOOGLE_CLOUD_PROJECT}.{settings.BIGQUERY_DATASET}.customers` c
    LEFT JOIN customer_balances cb ON c.customer_id = cb.customer_id
    LEFT JOIN customer_fds cf ON c.customer_id = cf.customer_id
    LEFT JOIN customer_cc cc ON c.customer_id = cc.customer_id
    LEFT JOIN customer_loans cl ON c.customer_id = cl.customer_id
    LEFT JOIN customer_tx tx ON c.customer_id = tx.customer_id
    WHERE c.is_current = TRUE AND c.customer_status = "ACTIVE"
    ORDER BY wealth_score DESC
    LIMIT 20
    """
    top_20 = list(client.query(q_rank).result())
    
    import uuid
    if not top_20:
        print("No customers found to populate.")
        return

    # To avoid the streaming buffer issue, we construct a DML INSERT query
    values_clauses = []
    query_parameters = []
    for i, r in enumerate(top_20):
        demo_id = f"demo-{uuid.uuid4().hex[:8]}"
        cust_id = str(r.customer_id)
        name = r.name
        email = r.email
        
        # Append to value list
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
    print(f"Successfully inserted {len(top_20)} demo customers via DML.")


if __name__ == "__main__":
    setup_demo_environment()
