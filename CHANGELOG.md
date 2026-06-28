# 📄 Semantic Changelog

All notable changes to **BankPilot** will be documented in this file, adhering to the [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and [Semantic Versioning](https://semver.org/spec/v2.0.0.html) conventions.

---

## [1.0.0] - 2026-06-28

This release establishes the baseline production-grade architecture of the **BankPilot** AI-powered financial platform, delivering secure, multi-agent orchestration alongside a responsive web interface.

### Added
*   **Root Agent Orchestrator**: Conversational agent powered by the Google Agent Development Kit (ADK) that classifies user intent and securely delegates operations.
*   **BigQuery SQL Analytics Agent**: High-accuracy NL2SQL generation sub-agent leveraging BigQuery Column-Level Semantic Metadata.
*   **Transaction Execution Sub-Agent**: Implements a secure, two-stage transaction confirmation loop for money transfers and card payments.
*   **FastAPI Customer Identity Service**: Provides stateless user identity resolution, Firebase Admin SDK JWT decoding, and automated, customer-scoped view generation.
*   **BigQuery SCD Type 2 Schemas**: Implemented Slowly Changing Dimensions (SCD Type 2) tracking for Customers, Accounts, and Credit Cards tables.
*   **Double-Entry Ledger Model**: Standardized transactional data to matched DEBIT/CREDIT pairs sharing unique `reference_id` attributes.
*   **Premium Next.js Client Portal**: Feature-rich React interface featuring smooth native scroll layouts, code block constraints, and a step-by-step AI activity timeline.
*   **Terraform Infrastructure IaC**: Programmatic table schema mapping, and dataset configurations under `infra/bq_schema/`.

### Fixed
*   **Mobile View Responsiveness**: Resolved dynamic width expansion issues on small viewports (Pixel 7 / iPhone SE) by replacing the Radix ScrollArea with native layout boundaries.
*   **Aligned Data Pipelines**: Standardized the synthetic data generation categories mapping, utility codes, and transaction timestamp chronologies relative to the account active period.
*   **Timezone-Aware Excel Exports**: Corrected pandas database exports, converting timezone-aware timestamps to naive date formats to prevent openpyxl exceptions.

### Changed
*   **Zero-Trust Boundaries**: Completely isolated raw database query capabilities behind customer-specific authorized views.
*   **Comprehensive Documentation Suite**: Created exhaustive architectural, security, deployment, and API guides under `/docs`.
