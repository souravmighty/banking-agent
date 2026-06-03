"""Database Agent: get data from database (BigQuery) using NL2SQL."""

import logging
import os
from typing import Any, Dict, Optional

# from ...utils.utils import get_env_var, USER_AGENT
from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.tools import BaseTool, ToolContext
from google.adk.tools.bigquery import BigQueryToolset, BigQueryCredentialsConfig
from google.adk.tools.bigquery.config import BigQueryToolConfig, WriteMode
from google.genai import types
from . import tools
# from .chase_sql import chase_db_tools
from .prompts import return_instructions_bigquery
from dotenv import load_dotenv
from pathlib import Path
from google.oauth2 import service_account

# Load Service Account credentials
script_dir = Path(__file__).resolve().parent
# KEY_PATH = script_dir.parent.parent.parent / "keys" / "adk-agent-sa.json"
# credentials = service_account.Credentials.from_service_account_file(KEY_PATH)

# Configure the toolset
# credentials_config = BigQueryCredentialsConfig(credentials=credentials)

load_dotenv()

logger = logging.getLogger(__name__)

NL2SQL_METHOD = os.getenv("NL2SQL_METHOD", "BASELINE")

USER_AGENT = "bq-agent"



# BigQuery built-in tools in ADK
# https://google.github.io/adk-docs/tools/built-in-tools/#bigquery
ADK_BUILTIN_BQ_EXECUTE_SQL_TOOL = "execute_sql"


def setup_before_agent_call(callback_context: CallbackContext) -> None:
    """Setup the agent."""

    if "database_settings" not in callback_context.state:
        callback_context.state["database_settings"] = (
            tools.get_database_settings(email_id=os.getenv("CUSTOMER_EMAIL_ID"))
        )
        
    if "customer_profile" not in callback_context.state:
        callback_context.state["customer_profile"] = tools.get_customer_profile(email_id=os.getenv("CUSTOMER_EMAIL_ID"))

def store_results_in_context(
    tool: BaseTool,
    args: Dict[str, Any],
    tool_context: ToolContext,
    tool_response: Dict,
) -> Optional[Dict]:

    # We are setting a state for the data science agent to be able to use the
    # sql query results as context
    if tool.name == ADK_BUILTIN_BQ_EXECUTE_SQL_TOOL:
        if tool_response["status"] == "SUCCESS":
            tool_context.state["bigquery_query_result"] = tool_response["rows"]

    return None


bigquery_tool_filter = [ADK_BUILTIN_BQ_EXECUTE_SQL_TOOL]
bigquery_tool_config = BigQueryToolConfig(
    write_mode=WriteMode.BLOCKED, application_name=USER_AGENT
)
bigquery_toolset = BigQueryToolset(
    tool_filter=bigquery_tool_filter, bigquery_tool_config=bigquery_tool_config
)



bigquery_agent = LlmAgent(
    model=os.getenv("BIGQUERY_AGENT_MODEL", "gemini-2.5-pro"),
    name="bigquery_agent",
    instruction=return_instructions_bigquery(),
    tools=[
        tools.bigquery_nl2sql,
        bigquery_toolset,
    ],
    before_agent_callback=setup_before_agent_call,
    after_tool_callback=store_results_in_context,
    generate_content_config=types.GenerateContentConfig(temperature=0.01),
)