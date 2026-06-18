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
import logging

from bq_agent.mcp_server import tools

from fastmcp import FastMCP, Context

from fastmcp.server.auth.providers.google import GoogleProvider
from fastmcp.server.dependencies import get_access_token, get_context
from fastmcp.server.middleware import Middleware, MiddlewareContext
from mcp import McpError
from mcp.types import ErrorData
import dotenv 

from google.cloud import bigquery
from dataclasses import dataclass
# -----------------------------------------------------------------------------
# Logging & environment setup
# -----------------------------------------------------------------------------

logger = logging.getLogger("mcp.rs.google")  # (10) A named logger for our service
logging.basicConfig(level=logging.INFO)      # (11) Print INFO+ logs to stdout (adjust as needed)

dotenv.load_dotenv()  # (12) Load .env file into os.environ (only affects current process)

def _get_bq_client():
    """Return a BigQuery client (uses ADC or path set in env var)."""
    key_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if key_path:
        return bigquery.Client.from_service_account_json(key_path)
    return bigquery.Client(project="banking-agent-adk-mcp")

bq_client = _get_bq_client()

PROJECT_DATASET_CUSTOMERS = "banking-agent-adk-mcp.banking_data.customers"
PROJECT_DATASET_ACCOUNTS = "banking-agent-adk-mcp.banking_data.accounts"

# -----------------------------------------------------------------------------
# Configuration – these can all be supplied via environment variables.
# When the variable is missing, we fall back to safe local defaults for dev.
# -----------------------------------------------------------------------------

# (13) **RS_BASE_URL**: The public base URL of THIS server (the RS+AS facade).
#      Clients will use this value for discovery and redirects. It must match
#      how the browser/client can actually reach you. In local dev we default
#      to http://localhost:8005.
BASE_URL = os.environ.get("RS_BASE_URL", "http://localhost:8080")

# (14) Local bind host and port for the Uvicorn server.
#      HOST "0.0.0.0" listens on all interfaces (fine in dev), PORT defaults to 8005.
HOST = os.environ.get("RS_HOST", "0.0.0.0")
PORT = int(os.environ.get("RS_PORT", "8080"))

# (15) **MCP_PATH** is the exact path segment under BASE_URL that is the
#      protected MCP endpoint. This string becomes the **resource indicator**.
#      IMPORTANT: CONSISTENCY MATTERS. If you choose "/mcp", then everywhere
#      (metadata, clients, and resource= param) must use "/mcp" (no trailing '/').
MCP_PATH = os.environ.get("MCP_PATH", "/mcp")

# (16) Google OAuth app credentials. These identify your Google project to Google.
#      They are used by the provider when exchanging the auth code for tokens.
#      If missing, we exit with a clear error (since auth can’t work without them).
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "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")

# (17) The path on THIS server where Google will redirect the user back with
#      the authorization code. You must register the full URL
#      (BASE_URL + REDIRECT_PATH) in your Google Cloud Console OAuth client.
REDIRECT_PATH = os.environ.get("GOOGLE_REDIRECT_PATH", "/auth/callback")

# (18) The minimal scopes we ask Google for. In many OAuth tutorials you’ll also
#      see `email` and `profile`, but modern Google profile/email fetch uses:
#        • openid
#        • https://www.googleapis.com/auth/userinfo.email
#        • https://www.googleapis.com/auth/userinfo.profile
#      We split on whitespace so you can define REQUIRED_SCOPES in .env as a single line.
REQUIRED_SCOPES = os.environ.get(
    "REQUIRED_SCOPES",
    "openid https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/userinfo.profile",
).split()

# (19) DCR: allow MCP clients to dynamically register loopback redirect URIs.
#      In dev, MCP clients typically spin up a small local HTTP listener on a
#      random port (e.g., http://localhost:53530/oauth/callback). We permit
#      localhost patterns by default. In production, lock this down.
ALLOWED_CLIENT_REDIRECTS = os.environ.get(
    "ALLOWED_CLIENT_REDIRECT_URIS",
    "http://localhost:*;http://127.0.0.1:*",
).split(";")

# (20) A derived, canonical **resource** string (audience). This must match how
#      clients connect. We expose it in `.well-known/oauth-protected-resource`.
#      Clients will include this exact value as the `resource=` parameter in
#      their authorization request so that Google issues a token bound to it.
RESOURCE = f"{BASE_URL}{MCP_PATH}"  # e.g., "http://localhost:8005/mcp"
#      ⚠️ DO NOT add a trailing slash here unless ALL clients also use the slash.


