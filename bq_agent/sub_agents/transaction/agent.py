
import os
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams
from .prompts import return_instructions_transaction

transaction_agent = LlmAgent(
    model=os.getenv("TRANSACTION_AGENT_MODEL", "gemini-2.5-flash"),
    name="transaction_agent",
    instruction=return_instructions_transaction(),
    tools=[
        McpToolset(
            connection_params=StreamableHTTPConnectionParams(
                url=os.environ.get("MCP_SERVER_URL", "http://localhost:8080/mcp")
            ),
            tool_filter=['make_transaction', 'credit_card_payment']
        )
    ],
)
