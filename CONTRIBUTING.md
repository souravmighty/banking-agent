# 🤝 Contributing to ApexBanking

Thank you for your interest in contributing to **ApexBanking**! As a production-inspired multi-agent AI platform, we maintain high standards for architectural clean-code, comprehensive documentation, and secure agent design.

---

## 📋 Code of Conduct & Standards

To ensure the system remains resilient, scalable, and secure, all contributions must adhere to the following core guidelines:

1.  **Strict Security Practices**:
    *   **Zero Client-Side Trust**: Never trust inputs or identity claims supplied directly by the client portal UI. All requests *must* traverse the `customer-identity-service` with cryptographically verified Bearer tokens.
    *   **Database Sandbox**: Never let an AI agent query base tables directly. Queries must target only the customer-specific authorized views.
2.  **Modular Multi-Agent Conventions**:
    *   Keep agents focused on their single, highly specialized domain (e.g. analytical vs transactional).
    *   Ensure all routing parameters and tools are declared with clean, descriptive docstrings and type hints.
3.  **Comprehensive Schema-Mapping**:
    *   If you alter BigQuery tables, you must declare them inside `infra/bq_schema/main.tf` alongside detailed column descriptions (**Semantic Metadata**).

---

## 🏗️ Local Development Setup

To establish a complete, localized replication of the ApexBanking stack:

1.  **Clone the Repository & Sync Packages**:
    ```bash
    git clone https://github.com/your-username/banking-agent.git
    cd banking-agent
    
    # Install dependencies using uv
    uv sync
    ```
2.  **Configure Local Environments**:
    Create `.env` using `.env.example`:
    ```bash
    cp .env.example .env
    ```
3.  **Verify Linter Compliance**:
    Ensure the codebase adheres to formatting rules before opening pull requests:
    ```bash
    make lint
    ```

---

## 📁 Repository Conventions

### Folder Structure Overview
*   **`app/`**: Holds the central Root Agent orchestrator and sub-agents (Google ADK engine).
*   **`customer-identity-service/`**: Stateless identity mapping API (FastAPI container).
*   **`infra/`**: Terraform configurations, schemas, and synthetic data loading scripts.
*   **`mcp_server/`**: Model Context Protocol (MCP) server exposing BigQuery tools.
*   **`nextjs/`**: Interactive chat interface portal (React + Tailwind client).

### Branch Naming Conventions
*   `feature/` - Additions of new capabilities, tools, or agents (e.g., `feature/analytics-copilot`).
*   `bugfix/` - Fixes for UI, data generation mapping, or security boundary issues (e.g., `bugfix/mobile-overflow`).
*   `docs/` - Improvements to architecture, security, or setup guides (e.g., `docs/auth-sequence`).

---

## 🚀 Pull Request Guidelines

1.  Ensure that all tests, format checks, and type-checks pass cleanly without warnings.
2.  Provide a clear, detailed PR description explaining the engineering rationale and trade-offs of your changes.
3.  Include corresponding updates in the `/docs` folder if you alter database schemas, system prompts, or deployment workflows.
