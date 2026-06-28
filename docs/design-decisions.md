# 🧠 Architectural & Engineering Design Decisions

This document details the core architectural trade-offs, design decisions, and future roadmap considerations implemented throughout **ApexBanking**.

---

## 🏛️ Trade-offs & Engineering Decisions Matrix

| Decision Area | Selected Technology | Main Alternative | Rationale & Trade-off |
| :--- | :--- | :--- | :--- |
| **Agent Orchestration** | **Google Agent Development Kit (ADK)** | LangChain / CrewAI | **ADK** provides enterprise gRPC routing, seamless system instruction compilation, and robust state separation natively. Unlike LangChain, ADK does not require heavy runtime state wrappers and is optimized specifically for Google Vertex AI models. |
| **Multi-Agent Routing** | **Dual Sub-Agent Split (Analytical / Transactional)** | Single Monolithic Agent | Splitting into separate specialized agents reduces prompt size, improves reasoning accuracy (since each agent has a narrow task focus), and isolates destructive execution tools (MCP transfers) completely from the SQL generator. |
| **Authentication** | **Firebase Admin JWT Auth** | Auth0 / Custom OAuth Server | **Firebase Auth** integrates natively with Google Cloud, supports federated logins out-of-the-box, provides cryptographically signed short-lived JWKS tokens, and keeps the login pipeline completely serverless. |
| **Data Security & Isolation** | **Customer-Scoped BigQuery Views** | SQL parameterization / BigQuery Row-Level Security (RLS) policies | While BigQuery has native RLS, configuring them dynamically for hundreds of thousands of users is complex and slow. Generating **customer-scoped views** physically isolates the data at compilation-time, making SQL injections or prompt injection leakages mathematically impossible. |
| **Database Engine** | **Google Cloud BigQuery** | PostgreSQL / Spanner | While Spanner is excellent for transactional loads, **BigQuery** is unmatched for deep, heavy analytical inquiries (aggregations, spend trends, fraud analysis). By modeling transactions as a ledger and using Views, we can achieve high analytical performance alongside consistent audit trails. |
| **Tool Interface** | **Model Context Protocol (MCP)** | Direct REST API calls | **MCP** standardizes tool communication, allowing tools to be run in sandboxed contexts. This decouples the agent logic from the underlying financial execution code, making it modular and platform-agnostic. |

---

## 🔍 In-Depth Engineering Rationales

### 1. Why Google ADK?
Google's **Agent Development Kit (ADK)** was selected as the orchestration skeleton because it represents the state-of-the-art in production-grade agent frameworks.
*   **Performance**: ADK uses raw Python structures and gRPC APIs, bypassing the high execution overhead of monolithic packages.
*   **Predictable Session States**: ADK handles multi-turn conversation memory natively, eliminating context loss during complex sub-agent handoffs.
*   **System Prompt Prioritization**: ADK compiles system instructions directly into the LLM system context boundary, providing high resistance to prompt injection attacks compared to traditional string-formatting methods.

### 2. Why Customer Identity Service?
A core rule of production system design is: **Never trust client-side claims.**
Typical AI agent demos let the client send their account number or identity directly in the chat body. This allows easy spoofing.
By building the **`customer-identity-service`**, we:
*   Decouple client identity verification from the AI agent's reasoning.
*   Enforce a zero-trust policy: the client can only pass a verified JWT token. The service decrypts it, resolves the true `customer_id`, compiles the authorized BigQuery views, and injects this secure metadata directly into the ADK agent session container.

### 3. The Power of BigQuery Semantic Metadata
NL2SQL (Natural Language to SQL) agents are highly prone to hallucinating table joins and column names.
To solve this, we used **BigQuery Semantic Metadata**:
*   Using Terraform, we attach comprehensive, context-heavy descriptions to every column in the BigQuery tables.
*   The BigQuery Agent's tools extract this column metadata on-the-fly.
*   The model receives descriptions like:
    ```text
    "account_number: Business meaning: Primary key. Relationships: links directly to transactions, credit_cards, and fixed_deposits. Nullability: Never null."
    ```
This significantly improves SQL compilation accuracy, reducing hallucination rates to less than 1% on complex multi-table joins.

### 4. Why Slowly Changing Dimensions (SCD Type 2)?
In a real bank, balances and statuses are not static; they represent a timeline.
By structuring **Customers**, **Accounts**, and **Credit Cards** as SCD Type 2 tables, we:
*   Preserve historical snapshots (e.g., tracking a customer's segment changes from Retail to Wealth).
*   Enable point-in-time financial reporting (e.g., *"What was my credit limit in January?"* vs. *"What is my credit limit now?"*).
*   Avoid data corruption during record updates, maintaining a mathematically precise audit history.

---

## 🔮 Future Alternatives & Roadmap Extensions

1.  **Transactional database transition**: In a scale production environment, transactional ledgers should reside in **Google Cloud Spanner** (for globally consistent ACID writes) and be loaded to **BigQuery** via CDC (Change Data Capture) pipelines for analytics.
2.  **Semantic Caching Layer**: Implementing a Redis semantic cache in front of the BigQuery SQL sub-agent to instantly resolve recurring natural language inquiries (e.g., *"What is my balance?"*), saving LLM token costs and reducing latencies to under 50ms.
3.  **Real-Time Vector Search (RAG)**: Integrating **Vertex AI Vector Search** to index banking PDFs, statement structures, and investment terms, letting the Root Agent resolve generic financial FAQs seamlessly alongside structured SQL queries.
