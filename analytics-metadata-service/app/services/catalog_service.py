from typing import Optional, List, Dict
from datetime import datetime, timezone
from app.repositories.metadata_repository import MetadataRepository
from app.models.catalog import (
    CompactCatalogResponse,
    CompactTableCatalogEntry,
    CompactMetricCatalogEntry,
    CompactDimensionCatalogEntry,
)
from app.utils.normalization import normalize_name

class CatalogService:
    """
    Generates compact semantic catalogs optimized for LLM Analytics Planner reasoning.
    """
    def __init__(self, repository: MetadataRepository):
        self.repository = repository

    def get_compact_catalog(self, domain: Optional[str] = None) -> CompactCatalogResponse:
        tables = self.repository.get_all_tables()
        metrics = self.repository.get_all_metrics()
        dimensions = self.repository.get_all_dimensions()
        relationships = self.repository.get_all_relationships()
        
        # Build relationship mapping for fast related_tables lookup
        rel_map: Dict[str, List[str]] = {}
        for r in relationships:
            left_norm = normalize_name(r.left_table)
            right_norm = normalize_name(r.right_table)
            if left_norm not in rel_map:
                rel_map[left_norm] = []
            if right_norm not in rel_map:
                rel_map[right_norm] = []
            if r.right_table not in rel_map[left_norm]:
                rel_map[left_norm].append(r.right_table)
            if r.left_table not in rel_map[right_norm]:
                rel_map[right_norm].append(r.left_table)
                
        # Build key metrics mapping per table
        table_metric_map: Dict[str, List[str]] = {}
        for m in metrics:
            for st in m.source_tables:
                st_norm = normalize_name(st)
                if st_norm not in table_metric_map:
                    table_metric_map[st_norm] = []
                table_metric_map[st_norm].append(m.metric_name)
                
        # Build key dimensions per table
        table_dim_map: Dict[str, List[str]] = {}
        for d in dimensions:
            st_norm = normalize_name(d.source_table)
            if st_norm not in table_dim_map:
                table_dim_map[st_norm] = []
            table_dim_map[st_norm].append(d.dimension_name)

        compact_tables: List[CompactTableCatalogEntry] = []
        for t in tables:
            # Filter domain if requested
            if domain and t.business_domain and t.business_domain.upper() != domain.upper():
                continue
                
            t_norm = normalize_name(t.table_name)
            
            # Key dimensions: derived from columns marked is_dimension + explicit dimensions catalog
            k_dims = set(table_dim_map.get(t_norm, []))
            for c in t.columns:
                if c.is_dimension and not c.is_sensitive:
                    k_dims.add(c.column_name)
                    
            entry = CompactTableCatalogEntry(
                table=t.table_name,
                dataset=t.dataset_name,
                description=t.description,
                business_domain=t.business_domain,
                business_entity=t.business_entity,
                grain=t.grain,
                preferred_analytics_source=t.preferred_analytics_source,
                key_metrics=table_metric_map.get(t_norm, []),
                key_dimensions=sorted(list(k_dims)),
                related_tables=rel_map.get(t_norm, []),
                scd_type=t.scd_type.value if hasattr(t.scd_type, "value") else str(t.scd_type),
                sensitivity_level=t.sensitivity_level.value if hasattr(t.sensitivity_level, "value") else str(t.sensitivity_level),
                allowed_for_analytics=t.allowed_for_analytics,
                allowed_for_nl2sql=t.allowed_for_nl2sql,
            )
            compact_tables.append(entry)

        compact_metrics: List[CompactMetricCatalogEntry] = []
        for m in metrics:
            c_metric = CompactMetricCatalogEntry(
                metric=m.metric_name,
                display_name=m.display_name,
                description=m.description,
                business_definition=m.business_definition,
                source_tables=m.source_tables,
                allowed_dimensions=m.allowed_dimensions,
                default_aggregation=m.default_aggregation,
                unit=m.unit,
            )
            compact_metrics.append(c_metric)

        compact_dimensions: List[CompactDimensionCatalogEntry] = []
        for d in dimensions:
            h_levels = d.hierarchy.levels if d.hierarchy else None
            c_dim = CompactDimensionCatalogEntry(
                dimension=d.dimension_name,
                description=d.description,
                source=f"{d.source_table}.{d.source_column}",
                hierarchy=h_levels,
            )
            compact_dimensions.append(c_dim)

        return CompactCatalogResponse(
            tables=compact_tables,
            metrics=compact_metrics,
            dimensions=compact_dimensions,
            version="1.0.0",
            generated_at=datetime.now(timezone.utc),
        )
