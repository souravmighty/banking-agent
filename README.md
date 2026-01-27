# Banking Agent System

A sophisticated multi-agent banking system built with Google's Agent Development Kit (ADK), demonstrating advanced conversational AI for financial operations.

## 🏦 Overview

This project showcases a dual-agent architecture that combines natural language processing with secure financial transactions. The system intelligently routes user requests to specialized agents—one for data analysis and one for transactional operations—while maintaining security through Row-Level Security (RLS) and OAuth2 authentication.

### Key Features

- **Dual-Agent Architecture**: Separate Query and Transaction agents for optimal task specialization
- **NL2SQL Engine**: Converts natural language questions into BigQuery SQL queries dynamically
- **Model Context Protocol (MCP)**: Secure tool-based interactions for financial operations
- **Row-Level Security**: Automatic data filtering per customer
- **OAuth2 Integration**: Google authentication with automatic token validation
- **Real-time Operations**: Money transfers and credit card payments via dedicated MCP server
- **BigQuery Integration**: Scalable data analysis on customer transactions and accounts

## 📋 Table of Contents

- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Data Generation](#data-generation)
- [Deployment](#deployment)
- [API Usage](#api-usage)
- [Configuration](#configuration)
- [Project Structure](#project-structure)
- [Dependencies](#dependencies)
- [Security](#security)

## 🏗️ Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Root Banking Agent                        │
│              (Intent Classification & Routing)               │
└────────────────────┬──────────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
        ▼                         ▼
┌──────────────────┐      ┌──────────────────┐
│  BigQuery Agent  │      │ Transaction Agent│
│  (Data Queries)  │      │ (Money Transfers)│
│   • NL2SQL       │      │ • Make Transfer  │
│   • Query Exec   │      │ • Card Payments  │
└──────────────────┘      └────────┬─────────┘
        │                           │
        ▼                           ▼
    BigQuery              MCP Server Tools
   Database             (OAuth Protected)
```

### Key Workflows

**1. Data Query Flow:**
- User asks natural language question
- Root agent routes to BigQuery agent
- NL2SQL engine generates SQL query
- Query executes with RLS filters
- Results returned to user

**2. Transaction Flow:**
- User requests transfer or payment
- Root agent routes to Transaction agent
- MCP server validates via OAuth
- Transaction executes in BigQuery
- Confirmation returned to user

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Google Cloud Project with BigQuery enabled
- Service account credentials (JSON key file)
- Google OAuth2 credentials (for MCP authentication)

### Installation

1. **Clone and setup environment:**
```bash
cd banking-agent
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Configure credentials:**
```bash
# Set your GCP project credentials
export GOOGLE_APPLICATION_CREDENTIALS=./keys/my-creds.json

# Set OAuth2 credentials
export GOOGLE_CLIENT_ID="your-client-id.apps.googleusercontent.com"
export GOOGLE_CLIENT_SECRET="your-client-secret"
```

3. **Set environment variables:**
```bash
# Copy example file and customize
cp .env.oauth.example .env

# Key variables to set:
export GCP_PROJECT_ID="your-project-id"
export CUSTOMER_EMAIL_ID="customer@example.com"
export DATASET_CONFIG_FILE="banking_dataset_config.json"
```

4. **Generate and upload data:**
```bash
# Generate sample banking dataset
python src/generate_data.py

# Upload to BigQuery
python src/upload_to_bigquery.py
```

5. **Deploy infrastructure (optional):**
```bash
cd terraform
terraform init
terraform plan
terraform apply
```

## 📊 Data Generation

The project includes a comprehensive data generation script that creates realistic banking datasets:

### Generated Tables

- **`customers`**: 1,000 customer records with profiles and KYC status
- **`accounts`**: 1,500-3,000 accounts (mix of checking, savings, credit, loan)
- **`transactions`**: 50,000 transaction records across all accounts
- **`products`**: Banking products (credit cards, loans, deposits)
- **`customer_products`**: Customer-product relationships and application status
- **`credit_scores`**: Credit scores from various bureaus (EXPERIAN, EQUIFAX, TRANSUNION, CIBIL)

### Generate Data

```bash
cd src
python generate_data.py
```

Generated CSV files are saved to `data/` directory.

### Upload to BigQuery

```bash
export GCP_PROJECT_ID="your-project-id"
python src/upload_to_bigquery.py
```

## 🌍 Deployment

### Using Terraform

The `terraform/` directory contains complete infrastructure-as-code:

```bash
cd terraform

# Initialize Terraform
terraform init

# Review planned changes
terraform plan -var="project_id=YOUR_PROJECT_ID"

# Apply configuration
terraform apply -var="project_id=YOUR_PROJECT_ID"
```

**Resources Created:**
- BigQuery dataset (`banking_data`)
- 6 BigQuery tables with proper schemas
- GCS bucket for data staging
- IAM roles and permissions

### Manual Deployment

1. Create BigQuery dataset: `banking_data`
2. Create tables using schemas from terraform/main.tf
3. Upload CSV files using src/upload_to_bigquery.py

## 🔌 API Usage

### Starting the MCP Server

```bash
# Using FastMCP CLI (recommended)
fastmcp run bq_agent/mcp_server/server.py:mcp --transport http --port 8080

# Or run directly with Python
export MCP_HOST=0.0.0.0
export MCP_PORT=8080
python -m bq_agent.mcp_server.server
```

## ⚙️ Configuration

### Environment Variables

```bash
# GCP Configuration
GCP_PROJECT_ID=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=./keys/my-creds.json

# BigQuery Configuration
DATASET_ID=banking_data
BQ_DATA_PROJECT_ID=your-project-id
BQ_COMPUTE_PROJECT_ID=your-project-id

# Agent Configuration
ROOT_AGENT_MODEL=gemini-2.5-flash
BIGQUERY_AGENT_MODEL=gemini-2.5-pro
TRANSACTION_AGENT_MODEL=gemini-2.5-flash
BASELINE_NL2SQL_MODEL=gemini-2.5-pro

# OAuth2 Configuration
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
RS_BASE_URL=http://localhost:8080
MCP_PATH=/mcp

# Customer Configuration
CUSTOMER_EMAIL_ID=customer@example.com
DATASET_CONFIG_FILE=banking_dataset_config.json
```

### Dataset Configuration

Edit banking_dataset_config.json:

```json
{
  "datasets": [
    {
      "type": "bigquery",
      "name": "Banking Data",
      "description": "Customer, account, and transaction data",
      "project_id": "your-project-id",
      "dataset_id": "banking_data"
    }
  ]
}
```

## 📁 Project Structure

```
banking-agent/
├── bq_agent/                          # Main agent package
│   ├── agent.py                       # Root agent orchestrator
│   ├── prompts.py                     # Agent instructions
│   ├── tools.py                       # Tool definitions
│   ├── mcp_server/                    # MCP server for transactions
│   │   ├── server.py                  # FastMCP server implementation
│   │   ├── tools.py                   # BigQuery-backed tools
│   │   └── README.md                  # MCP documentation
│   └── sub_agents/                    # Specialized agents
│       ├── bigquery/                  # Query agent
│       │   ├── agent.py               # BigQuery agent logic
│       │   ├── tools.py               # NL2SQL and execution tools
│       │   └── prompts.py             # BigQuery prompts
│       └── transaction/               # Transaction agent
│           ├── agent.py               # Transaction agent logic
│           └── prompts.py             # Transaction prompts
├── data/                              # Generated datasets
│   ├── customers.csv
│   ├── accounts.csv
│   ├── transactions.csv
│   ├── products.csv
│   ├── customer_products.csv
│   └── credit_scores.csv
├── src/                               # Data generation scripts
│   ├── generate_data.py               # Dataset generation
│   ├── upload_to_bigquery.py          # BigQuery upload
│   └── test.py                        # Tests
├── terraform/                         # Infrastructure as Code
│   ├── main.tf                        # Resource definitions
│   ├── variables.tf                   # Variable declarations
│   └── outputs.tf                     # Output definitions
├── keys/                              # Service account credentials
│   └── my-creds.json                  # GCP service account key
├── ref/                               # Reference documentation
│   ├── adk-docs.txt                   # ADK documentation
│   ├── fastmcp-doc.txt                # FastMCP documentation
│   └── authn-adk-all-in-one/          # Authentication demo
├── .env                               # Environment variables
├── .env.oauth.example                 # OAuth2 configuration example
├── .gitignore                         # Git ignore rules
├── requirements.txt                   # Python dependencies
├── banking_dataset_config.json        # Dataset configuration
├── PROJECT_SUMMARY.md                 # Project documentation
└── README.md                          # This file
```

## 📦 Dependencies

### Core Libraries

- **google-adk** (^0.4.0) - Agent Development Kit
- **fastmcp** (^0.12.0) - Model Context Protocol
- **google-cloud-bigquery** (^3.20.0) - BigQuery client
- **google-genai** (^0.4.0) - Generative AI client
- **pandas** (^2.0.0) - Data manipulation
- **faker** (^20.0.0) - Data generation

### Authentication

- **python-dotenv** - Environment variable management
- **google-auth** - Google authentication

### Infrastructure

- **Terraform** (>= 1.0) - Infrastructure as Code
- **google-provider** (>= 5.0) - Terraform Google provider

## 🔐 Security

### Authentication & Authorization

1. **OAuth2 with Google**: All MCP server endpoints require Google OAuth2 authentication
2. **Row-Level Security (RLS)**: BigQuery views automatically filter data by authenticated customer email
3. **Service Account Isolation**: GCP service account permissions limited to required resources
4. **Token Validation**: Access tokens validated on every MCP request

### Data Protection

- Credentials stored in environment variables or `.env` file (never hardcoded)
- Service account keys in `keys/` directory (added to `.gitignore`)
- BigQuery dataset configured with deletion protection
- Customer data isolated through RLS and view-based access

### Transaction Security

- Two-step confirmation required for all transfers
- Amount validation and balance checks
- Transactional consistency for account updates
- Audit trail through transaction table


## 📝 License

This project is provided as-is for demonstration purposes.

## 🙋 Support

For issues and questions:

1. Check existing documentation in `ref/` and `bq_agent/mcp_server/README.md`
2. Review [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) for architectural details
3. Check environment configuration in `.env` file
4. Review BigQuery error logs in Google Cloud Console

---

**Built with:** Google Agent Development Kit (ADK), Model Context Protocol (MCP), BigQuery, and Vertex AI
**Authentication:** Google OAuth2 with Row-Level Security
**Infrastructure:** Terraform & Google Cloud Platform
