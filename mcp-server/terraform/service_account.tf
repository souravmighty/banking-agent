# ------------------------------------------------------------------------------
# Data sources
# ------------------------------------------------------------------------------
data "google_project" "project" {
  project_id = var.project_id
}

# ------------------------------------------------------------------------------
# Dedicated Runtime Service Account for MCP Transaction Server
# ------------------------------------------------------------------------------
resource "google_service_account" "mcp_server_sa" {
  account_id   = var.service_account_id
  display_name = var.service_account_display_name
  description  = "Runtime service account for BankPilot MCP Transaction Server with BigQuery ledger access"
  project      = var.project_id

  depends_on = [google_project_service.services]
}

# ------------------------------------------------------------------------------
# IAM Roles for MCP Server Service Account
# ------------------------------------------------------------------------------
locals {
  mcp_sa_roles = [
    "roles/bigquery.dataEditor",         # Read/write access to update ledger & accounts
    "roles/bigquery.jobUser",            # Execute queries and transactions in BigQuery
    "roles/logging.logWriter",           # Ingest application logs to Cloud Logging
    "roles/monitoring.metricWriter",     # Write telemetry and performance metrics
    "roles/secretmanager.secretAccessor" # Read secrets (e.g. Resend API key)
  ]
}

resource "google_project_iam_member" "mcp_sa_role_bindings" {
  for_each = toset(local.mcp_sa_roles)

  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.mcp_server_sa.email}"

  depends_on = [
    google_service_account.mcp_server_sa,
    google_project_service.services
  ]
}

# ------------------------------------------------------------------------------
# Cloud Build CI/CD Service Account Permissions
# ------------------------------------------------------------------------------
# Allow Cloud Build to act as the runtime service account during Cloud Run deployment
resource "google_service_account_iam_member" "cloudbuild_sa_user" {
  service_account_id = google_service_account.mcp_server_sa.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${data.google_project.project.number}@cloudbuild.gserviceaccount.com"

  depends_on = [
    google_service_account.mcp_server_sa,
    google_project_service.services
  ]
}

# Allow Cloud Build to administer Cloud Run services
resource "google_project_iam_member" "cloudbuild_run_admin" {
  project = var.project_id
  role    = "roles/run.admin"
  member  = "serviceAccount:${data.google_project.project.number}@cloudbuild.gserviceaccount.com"

  depends_on = [google_project_service.services]
}

# ------------------------------------------------------------------------------
# Optional Secret Manager: Resend API Key
# ------------------------------------------------------------------------------
resource "google_secret_manager_secret" "resend_api_key" {
  count     = var.resend_api_key != "" ? 1 : 0
  secret_id = "mcp-server-resend-api-key"
  project   = var.project_id

  replication {
    auto {}
  }

  depends_on = [google_project_service.services]
}

resource "google_secret_manager_secret_version" "resend_api_key_version" {
  count       = var.resend_api_key != "" ? 1 : 0
  secret      = google_secret_manager_secret.resend_api_key[0].id
  secret_data = var.resend_api_key
}

resource "google_secret_manager_secret_iam_member" "resend_api_key_accessor" {
  count     = var.resend_api_key != "" ? 1 : 0
  secret_id = google_secret_manager_secret.resend_api_key[0].id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.mcp_server_sa.email}"
}
