from typing import List, Optional
from app.repositories.metadata_repository import MetadataRepository
from app.models.search import (
    SearchRequest,
    SearchResponse,
    SearchResultItem,
    SearchResultType,
)
from app.utils.normalization import tokenize_text, compute_text_relevance

class MetadataSearchService:
    """
    Search engine for discovering tables, columns, metrics, dimensions, and business terms.
    Designed with a deterministic keyword/token matching implementation and extensible
    for semantic/vector embeddings.
    """
    def __init__(self, repository: MetadataRepository):
        self.repository = repository

    def search(self, request: SearchRequest) -> SearchResponse:
        query = request.query.strip()
        query_tokens = tokenize_text(query)
        allowed_types = set(request.types) if request.types else None

        results: List[SearchResultItem] = []

        # 1. Search Business Terms
        if not allowed_types or SearchResultType.BUSINESS_TERM in allowed_types:
            for bt in self.repository.get_all_business_terms():
                # Check term itself
                term_score = compute_text_relevance(query_tokens, bt.term)
                if term_score > 0:
                    results.append(SearchResultItem(
                        item_type=SearchResultType.BUSINESS_TERM,
                        name=bt.term,
                        display_name=bt.term,
                        description=bt.definition,
                        score=term_score + 0.3,  # Boost business term direct hits
                        matched_field="term",
                        matched_text=bt.term,
                        metadata={
                            "mapped_metric": bt.mapped_metric,
                            "mapped_dimension": bt.mapped_dimension,
                            "mapped_table": bt.mapped_table,
                        }
                    ))
                    continue
                # Check synonyms
                for syn in bt.synonyms:
                    syn_score = compute_text_relevance(query_tokens, syn)
                    if syn_score > 0:
                        results.append(SearchResultItem(
                            item_type=SearchResultType.BUSINESS_TERM,
                            name=bt.term,
                            display_name=bt.term,
                            description=bt.definition,
                            score=syn_score + 0.2,
                            matched_field="synonym",
                            matched_text=syn,
                            metadata={
                                "mapped_metric": bt.mapped_metric,
                                "mapped_dimension": bt.mapped_dimension,
                                "mapped_table": bt.mapped_table,
                            }
                        ))
                        break

        # 2. Search Metrics
        if not allowed_types or SearchResultType.METRIC in allowed_types:
            for m in self.repository.get_all_metrics():
                score = max(
                    compute_text_relevance(query_tokens, m.metric_name) * 1.2,
                    compute_text_relevance(query_tokens, m.display_name) * 1.1,
                    compute_text_relevance(query_tokens, m.business_definition),
                    compute_text_relevance(query_tokens, m.description),
                )
                if score > 0:
                    matched_f = "metric_name" if compute_text_relevance(query_tokens, m.metric_name) > 0 else "business_definition"
                    results.append(SearchResultItem(
                        item_type=SearchResultType.METRIC,
                        name=m.metric_name,
                        display_name=m.display_name,
                        description=m.business_definition or m.description,
                        score=score,
                        matched_field=matched_f,
                        matched_text=m.metric_name if matched_f == "metric_name" else m.business_definition,
                        metadata={
                            "source_tables": m.source_tables,
                            "sql_expression": m.sql_expression,
                            "default_aggregation": m.default_aggregation,
                        }
                    ))

        # 3. Search Tables
        if not allowed_types or SearchResultType.TABLE in allowed_types:
            for t in self.repository.get_all_tables():
                score = max(
                    compute_text_relevance(query_tokens, t.table_name) * 1.2,
                    compute_text_relevance(query_tokens, t.description or ""),
                    compute_text_relevance(query_tokens, t.business_purpose or ""),
                    compute_text_relevance(query_tokens, " ".join(t.tags)),
                )
                if score > 0:
                    matched_f = "table_name" if compute_text_relevance(query_tokens, t.table_name) > 0 else "description"
                    results.append(SearchResultItem(
                        item_type=SearchResultType.TABLE,
                        name=t.table_name,
                        display_name=t.table_name,
                        description=t.description or "",
                        score=score,
                        matched_field=matched_f,
                        matched_text=t.table_name if matched_f == "table_name" else (t.description or ""),
                        metadata={
                            "dataset": t.dataset_name,
                            "business_domain": t.business_domain,
                            "grain": t.grain,
                            "scd_type": t.scd_type.value if hasattr(t.scd_type, "value") else str(t.scd_type),
                            "preferred_analytics_source": t.preferred_analytics_source,
                        }
                    ))

                # 4. Search Columns within tables
                if not allowed_types or SearchResultType.COLUMN in allowed_types:
                    for col in t.columns:
                        c_score = max(
                            compute_text_relevance(query_tokens, col.column_name) * 1.1,
                            compute_text_relevance(query_tokens, col.business_description or ""),
                            compute_text_relevance(query_tokens, col.description or ""),
                        )
                        if c_score > 0:
                            results.append(SearchResultItem(
                                item_type=SearchResultType.COLUMN,
                                name=f"{t.table_name}.{col.column_name}",
                                display_name=col.column_name,
                                description=col.business_description or col.description or "",
                                parent_table=t.table_name,
                                score=c_score * 0.9,
                                matched_field="column_name",
                                matched_text=col.column_name,
                                metadata={
                                    "data_type": col.data_type,
                                    "semantic_type": col.semantic_type.value if col.semantic_type else None,
                                    "is_metric": col.is_metric,
                                    "is_dimension": col.is_dimension,
                                }
                            ))

        # 5. Search Dimensions
        if not allowed_types or SearchResultType.DIMENSION in allowed_types:
            for d in self.repository.get_all_dimensions():
                d_score = max(
                    compute_text_relevance(query_tokens, d.dimension_name) * 1.1,
                    compute_text_relevance(query_tokens, d.description),
                )
                if d_score > 0:
                    results.append(SearchResultItem(
                        item_type=SearchResultType.DIMENSION,
                        name=d.dimension_name,
                        display_name=d.display_name,
                        description=d.description,
                        parent_table=d.source_table,
                        score=d_score,
                        matched_field="dimension_name",
                        matched_text=d.dimension_name,
                        metadata={
                            "source_column": d.source_column,
                            "hierarchy": d.hierarchy.levels if d.hierarchy else None,
                        }
                    ))

        # Sort by score descending and deduplicate by name+type
        results.sort(key=lambda x: x.score, reverse=True)
        
        seen = set()
        deduped: List[SearchResultItem] = []
        for r in results:
            key = (r.item_type, r.name)
            if key not in seen:
                seen.add(key)
                deduped.append(r)

        top_results = deduped[:request.top_k]

        return SearchResponse(
            query=request.query,
            total_results=len(deduped),
            results=top_results,
        )