# -----------------------------------------------------------------------------
# Build the Google OAuth provider (our AS facade that delegates to Google)
# -----------------------------------------------------------------------------

# (21) We now construct a GoogleProvider. This single object:
#       • Publishes AS metadata (/.well-known/oauth-authorization-server),
#       • Provides /authorize, /token, /register endpoints,
#       • Manages PKCE + DCR,
#       • Talks to Google for user login and token validation,
#       • Integrates with FastMCP so the protected `/mcp` endpoint knows how
#         to challenge clients and verify their bearer tokens.
google_auth = GoogleProvider(
    client_id=GOOGLE_CLIENT_ID,                     # (22) Your Google OAuth client id
    client_secret=GOOGLE_CLIENT_SECRET,             # (23) Your Google OAuth client secret
    base_url=BASE_URL,                              # (24) Public base URL of THIS server
    redirect_path=REDIRECT_PATH,                    # (25) Callback path (BASE_URL + this) registered at Google
    required_scopes=REQUIRED_SCOPES,                # (26) Scopes we require from Google
    allowed_client_redirect_uris=ALLOWED_CLIENT_REDIRECTS,  # (27) DCR patterns for loopback OAuth clients
    # (28) The provider infers the resource from how `/mcp` is mounted by FastMCP,
    #      but we document RESOURCE above to emphasize the importance of exact match.
)

MCP_NAME = os.environ.get("MCP_NAME", "Banking MCP Server")


class AuthMiddleware(Middleware):
    async def on_initialize(self, context: Context, call_next):


        if not context.fastmcp_context.get_state("customer_data"):
            token = get_access_token()
            user_email = token.claims.get("email")
            if not user_email:
                raise McpError(ErrorData(code=-32000, message="Please sign in via Google to proceed."))

            # 2. Perform the BigQuery registration check
            customer_record = _check_bigquery_registration(user_email)
            
            if not customer_record:
                raise McpError(ErrorData(code=-32001, message=f"Access Denied: {user_email} is not a registered customer."))

            # 3. STORE IN SESSION: This stays on the server side
            context.fastmcp_context.set_state("customer_data", customer_record)
            ctx = get_context()
            print(type(ctx.get_state("customer_data")))

        # Log successful initialization
        await call_next(context)
        print("Customer authenticated successfully")
        
# class FetchCustomerMiddleware(Middleware):
#     async def on_call_tool(self, context: Context, call_next):


#         if not context.fastmcp_context.get_state("customer_data"):
#             token = get_access_token()
#             user_email = token.claims.get("email")
#             if not user_email:
#                 raise McpError(ErrorData(code=-32000, message="Please sign in via Google to proceed."))

#             # 2. Perform the BigQuery registration check
#             customer_record = _check_bigquery_registration(user_email)
            
#             if not customer_record:
#                 raise McpError(ErrorData(code=-32001, message=f"Access Denied: {user_email} is not a registered customer."))

#             # 3. STORE IN SESSION: This stays on the server side
#             context.fastmcp_context.set_state("customer_id", customer_record['customer_id'])

#         # Log successful initialization
#         await call_next(context)
#         print("Customer ID fetched successfully")
        
        
# Create the MCP server
mcp = FastMCP(
  name=MCP_NAME,
   instructions=(
        "Protected MCP server that delegates OAuth to Google via a DCR-capable proxy."
    ),  # (31) Short description for clients
    auth=google_auth,  # (32) The magic glue: provides 401 challenges + metadata + OAuth endpoints
)

mcp.add_middleware(AuthMiddleware())
# mcp.add_middleware(FetchCustomerMiddleware())


