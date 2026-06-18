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

- `POST /api/v1/registration/check-email`: Check if email is pre-authorized.
- `POST /api/v1/registration/link-user`: Link verified Firebase user to customer.
- `GET /api/v1/auth/me`: Get current customer profile.
- `GET /api/v1/adk/context`: Context for Google ADK agents.
- `GET /api/v1/mcp/customer-context`: Context for MCP transaction servers.
