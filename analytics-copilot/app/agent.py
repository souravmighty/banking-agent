import contextvars
import gc
import inspect
import json
import logging
import os
import threading
import time
from datetime import date
from typing import Any

import google.genai
import google.genai.types as genai_types
from dotenv import load_dotenv
from fastapi import FastAPI
from google import genai
from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.planners import BuiltInPlanner
from starlette.middleware import Middleware

_logger = logging.getLogger("banking_agent_patch")

# Monkey-patch google.genai.Client to force GEMINI_API_LOCATION if set
_original_client_init = google.genai.Client.__init__


def _patched_client_init(self, *args, **kwargs):
    api_location = os.environ.get("GEMINI_API_LOCATION")
    if api_location:
        _logger.info("Patched Client.__init__: forcing location to %s", api_location)
        kwargs["location"] = api_location
        if (
            "vertexai" not in kwargs
            and os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", "TRUE") == "TRUE"
        ):
            kwargs["vertexai"] = True
    _original_client_init(self, *args, **kwargs)


google.genai.Client.__init__ = _patched_client_init

os.environ["GOOGLE_CLOUD_LOCATION"] = "global"

try:
    from .prompts import return_instructions_root
    from .sub_agents.bigquery.tools import get_analytics_metadata
    from .tools import call_bigquery_agent, call_visualization_agent
except (ImportError, ValueError):
    from app.prompts import return_instructions_root
    from app.sub_agents.bigquery.tools import get_analytics_metadata
    from app.tools import call_bigquery_agent, call_visualization_agent

load_dotenv()

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger(__name__)

# AgentOps Observability Initialization
agentops_api_key = os.environ.get("AGENTOPS_API_KEY")
if agentops_api_key:
    try:
        import agentops

        agentops.init(
            api_key=agentops_api_key,
            default_tags=["analytics-copilot", "banking-agent", "dev"],
            auto_start_session=True,
            instrument_llm_calls=True,
        )
        _logger.info("AgentOps initialized successfully in analytics copilot.")
    except Exception as e:
        _logger.warning("Could not initialize AgentOps: %s", e)


client = genai.Client(
    vertexai=True,
    project=os.getenv("GOOGLE_CLOUD_PROJECT"),
    location=os.getenv("GEMINI_API_LOCATION", "us"),
)

firebase_jwt_var = contextvars.ContextVar("firebase_jwt", default="")
_session_tokens = {}  # Global mapping from user/session to token
_last_token = (
    ""  # Thread-safe/process-safe global fallback for the single-user local app
)


class ASGIJWTInterceptorMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] not in ("http", b"http", "websocket", b"websocket"):
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))

        token = ""
        fb_token_bytes = headers.get(b"x-firebase-id-token") or headers.get(
            b"x-auth-token"
        )
        if fb_token_bytes:
            token = fb_token_bytes.decode("utf-8")
            _logger.info(
                "ASGIJWTInterceptorMiddleware: Captured JWT from custom X-Firebase-Id-Token / X-Auth-Token header."
            )
        else:
            auth_bytes = headers.get(b"authorization", b"")
            auth_header = auth_bytes.decode("utf-8") if auth_bytes else ""
            if auth_header.startswith("Bearer "):
                token = auth_header[7:]
                _logger.info(
                    "ASGIJWTInterceptorMiddleware: Captured JWT from Authorization header."
                )

        if token:
            firebase_jwt_var.set(token)
            global _last_token
            _last_token = token
        else:
            firebase_jwt_var.set("")

        method = scope.get("method", "")

        receive_to_use = receive
        if token and method == "POST":
            messages = []
            try:
                body = b""
                more_body = True
                while more_body:
                    message = await receive()
                    messages.append(message)
                    body += message.get("body", b"")
                    more_body = message.get("more_body", False)

                try:
                    body_json = json.loads(body.decode("utf-8"))
                    user_id = (
                        body_json.get("user_id")
                        or body_json.get("userId")
                        or body_json.get("input", {}).get("user_id")
                        or body_json.get("input", {}).get("userId")
                    )
                    session_id = (
                        body_json.get("session_id")
                        or body_json.get("sessionId")
                        or body_json.get("input", {}).get("session_id")
                        or body_json.get("input", {}).get("sessionId")
                    )

                    if user_id and session_id:
                        _session_tokens[(user_id, session_id)] = token
                        _session_tokens[session_id] = token
                        _logger.info(
                            "Successfully mapped session %s (user: %s) to JWT token in middleware.",
                            session_id,
                            user_id,
                        )
                except Exception as parse_err:
                    _logger.warning(
                        "Failed to parse JSON body in middleware: %s", parse_err
                    )

                async def mock_receive():
                    if messages:
                        return messages.pop(0)
                    return await receive()

                receive_to_use = mock_receive
            except Exception as e:
                _logger.error("Error reading body in middleware: %s", e)

        await self.app(scope, receive_to_use, send)


