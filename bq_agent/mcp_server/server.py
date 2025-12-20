"""MCP server entrypoint using FastMCP HTTP transport.

This module follows the FastMCP quickstart pattern: it creates a `FastMCP`
server, registers tools using `@mcp.tool`, and exposes the server via the
HTTP transport. You can run it directly with Python or with the FastMCP CLI:

Direct run (HTTP transport):

  export MCP_HOST=0.0.0.0
  export MCP_PORT=8000
  python -m bq_agent.mcp_server.server

FastMCP CLI (recommended for more options):

  fastmcp run bq_agent/mcp_server/server.py:mcp --transport http --port 8000

The server exposes tools at the MCP HTTP endpoint (e.g. http://host:port/mcp).
Clients can use `fastmcp.Client` to call tools as shown in FastMCP docs.
"""

import os
from typing import Any, Dict

from bq_agent.mcp_server import tools

from fastmcp import FastMCP


MCP_NAME = os.environ.get("MCP_NAME", "Banking MCP Server")
MCP_HOST = os.environ.get("MCP_HOST", "0.0.0.0")
MCP_PORT = int(os.environ.get("MCP_PORT", "8080"))



# Create the MCP server
mcp = FastMCP(MCP_NAME)


@mcp.tool
async def make_transaction(from_account_id: int, to_account_id: int, amount: float, confirm: bool = False) -> Dict[str, Any]:
    """Wrapper tool that delegates to the BigQuery-backed implementation.

    Signature follows the documented API so clients can call it remotely.
    """
    return tools.make_transaction(from_account_id=from_account_id, to_account_id=to_account_id, amount=amount, confirm=confirm)


@mcp.tool
async def credit_card_payment(cc_account_id: int, from_account_id: int, option: str = "full", amount: float = None, confirm: bool = False) -> Dict[str, Any]:
    """Wrapper tool to pay credit card bills via `make_transaction`.
    """
    # Keep amount default as None to match tools.credit_card_payment signature
    return tools.credit_card_payment(cc_account_id=cc_account_id, from_account_id=from_account_id, option=option, amount=amount, confirm=confirm)


def main():
    # Run with HTTP transport by default for remote access
    mcp.run(transport="streamable-http", host=MCP_HOST, port=MCP_PORT)


if __name__ == "__main__":
    main()
