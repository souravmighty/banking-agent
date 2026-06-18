"""This file contains the tools used by the database agent."""

import datetime
import logging
import os
from dotenv import load_dotenv

import numpy as np
import pandas as pd
# from data_science.utils.utils import get_env_var, USER_AGENT
from google.adk.tools import ToolContext
from google.adk.tools.bigquery.client import get_bigquery_client
from google.cloud import bigquery
from google.genai import Client
from google.oauth2 import service_account
from google.genai.types import HttpOptions
from google.api_core.exceptions import NotFound
from pathlib import Path

# 1. Get the folder where this script lives
script_dir = Path(__file__).resolve().parent

load_dotenv()  # Load environment variables from .env file

# from .chase_sql import chase_constants
# from ...utils.utils import USER_AGENT
USER_AGENT = "bq-agent"

logger = logging.getLogger(__name__)

# Assume that `BQ_COMPUTE_PROJECT_ID` and `BQ_DATA_PROJECT_ID` are set in the
# environment. See the `data_agent` README for more details.
# dataset_id = get_env_var("BQ_DATASET_ID")
# data_project = get_env_var("BQ_DATA_PROJECT_ID")
# compute_project = get_env_var("BQ_COMPUTE_PROJECT_ID")
# vertex_project = get_env_var("GOOGLE_CLOUD_PROJECT")
# location = get_env_var("GOOGLE_CLOUD_LOCATION")

dataset_id = os.getenv("BQ_DATASET_ID")
data_project = os.getenv("BQ_PROJECT_ID")
compute_project = os.getenv("GOOGLE_CLOUD_PROJECT")
vertex_project = os.getenv("GOOGLE_CLOUD_PROJECT")
location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
http_options = HttpOptions(headers={"user-agent": USER_AGENT})
llm_client = Client(
    vertexai=True,
    project=vertex_project,
    location=location,
    http_options=http_options,
)

MAX_NUM_ROWS = 10000


def _serialize_value_for_sql(value):
    """Serializes a Python value from a pandas DataFrame into a BigQuery SQL literal."""
    if isinstance(value, (list, np.ndarray)):
        # Format arrays.
        return f"[{', '.join(_serialize_value_for_sql(v) for v in value)}]"
    if pd.isna(value):
        return "NULL"
    if isinstance(value, str):
        # Escape single quotes and backslashes for SQL strings.
        # NOTE: This will throw an exception in Python <= 3.11 because
        # Python 3.12 introduces better f-string handling.
        new_value = value.replace("\\", "\\\\").replace("'", "''")
        return f"'{new_value}'"
    if isinstance(value, bytes):
        decoded = value.decode("utf-8", "replace")
        new_value = decoded.replace("\\", "\\\\").replace("'", "''")
        return f"b'{new_value}'"
    if isinstance(value, (datetime.datetime, datetime.date, pd.Timestamp)):
        # Timestamps and datetimes need to be quoted.
        return f"'{value}'"
    if isinstance(value, dict):
        # For STRUCT, BQ expects ('val1', 'val2', ...).
        # The values() order from the dataframe should match the column order.
        string_values = [_serialize_value_for_sql(v) for v in value.values()]
        return f'({", ".join(string_values)})'
    return str(value)


database_settings = None


def get_database_settings(email_id):
    """Get database settings."""
    global database_settings
    if database_settings is None:
        database_settings = update_database_settings(email_id=email_id)
    return database_settings


def update_database_settings(email_id):
    """Update database settings."""
    global database_settings
    
    sanitized_email = email_id.replace('@', '_').replace('.', '_')
    target_dataset_id = f"customer_{sanitized_email}"
    create_customer_views(
        email_id=email_id,
        target_dataset_id=target_dataset_id,
    )
    schema = get_bigquery_schema_and_samples(bq_data_project=data_project, bq_dataset_id=target_dataset_id)
    database_settings = {
        # "data_project_id": get_env_var("BQ_DATA_PROJECT_ID"),
        # "dataset_id": get_env_var("BQ_DATASET_ID"),
        "data_project_id": data_project,
        "dataset_id": target_dataset_id,
        "schema": schema,
    }
    return database_settings

def get_customer_profile(email_id):
    """Get customer profile."""
    global customer_profile
    sanitized_email = email_id.replace('@', '_').replace('.', '_')
    customer_profile = get_customer_details(
        project_id=data_project,
        target_dataset_id=f"customer_{sanitized_email}",
    )
    return customer_profile


