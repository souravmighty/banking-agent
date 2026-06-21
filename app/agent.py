import base64
import json
import logging
import os
from datetime import date
from dotenv import load_dotenv


from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.tools import BaseTool, ToolContext

# from google.adk.tools import load_artifacts
from google.genai import types
# from opentelemetry import trace
# from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
#     OTLPSpanExporter,
# )
# from opentelemetry.sdk import trace as trace_sdk
# from opentelemetry.sdk.trace.export import SimpleSpanProcessor

from .prompts import return_instructions_root

from .sub_agents.bigquery.tools import get_customer_profile, get_database_settings
from .tools import call_bigquery_agent, call_transaction_agent

from .sub_agents import bigquery_agent

load_dotenv()

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger(__name__)

import contextvars
import httpx
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional

firebase_jwt_var = contextvars.ContextVar("firebase_jwt", default="")
_session_tokens = {}  # Global mapping from user/session to token
_last_token = ""      # Thread-safe/process-safe global fallback for the single-user local app

class ASGIJWTInterceptorMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] not in ("http", b"http", "websocket", b"websocket"):
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))
        auth_bytes = headers.get(b"authorization", b"")
        auth_header = auth_bytes.decode("utf-8") if auth_bytes else ""
        
        token = ""
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            firebase_jwt_var.set(token)
            global _last_token
            _last_token = token
            _logger.info("ASGIJWTInterceptorMiddleware: Captured JWT token.")
        else:
            firebase_jwt_var.set("")
            
        # Try to parse session_id and user_id from POST requests to map token
        path = scope.get("path", "")
        if token and path in ("/run_sse", "/run") and scope.get("method") == "POST":
            try:
                # Read ASGI body stream safely
                body = b""
                more_body = True
                messages = []
                while more_body:
                    message = await receive()
                    messages.append(message)
                    body += message.get("body", b"")
                    more_body = message.get("more_body", False)
                
                # Parse body
                try:
                    body_json = json.loads(body.decode("utf-8"))
                    user_id = body_json.get("user_id") or body_json.get("userId")
                    session_id = body_json.get("session_id") or body_json.get("sessionId")
                    if user_id and session_id:
                        _session_tokens[(user_id, session_id)] = token
                        _session_tokens[session_id] = token
                        _logger.info("Successfully mapped session %s to JWT token in middleware.", session_id)
                except Exception as parse_err:
                    _logger.warning("Failed to parse JSON body in middleware: %s", parse_err)
                
                # Replay receive messages for FastAPI app to consume
                async def mock_receive():
                    if messages:
                        return messages.pop(0)
                    return await receive()
                
                await self.app(scope, mock_receive, send)
                return
            except Exception as e:
                _logger.error("Error reading body in middleware: %s", e)
                
        await self.app(scope, receive, send)

# Inject into existing FastAPI instances (since agent.py is loaded after FastAPI starts)
import gc
from fastapi import FastAPI
from starlette.middleware import Middleware

def inject_middleware_into_existing_apps():
    _logger.info("Running inject_middleware_into_existing_apps. Scanning GC...")
    try:
        objects = gc.get_objects()
        _logger.info("GC returned %d objects.", len(objects))
    except Exception as scan_err:
        _logger.error("Failed to call gc.get_objects(): %s", scan_err)
        return

    found_any = False
    for obj in objects:
        try:
            # Match by isinstance or class name to handle dynamic reloading/module class loading differences
            if isinstance(obj, FastAPI) or obj.__class__.__name__ == "FastAPI":
                found_any = True
                _logger.info("Found FastAPI instance in GC (class: %s). Already intercepted? %s", 
                             obj.__class__.__name__, hasattr(obj, "_asgi_jwt_intercepted"))
                if not hasattr(obj, "_asgi_jwt_intercepted"):
                    # Append directly to user_middleware so it's preserved if the middleware stack is rebuilt
                    obj.user_middleware.append(Middleware(ASGIJWTInterceptorMiddleware))
                    # Clear cached middleware stack so it's rebuilt on the next request
                    if hasattr(obj, "middleware_stack"):
                        obj.middleware_stack = None
                    if hasattr(obj, "_middleware_stack"):
                        obj._middleware_stack = None
                    obj._asgi_jwt_intercepted = True
                    _logger.info("Successfully injected ASGIJWTInterceptorMiddleware into existing FastAPI instance and cleared middleware stack cache.")
        except ReferenceError:
            # Safe ignore for weak references
            pass
        except Exception as e:
            _logger.warning("Error inspecting object of class %s: %s", getattr(obj, "__class__", None), e)
            
    if not found_any:
        _logger.warning("No FastAPI instance found in GC during inject_middleware_into_existing_apps scan.")