def inject_middleware_into_existing_apps():
    _logger.info("Running inject_middleware_into_existing_apps. Scanning GC...")
    try:
        objects = gc.get_objects()
    except Exception as scan_err:
        _logger.error("Failed to call gc.get_objects(): %s", scan_err)
        return

    found_any = False
    for obj in objects:
        try:
            if isinstance(obj, FastAPI) or obj.__class__.__name__ == "FastAPI":
                found_any = True
                if not hasattr(obj, "_asgi_jwt_intercepted"):
                    obj.user_middleware.append(Middleware(ASGIJWTInterceptorMiddleware))
                    if hasattr(obj, "middleware_stack"):
                        obj.middleware_stack = None
                    if hasattr(obj, "_middleware_stack"):
                        obj._middleware_stack = None
                    obj._asgi_jwt_intercepted = True
                    _logger.info(
                        "Successfully injected ASGIJWTInterceptorMiddleware into FastAPI instance."
                    )
        except ReferenceError:
            pass
        except Exception as e:
            _logger.warning(
                "Error inspecting object of class %s: %s",
                getattr(obj, "__class__", None),
                e,
            )

    if not found_any:
        _logger.warning(
            "No FastAPI instance found in GC during inject_middleware_into_existing_apps scan."
        )


inject_middleware_into_existing_apps()

original_init = FastAPI.__init__


def patched_init(self, *args, **kwargs):
    original_init(self, *args, **kwargs)
    self.user_middleware.append(Middleware(ASGIJWTInterceptorMiddleware))
    self._asgi_jwt_intercepted = True


FastAPI.__init__ = patched_init


def get_firebase_jwt_token(callback_context: CallbackContext | None = None) -> str:
    """Extract authenticated JWT token for BANK_STAFF authorization."""
    # 1. Try global session dictionary
    if callback_context:
        try:
            session_id = callback_context.session.id
            user_id = callback_context.session.user_id

            token = _session_tokens.get((user_id, session_id))
            if token:
                return token

            token = _session_tokens.get(session_id)
            if token:
                return token
        except Exception as e:
            _logger.warning(
                "Error extracting session info in get_firebase_jwt_token: %s", e
            )

    # 2. Try contextvars
    token = firebase_jwt_var.get()
    if token:
        return token

    # 3. Fallback to _last_token
    if _last_token:
        return _last_token

    # 4. Fallback to environment variable for testing
    env_token = os.getenv("LOCAL_TEST_JWT")
    if env_token:
        return env_token

    # 5. Fallback to call stack inspection
    for frame_info in inspect.stack():
        try:
            locals_dict = frame_info.frame.f_locals
            for key, val in locals_dict.items():
                if key in ("request", "req") and hasattr(val, "headers"):
                    auth_header = val.headers.get("Authorization")
                    if auth_header and auth_header.startswith("Bearer "):
                        return auth_header[7:]

                if key == "scope" and isinstance(val, dict) and "headers" in val:
                    headers = dict(val.get("headers", []))
                    auth_bytes = headers.get(b"authorization", b"")
                    auth_header = auth_bytes.decode("utf-8") if auth_bytes else ""
                    if auth_header.startswith("Bearer "):
                        return auth_header[7:]
        except Exception:
            pass

    return ""


