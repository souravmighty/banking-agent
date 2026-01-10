import base64
import json
import logging
import os
from datetime import date
from dotenv import load_dotenv


from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext

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

# Initialize module-level config variables
_dataset_config = {}
_database_settings = {}
_supported_dataset_types = ["bigquery", "alloydb"]
_required_dataset_config_params = ["name", "description"]


def load_dataset_config():
    """Load the dataset configurations for the agent from the config file"""

    dataset_config_file = os.getenv("DATASET_CONFIG_FILE", "")
    if not dataset_config_file:
        _logger.fatal("DATASET_CONFIG_FILE env var not set")

    with open(dataset_config_file, "r", encoding="utf-8") as f:
        dataset_config = json.load(f)

    if "datasets" not in dataset_config:
        _logger.fatal("No 'datasets' entry in dataset config")

    for dataset in dataset_config["datasets"]:
        if "type" not in dataset:
            _logger.fatal("Missing dataset type")
        if dataset["type"] not in _supported_dataset_types:
            _logger.fatal("Dataset type '%s' not supported", dataset["type"])

        for p in _required_dataset_config_params:
            if p not in dataset:
                _logger.fatal(
                    "Missing required param '%s' from %s dataset config",
                    p,
                    dataset["type"],
                )

    return dataset_config


# def get_database_settings(db_type: str) -> dict:
#     """Wrapper function to get database settings by type"""
#     assert db_type in _supported_dataset_types
#     if db_type == "bigquery":
#         return get_bq_database_settings()
#     else:
#         return get_alloydb_database_settings()
    


def init_database_settings(dataset_config: dict) -> dict:
    """Initializes the database settings for the configured datasets"""
    db_settings = {}
    for dataset in dataset_config["datasets"]:
        db_settings[dataset["type"]] = get_database_settings(email_id=os.environ.get("CUSTOMER_EMAIL_ID"))
    return db_settings

def get_customer_details_for_instructions() -> str:
    """Returns the customer profile instructions block"""
    
    customer_details = f"""<CUSTOMER_PROFILE>
    {_customer_profile}
</CUSTOMER_PROFILE>
"""
    return customer_details



def get_dataset_definitions_for_instructions() -> str:
    """Returns the dataset definitions instructions block"""

    dataset_definitions = """
<DATASETS>
"""
    for dataset in _dataset_config["datasets"]:
        dataset_type = dataset["type"]
        dataset_definitions += f"""
<{dataset_type.upper()}>
<DESCRIPTION>
{dataset["description"]}
</DESCRIPTION>
<SCHEMA>
--------- The schema of the relevant database with a few sample rows. --------
{_database_settings[dataset_type]["schema"]}
</SCHEMA>
</{dataset_type.upper()}>

"""
    dataset_definitions += """
</DATASETS>
"""

    return dataset_definitions


def load_database_settings_in_context(callback_context: CallbackContext):
    """Load database settings into the callback context on first use."""
    if "database_settings" not in callback_context.state:
        callback_context.state["database_settings"] = _database_settings
        
    if "customer_profile" not in callback_context.state:
        callback_context.state["customer_profile"] = _customer_profile
        
    
def get_root_agent() -> LlmAgent:
    tools = []
    sub_agents = []
    for dataset in _dataset_config["datasets"]:
        if dataset["type"] == "bigquery":
            tools.append(call_bigquery_agent)
        elif dataset["type"] == "alloydb":
            tools.append(call_alloydb_agent)

    tools.append(call_transaction_agent)
    agent = LlmAgent(
        model=os.getenv("ROOT_AGENT_MODEL", "gemini-2.5-flash"),
        name="data_science_root_agent",
        instruction=return_instructions_root()
        + get_dataset_definitions_for_instructions()
        + get_customer_details_for_instructions(),
        global_instruction=(
            f"""
            You are Banking Customer facing helpful Multi Agent System.
            Todays date: {date.today()}
            """
        ),
        # sub_agents=[bigquery_agent],  # type: ignore
        tools=tools,  # type: ignore
        before_agent_callback=load_database_settings_in_context,
        generate_content_config=types.GenerateContentConfig(temperature=0.01),
    )

    return agent


# Initialize dataset configurations and database info before the agent starts
_dataset_config = load_dataset_config()
_database_settings = init_database_settings(_dataset_config)

_customer_profile = get_customer_profile(os.environ.get("CUSTOMER_EMAIL_ID"))


# Fetch the root agent
root_agent = get_root_agent()

