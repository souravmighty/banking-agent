from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from app.repositories.metadata_repository import MetadataRepository
from app.models.sync import ValidationResult, ValidationIssue
from app.models.table import SCDType
from app.utils.normalization import normalize_name

class MetadataValidator:
    """
    Validates selected tables, metrics, dimensions, relationships, and governance rules.
    """
    def __init__(self, repository: MetadataRepository):
        self.repository = repository

    def validate_selection(
        self,
        tables: List[str],
        metrics: List[str],
        dimensions: List[str],
    ) -> ValidationResult:
        errors: List[ValidationIssue] = []
        warnings: List[ValidationIssue] = []
        
        norm_selected_tables = {normalize_name(t) for t in tables}
        
        # 1. Validate Table Existence & Governance
        for t_name in tables:
            t_meta = self.repository.get_table(t_name)
            if not t_meta:
                errors.append(ValidationIssue(
                    severity="ERROR",
                    entity_type="TABLE",
                    entity_name=t_name,
                    message=f"Table '{t_name}' not found in metadata repository."
                ))
            else:
                if not t_meta.allowed_for_analytics or not t_meta.allowed_for_nl2sql:
                    errors.append(ValidationIssue(
                        severity="ERROR",
                        entity_type="GOVERNANCE",
                        entity_name=t_name,
                        message=f"Table '{t_name}' is marked as restricted/operational and cannot be queried by Analytics Copilot."
                    ))
                if not t_meta.grain:
                    warnings.append(ValidationIssue(
                        severity="WARNING",
                        entity_type="TABLE",
                        entity_name=t_name,
                        message=f"Table '{t_name}' does not have an explicit grain definition."
                    ))
                if t_meta.scd_type == SCDType.SCD_TYPE_2:
                    if not t_meta.current_flag_column and not (t_meta.effective_from_column and t_meta.effective_to_column):
                        warnings.append(ValidationIssue(
                            severity="WARNING",
                            entity_type="TABLE",
                            entity_name=t_name,
                            message=f"SCD Type 2 table '{t_name}' is missing temporal column configuration."
                        ))

        # 2. Validate Metrics
        for m_name in metrics:
            m_meta = self.repository.get_metric(m_name)
            if not m_meta:
                errors.append(ValidationIssue(
                    severity="ERROR",
                    entity_type="METRIC",
                    entity_name=m_name,
                    message=f"Metric '{m_name}' not found in metric catalog."
                ))
            else:
                # Check if at least one source table of this metric is in selected tables
                norm_source_tables = {normalize_name(st) for st in m_meta.source_tables}
                if norm_selected_tables and not norm_source_tables.intersection(norm_selected_tables):
                    warnings.append(ValidationIssue(
                        severity="WARNING",
                        entity_type="METRIC",
                        entity_name=m_name,
                        message=(
                            f"Metric '{m_name}' requires source table in {m_meta.source_tables}, "
                            f"none of which are currently in selected tables {tables}."
                        )
                    ))

        # 3. Validate Dimensions
        for d_name in dimensions:
            d_meta = self.repository.get_dimension(d_name)
            if not d_meta:
                warnings.append(ValidationIssue(
                    severity="WARNING",
                    entity_type="DIMENSION",
                    entity_name=d_name,
                    message=f"Dimension '{d_name}' not found in dimension catalog."
                ))
            else:
                norm_source = normalize_name(d_meta.source_table)
                if norm_selected_tables and norm_source not in norm_selected_tables:
                    # Check if dimension column exists in any of the selected tables
                    found_in_any = False
                    for st in norm_selected_tables:
                        st_meta = self.repository.get_table(st)
                        if st_meta and any(normalize_name(c.column_name) == normalize_name(d_meta.source_column) for c in st_meta.columns):
                            found_in_any = True
                            break
                    if not found_in_any:
                        warnings.append(ValidationIssue(
                            severity="WARNING",
                            entity_type="DIMENSION",
                            entity_name=d_name,
                            message=(
                                f"Dimension '{d_name}' is sourced from '{d_meta.source_table}', "
                                f"which is not in selected tables {tables}."
                            )
                        ))

        # 4. Validate Multi-Table Relationships
        if len(norm_selected_tables) > 1:
            rels = self.repository.get_relationships_for_tables(list(norm_selected_tables))
            # Check for join path
            connected_tables = set()
            for r in rels:
                l_norm = normalize_name(r.left_table)
                r_norm = normalize_name(r.right_table)
                if l_norm in norm_selected_tables and r_norm in norm_selected_tables:
                    connected_tables.add(l_norm)
                    connected_tables.add(r_norm)
            
            unconnected = norm_selected_tables - connected_tables
            if unconnected and len(norm_selected_tables) > 1:
                warnings.append(ValidationIssue(
                    severity="WARNING",
                    entity_type="RELATIONSHIP",
                    entity_name=", ".join(unconnected),
                    message=f"Tables {list(unconnected)} have no direct defined relationship with other selected tables. Join with care."
                ))

        is_valid = len(errors) == 0
        return ValidationResult(
            valid=is_valid,
            total_tables=len(tables),
            total_metrics=len(metrics),
            total_dimensions=len(dimensions),
            total_relationships=len(self.repository.get_relationships_for_tables(tables)),
            errors=errors,
            warnings=warnings,
            validated_at=datetime.now(timezone.utc),
        )

    def validate_entire_repository(self) -> ValidationResult:
        """Validates all registered tables, metrics, dimensions, and relationships."""
        all_tables = [t.table_name for t in self.repository.get_all_tables()]
        all_metrics = [m.metric_name for m in self.repository.get_all_metrics()]
        all_dims = [d.dimension_name for d in self.repository.get_all_dimensions()]
        return self.validate_selection(all_tables, all_metrics, all_dims)
