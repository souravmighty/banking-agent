# Migration Notes: Banking Data Platform Overhaul (V2)

This document details the comprehensive redesign of the banking data platform, focusing on business keys, SCD Type 2 implementation, and a modernized product suite.

## Phase 2 Rationale
Following the initial ledger-style transaction model (Phase 1), Phase 2 elevates the platform to enterprise standards. By shifting to **Business Keys** (`account_number`), we align the data model with how users and agents interact with a bank. The implementation of **SCD Type 2** provides the historical depth necessary for realistic analytics, auditing, and "point-in-time" AI context.

### Key Refinements (Phase 2.1)
*   **16-Digit Customer IDs**: `customer_id` is now generated as a random 16-digit unique integer to simulate global banking standards.
*   **Table Simplification**: Removed the `products` and `customer_products` tables. Modernized product tracking is now handled directly via specialized tables (`loans`, `fixed_deposits`, `credit_cards`).

## Major Architectural Changes

### 1. Business Keys Over Surrogate IDs
*   **Removed**: `account_id` (INTEGER) has been deprecated across the platform.
*   **New Primary Identifier**: `account_number` (STRING) is now the primary key for all user-facing interactions.
*   **Impact**: SQL generation agents now use account numbers for joins and filters, mirroring real-world banking queries.

### 2. Slowly Changing Dimensions (SCD Type 2)
Implemented for `customers`, `accounts`, and `credit_cards`.
*   **Fields Added**: `eff_start_ts`, `eff_end_ts`, `is_current`, `record_version`.
*   **Logic**: Every time a critical attribute changes (e.g., segment upgrade, account freeze), a new record version is created.
*   **Query Pattern**: Always filter by `is_current = true` to get the latest state, or use start/end timestamps for historical analysis.

### 3. Expanded Product Tables
*   **`loans`**: Full loan lifecycle (Sanctioned amount, EMI, tenure).
*   **`fixed_deposits`**: Investment tracking with maturity and interest.
*   **`beneficiaries`**: Saved payee management.
*   **`credit_cards`**: Specialized credit management (previously a generic account type).

## Component Impacts

### Synthetic Data Generation (`src/generate_data.py`)
*   **Segmented Rules**: Implemented Realistic distribution (RETAIL: 60%, PREMIUM: 20%, etc.) with tailored product ownership and balance ranges.
*   **History Simulation**: Generates 20-30% historical record density for SCD tables to test versioning logic.
*   **Integrity**: Enforces cross-table constraints (no orphan transactions or accounts).

### BigQuery & Terraform (`terraform/main.tf`)
*   **Enriched Metadata**: Every field description now contains business context, example values, and usage notes for AI agents.
*   **Schema Consistency**: All tables updated to reflect the new identifiers and SCD fields.

### RLS Views (`app/sub_agents/bigquery/tools.py`)
*   **Simplified Joins**: Views now join on `account_number`.
*   **SCD Filtering**: Every view automatically filters for `is_current = true`, ensuring the agent only operates on the latest valid data.

### MCP Tools (`mcp_server/tools.py`)
*   **API Update**: `make_transaction` and `credit_card_payment` now accept and return account numbers.
*   **Ledger Consistency**: Continues to support dual-row entry for transfers sharing a `reference_id`.

## Usage Notes for AI Agents
*   **Current State**: Always include `is_current = true` in WHERE clauses when querying Customers or Accounts.
*   **Account Numbers**: Use strings for account numbers (e.g., `'100234567890'`) instead of integers.
*   **Enriched Context**: Use the provided field descriptions to understand complex relationships like `utilization_percentage` or `emi_amount`.

## Phase 2.2: Semantic Metadata Support for AI Agents

This phase enhances the Banking Data Platform with unified semantic metadata support to improve AI agents' schema understanding, SQL generation quality, and dynamic discovery.

### 1. Enriched Table and Field Descriptions (BigQuery & Terraform)
- **Table-Level Descriptions**: Every BigQuery table now includes a comprehensive, LLM-optimized description detailing business purpose, primary business keys, relationships, typical usage, SCD Type 2 details, and typical AI questions.
- **Field-Level Descriptions**: Every column in every table has been updated to include business meaning, example values, allowed values, relationships, and nullability.

### 2. Customer Identity Service Context API Overhaul
- **Dynamic Metadata Retrieval**: The `/adk/context` endpoint now leverages both **BigQuery Table Metadata APIs** and **INFORMATION_SCHEMA.COLUMNS** to retrieve table/field descriptions, column types, and nullability dynamically on demand.
- **SCD Semantics Injection**: The service dynamically identifies if a table is SCD Type 2 and injects critical guidance to prevent querying expired records: `"Use is_current = TRUE unless historical analysis is requested."`.
- **Structured Response Format**: The response is structured in Pydantic models containing `view_name`, `table_description`, `is_scd_type_2`, `scd_columns`, and list of `fields` (with name, type, and description) while preserving backward compatibility.