def get_bigquery_schema_and_samples(bq_data_project, bq_dataset_id):
    """Retrieves schema and sample values for the BigQuery dataset tables."""
    client = get_bigquery_client(
        project=compute_project,
        credentials=None,
        user_agent=USER_AGENT,
        location=location,
    )
    dataset_ref = bigquery.DatasetReference(bq_data_project, bq_dataset_id)
    tables_context = {}
    for table in client.list_tables(dataset_ref):
        table_info = client.get_table(
            bigquery.TableReference(dataset_ref, table.table_id)
        )
        table_schema = [
            (schema_field.name, schema_field.field_type)
            for schema_field in table_info.schema
        ]
        table_ref = dataset_ref.table(table.table_id)
        # sample_values = []
        
        # sample_query = f"SELECT * FROM `{table_ref}` LIMIT 5"
        # sample_values = (
        #     client.query(sample_query).to_dataframe().to_dict(orient="list")
        # )
        # for key in sample_values:
        #     sample_values[key] = [
        #         _serialize_value_for_sql(v) for v in sample_values[key]
        #     ]
        tables_context[str(table_ref)] = {
            "table_schema": table_schema,
            # "example_values": sample_values,
        }

    return tables_context



def create_customer_views(email_id, target_dataset_id):
    """
    Creates BigQuery views for a specific customer email, limiting data visibility 
    across all related tables.
    
    Args:
        email_id (str): The customer's email address to filter by.
        target_dataset_id (str): The ID of the dataset where views should be created 
                                 (e.g., 'specific_customer_views').
        project_id (str): The GCP project ID containing the source data.
    """
    # KEY_PATH = script_dir.parent.parent.parent / "keys" / "service-account-key.json"

    # Create credentials from the file
    # credentials = service_account.Credentials.from_service_account_file(KEY_PATH)
    client = bigquery.Client(project=data_project, location=location)
    # client = get_bigquery_client(
    #     project=compute_project,
    #     credentials=None,
    #     user_agent=USER_AGENT,
    # )
    
    full_source_path = f"{data_project}.{dataset_id}"
    
    # Mapping of Table Name -> SQL Logic for filtering
    # We use JOINs to trace everything back to the 'customers' table where the email exists.
    view_definitions = {
        
        # 1. Base Table: Customers (Direct Filter)
        "customers": f"""
            SELECT * FROM `{full_source_path}.customers`
            WHERE email = '{email_id}' AND is_current = true
        """,
        
        # 2. Accounts (Join via customer_id)
        "accounts": f"""
            SELECT t.* FROM `{full_source_path}.accounts` t
            JOIN `{full_source_path}.customers` c 
              ON t.customer_id = c.customer_id
            WHERE c.email = '{email_id}' AND t.is_current = true AND c.is_current = true
        """,
        
        # 3. Credit Scores (Join via customer_id)
        "credit_scores": f"""
            SELECT t.* FROM `{full_source_path}.credit_scores` t
            JOIN `{full_source_path}.customers` c 
              ON t.customer_id = c.customer_id
            WHERE c.email = '{email_id}' AND c.is_current = true
        """,
        
        # 4. Transactions (Filter by account_number)
        "transactions": f"""
            SELECT t.* FROM `{full_source_path}.transactions` t
            JOIN `{full_source_path}.accounts` a 
              ON t.account_number = a.account_number
            JOIN `{full_source_path}.customers` c 
              ON a.customer_id = c.customer_id
            WHERE c.email = '{email_id}' AND a.is_current = true AND c.is_current = true
        """,

        # 5. Credit Cards (Join via customer_id)
        "credit_cards": f"""
            SELECT t.* FROM `{full_source_path}.credit_cards` t
            JOIN `{full_source_path}.customers` c 
              ON t.customer_id = c.customer_id
            WHERE c.email = '{email_id}' AND t.is_current = true AND c.is_current = true
        """,

        # 6. Beneficiaries (Join via customer_id)
        "beneficiaries": f"""
            SELECT t.* FROM `{full_source_path}.beneficiaries` t
            JOIN `{full_source_path}.customers` c 
              ON t.customer_id = c.customer_id
            WHERE c.email = '{email_id}' AND c.is_current = true
        """,

        # 7. Loans (Join via customer_id)
        "loans": f"""
            SELECT t.* FROM `{full_source_path}.loans` t
            JOIN `{full_source_path}.customers` c 
              ON t.customer_id = c.customer_id
            WHERE c.email = '{email_id}' AND c.is_current = true
        """,

        # 8. Fixed Deposits (Join via customer_id)
        "fixed_deposits": f"""
            SELECT t.* FROM `{full_source_path}.fixed_deposits` t
            JOIN `{full_source_path}.customers` c 
              ON t.customer_id = c.customer_id
            WHERE c.email = '{email_id}' AND c.is_current = true
        """
    }

    # Create target dataset if it doesn't exist
    try:
        client.get_dataset(target_dataset_id)
        print(f"Dataset {target_dataset_id} already exists.")
    except NotFound:
        dataset = bigquery.Dataset(f"{client.project}.{target_dataset_id}")
        dataset.location = location  # Adjust location as needed
        client.create_dataset(dataset)
        print(f"Created dataset {target_dataset_id}.")
        # Loop through definitions and create views
        print(f"Creating views for user: {email_id}...")
        for table_name, sql_query in view_definitions.items():
            view_id = f"{client.project}.{target_dataset_id}.{table_name}"
            view = bigquery.Table(view_id)
            view.view_query = sql_query
            
            # Make the creation idempotent (overwrite if exists)
            client.create_table(view, exists_ok=True)
            print(f" - Created view: {table_name}")

        print("All views created successfully.")


