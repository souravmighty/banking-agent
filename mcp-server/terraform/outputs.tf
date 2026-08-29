output "service_account_email" {
  description = "The email address of the MCP Server runtime service account"
  value       = google_service_account.mcp_server_sa.email
}

output "service_account_id" {
  description = "The unique ID of the MCP Server service account"
  value       = google_service_account.mcp_server_sa.id
}

output "cloud_run_service_name" {
  description = "The name of the deployed Cloud Run service"
  value       = var.deploy_cloud_run ? google_cloud_run_v2_service.mcp_server[0].name : var.cloud_run_service_name
}

output "cloud_run_service_url" {
  description = "The HTTP URI of the deployed Cloud Run MCP service"
  value       = var.deploy_cloud_run ? google_cloud_run_v2_service.mcp_server[0].uri : null
}

output "mcp_endpoint_url" {
  description = "The FastMCP endpoint URI for ADK McpToolset integration"
  value       = var.deploy_cloud_run ? "${google_cloud_run_v2_service.mcp_server[0].uri}/mcp" : null
}
