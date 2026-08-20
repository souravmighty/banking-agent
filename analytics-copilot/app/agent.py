# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Dynamic Graph Workflow implementation for Analytics Copilot in Google ADK 2.0.

Integrates with analytics-metadata-service and adheres to BigQuery NL2SQL standards
from banking-agent-rag-mcp.
"""

import json
import logging
import os
import re
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from google import genai
from google.adk.agents.context import Context
from google.adk.apps import App
from google.adk.events.event import Event
from google.adk.workflow import Workflow, node
from google.genai import types

from app.metadata_client import metadata_client
from app.schemas import (
    AnalyticsSynthesis,
    HypothesisPlan,
    HypothesisResult,
    HypothesisTask,
)
from app.tools import execute_bigquery_query

load_dotenv()

logger = logging.getLogger(__name__)

MODEL = os.getenv("ANALYTICS_COPILOT_MODEL", "gemini-2.5-flash")
BQ_PROJECT_ID = os.getenv("BQ_PROJECT_ID", "banking-agent-rag-mcp")


def _get_genai_client() -> genai.Client:
    """Initializes and returns the Google GenAI client."""
    use_vertex = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "true").lower() == "true"
    project = os.getenv("GOOGLE_CLOUD_PROJECT", BQ_PROJECT_ID)
    location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    api_key = os.getenv("GEMINI_API_KEY")

    if api_key:
        return genai.Client(api_key=api_key)
    return genai.Client(vertexai=use_vertex, project=project, location=location)


def _extract_text(node_input: Any) -> str:
    """Helper to extract user prompt string from various input types."""
    if isinstance(node_input, str):
        return node_input
    if isinstance(node_input, types.Content):
        parts = [p.text for p in (node_input.parts or []) if hasattr(p, "text") and p.text]
        return "\n".join(parts) if parts else ""
    if isinstance(node_input, dict):
        return node_input.get("text", str(node_input))
    return str(node_input)


def _clean_sql(raw_sql: str) -> str:
    """Cleans markdown wrappers and trailing delimiters from generated SQL."""
    sql = re.sub(r"^```(?:sql)?\s*", "", raw_sql.strip(), flags=re.IGNORECASE)
    sql = re.sub(r"\s*```$", "", sql).strip()
    return sql


def _format_catalog_for_prompt(catalog: Dict[str, Any]) -> str:
    """Formats the Layer A compact catalog for the planning agent."""
    lines = []
    lines.append(f"BigQuery Project: `{BQ_PROJECT_ID}`")
    lines.append("Datasets: `banking_data` (Core Banking Entities) and `analytics` (Analytical Data Marts)")
    lines.append("\nAvailable Tables & Marts:")
    for t in catalog.get("tables", []):
        scd = " [SCD Type 2]" if t.get("is_scd2") else ""
        lines.append(f"- `{t.get('dataset_name', 'banking_data')}.{t.get('table_name')}`{scd} ({t.get('business_domain', 'GENERAL')}): {t.get('description', '')}")
        if t.get("key_columns"):
            lines.append(f"  * Key columns: {', '.join(t['key_columns'])}")

    if catalog.get("metrics"):
        lines.append("\nCurated Business Metrics:")
        for m in catalog.get("metrics", []):
            lines.append(f"- `{m.get('metric_name')}` ({m.get('display_name')}): {m.get('business_definition', '')} [Tables: {', '.join(m.get('source_tables', []))}]")

    return "\n".join(lines)


async def plan_hypotheses(ctx: Context, node_input: Any):
    """Stage 1: Analyzes user query against compact catalog, establishes cohort baseline, and generates 1-7 hypotheses."""
    question_text = _extract_text(node_input)
    if not question_text or not question_text.strip():
        question_text = "Why have credit card balances dropped in recent months?"

    client = _get_genai_client()
    catalog = metadata_client.get_compact_catalog()
    catalog_summary = _format_catalog_for_prompt(catalog)

    prompt = f"""You are a Lead Financial Analytics Strategist and BigQuery Warehouse Architect.
A business stakeholder has asked the following analytical question:
"{question_text}"

Governed Data Warehouse Catalog:
{catalog_summary}

