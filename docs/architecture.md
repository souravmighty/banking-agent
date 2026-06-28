# 🏗️ Core Architecture Blueprint

This document details the macro architecture, components, and communication standards used throughout **BankPilot**.

---

## 🏛️ High-Level System Architecture

BankPilot is a distributed financial operations platform that acts as a secure, AI-native layer over a Google Cloud BigQuery transaction database. It employs a **Zero-Trust** security architecture that prevents direct client-database access by routing all queries through a multi-agent routing system.

```mermaid
graph TD
    User([User / Client Portal]) <-->|gRPC / WebSockets| NextJS[Next.js Web UI]
    NextJS <-->|gRPC / HTTP API| Root[Root Agent Orchestrator]
    NextJS <-->|JWT Auth & Map Identity| CIS[customer-identity-service]

    CIS -->|Provides Authorized Profile Context| Root
    CIS -->|Restricts Tool Executions| MCP[Model Context Protocol Server]
    
    subgraph Multi-Agent Workspace [Multi-Agent Workspace]
        Root <-->|Route Intent| BQAgent[BigQuery Agent]
        Root <-->|Route Intent| TxAgent[Transaction Agent]
    end

    subgraph Data Platform [Google Cloud Platform]
        BQAgent <-->|NL2SQL / RLS Views| BQ[(BigQuery Dataset)]
        TxAgent <-->|Tools Interface| MCP
        MCP <-->|Secure Double-Entry Ledger Updates| BQ
    end

    classDef agent fill:#0A2540,stroke:#639FAB,stroke-width:2px,color:#fff;
    classDef infra fill:#f4f6f8,stroke:#333,stroke-width:1px;
    class Root,BQAgent,TxAgent agent;
    class BQ,MCP,NextJS,CIS infra;
```

---

## 🔌 System Components & Core Responsibilities

### 1. Next.js SPA Client Portal (`/nextjs`)
*   **Purpose**: Premium user interface delivering an interactive chat experience, transaction logs, and real-time AI activity tracing.
*   **Design Paradigm**: Employs React Hooks and Tailwind CSS. Avoids local storage for sensitive banking states; relies entirely on Firebase Auth JWT tokens and secure microservice endpoints.

### 2. Customer Identity Service (`/customer-identity-service`)
*   **Purpose**: Resolves anonymous Firebase/Google credentials into validated bank customers and registers customer-scoped secure resources.
*   **Design Paradigm**: Written in FastAPI, acting as the security gatekeeper.
    *   Authenticates incoming requests via Firebase Admin JWT validation.
    *   Generates/refreshes customer-specific **Row-Level Security (RLS) views** inside BigQuery.
    *   Provides tokenized profile scopes to downstream AI layers.

### 3. Root Agent Orchestrator (`/app`)
*   **Purpose**: A Google Agent Development Kit (ADK) server acting as the router and primary conversational interface.
*   **Design Paradigm**: Uses Vertex AI models (`gemini-2.5-pro` and `gemini-2.5-flash`). Evaluates client intent, manages state constraints, and securely delegates analytical or transactional operations to sub-agents.

### 4. BigQuery Analytical Sub-Agent (`/app/sub_agents/bigquery`)
*   **Purpose**: Executes dynamic NL2SQL translation and executes user queries securely.
*   **Design Paradigm**: Leverages Google GenAI with enriched schema metadata. Queries *only* the user-authorized views created by the identity service. Under no circumstance can this agent query base tables directly.

### 5. Transaction Sub-Agent (`/app/sub_agents/transaction`)
*   **Purpose**: Handles multi-step bank actions such as wire transfers, credit card payments, or investments.
*   **Design Paradigm**: Works in tandem with the Model Context Protocol (MCP) server. Conducts a two-stage verification flow: verifies recipient, verifies funding limits, and asks for explicit confirmation before calling financial APIs.

### 6. MCP Transaction Server (`/mcp_server`)
*   **Purpose**: A Model Context Protocol server exposing verified tools directly backed by BigQuery ledger transactions.
*   **Design Paradigm**: Connects securely to the database to insert dual-row balanced ledger records (`DEBIT`/`CREDIT`) under ACID transactions.

---

## 🔄 Dynamic Flows

### Analytical Inquiries Flow
```mermaid
sequenceDiagram
    autonumber
    actor User as Client
    participant UI as Next.js Web UI
    participant CIS as customer-identity-service
    participant Root as Root Agent (ADK)
    participant BQA as BigQuery Sub-Agent
    participant BQ as BigQuery (RLS)

    User->>UI: "What was my highest shopping expense last month?"
    UI->>CIS: GET /adk/context (Bearer JWT Token)
    CIS-->>UI: Return Mapped Profile & Authorized Views Specs
    UI->>Root: POST /chat/message (Prompt + Profile Context)
    Root->>Root: Classify Intent -> Analytics
    Root->>BQA: Delegate analytical task with authorized view names
    BQA->>BQA: Generate SQL referencing customer-scoped view
    BQA->>BQ: Run SQL query (Strictly isolated rows)
    BQ-->>BQA: Return analytical results
    BQA-->>Root: Return formatted answer
    Root-->>UI: Return conversational answer & activity trace
    UI-->>User: Render responsive chat bubble & transaction table
```

### Transaction Operations Flow
```mermaid
sequenceDiagram
    autonumber
    actor User as Client
    participant UI as Next.js Web UI
    participant CIS as customer-identity-service
    participant Root as Root Agent (ADK)
    participant TxA as Transaction Sub-Agent
    participant MCP as MCP Server Tools
    participant BQ as BigQuery (Ledger)

    User->>UI: "Transfer ₹5,000 to Raj"
    UI->>CIS: GET /adk/context (Bearer JWT Token)
    CIS-->>UI: Return Mapped Profile & Account Authorizations
    UI->>Root: POST /chat/message (Prompt + Profile Context)
    Root->>Root: Classify Intent -> Transactional
    Root->>TxA: Delegate Transfer Task
    TxA->>MCP: Call Tool "get_beneficiary" (Verify recipient)
    MCP-->>TxA: Recipient verified (Raj - Savings)
    TxA-->>UI: "Please confirm: Transfer ₹5,000 to Raj's account ending in 1234?"
    UI->>Root: "Yes, proceed."
    Root->>TxA: Confirm and execute
    TxA->>MCP: Call Tool "create_transfer" (sender_acc, recipient_acc, amount)
    Note over MCP,BQ: MCP queries CIS /auth/me with credentials to verify source ownership
    MCP->>BQ: Insert Debit & Credit entries (reference_id) under transaction block
    BQ-->>MCP: Balance updated, Ledger Committed
    MCP-->>TxA: Return transaction receipt details
    TxA-->>Root: Return transaction confirmation
    Root-->>UI: Conversational confirmation
    UI-->>User: Render transaction confirmation card on UI
```