inject_middleware_into_existing_apps()

# Patched FastAPI __init__ to register the middleware automatically for any future instances
original_init = FastAPI.__init__
def patched_init(self, *args, **kwargs):
    original_init(self, *args, **kwargs)
    self.user_middleware.append(Middleware(ASGIJWTInterceptorMiddleware))
    self._asgi_jwt_intercepted = True

FastAPI.__init__ = patched_init

def reconstruct_database_settings(authorized_views: dict) -> dict:
    """Reconstruct database settings format with enhanced schema metadata directly from dictionary."""
    project_id = os.getenv("BQ_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT") or "banking-agent-rag-mcp"
    schema_dict = {}
    dataset_id = "customer_views"
    
    for view_name, view in authorized_views.items():
        if view_name and "." in view_name:
            parts = view_name.split(".")
            dataset_id = parts[0]
            table_id = parts[1]
        else:
            table_id = view_name or ""
            
        full_table_ref = f"{project_id}.{dataset_id}.{table_id}"
        
        table_schema = []
        fields = view.get("schema") or []
        for field in fields:
            table_schema.append({
                "column_name": field.get("column_name"),
                "type": field.get("type"),
                "description": field.get("description", ""),
                "mode": field.get("mode", "NULLABLE")
            })
            
        schema_dict[full_table_ref] = {
            "table_description": view.get("table_description", ""),
            "table_schema": table_schema
        }
        
    return {
        "bigquery": {
            "data_project_id": project_id,
            "dataset_id": dataset_id,
            "schema": schema_dict
        }
    }

# Initialize module-level config variables
_dataset_config = {
  "datasets": [
    {
      "type": "bigquery",
      "name": "banking_data",
      "description": "This data warehouse is used to store customer banking information including transactions, account details, and customer demographics."
    }
  ]
}

_database_settings = {}
_supported_dataset_types = ["bigquery", "alloydb"]
_required_dataset_config_params = ["name", "description"]


# def load_dataset_config():
#     """Load the dataset configurations for the agent from the config file"""

#     dataset_config_file = "banking_dataset_config.json"  # os.environ.get("DATASET_CONFIG_FILE")
#     if not dataset_config_file:
#         _logger.fatal("Dataset config file path not provided.")

#     with open(dataset_config_file, "r", encoding="utf-8") as f:
#         dataset_config = json.load(f)
        

#     if "datasets" not in dataset_config:
#         _logger.fatal("No 'datasets' entry in dataset config")

#     for dataset in dataset_config["datasets"]:
#         if "type" not in dataset:
#             _logger.fatal("Missing dataset type")
#         if dataset["type"] not in _supported_dataset_types:
#             _logger.fatal("Dataset type '%s' not supported", dataset["type"])

#         for p in _required_dataset_config_params:
#             if p not in dataset:
#                 _logger.fatal(
#                     "Missing required param '%s' from %s dataset config",
#                     p,
#                     dataset["type"],
#                 )

#     return dataset_config


# def get_database_settings(db_type: str) -> dict:
#     """Wrapper function to get database settings by type"""
#     assert db_type in _supported_dataset_types
#     if db_type == "bigquery":
#         return get_bq_database_settings()
#     else:
#         return get_alloydb_database_settings()
    


def init_database_settings(dataset_config: dict, email_id: str) -> dict:
    """Initializes the database settings for the configured datasets"""
    db_settings = {}
    for dataset in dataset_config["datasets"]:
        db_settings[dataset["type"]] = get_database_settings(email_id=email_id)
    return db_settings

