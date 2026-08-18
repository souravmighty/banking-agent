import os
import yaml
import threading
from typing import List, Dict, Optional, Any
from pathlib import Path

from app.core.config import settings
from app.core.logging import logger
from app.models.table import TableMetadata, ObjectType, SCDType
from app.models.column import ColumnMetadata, SemanticType, SensitivityLevel
from app.models.metric import MetricMetadata
from app.models.dimension import DimensionMetadata, DimensionHierarchy
from app.models.relationship import TableRelationship, RelationshipType
from app.models.business_term import BusinessTerm
from app.models.query_guidance import QueryGuidanceRule, RuleType
from app.utils.normalization import normalize_name

class MetadataRepository:
    """
    Manages loading, merging, caching, and querying of analytical metadata
    from curated YAML configurations and runtime synchronization.
    """
    def __init__(self, metadata_dir: Optional[str] = None):
        self.metadata_dir = Path(metadata_dir or settings.METADATA_DIR)
        self._lock = threading.RLock()
        
        # In-memory stores
        self._tables: Dict[str, TableMetadata] = {}
        self._metrics: Dict[str, MetricMetadata] = {}
        self._dimensions: Dict[str, DimensionMetadata] = {}
        self._relationships: List[TableRelationship] = []
        self._business_terms: List[BusinessTerm] = []
        self._query_guidance: List[QueryGuidanceRule] = []
        
        self.load_curated_metadata()

    def load_curated_metadata(self) -> None:
        """Loads all YAML configurations from the metadata directory."""
        with self._lock:
            try:
                self._load_tables_yaml()
                self._load_metrics_yaml()
                self._load_dimensions_yaml()
                self._load_relationships_yaml()
                self._load_business_terms_yaml()
                self._load_query_guidance_yaml()
                logger.info(
                    f"Curated metadata loaded: {len(self._tables)} tables, "
                    f"{len(self._metrics)} metrics, {len(self._dimensions)} dimensions, "
                    f"{len(self._relationships)} relationships."
                )
            except Exception as e:
                logger.error(f"Failed loading curated metadata from {self.metadata_dir}: {str(e)}")

    def _load_tables_yaml(self) -> None:
        filepath = self.metadata_dir / "tables.yaml"
        if not filepath.exists():
            return
        with open(filepath, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
            
        tables_list = data.get("tables", [])
        for t_dict in tables_list:
            cols: List[ColumnMetadata] = []
            for c_dict in t_dict.get("columns", []):
                sem_type = None
                if c_dict.get("semantic_type"):
                    try:
                        sem_type = SemanticType(c_dict["semantic_type"])
                    except ValueError:
                        sem_type = SemanticType.OTHER

                sens_level = SensitivityLevel.INTERNAL
                if c_dict.get("sensitivity_level"):
                    try:
                        sens_level = SensitivityLevel(c_dict["sensitivity_level"])
                    except ValueError:
                        sens_level = SensitivityLevel.INTERNAL

                col = ColumnMetadata(
                    column_name=c_dict.get("column_name"),
                    data_type=c_dict.get("data_type", "STRING"),
                    nullable=c_dict.get("nullable", True),
                    ordinal_position=c_dict.get("ordinal_position", 0),
                    description=c_dict.get("description"),
                    business_description=c_dict.get("business_description"),
                    semantic_type=sem_type,
                    is_primary_key=c_dict.get("is_primary_key", False),
                    is_foreign_key=c_dict.get("is_foreign_key", False),
                    references_table=c_dict.get("references_table"),
                    references_column=c_dict.get("references_column"),
                    is_metric=c_dict.get("is_metric", False),
                    is_dimension=c_dict.get("is_dimension", False),
                    is_filterable=c_dict.get("is_filterable", True),
                    is_groupable=c_dict.get("is_groupable", False),
                    is_sortable=c_dict.get("is_sortable", True),
                    is_time_dimension=c_dict.get("is_time_dimension", False),
                    is_sensitive=c_dict.get("is_sensitive", False),
                    sensitivity_level=sens_level,
                    allowed_aggregations=c_dict.get("allowed_aggregations", []),
                    default_aggregation=c_dict.get("default_aggregation"),
                    example_values=c_dict.get("example_values"),
                    tags=c_dict.get("tags", []),
                )
                cols.append(col)

            scd_type = SCDType.NONE
            if t_dict.get("scd_type"):
                try:
                    scd_type = SCDType(t_dict["scd_type"])
                except ValueError:
                    scd_type = SCDType.NONE

            sens_lvl = SensitivityLevel.INTERNAL
            if t_dict.get("sensitivity_level"):
                try:
                    sens_lvl = SensitivityLevel(t_dict["sensitivity_level"])
                except ValueError:
                    sens_lvl = SensitivityLevel.INTERNAL

            obj_type = ObjectType.TABLE
            if t_dict.get("object_type"):
                try:
                    obj_type = ObjectType(t_dict["object_type"])
                except ValueError:
                    obj_type = ObjectType.TABLE

            table_meta = TableMetadata(
                project_id=t_dict.get("project_id", settings.GOOGLE_CLOUD_PROJECT),
                dataset_name=t_dict.get("dataset_name", settings.BIGQUERY_DATASET),
                table_name=t_dict.get("table_name"),
                object_type=obj_type,
                description=t_dict.get("description"),
                business_domain=t_dict.get("business_domain"),
                business_entity=t_dict.get("business_entity"),
                business_purpose=t_dict.get("business_purpose"),
                grain=t_dict.get("grain"),
                scd_type=scd_type,
                natural_key=t_dict.get("natural_key", []),
                primary_key=t_dict.get("primary_key", []),
                preferred_analytics_source=t_dict.get("preferred_analytics_source", False),
                allowed_for_analytics=t_dict.get("allowed_for_analytics", True),
                allowed_for_nl2sql=t_dict.get("allowed_for_nl2sql", True),
                allowed_for_visualization=t_dict.get("allowed_for_visualization", True),
                sensitivity_level=sens_lvl,
                data_owner=t_dict.get("data_owner"),
                partitioning=t_dict.get("partitioning"),
                clustering_columns=t_dict.get("clustering_columns", []),
                effective_from_column=t_dict.get("effective_from_column"),
                effective_to_column=t_dict.get("effective_to_column"),
                current_flag_column=t_dict.get("current_flag_column"),
                tags=t_dict.get("tags", []),
                columns=cols,
            )
            self._tables[normalize_name(table_meta.table_name)] = table_meta

    def _load_metrics_yaml(self) -> None:
        filepath = self.metadata_dir / "metrics.yaml"
        if not filepath.exists():
            return
        with open(filepath, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
            
        for m_dict in data.get("metrics", []):
            metric = MetricMetadata(
                metric_name=m_dict.get("metric_name"),
                display_name=m_dict.get("display_name", m_dict.get("metric_name")),
                description=m_dict.get("description", ""),
                business_definition=m_dict.get("business_definition", ""),
                sql_expression=m_dict.get("sql_expression"),
                default_aggregation=m_dict.get("default_aggregation", "SUM"),
                data_type=m_dict.get("data_type", "FLOAT"),
                unit=m_dict.get("unit"),
                source_tables=m_dict.get("source_tables", []),
                allowed_dimensions=m_dict.get("allowed_dimensions", []),
                allowed_filters=m_dict.get("allowed_filters", []),
                is_ratio=m_dict.get("is_ratio", False),
                numerator_metric=m_dict.get("numerator_metric"),
                denominator_metric=m_dict.get("denominator_metric"),
                calculation_notes=m_dict.get("calculation_notes"),
                tags=m_dict.get("tags", []),
            )
            self._metrics[normalize_name(metric.metric_name)] = metric

    def _load_dimensions_yaml(self) -> None:
        filepath = self.metadata_dir / "dimensions.yaml"
        if not filepath.exists():
            return
        with open(filepath, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        for d_dict in data.get("dimensions", []):
            h_obj = None
            if d_dict.get("hierarchy"):
                h_data = d_dict["hierarchy"]
                h_obj = DimensionHierarchy(
                    level=h_data.get("level", 1),
                    parent=h_data.get("parent"),
                    children=h_data.get("children", []),
                    levels=h_data.get("levels", []),
                )
            dim = DimensionMetadata(
                dimension_name=d_dict.get("dimension_name"),
                display_name=d_dict.get("display_name", d_dict.get("dimension_name")),
                description=d_dict.get("description", ""),
                source_table=d_dict.get("source_table", ""),
                source_column=d_dict.get("source_column", ""),
                data_type=d_dict.get("data_type", "STRING"),
                allowed_filters=d_dict.get("allowed_filters", []),
                allowed_grouping=d_dict.get("allowed_grouping", True),
                hierarchy=h_obj,
                tags=d_dict.get("tags", []),
            )
            self._dimensions[normalize_name(dim.dimension_name)] = dim

    def _load_relationships_yaml(self) -> None:
        filepath = self.metadata_dir / "relationships.yaml"
        if not filepath.exists():
            return
        with open(filepath, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        self._relationships = []
        for r_dict in data.get("relationships", []):
            rel_type = RelationshipType.ONE_TO_MANY
            if r_dict.get("relationship_type"):
                try:
                    rel_type = RelationshipType(r_dict["relationship_type"])
                except ValueError:
                    rel_type = RelationshipType.ONE_TO_MANY

            rel = TableRelationship(
                left_table=r_dict.get("left_table"),
                left_column=r_dict.get("left_column"),
                right_table=r_dict.get("right_table"),
                right_column=r_dict.get("right_column"),
                relationship_type=rel_type,
                business_description=r_dict.get("business_description", ""),
                allowed_for_analytics=r_dict.get("allowed_for_analytics", True),
                join_warning=r_dict.get("join_warning"),
                join_sql_template=r_dict.get("join_sql_template"),
            )
            self._relationships.append(rel)

    def _load_business_terms_yaml(self) -> None:
        filepath = self.metadata_dir / "business_terms.yaml"
        if not filepath.exists():
            return
        with open(filepath, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        self._business_terms = []
        for bt_dict in data.get("business_terms", []):
            bt = BusinessTerm(
                term=bt_dict.get("term"),
                mapped_metric=bt_dict.get("mapped_metric"),
                mapped_dimension=bt_dict.get("mapped_dimension"),
                mapped_table=bt_dict.get("mapped_table"),
                definition=bt_dict.get("definition", ""),
                synonyms=bt_dict.get("synonyms", []),
            )
            self._business_terms.append(bt)

    def _load_query_guidance_yaml(self) -> None:
        filepath = self.metadata_dir / "query_guidance.yaml"
        if not filepath.exists():
            return
        with open(filepath, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        self._query_guidance = []
        for q_dict in data.get("rules", []):
            r_type = RuleType.GENERAL
            if q_dict.get("rule_type"):
                try:
                    r_type = RuleType(q_dict["rule_type"])
                except ValueError:
                    r_type = RuleType.GENERAL

            rule = QueryGuidanceRule(
                id=q_dict.get("id", "QG"),
                title=q_dict.get("title", ""),
                target_tables=q_dict.get("target_tables", []),
                target_metrics=q_dict.get("target_metrics", []),
                rule_type=r_type,
                rule_text=q_dict.get("rule_text", ""),
                sql_snippet=q_dict.get("sql_snippet"),
            )
            self._query_guidance.append(rule)

    def merge_technical_metadata(self, discovered_tables: List[TableMetadata]) -> int:
        """
        Merges technical metadata discovered from BigQuery into the curated catalog.
        Curated business fields take precedence; technical properties are updated.
        """
        with self._lock:
            updated_count = 0
            for disc_table in discovered_tables:
                norm_name = normalize_name(disc_table.table_name)
                if norm_name in self._tables:
                    existing = self._tables[norm_name]
                    # Update technical fields
                    existing.project_id = disc_table.project_id or existing.project_id
                    existing.dataset_name = disc_table.dataset_name or existing.dataset_name
                    existing.object_type = disc_table.object_type or existing.object_type
                    if not existing.description and disc_table.description:
                        existing.description = disc_table.description
                    if disc_table.partitioning:
                        existing.partitioning = disc_table.partitioning
                    if disc_table.clustering_columns:
                        existing.clustering_columns = disc_table.clustering_columns
                    existing.created_at = disc_table.created_at or existing.created_at
                    existing.modified_at = disc_table.modified_at or existing.modified_at
                    
                    # Merge columns
                    disc_col_map = {normalize_name(c.column_name): c for c in disc_table.columns}
                    for existing_col in existing.columns:
                        c_norm = normalize_name(existing_col.column_name)
                        if c_norm in disc_col_map:
                            disc_c = disc_col_map[c_norm]
                            existing_col.data_type = disc_c.data_type
                            existing_col.nullable = disc_c.nullable
                            existing_col.ordinal_position = disc_c.ordinal_position
                            if not existing_col.description and disc_c.description:
                                existing_col.description = disc_c.description
                    
                    # Add any newly discovered columns not in curated
                    existing_col_names = {normalize_name(c.column_name) for c in existing.columns}
                    for disc_c in disc_table.columns:
                        if normalize_name(disc_c.column_name) not in existing_col_names:
                            existing.columns.append(disc_c)
                            
                    updated_count += 1
                else:
                    # New discovered table without prior curation
                    self._tables[norm_name] = disc_table
                    updated_count += 1
            return updated_count

    # Accessor methods
    def get_all_tables(self) -> List[TableMetadata]:
        with self._lock:
            return list(self._tables.values())

    def get_table(self, table_name: str) -> Optional[TableMetadata]:
        with self._lock:
            return self._tables.get(normalize_name(table_name))

    def get_all_metrics(self) -> List[MetricMetadata]:
        with self._lock:
            return list(self._metrics.values())

    def get_metric(self, metric_name: str) -> Optional[MetricMetadata]:
        with self._lock:
            return self._metrics.get(normalize_name(metric_name))

    def get_all_dimensions(self) -> List[DimensionMetadata]:
        with self._lock:
            return list(self._dimensions.values())

    def get_dimension(self, dimension_name: str) -> Optional[DimensionMetadata]:
        with self._lock:
            return self._dimensions.get(normalize_name(dimension_name))

    def get_all_relationships(self) -> List[TableRelationship]:
        with self._lock:
            return list(self._relationships)

    def get_relationships_for_tables(self, table_names: List[str]) -> List[TableRelationship]:
        with self._lock:
            norm_tables = {normalize_name(t) for t in table_names}
            return [
                r for r in self._relationships
                if normalize_name(r.left_table) in norm_tables or normalize_name(r.right_table) in norm_tables
            ]

    def get_all_business_terms(self) -> List[BusinessTerm]:
        with self._lock:
            return list(self._business_terms)

    def get_all_query_guidance(self) -> List[QueryGuidanceRule]:
        with self._lock:
            return list(self._query_guidance)

    def get_query_guidance_for_assets(self, table_names: List[str], metric_names: List[str]) -> List[QueryGuidanceRule]:
        with self._lock:
            norm_tables = {normalize_name(t) for t in table_names}
            norm_metrics = {normalize_name(m) for m in metric_names}
            matched: List[QueryGuidanceRule] = []
            for rule in self._query_guidance:
                rule_tables = {normalize_name(t) for t in rule.target_tables}
                rule_metrics = {normalize_name(m) for m in rule.target_metrics}
                if rule_tables.intersection(norm_tables) or rule_metrics.intersection(norm_metrics) or (not rule.target_tables and not rule.target_metrics):
                    matched.append(rule)
            return matched
