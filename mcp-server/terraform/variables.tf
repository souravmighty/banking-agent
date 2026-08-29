variable "project_id" {
  description = "The Google Cloud Project ID where MCP Transaction Server resources will be created"
  type        = string
  default     = "banking-agent-rag-mcp"
}

variable "region" {
  description = "The Google Cloud Region for Cloud Run and regional resources"
  type        = string
  default     = "us-central1"
}

variable "service_account_id" {
  description = "The ID for the dedicated MCP Server runtime service account"
  type        = string
  default     = "mcp-server-sa"
}

variable "service_account_display_name" {
  description = "Display name for the MCP Server service account"
  type        = string
  default     = "BankPilot MCP Transaction Server Service Account"
}

variable "cloud_run_service_name" {
  description = "Name of the Cloud Run service"
  type        = string
  default     = "transaction-mcp-server"
}

variable "container_image" {
  description = "Container image URL to deploy to Cloud Run"
  type        = string
  default     = "gcr.io/banking-agent-rag-mcp/transaction-mcp-server:latest"
}

variable "deploy_cloud_run" {
  description = "Whether to provision the Cloud Run service in Terraform (set to false if deployed via Cloud Build)"
  type        = bool
  default     = true
}

variable "allow_unauthenticated" {
  description = "Whether to allow unauthenticated invocations to the Cloud Run service"
  type        = bool
  default     = true
}

variable "banking_dataset_id" {
  description = "BigQuery dataset containing banking ledger, accounts, cards, transactions"
  type        = string
  default     = "banking_data"
}

variable "customer_identity_dataset_id" {
  description = "BigQuery dataset containing customer identity mappings"
  type        = string
  default     = "customer_identity"
}

variable "email_from" {
  description = "Default sender email address for OTP challenge emails"
  type        = string
  default     = "BankPilot <security@contact.souravmaiti.dev>"
}

variable "resend_api_key" {
  description = "Resend API key for transactional email dispatch"
  type        = string
  default     = ""
  sensitive   = true
}

variable "gcp_services" {
  description = "List of GCP API services required for MCP Server execution and deployment"
  type        = list(string)
  default = [
    "run.googleapis.com",
    "bigquery.googleapis.com",
    "cloudbuild.googleapis.com",
    "containerregistry.googleapis.com",
    "artifactregistry.googleapis.com",
    "iam.googleapis.com",
    "secretmanager.googleapis.com",
    "logging.googleapis.com",
    "monitoring.googleapis.com"
  ]
}
