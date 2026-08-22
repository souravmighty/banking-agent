.PHONY: install dev dev-backend dev-frontend identity-service customer-data-service analytics-metadata-service analytics-copilot analytics-copilot-api test-identity-service test-metadata-service test-analytics-copilot bq-setup generate-data upload-data data-setup lint deploy-adk deploy-identity-service deploy-data-service

install:
	@command -v uv >/dev/null 2>&1 || { echo "uv is not installed. Installing uv..."; curl -LsSf https://astral.sh/uv/0.6.12/install.sh | sh; source $HOME/.local/bin/env; }
	uv sync && npm --prefix nextjs install

dev:
	make dev-backend & make dev-frontend & make identity-service & make customer-data-service & make analytics-copilot-api

dev-backend:
	uv run adk api_server . --allow_origins="*"

dev-frontend:
	npm --prefix nextjs run dev

identity-service:
	cd customer-identity-service && env -u VIRTUAL_ENV uv run uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

customer-data-service:
	cd customer-data-service && env -u VIRTUAL_ENV uv run uvicorn app.main:app --host 0.0.0.0 --port 8081 --reload

analytics-metadata-service:
	cd analytics-metadata-service && env -u VIRTUAL_ENV uv run uvicorn app.main:app --host 0.0.0.0 --port 8003 --reload

analytics-copilot:
	env -u VIRTUAL_ENV uv run --project analytics-copilot adk web analytics-copilot --port 8502

analytics-copilot-api:
	cd analytics-copilot && env -u VIRTUAL_ENV uv run uvicorn app.fast_api_app:app --host 0.0.0.0 --port 8002

test-identity-service:
	cd customer-identity-service && PYTHONPATH=. uv run pytest tests/

test-metadata-service:
	cd analytics-metadata-service && PYTHONPATH=. uv run pytest tests/

test-analytics-copilot:
	cd analytics-copilot && PYTHONPATH=. uv run pytest tests/

eval-analytics-copilot:
	cd analytics-copilot && env -u VIRTUAL_ENV uv run agents-cli eval run --config tests/eval/eval_config.yaml

eval-banking-suite:
	cd analytics-copilot && env -u VIRTUAL_ENV uv run agents-cli eval run --dataset tests/eval/datasets/banking_analytics_suite.json --config tests/eval/eval_config.yaml

eval-safety-suite:
	cd analytics-copilot && env -u VIRTUAL_ENV uv run agents-cli eval run --dataset tests/eval/datasets/adversarial_safety.json --config tests/eval/eval_config.yaml

adk-web:
	uv run adk web --port 8501

# Infrastructure & Data Management
bq-setup:
	cd infra/bq_schema && terraform init && terraform apply -auto-approve

generate-data:
	cd infra/data_scripts && python3 generate_data.py

upload-data:
	cd infra/data_scripts && python3 upload_to_bigquery.py

# Full data platform setup
data-setup: bq-setup generate-data upload-data

lint:
	uv run codespell
	uv run ruff check . --diff
	uv run ruff format . --check --diff
	uv run mypy .

# Deploy the agent remotely
deploy-adk:
	PYTHONPATH=. uv run python3 -m deployment.remote --create

# Deploy the customer identity service remotely to GCP Cloud Run
deploy-identity-service:
	cd customer-identity-service && gcloud builds submit --config cloudbuild.yaml .

# Deploy the customer data service remotely to GCP Cloud Run
deploy-data-service:
	cd customer-data-service && gcloud builds submit --config cloudbuild.yaml .


