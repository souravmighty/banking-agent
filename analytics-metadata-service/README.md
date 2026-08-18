# BankPilot Analytics Metadata & Semantic Service

A production-grade, governed **FastAPI Microservice** that serves as the semantic metadata layer between the **BankPilot Analytics Copilot** and **Google BigQuery** banking data warehouse.

---

## Architecture & Retrieval Pattern

```text
Business User Question
        │
        ▼
Analytics Planner / LLM
        │
        │ Compact semantic catalog (GET /metadata/catalog)
        │ (tables + metrics + dimensions + relationships)
        ▼
Select relevant tables / metrics
        │
        ▼
Analytics Metadata Service
        │
        │ Detailed metadata for selected assets only (POST /metadata/context or POST /metadata/nl2sql-context)
        ▼
Detailed analytical context + SCD2 guidance + Join warnings + PII sanitized schema
        │
        ▼
Hypothesis Agent / NL2SQL Agent
        │
        ▼
Validated SQL
        │
        ▼
BigQuery Data Warehouse
```

---

## Key Features

1. **Two-Layer Metadata Design**:
   - **Layer A (Compact Semantic Catalog)**: Fast, token-efficient table summaries, business grains, key metrics, key dimensions, and relationships specifically designed for LLM planner reasoning.
   - **Layer B (Detailed Metadata & Prompt Context)**: Deep schema, physical BigQuery column types, PK/FK relationships, explicit Slowly Changing Dimension (SCD Type 2) guidance, fan-out join warnings, and PII masking for selected assets.
2. **Slowly Changing Dimension (SCD Type 2) Support**:
   - Explicit configuration of `natural_key`, `effective_from_column`, `effective_to_column`, and `current_flag_column`.
   - Automatic generation of current-state filters (`WHERE is_current = TRUE`) and point-in-time historical filters (`WHERE eff_start_ts <= TIMESTAMP(D) AND (eff_end_ts > TIMESTAMP(D) OR eff_end_ts IS NULL)`).
3. **Curated & Governed Semantic Models**:
   - Version-controlled YAML definitions in `metadata/` (`tables.yaml`, `metrics.yaml`, `dimensions.yaml`, `relationships.yaml`, `business_terms.yaml`, `query_guidance.yaml`).
   - Merge logic preserves business curation and semantic types while dynamically synchronizing technical schema from BigQuery.
4. **Governance & PII Protection**:
   - Operational tables (`customer_identity_mapping`) are strictly blocked from analytical queries.
   - PII columns (`email`, `phone`, `address`, `card_number`, `firebase_uid`) are sanitized/filtered out from NL2SQL context.
5. **Metadata Search**:
   - Search across table definitions, columns, metric formulas, dimensions, and business term synonyms.
6. **Admin Sync & Validation**:
   - Automatic schema discovery from BigQuery `INFORMATION_SCHEMA` and full graph consistency validation.

---

## API Endpoints

### 1. Catalog & Context
- `GET /metadata/catalog` — Compact semantic catalog for the Analytics Planner.
- `POST /metadata/context` — Detailed analytical context for selected tables, metrics, and dimensions.
- `POST /metadata/nl2sql-context` — Pre-rendered, LLM-ready markdown prompt context with join warnings and SCD rules.

### 2. Assets & Semantic Definitions
- `GET /metadata/tables` — List all registered warehouse tables and analytical marts.
- `GET /metadata/tables/{table_name}` — Get full schema and metadata for a specific table.
- `GET /metadata/metrics` — List all curated analytical metrics and formulas.
- `GET /metadata/metrics/{metric_name}` — Get formula, default aggregations, and allowed dimensions for a metric.
- `GET /metadata/dimensions` — List all dimensions and drill-down hierarchies.
- `GET /metadata/dimensions/{dimension_name}` — Get detail for a specific dimension.
- `GET /metadata/relationships` — List all join keys, cardinalities, and fan-out join warnings.
- `GET /metadata/business-terms` — Natural language banking glossary mapped to metrics and dimensions.
- `GET /metadata/query-guidance` — Curated SQL generation rules and query optimization hints.

### 3. Search
- `POST /metadata/search` — Keyword/metadata search across entities with ranked relevance scoring.

### 4. Admin & Health
- `GET /health` — Service health and configuration status.
- `POST /admin/sync` — Synchronize technical schema from BigQuery and merge into catalog.
- `POST /admin/validate` — Run full integrity and governance validation across all catalog assets.

---

## Directory Structure

```text
analytics-metadata-service/
├── app/
│   ├── api/
│   │   ├── dependencies.py
│   │   └── routes/
│   │       ├── admin.py
│   │       ├── catalog.py
│   │       ├── health.py
│   │       ├── metadata.py
│   │       ├── metrics.py
│   │       └── search.py
│   ├── core/
│   │   ├── config.py
│   │   ├── logging.py
│   │   └── security.py
│   ├── models/
│   │   ├── business_term.py
│   │   ├── catalog.py
│   │   ├── column.py
│   │   ├── context.py
│   │   ├── dimension.py
│   │   ├── metric.py
│   │   ├── query_guidance.py
│   │   ├── relationship.py
│   │   ├── search.py
│   │   ├── sync.py
│   │   └── table.py
│   ├── repositories/
│   │   ├── bigquery_schema_repository.py
│   │   └── metadata_repository.py
│   ├── services/
│   │   ├── catalog_service.py
│   │   ├── context_builder.py
│   │   ├── metadata_search.py
│   │   ├── metadata_service.py
│   │   ├── metadata_sync.py
│   │   └── metadata_validator.py
│   ├── utils/
│   │   └── normalization.py
│   └── main.py
├── metadata/
│   ├── business_terms.yaml
│   ├── dimensions.yaml
│   ├── metrics.yaml
│   ├── query_guidance.yaml
│   ├── relationships.yaml
│   └── tables.yaml
├── tests/
│   ├── test_admin.py
│   ├── test_catalog.py
│   ├── test_context.py
│   ├── test_governance.py
│   └── test_search.py
├── Dockerfile
├── requirements.txt
├── .env.example
└── README.md
```

---

## Running Locally

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
```

### 3. Start the Service
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8003 --reload
```

Interactive OpenAPI docs will be available at: `http://localhost:8003/docs`

### 4. Run Test Suite
```bash
pytest tests/
```
