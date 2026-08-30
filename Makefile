.PHONY: install dev dev-backend dev-frontend identity-service customer-data-service analytics-metadata-service analytics-copilot analytics-copilot-api ai-banking-assistant ai-banking-assistant-api mcp-server test-identity-service test-metadata-service test-analytics-copilot test-ai-banking-assistant test-mcp-server eval-analytics-copilot eval-ai-banking-assistant eval-banking-suite eval-safety-suite bq-setup mcp-server-infra generate-data upload-data data-setup lint deploy-adk deploy-identity-service deploy-data-service deploy-mcp-server deploy-analytics-copilot deploy-ai-banking-assistant

PROJECT_ID ?= banking-agent-rag-mcp
REGION ?= us-central1
APP_SERVICE_ACCOUNT ?= analytics-copilot-app@$(PROJECT_ID).iam.gserviceaccount.com
BANKING_APP_SERVICE_ACCOUNT ?= bq-agent@$(PROJECT_ID).iam.gserviceaccount.com

install:
	@command -v uv >/dev/null 2>&1 || { echo "uv is not installed. Installing uv..."; curl -LsSf https://astral.sh/uv/0.6.12/install.sh | sh; source $$HOME/.local/bin/env; }
	uv sync
	cd ai-banking-assistant && uv sync
	cd analytics-copilot && uv sync
	npm --prefix nextjs install

dev:
	make dev-backend & make dev-frontend & make identity-service & make customer-data-service & make analytics-copilot-api & make mcp-server

# AI Banking Assistant Services
dev-backend: ai-banking-assistant-api

ai-banking-assistant-api:
	cd ai-banking-assistant && env -u VIRTUAL_ENV uv run uvicorn app.fast_api_app:app --host 0.0.0.0 --port 8000 --reload

ai-banking-assistant:
	cd ai-banking-assistant && env -u VIRTUAL_ENV uv run agents-cli playground

dev-frontend:
	npm --prefix nextjs run dev

identity-service:
	cd customer-identity-service && env -u VIRTUAL_ENV uv run uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

customer-data-service:
	cd customer-data-service && env -u VIRTUAL_ENV uv run uvicorn app.main:app --host 0.0.0.0 --port 8081 --reload

mcp-server:
	cd mcp-server && env -u VIRTUAL_ENV uv run uvicorn app.server:app --host 0.0.0.0 --port 8080 --reload

analytics-metadata-service:
	cd analytics-metadata-service && env -u VIRTUAL_ENV uv run uvicorn app.main:app --host 0.0.0.0 --port 8003 --reload

analytics-copilot:
	cd analytics-copilot && env -u VIRTUAL_ENV python3 scripts/run_adk_web.py

adk-web-analytics-copilot:
	cd analytics-copilot && env -u VIRTUAL_ENV python3 scripts/run_adk_web.py

generate-staff-jwt:
	cd analytics-copilot && env -u VIRTUAL_ENV python3 scripts/generate_staff_jwt.py

analytics-copilot-api:
	cd analytics-copilot && env -u VIRTUAL_ENV uv run uvicorn app.fast_api_app:app --host 0.0.0.0 --port 8002

# Testing & Evals
test-identity-service:
	cd customer-identity-service && PYTHONPATH=. uv run pytest tests/

test-metadata-service:
	cd analytics-metadata-service && PYTHONPATH=. uv run pytest tests/

test-analytics-copilot:
	cd analytics-copilot && PYTHONPATH=. uv run pytest tests/

test-ai-banking-assistant:
	cd ai-banking-assistant && PYTHONPATH=. uv run pytest tests/

test-mcp-server:
	cd mcp-server && PYTHONPATH=. uv run pytest tests/

eval-analytics-copilot:
	cd analytics-copilot && env -u VIRTUAL_ENV uv run agents-cli eval run --config tests/eval/eval_config.yaml

eval-ai-banking-assistant:
	cd ai-banking-assistant && env -u VIRTUAL_ENV uv run agents-cli eval run --config tests/eval/eval_config.yaml

eval-banking-suite:
	cd analytics-copilot && env -u VIRTUAL_ENV uv run agents-cli eval run --dataset tests/eval/datasets/banking_analytics_suite.json --config tests/eval/eval_config.yaml

eval-safety-suite:
	cd analytics-copilot && env -u VIRTUAL_ENV uv run agents-cli eval run --dataset tests/eval/datasets/adversarial_safety.json --config tests/eval/eval_config.yaml

adk-web:
	cd ai-banking-assistant && uv run agents-cli playground

# Infrastructure & Data Management
bq-setup:
	cd bigquery-infra/bq_schema && terraform init && terraform apply -auto-approve

mcp-server-infra:
	cd mcp-server/terraform && terraform init && terraform apply -auto-approve

generate-data:
	cd bigquery-infra/data_scripts && python3 generate_data.py

upload-data:
	cd bigquery-infra/data_scripts && python3 upload_to_bigquery.py

# Full data platform setup
data-setup: bq-setup generate-data upload-data

lint:
	uv run codespell
	uv run ruff check . --diff
	uv run ruff format . --check --diff
	uv run mypy .

# Deploy AI Banking Assistant to GCP Agent Platform (Vertex AI Agent Runtime)
deploy-ai-banking-assistant:
	cd ai-banking-assistant && env -u VIRTUAL_ENV uv run agents-cli deploy \
		--project $(PROJECT_ID) \
		--region $(REGION) \
		--service-account $(BANKING_APP_SERVICE_ACCOUNT)

# Deploy legacy AdkApp remotely
deploy-adk:
	cd ai-banking-assistant && PYTHONPATH=. uv run python3 -m deployment.remote --create

# Deploy the customer identity service remotely to GCP Cloud Run
deploy-identity-service:
	cd customer-identity-service && gcloud builds submit --config cloudbuild.yaml .

# Deploy the customer data service remotely to GCP Cloud Run
deploy-data-service:
	cd customer-data-service && gcloud builds submit --config cloudbuild.yaml .

# Deploy the FastMCP transaction server remotely to GCP Cloud Run
deploy-mcp-server:
	cd mcp-server && gcloud builds submit --config cloudbuild.yaml .

# Deploy Analytics Copilot to GCP Agent Platform (Vertex AI Agent Runtime)
deploy-analytics-copilot:
	cd analytics-copilot && env -u VIRTUAL_ENV uv run agents-cli deploy \
		--project $(PROJECT_ID) \
		--region $(REGION) \
		--service-account $(APP_SERVICE_ACCOUNT)