def get_customer_details(project_id, target_dataset_id):
    """
    Queries the 'customers' and 'accounts' views from the specified dataset
    and returns the results in a dictionary.

    Args:
        target_dataset_id (str): The ID of the dataset where the views reside.
        project_id (str): The GCP project ID.

    Returns:
        dict: A dictionary containing 'customer_profile' (list of dicts) 
              and 'accounts' (list of dicts).
    """
    client = get_bigquery_client(
        project=compute_project,
        credentials=None,
        user_agent=USER_AGENT,
        location=location,
    )
    
    # Initialize the result dictionary
    result_data = {
        "customer_profile": [],
        "accounts": []
    }

    # 1. Query the Customers View
    # Since the view is already filtered by email, we can select everything.
    customer_query = f"SELECT * FROM `{project_id}.{target_dataset_id}.customers`"
    query_job = client.query(customer_query)
    
    
    # Convert rows to dictionary objects
    # row.items() returns (key, value) pairs which we turn into a dict
    # result_data["customer_profile"] = [dict(row.items()) for row in query_job]
    
    result_data["customer_profile"] = query_job.to_dataframe().to_dict(orient="list")
    for key in result_data["customer_profile"]:
        result_data["customer_profile"][key] = [
            _serialize_value_for_sql(v) for v in result_data["customer_profile"][key]
        ]
    # 2. Query the Accounts View
    accounts_query = f"SELECT * FROM `{project_id}.{target_dataset_id}.accounts`"
    query_job = client.query(accounts_query)
    
    # result_data["accounts"] = [dict(row.items()) for row in query_job]
    result_data["accounts"] = query_job.to_dataframe().to_dict(orient="list")
    for key in result_data["accounts"]:
        result_data["accounts"][key] = [
            _serialize_value_for_sql(v) for v in result_data["accounts"][key]
        ]

    
    
    return result_data


def bigquery_nl2sql(
    question: str,
    tool_context: ToolContext,
) -> str:
    """Generates a SQL query from a natural language question.

    Args:
        question (str): Natural language question.
        tool_context (ToolContext): The tool context to use for generating the
            SQL query.

    Returns:
        str: An SQL statement to answer this question.
    """
    logger.debug("bigquery_nl2sql - question: %s", question)

    prompt_template = """
You are a BigQuery SQL expert tasked with generating SQL in the Google SQL
dialect based on the user's natural language question.
Your task is to write a Bigquery SQL query that answers the following question
while using the provided context.

**Guidelines:**

- **Table Referencing:** Always use the full table name with the database prefix
  in the SQL statement.  Tables should be referred to using a fully qualified
  name with enclosed in backticks (`) e.g.
  `project_name.dataset_name.table_name`.  Table names are case sensitive.
- **Joins:** Join as few tables as possible. When joining tables, ensure all
  join columns are the same data type. Analyze the database and the table schema
  provided to understand the relationships between columns and tables.
- **Aggregations:**  Use all non-aggregated columns from the `SELECT` statement
  in the `GROUP BY` clause.
- **SQL Syntax:** Return syntactically and semantically correct SQL for BigQuery
  with proper relation mapping (i.e., project_id, owner, table, and column
  relation). Use SQL `AS` statement to assign a new name temporarily to a table
  column or even a table wherever needed. Always enclose subqueries and union
  queries in parentheses.
- **Column Usage:** Use *ONLY* the column names (column_name) mentioned in the
  Table Schema. Do *NOT* use any other column names. Associate `column_name`
  mentioned in the Table Schema only to the `table_name` specified under Table
  Schema.
- **FILTERS:** You should write query effectively  to reduce and minimize the
  total rows to be returned. For example, you can use filters (like `WHERE`,
  `HAVING`, etc. (like 'COUNT', 'SUM', etc.) in the SQL query.
- **LIMIT ROWS:**  The maximum number of rows returned should be less than
  {MAX_NUM_ROWS}.

**Schema:**

The database structure is defined by the following table schemas (possibly with
sample rows):

```
{SCHEMA}
```

**Natural language question:**

```
{QUESTION}
```

**Think Step-by-Step:** Carefully consider the schema, question, guidelines, and
best practices outlined above to generate the correct BigQuery SQL.

   """

    schema = tool_context.state["database_settings"]["bigquery"]["schema"]

    prompt = prompt_template.format(
        MAX_NUM_ROWS=MAX_NUM_ROWS, SCHEMA=schema, QUESTION=question
    )

    response = llm_client.models.generate_content(
        model=os.getenv("BASELINE_NL2SQL_MODEL", "gemini-2.5-pro"),
        contents=prompt,
        config={"temperature": 0.1},
    )

    sql = response.text
    if sql:
        sql = sql.replace("```sql", "").replace("```", "").strip()

    logger.debug("bigquery_nl2sql - sql:\n%s", sql)

    tool_context.state["sql_query"] = sql

    return sql
