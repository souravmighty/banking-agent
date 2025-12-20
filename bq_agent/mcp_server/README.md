# MCP server for bq_agent

This package exposes two remote tools for the banking dataset:

- `make_transaction(from_account_id, to_account_id, amount, confirm=False)`
- `credit_card_payment(cc_account_id, from_account_id, option='full', amount=None, confirm=False)`

How it works
- The implementation uses Google BigQuery to read and update the `accounts`
  and `transactions` tables in dataset `banking-agent-adk-mcp.banking_data`.
- The server follows the FastMCP quickstart pattern: a `FastMCP` server
  object named `mcp` is created at module import time and tools are
  registered with `@mcp.tool`. The server runs with the HTTP transport by
  default so clients can call tools remotely.

Quick start (FastMCP HTTP remote server)

1. Install deps:

```bash
pip install fastmcp google-cloud-bigquery
```

2. Set credentials if needed:

```bash
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json
```

3. Run the server (recommended: use FastMCP CLI):

```bash
# using the FastMCP CLI (starts HTTP transport on port 8000)
fastmcp run bq_agent/mcp_server/server.py:mcp --transport http --port 8000

# or run directly with python (env vars control host/port)
export MCP_HOST=0.0.0.0
export MCP_PORT=8080
python -m bq_agent.mcp_server.server
```

Call the server from a FastMCP client (example):

```python
import asyncio
from fastmcp import Client

async def call_tx():
    client = Client("http://localhost:8000/mcp")
    async with client:
        resp = await client.call_tool("make_transaction", {"from_account_id": 1, "to_account_id": 2, "amount": 50.0, "confirm": False})
        print(resp)

asyncio.run(call_tx())
```

Notes & caveats
- `fastmcp` is required to run this server in HTTP mode. The project
  previously included a FastAPI fallback; this server now expects FastMCP
  per the quickstart. If you need a fallback for environments without
  `fastmcp`, let me know and I can add one back.
- BigQuery is not an OLTP database. The code uses UPDATE statements and
  row inserts; for heavy concurrency or strict transactional guarantees you
  should move to a transactional store or add additional locking.
- The credit card fields (statement, minimum due) are estimated using
  heuristics; adapt as needed when richer data is available.
