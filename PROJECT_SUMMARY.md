# Project Summary

This document provides a comprehensive overview of the Banking Data Platform, including its architecture, data model, and core components.

## Architecture & Design Principles

The platform is built as a high-fidelity simulation of a modern banking environment, designed to power advanced AI agents (Google ADK), analytics copilots, and transactional workflows.

### Core Principles
*   **Business Keys**: All user-facing identifiers are business-centric (e.g., `account_number` instead of surrogate integer IDs).
*   **Historical Accuracy (SCD Type 2)**: Core entities maintain a full history of changes using effective start/end timestamps and versioning.
*   **Ledger Consistency**: Transfers are recorded as dual-entry DEBIT/CREDIT pairs sharing a unique `reference_id`.
*   **AI-Native Metadata**: Every BigQuery field is enriched with exhaustive descriptions to provide deep context for SQL generation agents.

## File Structure

```
/
├───terraform/                  # Infrastructure as Code (BigQuery)
│   ├───main.tf                 # SCD Type 2 table definitions & schemas
├───src/                        # Data Engineering & Ingestion
│   ├───generate_data.py        # Segmented synthetic data generator (SCD, Paired TXs)
│   ├───upload_to_bigquery.py   # Bulk ingestion scripts
├───mcp_server/                 # Transactional Layer (FastMCP)
│   ├───server.py               # OAuth2 protected tool entrypoints
│   ├───tools.py                # Ledger-aware financial logic (Transfers, CC Payments)
├───app/                        # Multi-Agent Orchestration (ADK)
│   ├───agent.py                # Root agent orchestrator
│   ├───sub_agents/             # Specialized agents (BigQuery, Transaction)
├───data/                       # Local synthetic dataset (CSVs)
│   ├───accounts.csv
│   ├───beneficiaries.csv
│   ├───credit_cards.csv
│   ├───credit_scores.csv
│   ├───customers.csv
│   ├───fixed_deposits.csv
│   ├───loans.csv
│   └───transactions.csv
├───MIGRATION_NOTES.md          # Technical record of schema evolutions
└───README.md                   # System documentation & usage guide
```

## Data Model Overview

1.  **Identity & Access**: Maps Firebase UIDs to bank customers; implements Row-Level Security (RLS) via authorized BigQuery views.
2.  **Core Banking (SCD Type 2)**:
    *   `customers`: Profiles, segments (Retail, Wealth, etc.), and risk levels.
    *   `accounts`: Savings, Current, and Salary accounts with balance tracking.
    *   `credit_cards`: Detailed card management (limit, utilization, billing).
3.  **Products & Interactions**:
    *   `transactions`: Ledger-style history with categories and merchant mapping.
    *   `loans`: Specialized loan account tracking (EMI, tenure, outstanding).
    *   `fixed_deposits`: Investment tracking with maturity and interest.
    *   `beneficiaries`: Customer-managed payee lists.

## Multi-Agent Workflow

*   **Root Agent**: Classifies user intent and routes to sub-agents.
*   **BigQuery Agent**: Translates natural language to SQL; queries RLS-filtered views.
*   **Transaction Agent**: Executes secure financial operations via the MCP server.