def reconstruct_database_settings_from_analytics_metadata(
    analytics_metadata: dict,
) -> dict:
    """Reconstruct database settings structure for BigQuery NL2SQL from the analytics metadata response."""
    project_id = (
        os.getenv("BQ_PROJECT_ID")
        or os.getenv("GOOGLE_CLOUD_PROJECT")
        or "banking-agent-rag-mcp"
    )
    schema_dict = {}

    datasets = analytics_metadata.get("datasets", {})
    for _ds_name, ds_info in datasets.items():
        # Process tables
        tables = ds_info.get("tables") or {}
        for tbl_name, tbl in tables.items():
            query_obj = tbl.get("query_object") or tbl_name
            table_schema = []
            fields = tbl.get("schema") or []
            for field in fields:
                table_schema.append(
                    {
                        "column_name": field.get("column_name"),
                        "type": field.get("type"),
                        "description": field.get("description", ""),
                        "mode": field.get("mode", "NULLABLE"),
                    }
                )

            schema_dict[query_obj] = {
                "logical_name": tbl.get("logical_name", ""),
                "object_type": tbl.get("object_type", "TABLE"),
                "table_description": tbl.get("table_description", ""),
                "grain": tbl.get("grain", ""),
                "primary_business_key": tbl.get("primary_business_key", ""),
                "relationship_information": tbl.get("relationship_information", ""),
                "is_scd_type_2": tbl.get("is_scd_type_2", False),
                "scd_columns": tbl.get("scd_columns", []),
                "ai_usage_guidance": tbl.get("ai_usage_guidance", ""),
                "table_schema": table_schema,
            }

        # Process views
        views = ds_info.get("views") or {}
        for view_name, vw in views.items():
            query_obj = vw.get("query_object") or view_name
            view_schema = []
            fields = vw.get("schema") or []
            for field in fields:
                view_schema.append(
                    {
                        "column_name": field.get("column_name"),
                        "type": field.get("type"),
                        "description": field.get("description", ""),
                        "mode": field.get("mode", "NULLABLE"),
                    }
                )

            schema_dict[query_obj] = {
                "logical_name": vw.get("logical_name", ""),
                "object_type": vw.get("object_type", "VIEW"),
                "table_description": vw.get("table_description", ""),
                "grain": vw.get("grain", ""),
                "primary_business_key": vw.get("primary_business_key", ""),
                "relationship_information": vw.get("relationship_information", ""),
                "is_scd_type_2": vw.get("is_scd_type_2", False),
                "scd_columns": vw.get("scd_columns", []),
                "ai_usage_guidance": vw.get("ai_usage_guidance", ""),
                "table_schema": view_schema,
            }

    return {
        "bigquery": {
            "data_project_id": project_id,
            "schema": schema_dict,
        }
    }


class AnalyticsMetadataCache:
    def __init__(self, ttl_seconds: int = 300):
        self._cache: dict[str, dict[str, Any]] = {}
        self._lock = threading.Lock()
        self.ttl = ttl_seconds

    def get(self, key: str) -> dict[str, Any] | None:
        """Retrieve metadata if it exists and hasn't expired."""
        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                if time.time() - entry["timestamp"] < self.ttl:
                    _logger.debug("AnalyticsMetadataCache HIT for key: %s", key)
                    return entry["data"]
                else:
                    _logger.debug("AnalyticsMetadataCache EXPIRED for key: %s", key)
                    del self._cache[key]
            return None

    def set(self, key: str, data: dict[str, Any]) -> None:
        """Cache fresh metadata with current timestamp."""
        with self._lock:
            self._cache[key] = {
                "data": data,
                "timestamp": time.time(),
            }
            _logger.debug("AnalyticsMetadataCache SET for key: %s", key)

    def clear(self) -> None:
        """Clear the cache."""
        with self._lock:
            self._cache.clear()


# Initialize a global cache with a 5-minute TTL (300 seconds)
analytics_metadata_cache = AnalyticsMetadataCache(ttl_seconds=300)