def get_customer_details_for_instructions(callback_context: CallbackContext) -> str:
    """Returns the customer profile instructions block"""
    
    customer_details = f"""<CUSTOMER_PROFILE>
    {get_customer_profile(email_id=callback_context.session.user_id)}
</CUSTOMER_PROFILE>
"""
    return customer_details



# def get_dataset_definitions_for_instructions(callback_context: CallbackContext) -> str:
#     """Returns the dataset definitions instructions block"""

#     dataset_definitions = """
# <DATASETS>
# """
#     for dataset in _dataset_config["datasets"]:
#         dataset_type = dataset["type"]
#         dataset_definitions += f"""
# <{dataset_type.upper()}>
# <DESCRIPTION>
# {dataset["description"]}
# </DESCRIPTION>
# <SCHEMA>
# --------- The schema of the relevant database with a few sample rows. --------
# {init_database_settings(_dataset_config, email_id=callback_context.session.user_id)[dataset_type]["schema"]}
# </SCHEMA>
# </{dataset_type.upper()}>

# """
#     dataset_definitions += """
# </DATASETS>
# """

#     return dataset_definitions


def get_firebase_jwt_token(callback_context: Optional[CallbackContext] = None) -> str:
    # 1. Try global session dictionary first
    if callback_context:
        try:
            session_id = callback_context.session.id
            user_id = callback_context.session.user_id
            
            # Check by (user_id, session_id)
            token = _session_tokens.get((user_id, session_id))
            if token:
                _logger.info("Retrieved JWT from _session_tokens via (user_id, session_id).")
                return token
                
            # Check by session_id
            token = _session_tokens.get(session_id)
            if token:
                _logger.info("Retrieved JWT from _session_tokens via session_id.")
                return token
        except Exception as e:
            _logger.warning("Error extracting session info in get_firebase_jwt_token: %s", e)

    # 2. Try contextvars
    token = firebase_jwt_var.get()
    if token:
        _logger.info("Retrieved JWT from contextvars.")
        return token
        
    # 3. Fallback to _last_token
    if _last_token:
        _logger.info("Retrieved JWT from global _last_token fallback.")
        return _last_token
        
    # 3.5. Fallback to environment variable for local testing (e.g., adk-web playground)
    env_token = os.getenv("LOCAL_TEST_JWT")
    if env_token:
        _logger.info("Retrieved JWT from LOCAL_TEST_JWT environment variable.")
        return env_token
        
    # 3.6. Dynamic mock token based on callback context user_id for local testing
    if callback_context and getattr(callback_context, "session", None) and getattr(callback_context.session, "user_id", None):
        user_id = callback_context.session.user_id
        if "@" in user_id:
            _logger.info("Using dynamic mock token for email: %s", user_id)
            return f"mock-token:{user_id}"
        
    # 4. Fallback to call stack inspection (handles first request imported dynamically)
    _logger.info("JWT not found in storage. Attempting call stack inspection...")
    import inspect
    for frame_info in inspect.stack():
        try:
            frame = frame_info.frame
            locals_dict = frame.f_locals
            func_name = frame_info.function
            
            # Log frames to debug where headers/scopes are hiding
            _logger.info("Stack frame: %s, locals: %s", func_name, list(locals_dict.keys()))
            
            # Try to get from any FastAPI/Starlette/Uvicorn request or scope variable
            for key, val in locals_dict.items():
                # Check for explicit request variable
                if key == "request" and hasattr(val, "headers"):
                    auth_header = val.headers.get("Authorization")
                    if auth_header and auth_header.startswith("Bearer "):
                        token = auth_header[7:]
                        _logger.info("Successfully extracted JWT from 'request' in stack frame '%s'.", func_name)
                        return token
                
                # Check for explicit scope variable
                if key == "scope" and isinstance(val, dict) and "headers" in val:
                    headers = dict(val.get("headers", []))
                    auth_bytes = headers.get(b"authorization", b"")
                    auth_header = auth_bytes.decode("utf-8") if auth_bytes else ""
                    if auth_header.startswith("Bearer "):
                        token = auth_header[7:]
                        _logger.info("Successfully extracted JWT from ASGI 'scope' in stack frame '%s'.", func_name)
                        return token
                        
                # Deep check: any dictionary containing 'headers'
                if isinstance(val, dict) and "headers" in val:
                    try:
                        headers = dict(val.get("headers", []))
                        auth_bytes = headers.get(b"authorization") or headers.get("authorization")
                        if auth_bytes:
                            auth_str = auth_bytes.decode("utf-8") if isinstance(auth_bytes, bytes) else str(auth_bytes)
                            if auth_str.startswith("Bearer "):
                                token = auth_str[7:]
                                _logger.info("Successfully extracted JWT from deep dict key '%s' in stack frame '%s'.", key, func_name)
                                return token
                    except Exception:
                        pass
        except Exception as inspect_err:
            _logger.debug("Error inspecting frame: %s", inspect_err)
            
    return ""



