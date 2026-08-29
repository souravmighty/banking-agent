# Enable required Google Cloud Service APIs
resource "google_project_service" "services" {
  for_each = toset(var.gcp_services)

  project            = var.project_id
  service            = each.key
  disable_on_destroy = false
}
