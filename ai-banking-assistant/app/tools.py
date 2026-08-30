import logging

from google.adk.tools import ToolContext
from google.adk.tools.agent_tool import AgentTool

import os
from google.adk.agents.readonly_context import ReadonlyContext
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams

from .sub_agents import bigquery_agent

logger = logging.getLogger(__name__)


import httpx
from typing import Optional


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


async def retrieve_product_policy_knowledge(
    query: str,
    product_type: Optional[str] = None,
    product_id: Optional[str] = None,
    document_type: Optional[str] = None,
    region: str = "IN",
    top_k: int = 8,
) -> dict:
    """
    Retrieves authoritative, governed bank knowledge (products, credit card benefits, loan rates,
    bank policies, FAQs, terms & conditions) from the enterprise RAG Engine.

    Args:
        query: Semantic search question or topic (e.g. "Platinum credit card dining rewards and lounge access",
               "Home loan interest rate and foreclosure terms", "International wire transfer limits").
        product_type: Optional product category filter (e.g. "CREDIT_CARD", "LOAN", "SAVINGS", "INVESTMENT", "ACCOUNT").
        product_id: Optional specific product identifier.
        document_type: Optional document type filter (e.g. "PRODUCT", "POLICY", "FAQ", "TERMS_AND_CONDITIONS", "SERVICE_INFORMATION").
        region: Geographic region filter (default: "IN").
        top_k: Number of relevant knowledge passages to retrieve (default: 8).

    Returns:
        dict: Retrieved knowledge passages, source document names, versions, and product terms.
    """
    logger.info("retrieve_product_policy_knowledge called with query: %s", query)
    identity_service_url = os.getenv("IDENTITY_SERVICE_URL", "http://localhost:8001")
    retrieve_endpoint = f"{identity_service_url.rstrip('/')}/api/v1/knowledge/retrieve"

    payload = {
        "query": query,
        "access_scope": "CUSTOMER",
        "product_type": product_type,
        "product_id": product_id,
        "document_type": document_type,
        "region": region,
        "top_k": top_k,
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            headers = {"Content-Type": "application/json"}
            
            # If deployed on Cloud Run, mint IAM ID token for service-to-service auth
            is_cloud_run = os.getenv("K_SERVICE") is not None or os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "FALSE").upper() == "TRUE"
            if is_cloud_run and not identity_service_url.startswith("http://localhost") and not identity_service_url.startswith("http://127.0.0.1"):
                try:
                    from google.auth.transport.requests import Request
                    from google.oauth2.id_token import fetch_id_token
                    headers["Authorization"] = f"Bearer {fetch_id_token(Request(), identity_service_url)}"
                except Exception as ex:
                    logger.warning("Could not fetch GCP ID token for identity service: %s", ex)

            response = await client.post(retrieve_endpoint, json=payload, headers=headers)
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(
                    "Identity service knowledge retrieve returned status %s: %s",
                    response.status_code,
                    response.text,
                )
    except Exception as e:
        logger.error("HTTP error calling knowledge retrieve endpoint: %s", e)

    # Fallback: Direct Vertex AI RAG Engine retrieval if identity service is not reachable
    try:
        import vertexai
        from vertexai.preview import rag
        corpus_name = os.getenv(
            "RAG_CORPUS_NAME",
            "projects/569817520730/locations/us-central1/ragCorpora/8212569007207743488",
        )
        vertexai.init(
            project=os.getenv("GOOGLE_CLOUD_PROJECT", "banking-agent-rag-mcp"),
            location=os.getenv("RAG_LOCATION", "us-central1"),
        )
        rag_res = rag.retrieval_query(
            text=query,
            rag_corpora=[corpus_name],
            similarity_top_k=top_k,
        )
        contexts = []
        raw_items = getattr(rag_res.contexts, "contexts", []) if hasattr(rag_res, "contexts") else []
        for item in raw_items:
            contexts.append({
                "text": getattr(item, "text", ""),
                "source_uri": getattr(item, "source_uri", ""),
                "distance": getattr(item, "distance", None),
                "relevance_score": getattr(item, "score", None),
            })
        return {"query": query, "results": contexts, "total_found": len(contexts)}
    except Exception as ex:
        logger.error("Direct RAG fallback also failed: %s", ex)
        return {"query": query, "results": [], "total_found": 0, "error": str(ex)}


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