def load_database_settings_in_context(callback_context: CallbackContext):
    """Load database settings into the callback context on first use."""
    # Check if context is already loaded
    if "customer_profile" in callback_context.state:
        return

    token = get_firebase_jwt_token(callback_context)
    _logger.info("Fetching context from identity-service. JWT length: %d", len(token) if token else 0)
    
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
        
    identity_service_url = os.getenv("IDENTITY_SERVICE_URL", "http://localhost:8080")
    context_url = f"{identity_service_url}/api/v1/adk/context"
    
    try:
        import httpx
        with httpx.Client(timeout=60.0) as client:
            response = client.get(context_url, headers=headers)
            if response.status_code != 200:
                _logger.error("Failed to fetch context from %s, status: %d, body: %s", 
                              context_url, response.status_code, response.text)
                clean_body = response.text.replace('"', "'").replace('\n', ' ')
                raise RuntimeError(f"Status {response.status_code}: {clean_body}")
            
            context_data = response.json()
            _logger.info("Successfully fetched context for customer %s", context_data.get("customer_id"))
            
            # Load all elements directly to the agent's state
            callback_context.state["customer_id"] = context_data.get("customer_id")
            callback_context.state["customer_profile"] = context_data.get("customer_profile")
            callback_context.state["authorized_account"] = context_data.get("authorized_account", [])
            
            # Reconstruct database_settings with enhanced schemas and descriptions
            callback_context.state["database_settings"] = reconstruct_database_settings(context_data.get("authorized_views", {}))
            
    except Exception as e:
        _logger.exception("Error fetching context from identity service")
        # Ensure error message is safe for JSON encoding in SSE
        safe_msg = str(e).replace('"', "'").replace('\n', ' ')
        raise RuntimeError(f"Failed to fetch context from identity service: {safe_msg}")
        
    
def get_root_agent() -> LlmAgent:
    tools = []
    sub_agents = []
    for dataset in _dataset_config["datasets"]:
        if dataset["type"] == "bigquery":
            tools.append(call_bigquery_agent)
        elif dataset["type"] == "alloydb":
            tools.append(call_alloydb_agent)

    # tools.append(call_transaction_agent)
    agent = LlmAgent(
        model=os.getenv("ROOT_AGENT_MODEL", "gemini-2.5-flash"),
        name="banking_root_agent",
        instruction=return_instructions_root,
        # + get_dataset_definitions_for_instructions(),
        # + get_customer_details_for_instructions(),
        global_instruction=(
            f"""
            You are Banking Customer facing helpful Multi Agent System.
            Todays date: {date.today().isoformat()}
            """
        ),
        # sub_agents=[bigquery_agent],  # type: ignore
        tools=tools,  # type: ignore
        before_agent_callback=load_database_settings_in_context,
        generate_content_config=types.GenerateContentConfig(temperature=0.01),
    )

    return agent


# Initialize dataset configurations and database info before the agent starts
# _dataset_config = load_dataset_config()

# _database_settings = init_database_settings(_dataset_config, email_id=tool_context.user_id)

# _customer_profile = get_customer_profile(email_id=tool_context.user_id)



# Fetch the root agent
root_agent = get_root_agent()