def load_analytics_metadata_in_context(callback_context: CallbackContext):
    """
    Load analytics metadata into the callback context before agent execution.
    Only loads analytical data definitions; does not load or store customer-specific PII or accounts.
    """
    # 1. Check if already loaded in this specific agent invocation state
    if (
        "analytics_metadata" in callback_context.state
        and "database_settings" in callback_context.state
    ):
        _logger.debug("Analytics metadata already present in callback_context.state")
        return

    # 2. Check session/user cache key
    user_id = getattr(callback_context.session, "user_id", "default_staff_user")
    cached_metadata = analytics_metadata_cache.get(user_id)
    if cached_metadata:
        _logger.info(
            "Using cached analytics metadata for user %s (bypassing HTTP fetch)",
            user_id,
        )
        callback_context.state["analytics_metadata"] = cached_metadata
        callback_context.state["database_settings"] = (
            reconstruct_database_settings_from_analytics_metadata(cached_metadata)
        )
        callback_context.state["user_role"] = cached_metadata.get(
            "user_role", "BANK_STAFF"
        )
        return

    # 3. Retrieve auth token and fetch from /analytics-metadata
    token = get_firebase_jwt_token(callback_context)
    _logger.info(
        "Fetching analytics metadata from identity service (JWT present: %s)",
        bool(token),
    )

    try:
        metadata = get_analytics_metadata(token=token)
        _logger.info("Successfully fetched analytics metadata from /analytics-metadata")

        # Cache in memory
        analytics_metadata_cache.set(user_id, metadata)

        # Store in state
        callback_context.state["analytics_metadata"] = metadata
        callback_context.state["database_settings"] = (
            reconstruct_database_settings_from_analytics_metadata(metadata)
        )
        callback_context.state["user_role"] = metadata.get("user_role", "BANK_STAFF")

    except Exception as e:
        _logger.exception("Failed to load analytics metadata in callback context")
        safe_msg = str(e).replace('"', "'").replace("\n", " ")
        raise RuntimeError(f"Failed to load analytics metadata: {safe_msg}") from e


def get_root_agent() -> LlmAgent:
    tools = [call_bigquery_agent, call_visualization_agent]

    agent = LlmAgent(
        model=os.getenv("ROOT_AGENT_MODEL", "gemini-3.7-flash"),
        name="analytics_root_agent",
        planner=BuiltInPlanner(
            thinking_config=genai_types.ThinkingConfig(thinking_budget=0)
        ),
        instruction=return_instructions_root,
        global_instruction=(
            f"""
            You are the Enterprise Analytics Copilot, an AI data analytics intelligence assistant for bank staff and executives.
            Today's date: {date.today().isoformat()}
            """
        ),
        tools=tools,
        before_agent_callback=load_analytics_metadata_in_context,
        generate_content_config=genai_types.GenerateContentConfig(temperature=0.01),
    )

    return agent


# Instantiate root agent
root_agent = get_root_agent()

# ====================================================================
# Observability & Tracing Plugins (BigQuery Analytics & AgentOps)
# ====================================================================
plugins = []

# Option 3: BigQuery Agent Analytics Plugin
bq_analytics_dataset = os.environ.get("BQ_ANALYTICS_DATASET_ID") or os.environ.get(
    "TELEMETRY_DATASET_ID"
)
gcp_project = os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("PROJECT_ID")
if bq_analytics_dataset and gcp_project:
    try:
        from google.adk.plugins.bigquery_agent_analytics_plugin import (
            BigQueryAgentAnalyticsPlugin,
        )

        bq_plugin = BigQueryAgentAnalyticsPlugin(
            project_id=gcp_project,
            dataset_id=bq_analytics_dataset,
            location=os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1"),
        )
        plugins.append(bq_plugin)
        _logger.info(
            "Configured BigQueryAgentAnalyticsPlugin with dataset: %s",
            bq_analytics_dataset,
        )
    except Exception as e:
        _logger.warning("Could not initialize BigQueryAgentAnalyticsPlugin: %s", e)

app = App(
    name="analytics-copilot",
    root_agent=root_agent,
    plugins=plugins,
)
