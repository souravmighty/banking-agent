# ------------------------------------------------------------------------------
# Cloud Run Service (V2) for MCP Transaction Server
# ------------------------------------------------------------------------------
resource "google_cloud_run_v2_service" "mcp_server" {
  count    = var.deploy_cloud_run ? 1 : 0
  name     = var.cloud_run_service_name
  location = var.region
  project  = var.project_id
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.mcp_server_sa.email

    scaling {
      min_instance_count = 0
      max_instance_count = 10
    }

    containers {
      image = var.container_image

      resources {
        limits = {
          cpu    = "1000m"
          memory = "1024Mi"
        }
      }

      ports {
        container_port = 8080
      }

      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }

      env {
        name  = "GOOGLE_CLOUD_LOCATION"
        value = var.region
      }

      env {
        name  = "BIGQUERY_DATASET"
        value = var.banking_dataset_id
      }

      env {
        name  = "CUSTOMER_IDENTITY_DATASET"
        value = var.customer_identity_dataset_id
      }

      env {
        name  = "EMAIL_FROM"
        value = var.email_from
      }

      dynamic "env" {
        for_each = var.resend_api_key != "" ? [1] : []
        content {
          name = "RESEND_API_KEY"
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.resend_api_key[0].secret_id
              version = "latest"
            }
          }
        }
      }
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }

  depends_on = [
    google_project_service.services,
    google_project_iam_member.mcp_sa_role_bindings,
    google_service_account.mcp_server_sa
  ]
}

# ------------------------------------------------------------------------------
# Cloud Run Invocation Access Policy
# ------------------------------------------------------------------------------
resource "google_cloud_run_v2_service_iam_member" "invoker" {
  count    = var.deploy_cloud_run && var.allow_unauthenticated ? 1 : 0
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.mcp_server[0].name
  role     = "roles/run.invoker"
  member   = "allUsers"

  depends_on = [google_cloud_run_v2_service.mcp_server]
}
