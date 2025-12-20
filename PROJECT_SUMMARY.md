
# Project Summary

This document provides a concise overview of the project, including its structure, dependencies, and architecture.

## File Structure

```
/
├───.gitignore
├───banking_dataset_config.json
├───requirements.txt
├───.git/...
├───bq_agent/
│   ├───__init__.py
│   ├───agent.py
│   ├───prompts.py
│   ├───tools.py
│   ├───__pycache__/
│   ├───mcp_server/
│   │   ├───__init__.py
│   │   ├───README.md
│   │   ├───server.py
│   │   ├───tools.py
│   │   └───__pycache__/
│   └───sub_agents/
│       ├───__init__.py
│       ├───__pycache__/
│       ├───bigquery/
│       │   ├───__init__.py
│       │   ├───agent.py
│       │   ├───prompts.py
│       │   └───tools.py
│       └───transaction/
│           ├───__init__.py
│           ├───agent.py
│           └───prompts.py
├───data/
│   ├───accounts.csv
│   ├───credit_scores.csv
│   ├───customer_products.csv
│   ├───customers.csv
│   ├───products.csv
│   └───transactions.csv
├───keys/
│   └───my-creds.json
├───ref/
│   ├───adk-docs.txt
│   ├───fastmcp-doc.txt
│   └───authn-adk-all-in-one/
│       └───...
├───src/
│   ├───generate_data.py
│   ├───test.py
│   └───upload_to_bigquery.py
└───terraform/
    ├───main.tf
    ├───outputs.tf
    └───variables.tf
```

## File Descriptions

### Root Directory

- **`.gitignore`**: Specifies which files and directories to ignore in Git version control.
- **`banking_dataset_config.json`**: Configuration file for the banking dataset, likely specifying dataset type and metadata.
- **`requirements.txt`**: Lists the Python dependencies required for the project.

### `bq_agent/`

- **`agent.py`**: The main agent logic, responsible for orchestrating sub-agents and tools to handle user requests related to the banking dataset.
- **`prompts.py`**: Contains prompts for the language model, guiding its behavior and responses.
- **`tools.py`**: Defines tools that the agent can use, such as calling the BigQuery agent.

#### `bq_agent/mcp_server/`

- **`README.md`**: Documentation for the MCP server, explaining how to run and interact with it.
- **`server.py`**: Implements the MCP server, exposing tools for making transactions and credit card payments.
- **`tools.py`**: Contains the implementation of the tools exposed by the MCP server, which interact with the BigQuery database.

#### `bq_agent/sub_agents/bigquery/`

- **`agent.py`**: The BigQuery agent, which handles natural language to SQL conversion and executes queries against the BigQuery database.
- **`prompts.py`**: Contains prompts for the BigQuery agent.
- **`tools.py`**: Defines tools for the BigQuery agent, such as `bigquery_nl2sql`.

#### `bq_agent/sub_agents/transaction/`

- **`agent.py`**: The Transaction agent, which handles transaction-related tasks by using tools from the MCP server.
- **`prompts.py`**: Contains prompts for the Transaction agent.

### `data/`

- **`*.csv`**: CSV files containing the banking dataset, including customer information, accounts, transactions, products, and credit scores.

### `keys/`

- **`my-creds.json`**: Service account credentials for accessing Google Cloud services, such as BigQuery.

### `ref/`

- **`adk-docs.txt`**: Documentation for the Agent Development Kit (ADK).
- **`fastmcp-doc.txt`**: Documentation for the FastMCP library.
- **`authn-adk-all-in-one/`**: A self-contained demo of ADK authentication, including an IDP, a hotel booking app, and an agent.

### `src/`

- **`generate_data.py`**: Script to generate the banking dataset.
- **`test.py`**: A test script for the project.
- **`upload_to_bigquery.py`**: Script to upload the generated data to BigQuery.

### `terraform/`

- **`main.tf`**: The main Terraform configuration file, which defines the Google Cloud resources to be created, such as the BigQuery dataset and tables.
- **`outputs.tf`**: Defines the outputs of the Terraform configuration, such as the BigQuery dataset ID.
- **`variables.tf`**: Defines the variables used in the Terraform configuration, such as the GCP project ID and region.

## Key Dependencies

- **`faker`**: Used to generate fake data for the banking dataset.
- **`pandas`**: Used for data manipulation and analysis.
- **`google-cloud-bigquery`**: The official Python client library for BigQuery, used to interact with the database.
- **`google-adk`**: The Agent Development Kit, used to build and run the agents.
- **`Flask`**: A web framework used in the authentication demo.
- **`SQLAlchemy`**: A SQL toolkit and Object Relational Mapper used in the authentication demo.
- **`python-dotenv`**: Used to manage environment variables.
- **`passlib[bcrypt]`**: Used for password hashing in the authentication demo.
- **`jinja2`**: A templating engine used by Flask.
- **`requests`**: A library for making HTTP requests.

## Overall Architecture Pattern

The project follows a multi-agent architecture, with a root agent that orchestrates sub-agents and tools to handle user requests. The root agent is responsible for classifying the user's intent and delegating the request to the appropriate sub-agent. The BigQuery agent is a sub-agent that handles natural language to SQL conversion and executes queries against the BigQuery database. The Transaction agent is another sub-agent that handles transaction-related tasks by using tools from the MCP server. The MCP server exposes tools for making transactions and credit card payments. The project also includes a data generation script, a data upload script, and a Terraform configuration for creating the necessary Google Cloud resources. The `ref/` directory contains documentation and a self-contained authentication demo.
