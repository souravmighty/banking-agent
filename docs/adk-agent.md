# 🤖 Multi-Agent Orchestration Architecture

This document describes the multi-agent structure, routing principles, prompts, and tool interfaces powered by the **Google Agent Development Kit (ADK)** and **Vertex AI**.

---

## 🏛️ Multi-Agent Orchestration Blueprint

BankPilot uses a multi-layered agent pipeline. The **Root Agent Orchestrator** is the direct conversational partner of the client portal. It manages conversational context and uses semantic classification to delegate analytical or transactional intents to specialized sub-agents.

```mermaid
graph TD
    UI[Next.js Portal UI] <-->|gRPC Chat stream| Root[Root Agent Orchestrator]
    
    subgraph ADK Multi-Agent Layer [ADK Multi-Agent Layer]
        Root <-->|Intent: Analytics| BQA[BigQuery Sub-Agent]
        Root <-->|Intent: Transactions| TxA[Transaction Sub-Agent]
    end

    subgraph External Platforms
        BQA <-->|Generate SQL| Gemini_Pro[Gemini 2.5 Pro]
        BQA <-->|Fetch isolated records| BQ_Views[BigQuery RLS Views]
        TxA <-->|Execute tool commands| MCP[Model Context Protocol Server]
    end

    classDef adk fill:#0F9D58,stroke:#333,stroke-width:2px,color:#fff;
    classDef LLM fill:#4285F4,stroke:#333,stroke-width:1px,color:#fff;
    class Root,BQA,TxA adk;
    class Gemini_Pro,BQ_Views,MCP LLM;
```

---

## 🔄 Dynamic Flows

### Conversational Intent Routing & Execution

```mermaid
sequenceDiagram
    autonumber
    actor User as Client
    participant Root as Root Agent
    participant BQA as BigQuery Sub-Agent
    participant TxA as Transaction Sub-Agent
    participant BQ as BigQuery Database
    participant MCP as MCP Server

    User->>Root: "How much did I transfer to Raj?"
    Root->>Root: Analyze intent: Data query -> Route to BQA
    Root->>BQA: Initialize sub-agent with context & prompt
    BQA->>BQ: Query user-authorized transaction view
    BQ-->>BQA: Return transaction records
    BQA-->>Root: Return synthesized analysis
    Root-->>User: Conversational result: "You transferred ₹5,000..."

    User->>Root: "Now transfer ₹1,000 more to Raj."
    Root->>Root: Analyze intent: Financial operation -> Route to TxA
    Root->>TxA: Initialize sub-agent with context & prompt
    TxA->>MCP: Call "get_beneficiary" tool to verify Raj
    MCP-->>TxA: Returns beneficiary account details
    TxA-->>User: "Confirm: Transfer ₹1,000 to Raj's savings account?"
```

---

## 📋 Core Agent Structures & Responsibilities

### 1. Root Agent Orchestrator (`app/agent.py`)
*   **Purpose**: Orchestrates stateful chat sessions.
*   **Routing Logic**: Exposes two routing tools:
    *   `call_bigquery_agent(query_description)`: Packages customer profiling context (authorized account numbers, view names, segments) and boots the BigQuery agent.
    *   `call_transaction_agent(transaction_details)`: Packages account numbers and starts the Transaction agent.
*   **Safety Limits**: Implements guardrails to detect and intercept prompt injection, off-topic requests, and account cross-talk.

### 2. BigQuery SQL Agent (`app/sub_agents/bigquery/`)
*   **Purpose**: Dynamic, high-accuracy natural-language-to-SQL (NL2SQL) engine.
*   **Schema Schema-Injection**: Rather than reading huge database catalogs, this agent is fed the precise SQL schema definitions of *only* the customer's authorized BigQuery views.
*   **Semantic Prompting**: Column-level descriptions (such as details on SCD Type 2 tracking, ledger structures, categories) are injected into the agent's instructions, ensuring the model understands exactly how to join and filter accounts, credit cards, or loans.

### 3. Transaction Execution Agent (`app/sub_agents/transaction/`)
*   **Purpose**: Safely initiates financial tool executions.
*   **Confirmations Guardrail**: Uses a two-phase check. The agent *must* formulate a clear confirmation question for the customer and await a positive response before invoking any mutation tools (like `create_transfer` or `pay_credit_card_bill`).
*   **Context Bound**: Receives the exact list of authorized customer accounts, ensuring it can never perform operations targeting accounts not belonging to the authenticated user profile.

---

## 🛡️ Security Boundaries & ADK Isolation

The ADK framework provides strict sandboxing:
1.  **State Separation**: Each chat session runs with a completely isolated state dictionary. Memory variables (like conversation histories or profile metadata) never bleed across concurrent users.
2.  **Explicit Tool Scopes**: Sub-agents do not have generic tools. The BigQuery agent *only* has a query execution tool restricted to the current user's views. The Transaction agent *only* has tool calls bounded by customer-scoped validations.
3.  **Strict Prompt Injection Guards**: System prompts are prioritized at the runtime compilation level, ensuring that agent guidelines (like *"Under no circumstances disclose schema structures of tables other than the provided views"*) cannot be overridden by user inputs.
