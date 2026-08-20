# Customer Identity Service

FastAPI microservice for Identity, Authorization, and Customer Context management.

## Features

- Firebase Auth Integration
- Pre-authorized Registration Flow
- Authorized BigQuery View Management
- Context endpoints for ADK Agents and MCP Servers

## Architecture

Clean architecture with:
- **Routers**: API endpoints
- **Services**: Business logic
- **Repositories**: Data access (BigQuery)
- **Schemas**: Pydantic models

## Local Development

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up environment:
   ```bash
   cp .env.example .env
   # Edit .env with your GCP details
   ```

3. Run the service:
   ```bash
   uvicorn app.main:app --reload
   ```

## Deployment (Cloud Run)

### Using Cloud Build
```bash
gcloud builds submit --config cloudbuild.yaml .
```

### Manual Deployment
```bash
gcloud run deploy customer-identity-service \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_CLOUD_PROJECT=your-project-id
```

## API Endpoints

### Customer-Facing Endpoints
- `POST /api/v1/registration/check-email`: Check if email is pre-authorized.
- `POST /api/v1/registration/link-user`: Link verified Firebase user to customer.
- `GET /api/v1/auth/me`: Get current customer profile.
- `GET /api/v1/adk/context` (or `/adk/context`): **Customer-facing context endpoint**.
  - **Audience**: Authenticated customer users.
  - **Returns**: `customer_id`, `customer_profile`, `authorized_views` (customer-scoped views such as `customer_views.customer_<id>_accounts_v`), and `authorized_account`.
  - **Purpose**: Initializes personal banking ADK agents with customer boundaries.
- `GET /api/v1/mcp/customer-context`: Context for MCP transaction servers.

### Bank Staff / Internal Analytics Endpoints
- `GET /api/v1/analytics-metadata` (or `/analytics-metadata`): **Privileged Analytics Copilot context endpoint**.
  - **Audience**: Authenticated `BANK_STAFF` users only (requires valid JWT with staff role or matching staff identity). Returns `401` if unauthenticated, `403` if called by a customer or demo user.
  - **Returns**: Approved operational BigQuery tables (`banking_data`) and curated analytical views (`analytics`), complete with:
    - Fully qualified `query_object` (e.g. `banking-agent-rag-mcp.banking_data.customers`, `banking-agent-rag-mcp.analytics.analytics_customer_360`)
    - Object classification: `object_type` (`TABLE` vs `VIEW`)
    - Rich business `table_description`
    - Semantic metadata: `primary_business_key`, `grain`, `relationship_information`
    - SCD Type 2 governance: `is_scd_type_2`, `scd_columns`, `ai_usage_guidance`
    - Curated `typical_ai_questions`
    - Full `schema` with `column_name`, `type`, `description`, and `mode`
  - **Security & Privacy**: Does **NOT** return `customer_id`, `customer_profile`, `authorized_account`, or customer-scoped views.
  - **Caching**: Results are cached in-memory with configurable TTL (`ANALYTICS_METADATA_CACHE_TTL_SECONDS`). Pass `?refresh=true` to force a cache refresh.

## Configuration

Analytics metadata behavior can be customized via environment variables in `.env`:

| Variable | Default | Description |
| :--- | :--- | :--- |
| `BIGQUERY_ANALYTICS_DATASET` | `analytics` | BigQuery dataset containing curated analytical views. |
| `ANALYTICS_ALLOWED_TABLES` | `customers,accounts,transactions,credit_cards,loans,fixed_deposits,credit_scores` | Comma-separated allowlist of approved operational tables in `banking_data`. |
| `ANALYTICS_ALLOWED_VIEWS` | `analytics_customer_360,analytics_customer_acquisition,analytics_transactions,analytics_products,analytics_balances` | Comma-separated allowlist of approved views in `analytics`. |
| `ANALYTICS_METADATA_CACHE_TTL_SECONDS` | `3600` | In-memory cache TTL in seconds for analytics metadata discovery. |

