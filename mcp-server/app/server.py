import logging
import os
from typing import Optional, Dict, Any
from fastmcp import FastMCP, Context
import fastmcp.server.dependencies as fastmcp_deps

from app.config import settings
from app.auth import active_auth_token, auth_manager
from app import tools as transaction_tools

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("mcp-server")

# Initialize FastMCP Server
mcp = FastMCP(
    name=settings.PROJECT_NAME,
)


def _extract_and_set_context_token(explicit_token: Optional[str] = None):
    """Helper to capture auth token from HTTP headers or explicit parameter into contextvars."""
    token = explicit_token
    if not token:
        try:
            headers = fastmcp_deps.get_http_headers()
            if headers:
                token = auth_manager.extract_token_from_headers(headers)
        except Exception:
            pass
    if token:
        active_auth_token.set(token)
    return token


@mcp.tool()
def transfer_money(
    beneficiary: str,
    amount: float,
    currency: str = "INR",
    source_account: Optional[str] = None,
    auth_token: Optional[str] = None,
    idempotency_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Transfers money to an existing authorized beneficiary payee.
    
    If the amount exceeds the customer's transaction threshold (default INR 5,000),
    a 2-Factor OTP challenge is generated and dispatched to the customer's registered email.
    
    Args:
        beneficiary: Beneficiary name, ID, or account number (must be in authorized payees).
        amount: Amount to transfer (must be positive).
        currency: Currency code (default: 'INR').
        source_account: Optional source bank account number. Defaults to primary active account.
        auth_token: Optional authentication token if not supplied via headers.
        idempotency_key: Optional idempotency key to prevent double execution.
    """
    _extract_and_set_context_token(auth_token)
    return transaction_tools.transfer_money(
        beneficiary=beneficiary,
        amount=amount,
        currency=currency,
        source_account=source_account,
        auth_token=auth_token,
        idempotency_key=idempotency_key
    )


@mcp.tool()
def pay_credit_card(
    card_identifier: str,
    amount: float,
    source_account: Optional[str] = None,
    auth_token: Optional[str] = None,
    idempotency_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Pays an authenticated customer's credit card bill from their active deposit account.
    
    If the payment amount exceeds the customer's transaction threshold (default INR 5,000),
    a 2-Factor OTP challenge is generated and dispatched to the customer's registered email.
    
    Args:
        card_identifier: Card account number, card number, or last 4 digits.
        amount: Payment amount (must be positive).
        source_account: Optional source deposit account. Defaults to primary active account.
        auth_token: Optional authentication token.
        idempotency_key: Optional unique idempotency key.
    """
    _extract_and_set_context_token(auth_token)
    return transaction_tools.pay_credit_card(
        card_identifier=card_identifier,
        amount=amount,
        source_account=source_account,
        auth_token=auth_token,
        idempotency_key=idempotency_key
    )


@mcp.tool()
def verify_transaction_otp(
    challenge_id: str,
    otp: str
) -> Dict[str, Any]:
    """
    Verifies a transaction-bound OTP challenge and atomically executes the approved operation.
    
    Args:
        challenge_id: The security challenge identifier returned when OTP was triggered.
        otp: The 6-digit code sent to the customer's registered email.
    """
    return transaction_tools.verify_transaction_otp(
        challenge_id=challenge_id,
        otp=otp
    )


@mcp.tool()
def get_transaction_limit(
    auth_token: Optional[str] = None
) -> Dict[str, Any]:
    """
    Returns the authenticated customer's transaction thresholds and OTP limit policies.
    """
    _extract_and_set_context_token(auth_token)
    return transaction_tools.get_transaction_limit(
        auth_token=auth_token
    )


@mcp.tool()
def update_transaction_limit(
    new_limit: float,
    currency: str = "INR",
    auth_token: Optional[str] = None
) -> Dict[str, Any]:
    """
    Requests an update to the customer's single-transaction threshold.
    Because this modifies security policy, it requires OTP step-up verification.
    
    Args:
        new_limit: Requested new limit amount in INR (maximum INR 100,000).
        currency: Currency code (default: 'INR').
        auth_token: Optional authentication token.
    """
    _extract_and_set_context_token(auth_token)
    return transaction_tools.update_transaction_limit(
        new_limit=new_limit,
        currency=currency,
        auth_token=auth_token
    )


@mcp.tool()
def get_transaction_status(
    identifier: str
) -> Dict[str, Any]:
    """
    Checks the status of a transaction, challenge, or transfer reference.
    
    Args:
        identifier: A transaction_id (TXN_...), reference_id (REF_...), or challenge_id (ch_...).
    """
    return transaction_tools.get_transaction_status(
        identifier=identifier
    )


@mcp.tool()
def add_beneficiary(
    beneficiary_name: str,
    beneficiary_account_number: str,
    bank_name: str,
    ifsc_code: str,
    auth_token: Optional[str] = None
) -> Dict[str, Any]:
    """
    Registers a new authorized beneficiary for fund transfers.
    
    Args:
        beneficiary_name: Full name or nickname of the payee.
        beneficiary_account_number: The bank account number of the payee.
        bank_name: Name of the payee's bank (e.g., 'HDFC Bank', 'State Bank of India', 'ICICI Bank').
        ifsc_code: Branch routing IFSC code for the payee bank.
        auth_token: Optional authentication token if not supplied via headers.
    """
    _extract_and_set_context_token(auth_token)
    return transaction_tools.add_beneficiary(
        beneficiary_name=beneficiary_name,
        beneficiary_account_number=beneficiary_account_number,
        bank_name=bank_name,
        ifsc_code=ifsc_code,
        auth_token=auth_token
    )


@mcp.custom_route("/health", methods=["GET"])
async def health(request):
    from starlette.responses import JSONResponse
    return JSONResponse({
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "tools": [
            "transfer_money",
            "pay_credit_card",
            "verify_transaction_otp",
            "get_transaction_limit",
            "update_transaction_limit",
            "get_transaction_status",
            "add_beneficiary"
        ]
    })


@mcp.custom_route("/", methods=["GET"])
async def root(request):
    from starlette.responses import JSONResponse
    return JSONResponse({
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "mcp_endpoint": "/mcp",
        "health_endpoint": "/health"
    })


# FastMCP ASGI app with lifespan and streamable HTTP session manager
app = mcp.http_app()


if __name__ == "__main__":
    import sys
    if "--stdio" in sys.argv or (len(sys.argv) > 1 and sys.argv[1] == "stdio"):
        # Run in Stdio mode for MCP clients like Claude Desktop / MCPJam stdio
        mcp.run(transport="stdio")
    else:
        # Run in HTTP / SSE mode for Cloud Run & HTTP MCP clients / MCPJam HTTP
        import uvicorn
        port = int(os.getenv("PORT", str(settings.MCP_PORT)))
        host = os.getenv("HOST", settings.MCP_HOST)
        uvicorn.run(
            "app.server:app",
            host=host,
            port=port,
            reload=False
        )