Your objective:
1. Identify the common base denominator and cohort filter criteria (e.g. active customer accounts, specific observation window) to ensure all parallel investigations operate on the exact same dataset baseline.
2. Formulate between 1 and 7 distinct, mutually-exclusive, and testable analytical hypotheses to investigate the root causes.
3. For EACH hypothesis:
   - Identify relevant warehouse tables from `banking_data` or `analytics` (e.g., `credit_cards`, `analytics_balances`, `analytics_customer_360`, `transactions`).
   - Identify relevant curated metrics (e.g. `credit_card_payoff_rate`, `credit_card_total_balance`, `credit_card_spend`).
   - Specify dimensions (e.g. `customer_segment`, `card_type`, `month`).
   - State the specific SQL intent and rationale.

Generate the structured hypothesis plan strictly following the schema."""

    response = await client.aio.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=HypothesisPlan,
            temperature=0.2,
        ),
    )

    plan_data = json.loads(response.text)
    plan = HypothesisPlan.model_validate(plan_data)

    tasks_as_dicts = [task.model_dump() for task in plan.hypotheses]
    status_msg = f"Generated {len(plan.hypotheses)} investigation hypotheses under cohort '{plan.common_base_cohort}'."

    yield Event(
        content=types.Content(
            role="model",
            parts=[types.Part.from_text(text=status_msg)],
        ),
        output=tasks_as_dicts,
        state={
            "plan": plan.model_dump(),
            "business_question": question_text,
            "common_base_cohort": plan.common_base_cohort,
        },
    )


@node(parallel_worker=True)
async def investigate_hypothesis(node_input: dict):
    """Stage 2: Parallel Worker node that retrieves semantic metadata context, generates BigQuery Google SQL, executes query, and evaluates findings."""
    task = HypothesisTask.model_validate(node_input)
    client = _get_genai_client()

    # Step 2a: Fetch Layer B rich semantic context from analytics-metadata-service
    selected_tables = task.relevant_tables or ["credit_cards", "analytics_balances"]
    selected_metrics = task.relevant_metrics or [task.target_metric]
    selected_dimensions = task.relevant_dimensions or ["customer_segment", "month"]

    context_data = metadata_client.get_nl2sql_context(
        selected_tables=selected_tables,
        selected_metrics=selected_metrics,
        selected_dimensions=selected_dimensions,
        question=f"{task.title}: {task.sql_intent}",
    )
    prompt_context_str = context_data.get("prompt_context_str", "")

    # Step 2b: Generate BigQuery Google SQL adhering to standard @app/sub_agents/bigquery NL2SQL guidelines
    nl2sql_prompt = f"""You are an AI assistant serving as an expert BigQuery SQL engineer for project `{BQ_PROJECT_ID}`.
Your job is to generate a single, highly accurate Google SQL query based on the question, hypothesis, and governed schema context.

Hypothesis ({task.id}): "{task.title}"
Rationale: {task.rationale}
Target Metric: {task.target_metric}
Intent: {task.sql_intent}
Common Base Cohort: {task.base_filters}

{prompt_context_str}

### Strict NL2SQL Guidelines:
1. **Table Referencing:**
   - Always use the database prefix enclosed in backticks for table names.
   - For example: `{BQ_PROJECT_ID}.banking_data.credit_cards` or `{BQ_PROJECT_ID}.analytics.analytics_balances`.
2. **Slowly Changing Dimensions (SCD Type 2):**
   - For SCD2 tables (e.g. `customers`, `accounts`, `credit_cards`), ALWAYS apply the current record filter `WHERE is_current = TRUE` (or `eff_end_ts IS NULL`) unless querying a specific historical point-in-time timestamp.
3. **Joins & Aggregations:**
   - Ensure join keys have matching types.
   - Aggregate transactional data before joining to avoid fan-out duplication.
   - If selecting non-aggregated columns alongside aggregations, include all non-aggregated columns in the `GROUP BY` clause.
4. **Google SQL & Column Usage:**
   - Use valid BigQuery Google SQL syntax.
   - Only select columns present in the schema. Do not project raw sensitive PII columns.
   - Add sensible LIMIT (max 1000 rows).

Return ONLY the executable SQL query string (no markdown formatting, no comments)."""

    sql_resp = await client.aio.models.generate_content(
        model=MODEL,
        contents=nl2sql_prompt,
        config=types.GenerateContentConfig(temperature=0.0),
    )
    generated_sql = _clean_sql(sql_resp.text)

    # Step 2c: Execute query against BigQuery warehouse tool
    query_result = execute_bigquery_query(generated_sql)

    # Step 2d: Evaluate query findings against the hypothesis
    scd2_used = "is_current" in generated_sql or "eff_start_ts" in generated_sql

    eval_prompt = f"""You are a Senior Quantitative Analytics Specialist.