def _check_bigquery_registration(email: str):
    """Queries BigQuery and returns a dictionary of IDs."""
    query = f"""
        SELECT c.customer_id, a.account_number, a.account_type
        FROM `{PROJECT_DATASET_CUSTOMERS}` c
        LEFT JOIN `{PROJECT_DATASET_ACCOUNTS}` a ON c.customer_id = a.customer_id
        WHERE c.email = @email AND c.is_current = true AND (a.is_current = true OR a.account_number IS NULL)
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("email", "STRING", email)]
    )
    results = list(bq_client.query(query, job_config=job_config).result())
    
    if not results:
        return None

    return {
        "customer_id": results[0].customer_id,
        "accounts": [{"number": r.account_number, "type": r.account_type} for r in results if r.account_number]
    }
    
# @dataclass
# class ConfirmTransaction:
#     confirm: bool
    
@mcp.tool
async def get_customer_info(ctx: Context) -> Dict[str, Any]:
    """Return dict with 'customer_id', 'accounts' and other details."""
    # ctx = get_context()
    customer_data = ctx.get_state("customer_data")
    return {
            "customer_id": customer_data["customer_id"],
            "accounts": customer_data["accounts"]
    }
    
@mcp.tool
async def make_transaction(from_account_number: str, to_account_number: str, amount: float, confirm: bool = False) -> Dict[str, Any]:
    """Wrapper tool that delegates to the BigQuery-backed implementation.

    Signature follows the documented API so clients can call it remotely.
    """
    return tools.make_transaction(from_account_number=from_account_number, to_account_number=to_account_number, amount=amount, confirm=confirm)
    

@mcp.tool                                                                     
async def credit_card_payment(cc_account_number: str, from_account_number: str, option: str = "full", amount: float = None, confirm: bool = False) -> Dict[str, Any]:
    """Wrapper tool to pay credit card bills via `make_transaction`.
    """
    # Keep amount default as None to match tools.credit_card_payment signature
    return tools.credit_card_payment(cc_account_number=cc_account_number, from_account_number=from_account_number, option=option, amount=amount, confirm=confirm)

@mcp.tool()
async def get_user_info(ctx: Context) -> dict[str, Any]:
    """
    Return information about the authenticated Google user
    (from the validated access token / userinfo).
    """
    # (38) Provider surfaces the current request’s verified access token via a dependency.
    #      We import here so the module remains importable even if FastMCP internals change.
    from fastmcp.server.dependencies import get_access_token  # type: ignore

    token = get_access_token()  # (39) Grab the verified token object for this request

    # (40) Depending on provider config, claims may include OIDC-like fields.
    #      For Google, we often also fetch userinfo to enrich these claims.
    return {
        "google_id": token.claims.get("sub"),       # (41) Subject (user id)
        "email": token.claims.get("email"),         # (42) Email (if scope allowed)
        "name": token.claims.get("name"),           # (43) Display name (if available)
        "picture": token.claims.get("picture"),     # (44) Avatar URL (if available)
        "locale": token.claims.get("locale"),       # (45) Locale (if available)
        
        # (46) If you need more profile fields, call Google’s userinfo endpoint
        #      (the provider already does this in many setups).
    }


if __name__ == "__main__":
    # (49) Fail fast if Google credentials are missing. Without these, the
    #      provider can’t exchange auth codes for tokens.
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        logger.error(
            "GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET is not set. "
            "Put them in your shell env or a .env file before starting the server."
        )
        raise SystemExit(1)

    # (50) Log the key values so you can spot mismatches (e.g., trailing slash issues).
    logger.info("🚀 RS base URL: %s", BASE_URL)
    logger.info("🛣  MCP endpoint path: %s", MCP_PATH)
    logger.info("🔁 Redirect path (Google): %s", REDIRECT_PATH)
    logger.info("🔐 Required scopes: %s", " ".join(REQUIRED_SCOPES))
    logger.info("🏁 Allowed DCR client redirects: %s", ALLOWED_CLIENT_REDIRECTS)
    logger.info("🎯 Resource (audience): %s", RESOURCE)

    # (51) Start the server with the **streamable-http** transport. This exposes:
    #       • POST /mcp (protected MCP over HTTP)
    #       • GET  /.well-known/oauth-protected-resource  (RS metadata)
    #       • GET  /.well-known/oauth-authorization-server (AS metadata)
    #       • GET  /authorize, POST /token, POST /register (AS facade)
    #       • GET  /auth/callback (Google → RS → client loopback)
    #
    #     `path=MCP_PATH` is CRUCIAL for resource correctness. The clients will
    #     include this full resource (BASE_URL + MCP_PATH) when authorizing.
    mcp.run(
        transport="streamable-http",  # (52) Use HTTP transport (good for local dev & desktop apps)
        host=HOST,                    # (53) Bind host (0.0.0.0 listens on all interfaces)
        port=PORT,                    # (54) Bind port (ensure it matches your BASE_URL)
        path=MCP_PATH,                # (55) Mount path for the MCP endpoint (defines the resource)
    )
