import logging

from google.adk.tools import ToolContext
from google.adk.tools.agent_tool import AgentTool

import os
from google.adk.agents.readonly_context import ReadonlyContext
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams

from .sub_agents import bigquery_agent

logger = logging.getLogger(__name__)


async def call_bigquery_agent(
    question: str,
    tool_context: ToolContext,
):
    """Tool to call bigquery database (nl2sql) agent."""
    logger.debug("call_bigquery_agent: %s", question)

    agent_tool = AgentTool(agent=bigquery_agent)

    bigquery_agent_output = await agent_tool.run_async(
        args={"request": question}, tool_context=tool_context
    )
    tool_context.state["bigquery_agent_output"] = bigquery_agent_output
    return bigquery_agent_output


def get_transaction_mcp_toolset() -> McpToolset:
    """
    Constructs an McpToolset connected to the remote FastMCP Transaction microservice.
    Uses dynamic header_provider to supply Cloud Run IAM tokens and
    end-user authentication tokens (Firebase JWT) on every tool call.
    """
    mcp_url = (
        os.getenv("TRANSACTION_MCP_SERVER_URL")
        or os.getenv("MCP_SERVER_URL")
        or "http://localhost:8080"
    )
    mcp_endpoint = mcp_url if mcp_url.rstrip("/").endswith("/mcp") else f"{mcp_url.rstrip('/')}/mcp"

    def _header_provider(ctx: ReadonlyContext) -> dict[str, str]:
        headers: dict[str, str] = {}
        
        # 1. Cloud Run service-to-service IAM authentication
        is_cloud_run = (
            os.getenv("K_SERVICE") is not None
            or os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "FALSE").upper() == "TRUE"
        )
        if is_cloud_run and not mcp_url.startswith("http://localhost") and not mcp_url.startswith("http://127.0.0.1"):
            try:
                from google.auth.transport.requests import Request
                from google.oauth2.id_token import fetch_id_token
                headers["Authorization"] = f"Bearer {fetch_id_token(Request(), mcp_url)}"
            except Exception as e:
                logger.warning("Could not mint GCP ID token for remote MCP server: %s", e)

        # 2. End-user banking identity token (Firebase JWT / test token)
        user_token = (
            ctx.state.get("jwt_token")
            or ctx.state.get("token")
            or (getattr(ctx.session, "state", {}).get("jwt_token") if hasattr(ctx, "session") and ctx.session else None)
        )
        if user_token:
            headers["x-firebase-id-token"] = user_token
            headers["x-auth-token"] = user_token
            if "Authorization" not in headers:
                headers["Authorization"] = f"Bearer {user_token}"

        return headers

    return McpToolset(
        connection_params=StreamableHTTPConnectionParams(
            url=mcp_endpoint,
            timeout=60.0,
        ),
        header_provider=_header_provider,
    )