Hypothesis ({task.id}): {task.title}
Target Metric: {task.target_metric}
Executed BigQuery SQL:
{generated_sql}

Query Status: {query_result.get('status')}
Row Count: {query_result.get('row_count')}
Query Result Data:
{json.dumps(query_result.get('rows', []), indent=2)}

Task:
1. Summarize key metric numbers found in the query results.
2. Provide concise findings assessing whether the empirical data supports or refutes this hypothesis.
3. State support_level as one of: CONFIRMED, REFUTED, or INCONCLUSIVE."""

    class SingleHypothesisEvaluation(HypothesisResult):
        pass

    eval_resp = await client.aio.models.generate_content(
        model=MODEL,
        contents=eval_prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=SingleHypothesisEvaluation,
            temperature=0.1,
        ),
    )

    eval_data = json.loads(eval_resp.text)
    eval_data["hypothesis_id"] = task.id
    eval_data["title"] = task.title
    eval_data["generated_sql"] = generated_sql
    eval_data["query_status"] = query_result.get("status", "SUCCESS")
    eval_data["scd2_applied"] = scd2_used

    worker_msg = f"[{task.id}] {task.title}: {eval_data.get('support_level', 'EVALUATED')}."
    yield Event(
        content=types.Content(
            role="model",
            parts=[types.Part.from_text(text=worker_msg)],
        ),
        output=eval_data,
    )


async def synthesize_insights(ctx: Context, node_input: list):
    """Stage 3: Fan-in aggregation, hypothesis ranking, and executive narrative report generation."""
    client = _get_genai_client()
    business_question = ctx.state.get(
        "business_question", "Why have credit card balances dropped in recent months?"
    )
    common_base_cohort = ctx.state.get("common_base_cohort", "All active accounts")

    results_summary = json.dumps(node_input, indent=2)

    synth_prompt = f"""You are the Chief Data & Analytics Officer.
The business stakeholder asked:
"{business_question}"

Common Base Baseline / Denominator:
{common_base_cohort}

The dynamic analytics workflow investigated multiple hypotheses in parallel against Google BigQuery ({BQ_PROJECT_ID}).
Collected investigation findings and empirical evidence:
{results_summary}

Your task:
1. Executive Summary: Deliver a crisp, data-backed answer explaining the primary root causes.
2. Rank Hypotheses: Rank each tested hypothesis by its relative impact/contribution. Specify verdict (CONFIRMED / REFUTED / INCONCLUSIVE), estimated impact, and summary.
3. Sufficiency Assessment: Decide if the current data is SUFFICIENT or if DEEP_DIVE_RECOMMENDED.
4. Recommended Next Steps: 2-4 actionable business next steps or further drills.
5. Narrative Report: A complete, beautifully formatted executive markdown report with sections:
   - Executive Summary
   - Primary Drivers & Ranked Hypotheses
   - Empirical Data Evidence & Metric Breakdown
   - Slowly Changing Dimensions (SCD2) & Data Integrity Governance
   - Sufficiency & Next Steps

Ensure the response strictly complies with the schema."""

    response = await client.aio.models.generate_content(
        model=MODEL,
        contents=synth_prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=AnalyticsSynthesis,
            temperature=0.2,
        ),
    )

    synthesis_data = json.loads(response.text)
    synthesis = AnalyticsSynthesis.model_validate(synthesis_data)

    yield Event(
        content=types.Content(
            role="model",
            parts=[types.Part.from_text(text=synthesis.narrative_report)],
        ),
        output=synthesis.model_dump(),
    )


# Define Google ADK 2.0 Graph Workflow
workflow_edges = [
    ("START", plan_hypotheses),
    (plan_hypotheses, investigate_hypothesis),
    (investigate_hypothesis, synthesize_insights),
]

root_agent = Workflow(
    name="analytics_copilot",
    edges=workflow_edges,
    description="Analytics Copilot with ADK 2.0 Dynamic Graph Workflow & BigQuery Semantic Metadata Integration",
)

app = App(
    root_agent=root_agent,
    name="app",
)
