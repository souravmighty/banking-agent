from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from app.repositories.metadata_repository import MetadataRepository
from app.services.metadata_validator import MetadataValidator
from app.models.table import TableMetadata, SCDType
from app.models.column import ColumnMetadata, SensitivityLevel
from app.models.metric import MetricMetadata
from app.models.dimension import DimensionMetadata
from app.models.relationship import TableRelationship
from app.models.query_guidance import QueryGuidanceRule
from app.models.context import (
    ContextRequest,
    ContextResponse,
    NL2SQLContextRequest,
    NL2SQLContextResponse,
)
from app.utils.normalization import normalize_name

class ContextBuilder:
    """
    Builds detailed and LLM-ready analytical contexts for the NL2SQL Agent.
    """
    def __init__(self, repository: MetadataRepository, validator: MetadataValidator):
        self.repository = repository
        self.validator = validator

    def build_context(self, request: ContextRequest) -> ContextResponse:
        # Validate selection
        val_result = self.validator.validate_selection(
            tables=request.tables,
            metrics=request.metrics,
            dimensions=request.dimensions,
        )

        selected_tables: List[TableMetadata] = []
        for t_name in request.tables:
            t_meta = self.repository.get_table(t_name)
            if t_meta:
                # Filter columns if exclude_pii is enabled
                if request.exclude_pii:
                    filtered_cols = [
                        c for c in t_meta.columns
                        if not (c.is_sensitive and c.sensitivity_level in [SensitivityLevel.PII, SensitivityLevel.RESTRICTED])
                    ]
                    # Create a copy with filtered columns
                    t_copy = t_meta.model_copy(update={"columns": filtered_cols})
                    selected_tables.append(t_copy)
                else:
                    selected_tables.append(t_meta)

        selected_metrics: List[MetricMetadata] = []
        for m_name in request.metrics:
            m_meta = self.repository.get_metric(m_name)
            if m_meta:
                selected_metrics.append(m_meta)

        selected_dimensions: List[DimensionMetadata] = []
        for d_name in request.dimensions:
            d_meta = self.repository.get_dimension(d_name)
            if d_meta:
                selected_dimensions.append(d_meta)

        # Relationships
        relationships = self.repository.get_relationships_for_tables(request.tables)

        # Query guidance
        guidance = self.repository.get_query_guidance_for_assets(request.tables, request.metrics)

        # SCD Guidance
        scd_guidance: Dict[str, Any] = {}
        for t in selected_tables:
            if t.scd_type == SCDType.SCD_TYPE_2:
                scd_guidance[t.table_name] = {
                    "scd_type": "SCD_TYPE_2",
                    "natural_key": t.natural_key,
                    "effective_from_column": t.effective_from_column,
                    "effective_to_column": t.effective_to_column,
                    "current_flag_column": t.current_flag_column,
                    "current_query_filter": f"{t.current_flag_column or 'is_current'} = TRUE",
                    "point_in_time_filter": (
                        f"{t.effective_from_column or 'eff_start_ts'} <= TIMESTAMP(date) AND "
                        f"({t.effective_to_column or 'eff_end_ts'} > TIMESTAMP(date) OR {t.effective_to_column or 'eff_end_ts'} IS NULL)"
                    )
                }

        warnings = [w.message for w in val_result.warnings]

        return ContextResponse(
            tables=selected_tables,
            metrics=selected_metrics,
            dimensions=selected_dimensions,
            relationships=relationships,
            query_guidance=guidance,
            scd_guidance=scd_guidance,
            warnings=warnings,
            validation=val_result.model_dump(),
            generated_at=datetime.now(timezone.utc),
        )

    def build_nl2sql_context(self, request: NL2SQLContextRequest) -> NL2SQLContextResponse:
        # Validate selection
        val_result = self.validator.validate_selection(
            tables=request.selected_tables,
            metrics=request.selected_metrics,
            dimensions=request.selected_dimensions,
        )

        table_payloads: List[Dict[str, Any]] = []
        governance_notes: List[str] = []
        scd_guidance_list: List[Dict[str, Any]] = []
        
        for t_name in request.selected_tables:
            t_meta = self.repository.get_table(t_name)
            if not t_meta:
                continue
                
            cols_summary: List[Dict[str, Any]] = []
            for c in t_meta.columns:
                if request.strict_governance and c.is_sensitive and c.sensitivity_level in [SensitivityLevel.PII, SensitivityLevel.RESTRICTED]:
                    governance_notes.append(f"Excluded sensitive column '{t_name}.{c.column_name}' ({c.sensitivity_level.value}) from SQL context.")
                    continue
                    
                cols_summary.append({
                    "name": c.column_name,
                    "type": c.data_type,
                    "nullable": c.nullable,
                    "description": c.business_description or c.description or "",
                    "semantic_type": c.semantic_type.value if c.semantic_type else None,
                    "is_primary_key": c.is_primary_key,
                    "is_foreign_key": c.is_foreign_key,
                    "references": f"{c.references_table}.{c.references_column}" if c.references_table else None,
                })
                
            table_payloads.append({
                "table_name": t_meta.table_name,
                "dataset": t_meta.dataset_name,
                "project": t_meta.project_id,
                "description": t_meta.description,
                "grain": t_meta.grain,
                "scd_type": t_meta.scd_type.value if hasattr(t_meta.scd_type, "value") else str(t_meta.scd_type),
                "preferred_analytics_source": t_meta.preferred_analytics_source,
                "columns": cols_summary,
            })

            if t_meta.scd_type == SCDType.SCD_TYPE_2:
                scd_guidance_list.append({
                    "table_name": t_meta.table_name,
                    "natural_key": t_meta.natural_key,
                    "current_filter": f"{t_meta.current_flag_column or 'is_current'} = TRUE",
                    "historical_guidance": (
                        f"For point-in-time state as of date D: WHERE {t_meta.effective_from_column or 'eff_start_ts'} <= TIMESTAMP(D) "
                        f"AND ({t_meta.effective_to_column or 'eff_end_ts'} > TIMESTAMP(D) OR {t_meta.effective_to_column or 'eff_end_ts'} IS NULL)"
                    ),
                })

        # Metric payloads
        metric_payloads: List[Dict[str, Any]] = []
        for m_name in request.selected_metrics:
            m_meta = self.repository.get_metric(m_name)
            if m_meta:
                metric_payloads.append({
                    "metric_name": m_meta.metric_name,
                    "display_name": m_meta.display_name,
                    "business_definition": m_meta.business_definition,
                    "sql_expression": m_meta.sql_expression,
                    "default_aggregation": m_meta.default_aggregation,
                    "unit": m_meta.unit,
                    "source_tables": m_meta.source_tables,
                    "calculation_notes": m_meta.calculation_notes,
                })

        # Dimension payloads
        dim_payloads: List[Dict[str, Any]] = []
        for d_name in request.selected_dimensions:
            d_meta = self.repository.get_dimension(d_name)
            if d_meta:
                dim_payloads.append({
                    "dimension_name": d_meta.dimension_name,
                    "description": d_meta.description,
                    "source": f"{d_meta.source_table}.{d_meta.source_column}",
                    "allowed_filters": d_meta.allowed_filters,
                    "hierarchy": d_meta.hierarchy.levels if d_meta.hierarchy else None,
                })

        # Relationships and Joins
        rels = self.repository.get_relationships_for_tables(request.selected_tables)
        join_guidance: List[Dict[str, Any]] = []
        for r in rels:
            # Only include if both sides or relevant side is in request
            join_guidance.append({
                "left": f"{r.left_table}.{r.left_column}",
                "right": f"{r.right_table}.{r.right_column}",
                "type": r.relationship_type.value if hasattr(r.relationship_type, "value") else str(r.relationship_type),
                "description": r.business_description,
                "join_warning": r.join_warning,
                "template": r.join_sql_template,
            })

        # Query Rules
        guidance_rules = self.repository.get_query_guidance_for_assets(request.selected_tables, request.selected_metrics)
        query_rules = [f"[{r.rule_type.value}] {r.rule_text}" for r in guidance_rules]

        warnings = [w.message for w in val_result.warnings]

        # Render Prompt Context String
        prompt_str = self._render_prompt_markdown(
            question=request.question,
            tables=table_payloads,
            metrics=metric_payloads,
            dimensions=dim_payloads,
            joins=join_guidance,
            scd=scd_guidance_list,
            rules=query_rules,
            warnings=warnings,
            governance=governance_notes,
        )

        return NL2SQLContextResponse(
            question=request.question,
            tables=table_payloads,
            metrics=metric_payloads,
            dimensions=dim_payloads,
            join_guidance=join_guidance,
            scd_guidance=scd_guidance_list,
            query_rules=query_rules,
            warnings=warnings,
            governance_notes=governance_notes,
            prompt_context_str=prompt_str,
            validation_passed=val_result.valid,
            generated_at=datetime.now(timezone.utc),
        )

    def _render_prompt_markdown(
        self,
        question: Optional[str],
        tables: List[Dict[str, Any]],
        metrics: List[Dict[str, Any]],
        dimensions: List[Dict[str, Any]],
        joins: List[Dict[str, Any]],
        scd: List[Dict[str, Any]],
        rules: List[str],
        warnings: List[str],
        governance: List[str],
    ) -> str:
        lines: List[str] = []
        lines.append("### ANALYTICAL CONTEXT & GOVERNED SCHEMA")
        if question:
            lines.append(f"**Target Question:** {question}\n")

        # Tables & Grain
        lines.append("#### Relevant Tables & Grain")
        for t in tables:
            pref = " (PREFERRED ANALYTICS SOURCE)" if t.get("preferred_analytics_source") else ""
            lines.append(f"- **`{t['dataset']}.{t['table_name']}`**{pref}")
            lines.append(f"  - Grain: {t.get('grain', 'Not specified')}")
            lines.append(f"  - Description: {t.get('description', '')}")
            lines.append("  - Columns:")
            for col in t.get("columns", []):
                pk_fk = " [PK]" if col.get("is_primary_key") else (" [FK]" if col.get("is_foreign_key") else "")
                sem = f" ({col['semantic_type']})" if col.get("semantic_type") else ""
                desc = f" - {col['description']}" if col.get("description") else ""
                lines.append(f"    * `{col['name']}` ({col['type']}){pk_fk}{sem}{desc}")

        # Metrics
        if metrics:
            lines.append("\n#### Curated Business Metrics")
            for m in metrics:
                lines.append(f"- **{m['display_name']} (`{m['metric_name']}`)**")
                lines.append(f"  - Business Definition: {m.get('business_definition', '')}")
                if m.get("sql_expression"):
                    lines.append(f"  - Calculation Expression: `{m['sql_expression']}` (Default Agg: {m.get('default_aggregation')})")
                if m.get("calculation_notes"):
                    lines.append(f"  - Notes: {m['calculation_notes']}")

        # Dimensions
        if dimensions:
            lines.append("\n#### Dimensions")
            for d in dimensions:
                hier = f" [Hierarchy: {' -> '.join(d['hierarchy'])}]" if d.get("hierarchy") else ""
                lines.append(f"- **{d['dimension_name']}** (Source: `{d['source']}`){hier}: {d['description']}")

        # Joins & Warnings
        if joins:
            lines.append("\n#### Join Rules & Relationships")
            for j in joins:
                lines.append(f"- `{j['left']}` ➔ `{j['right']}` ({j['type']})")
                lines.append(f"  - Business Meaning: {j['description']}")
                if j.get("join_warning"):
                    lines.append(f"  - ⚠️ WARNING: {j['join_warning']}")

        # SCD Guidance
        if scd:
            lines.append("\n#### Slowly Changing Dimension (SCD Type 2) Guidance")
            for s in scd:
                lines.append(f"- Table `{s['table_name']}`:")
                lines.append(f"  - Current State Filter: `{s['current_filter']}`")
                lines.append(f"  - Historical Filter: {s['historical_guidance']}")

        # Query Rules & Governance
        if rules:
            lines.append("\n#### Query Execution & Analytical Guidance")
            for r in rules:
                lines.append(f"- {r}")

        if governance:
            lines.append("\n#### Governance & Sensitivity Restrictions")
            for g in governance:
                lines.append(f"- 🔒 {g}")

        if warnings:
            lines.append("\n#### Context Validation Warnings")
            for w in warnings:
                lines.append(f"- ⚠️ {w}")

        return "\n".join(lines)
