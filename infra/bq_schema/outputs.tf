output "dataset_id" {
  description = "BigQuery dataset ID"
  value       = google_bigquery_dataset.banking_dataset.dataset_id
}

# output "staging_bucket" {
#   description = "GCS bucket for data staging"
#   value       = google_storage_bucket.data_staging.name
# }

output "tables" {
  description = "Created BigQuery tables"
  value = {
    customers                 = google_bigquery_table.customers.table_id
    accounts                  = google_bigquery_table.accounts.table_id
    transactions              = google_bigquery_table.transactions.table_id
    credit_scores             = google_bigquery_table.credit_scores.table_id
    credit_cards              = google_bigquery_table.credit_cards.table_id
    loans                     = google_bigquery_table.loans.table_id
    fixed_deposits            = google_bigquery_table.fixed_deposits.table_id
    beneficiaries             = google_bigquery_table.beneficiaries.table_id
    customer_identity_mapping = google_bigquery_table.customer_identity_mapping.table_id
  }
}

output "bigquery_console_url" {
  description = "URL to view the dataset in BigQuery console"
  value       = "https://console.cloud.google.com/bigquery?project=${var.project_id}&d=${google_bigquery_dataset.banking_dataset.dataset_id}&page=dataset"
}