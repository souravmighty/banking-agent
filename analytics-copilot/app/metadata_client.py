"""Client for integrating analytics-copilot with analytics-metadata-service.

Provides dual-mode integration:
1. Direct in-process fast loading from analytics-metadata-service repositories/services
2. HTTP client fallback targeting the deployed analytics-metadata-service REST API
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import httpx
import yaml

logger = logging.getLogger(__name__)

# Find repository path to analytics-metadata-service
CURRENT_DIR = Path(__file__).resolve().parent
REPO_ROOT = CURRENT_DIR.parent.parent
METADATA_SERVICE_DIR = REPO_ROOT / "analytics-metadata-service"
METADATA_DIR = METADATA_SERVICE_DIR / "metadata"

METADATA_SERVICE_URL = os.getenv("METADATA_SERVICE_URL", "http://localhost:8003")
ANALYTICS_COPILOT_API_KEY = os.getenv("ANALYTICS_COPILOT_API_KEY", "bankpilot-analytics-copilot-key")


class MetadataClient:
    """Client for querying the BankPilot Analytics Semantic Metadata Service."""

    def __init__(self, service_url: Optional[str] = None):
        self.service_url = (service_url or METADATA_SERVICE_URL).rstrip("/")
        self.headers = {
            "X-API-Key": ANALYTICS_COPILOT_API_KEY,
            "Content-Type": "application/json",
        }
        self._cached_catalog: Optional[Dict[str, Any]] = None
        self._in_process_service = None
        self._in_process_context_builder = None
        self._init_in_process_service()

    def _init_in_process_service(self) -> None:
        """Initializes direct in-process services if available in the repository."""
        if METADATA_DIR.exists():
            try:
                import sys
                metadata_service_str = str(METADATA_SERVICE_DIR)
                if metadata_service_str not in sys.path:
                    sys.path.insert(0, metadata_service_str)

                from app.repositories.metadata_repository import MetadataRepository
                from app.services.catalog_service import CatalogService
                from app.services.context_builder import ContextBuilder
                from app.services.metadata_validator import MetadataValidator

                repo = MetadataRepository(metadata_dir=str(METADATA_DIR))
                validator = MetadataValidator(repository=repo)
                self._in_process_service = CatalogService(repository=repo)
                self._in_process_context_builder = ContextBuilder(repository=repo, validator=validator)
                logger.info("Initialized direct in-process analytics-metadata-service loader from %s", METADATA_DIR)
            except Exception as e:
                logger.warning("Could not initialize in-process metadata service: %s. Using HTTP/fallback mode.", e)

    def get_compact_catalog(self, domain: Optional[str] = None) -> Dict[str, Any]:
        """Fetches the Layer A compact semantic catalog for the Analytics Planner."""
        if self._cached_catalog is not None and not domain:
            return self._cached_catalog

        # 1. Try in-process service
        if self._in_process_service is not None:
            try:
                catalog_obj = self._in_process_service.get_compact_catalog(domain=domain)
                result = catalog_obj.model_dump() if hasattr(catalog_obj, "model_dump") else catalog_obj.dict()
                if not domain:
                    self._cached_catalog = result
                return result
            except Exception as e:
                logger.warning("In-process catalog fetch failed: %s", e)

        # 2. Try HTTP service
        try:
            params = {"domain": domain} if domain else {}
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(
                    f"{self.service_url}/metadata/catalog",
                    headers=self.headers,
                    params=params,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    if not domain:
                        self._cached_catalog = data
                    return data
        except Exception as e:
            logger.debug("HTTP metadata catalog fetch unavailable: %s", e)

        # 3. Direct YAML fallback
        return self._load_fallback_catalog()

    def get_nl2sql_context(
        self,
        selected_tables: List[str],
        selected_metrics: Optional[List[str]] = None,
        selected_dimensions: Optional[List[str]] = None,
        question: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Fetches Layer B rich analytical context for NL2SQL generation."""
        selected_metrics = selected_metrics or []
        selected_dimensions = selected_dimensions or []

        # 1. Try in-process ContextBuilder
        if self._in_process_context_builder is not None:
            try:
                from app.models.context import NL2SQLContextRequest
                req = NL2SQLContextRequest(
                    question=question,
                    selected_tables=selected_tables,
                    selected_metrics=selected_metrics,
                    selected_dimensions=selected_dimensions,
                    strict_governance=True,
                )
                res = self._in_process_context_builder.build_nl2sql_context(req)
                return res.model_dump() if hasattr(res, "model_dump") else res.dict()
            except Exception as e:
                logger.warning("In-process nl2sql-context build failed: %s", e)

        # 2. Try HTTP service
        try:
            payload = {
                "question": question,
                "selected_tables": selected_tables,
                "selected_metrics": selected_metrics,
                "selected_dimensions": selected_dimensions,
                "strict_governance": True,
            }
            with httpx.Client(timeout=15.0) as client:
                resp = client.post(
                    f"{self.service_url}/metadata/nl2sql-context",
                    headers=self.headers,
                    json=payload,
                )
                if resp.status_code == 200:
                    return resp.json()
        except Exception as e:
            logger.debug("HTTP nl2sql-context fetch unavailable: %s", e)

        # 3. Basic fallback context
        return {
            "prompt_context_str": f"### Context for Tables: {', '.join(selected_tables)}\nMetrics: {', '.join(selected_metrics)}",
            "validation_passed": True,
            "warnings": [],
            "governance_notes": [],
        }

    def _load_fallback_catalog(self) -> Dict[str, Any]:
        """Loads catalog directly from YAML files if available."""
        if METADATA_DIR.exists():
            try:
                tables_file = METADATA_DIR / "tables.yaml"
                metrics_file = METADATA_DIR / "metrics.yaml"
                tables = []
                metrics = []
                if tables_file.exists():
                    with open(tables_file, "r") as f:
                        tables_data = yaml.safe_load(f)
                        for t in tables_data.get("tables", []):
                            if t.get("allowed_for_nl2sql", True):
                                tables.append({
                                    "table_name": t.get("table_name"),
                                    "dataset_name": t.get("dataset_name"),
                                    "business_domain": t.get("business_domain"),
                                    "grain": t.get("grain"),
                                    "description": t.get("description"),
                                    "key_columns": [c.get("column_name") for c in t.get("columns", []) if c.get("is_primary_key") or c.get("is_dimension")][:6],
                                    "is_scd2": t.get("scd_type") == "SCD_TYPE_2",
                                })
                if metrics_file.exists():
                    with open(metrics_file, "r") as f:
                        metrics_data = yaml.safe_load(f)
                        for m in metrics_data.get("metrics", []):
                            metrics.append({
                                "metric_name": m.get("metric_name"),
                                "display_name": m.get("display_name"),
                                "business_definition": m.get("business_definition"),
                                "sql_expression": m.get("sql_expression"),
                                "source_tables": m.get("source_tables", []),
                            })
                return {
                    "total_tables": len(tables),
                    "total_metrics": len(metrics),
                    "tables": tables,
                    "metrics": metrics,
                    "relationships": [],
                }
            except Exception as e:
                logger.error("Fallback YAML parsing failed: %s", e)

        return {"total_tables": 0, "total_metrics": 0, "tables": [], "metrics": [], "relationships": []}


# Singleton client
metadata_client = MetadataClient()
