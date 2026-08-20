variable "credentials" {
  description = "My Credentials"
  default     = "../../keys/tf-sa-key.json"
  #ex: if you have a directory where this file is called keys with your service account json file
  #saved there as my-creds.json you could use default = "./keys/my-creds.json"
}

variable "project_id" {
  description = "The GCP project ID"
  type        = string
  default     = "banking-agent-rag-mcp"
}

variable "region" {
  description = "The GCP region for resources"
  type        = string
  default     = "us-central1"
}

variable "location" {
  description = "The GCP location for resources"
  type        = string
  default     = "us-central1"
}

variable "dataset_id" {
  description = "BigQuery dataset ID"
  type        = string
  default     = "banking_data"
}

variable "customer_identity_dataset_id" {
  description = "BigQuery dataset ID for customer identity and demo tracking"
  type        = string
  default     = "customer_identity"
}

variable "analytics_dataset_id" {
  description = "BigQuery dataset ID for analytical mart views and metrics"
  type        = string
  default     = "analytics"
}