from datetime import datetime, date
from typing import Any, Dict, List, Optional
import uuid
from google.cloud import bigquery
from app.config import settings
from app.services.bigquery_service import BigQueryService
from app.utils.logger import logger


class KnowledgeRepository:
    def __init__(self, bq_service: Optional[BigQueryService] = None):
        self.bq = bq_service or BigQueryService()
        self.project_id = getattr(self.bq, "project_id", None) or settings.GOOGLE_CLOUD_PROJECT
        self.dataset = settings.IDENTITY_DATASET

    def _format_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Convert BigQuery row values to standard Python/JSON serializable types."""
        res = dict(row)
        for k, v in res.items():
            if isinstance(v, (datetime, date)):
                res[k] = v.isoformat()
            elif hasattr(v, "isoformat"):
                res[k] = v.isoformat()
            elif hasattr(v, "tolist"):
                res[k] = v.tolist()

        # Normalize access_control list
        raw_access = res.get("access_control")
        if raw_access is None or (isinstance(raw_access, (list, tuple)) and len(raw_access) == 0):
            aud = str(res.get("audience") or "ALL").upper()
            if aud == "CUSTOMER":
                res["access_control"] = ["CUSTOMER"]
            elif aud == "STAFF":
                res["access_control"] = ["STAFF"]
            else:
                res["access_control"] = ["CUSTOMER", "STAFF"]
        elif isinstance(raw_access, (list, tuple, set)):
            res["access_control"] = [str(x).upper() for x in raw_access]
        elif isinstance(raw_access, str):
            res["access_control"] = [x.strip().upper() for x in raw_access.split(",") if x.strip()]

        return res

    def insert_document(self, doc_data: Dict[str, Any]) -> Dict[str, Any]:
        now = datetime.utcnow().isoformat()
        
        raw_access = doc_data.get("access_control")
        if not raw_access:
            aud = str(doc_data.get("audience") or "ALL").upper()
            if aud == "CUSTOMER":
                raw_access = ["CUSTOMER"]
            elif aud == "STAFF":
                raw_access = ["STAFF"]
            else:
                raw_access = ["CUSTOMER", "STAFF"]
        elif isinstance(raw_access, str):
            raw_access = [x.strip() for x in raw_access.split(",") if x.strip()]
        
        access_control_list = [str(x).upper() for x in raw_access]
        if not access_control_list:
            access_control_list = ["CUSTOMER"]
        
        audience_str = "ALL" if len(access_control_list) > 1 else access_control_list[0]

        row = {
            "document_id": doc_data["document_id"],
            "logical_document_id": doc_data["logical_document_id"],
            "document_name": doc_data["document_name"],
            "original_filename": doc_data["original_filename"],
            "document_type": doc_data["document_type"],
            "product_type": doc_data.get("product_type"),
            "product_id": doc_data.get("product_id"),
            "product_name": doc_data.get("product_name"),
            "version": doc_data["version"],
            "status": doc_data.get("status", "PROCESSING"),
            "effective_from": str(doc_data["effective_from"]),
            "effective_to": str(doc_data["effective_to"]) if doc_data.get("effective_to") else None,
            "region": doc_data.get("region", "IN"),
            "audience": audience_str,
            "access_control": access_control_list,
            "gcs_uri": doc_data["gcs_uri"],
            "rag_file_id": doc_data.get("rag_file_id"),
            "rag_corpus_name": doc_data.get("rag_corpus_name", settings.RAG_CORPUS_NAME),
            "uploaded_by": doc_data["uploaded_by"],
            "uploaded_at": doc_data.get("uploaded_at", now),
            "updated_at": doc_data.get("updated_at", now),
            "ingestion_status": doc_data.get("ingestion_status", "PENDING"),
            "ingestion_error": doc_data.get("ingestion_error"),
            "is_active": doc_data.get("is_active", False),
        }

        query = f"""
            INSERT INTO `{self.project_id}.{self.dataset}.knowledge_documents`
            (
                document_id, logical_document_id, document_name, original_filename,
                document_type, product_type, product_id, product_name,
                version, status, effective_from, effective_to, region,
                audience, access_control, gcs_uri, rag_file_id, rag_corpus_name,
                uploaded_by, uploaded_at, updated_at, ingestion_status,
                ingestion_error, is_active
            )
            VALUES
            (
                @document_id, @logical_document_id, @document_name, @original_filename,
                @document_type, @product_type, @product_id, @product_name,
                @version, @status, CAST(@effective_from AS DATE), CAST(@effective_to AS DATE), @region,
                @audience, @access_control, @gcs_uri, @rag_file_id, @rag_corpus_name,
                @uploaded_by, CAST(@uploaded_at AS TIMESTAMP), CAST(@updated_at AS TIMESTAMP), @ingestion_status,
                @ingestion_error, @is_active
            )
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("document_id", "STRING", row["document_id"]),
                bigquery.ScalarQueryParameter("logical_document_id", "STRING", row["logical_document_id"]),
                bigquery.ScalarQueryParameter("document_name", "STRING", row["document_name"]),
                bigquery.ScalarQueryParameter("original_filename", "STRING", row["original_filename"]),
                bigquery.ScalarQueryParameter("document_type", "STRING", row["document_type"]),
                bigquery.ScalarQueryParameter("product_type", "STRING", row["product_type"]),
                bigquery.ScalarQueryParameter("product_id", "STRING", row["product_id"]),
                bigquery.ScalarQueryParameter("product_name", "STRING", row["product_name"]),
                bigquery.ScalarQueryParameter("version", "STRING", row["version"]),
                bigquery.ScalarQueryParameter("status", "STRING", row["status"]),
                bigquery.ScalarQueryParameter("effective_from", "STRING", row["effective_from"]),
                bigquery.ScalarQueryParameter("effective_to", "STRING", row["effective_to"]),
                bigquery.ScalarQueryParameter("region", "STRING", row["region"]),
                bigquery.ScalarQueryParameter("audience", "STRING", row["audience"]),
                bigquery.ArrayQueryParameter("access_control", "STRING", row["access_control"]),
                bigquery.ScalarQueryParameter("gcs_uri", "STRING", row["gcs_uri"]),
                bigquery.ScalarQueryParameter("rag_file_id", "STRING", row["rag_file_id"]),
                bigquery.ScalarQueryParameter("rag_corpus_name", "STRING", row["rag_corpus_name"]),
                bigquery.ScalarQueryParameter("uploaded_by", "STRING", row["uploaded_by"]),
                bigquery.ScalarQueryParameter("uploaded_at", "STRING", row["uploaded_at"]),
                bigquery.ScalarQueryParameter("updated_at", "STRING", row["updated_at"]),
                bigquery.ScalarQueryParameter("ingestion_status", "STRING", row["ingestion_status"]),
                bigquery.ScalarQueryParameter("ingestion_error", "STRING", row["ingestion_error"]),
                bigquery.ScalarQueryParameter("is_active", "BOOL", row["is_active"]),
            ]
        )
        self.bq.client.query(query, job_config=job_config).result()
        return row

    def get_document_by_id(self, document_id: str) -> Optional[Dict[str, Any]]:
        query = f"""
            SELECT *
            FROM `{self.project_id}.{self.dataset}.knowledge_documents`
            WHERE document_id = @document_id
            LIMIT 1
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("document_id", "STRING", document_id)
            ]
        )
        results = self.bq.execute_query(query, job_config)
        return self._format_row(results[0]) if results else None

    def get_active_document_by_logical_id(self, logical_document_id: str) -> Optional[Dict[str, Any]]:
        query = f"""
            SELECT *
            FROM `{self.project_id}.{self.dataset}.knowledge_documents`
            WHERE logical_document_id = @logical_document_id AND is_active = TRUE
            LIMIT 1
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("logical_document_id", "STRING", logical_document_id)
            ]
        )
        results = self.bq.execute_query(query, job_config)
        return self._format_row(results[0]) if results else None

    def get_versions_by_logical_id(self, logical_document_id: str) -> List[Dict[str, Any]]:
        query = f"""
            SELECT *
            FROM `{self.project_id}.{self.dataset}.knowledge_documents`
            WHERE logical_document_id = @logical_document_id
            ORDER BY uploaded_at DESC
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("logical_document_id", "STRING", logical_document_id)
            ]
        )
        results = self.bq.execute_query(query, job_config)
        return [self._format_row(r) for r in results]

    def check_version_exists(self, logical_document_id: str, version: str) -> bool:
        query = f"""
            SELECT COUNT(1) as cnt
            FROM `{self.project_id}.{self.dataset}.knowledge_documents`
            WHERE logical_document_id = @logical_document_id AND version = @version
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("logical_document_id", "STRING", logical_document_id),
                bigquery.ScalarQueryParameter("version", "STRING", version),
            ]
        )
        results = self.bq.execute_query(query, job_config)
        return results[0]["cnt"] > 0 if results else False

    def list_documents(
        self,
        document_type: Optional[str] = None,
        product_type: Optional[str] = None,
        status: Optional[str] = None,
        is_active: Optional[bool] = None,
        access_scope: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        where_clauses = []
        params = []

        if document_type:
            where_clauses.append("document_type = @document_type")
            params.append(bigquery.ScalarQueryParameter("document_type", "STRING", document_type))
        if product_type:
            where_clauses.append("product_type = @product_type")
            params.append(bigquery.ScalarQueryParameter("product_type", "STRING", product_type))
        if status:
            where_clauses.append("status = @status")
            params.append(bigquery.ScalarQueryParameter("status", "STRING", status))
        if is_active is not None:
            where_clauses.append("is_active = @is_active")
            params.append(bigquery.ScalarQueryParameter("is_active", "BOOL", is_active))
        if access_scope:
            where_clauses.append("@access_scope IN UNNEST(access_control)")
            params.append(bigquery.ScalarQueryParameter("access_scope", "STRING", access_scope.upper()))

        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

        query = f"""
            SELECT *
            FROM `{self.project_id}.{self.dataset}.knowledge_documents`
            {where_sql}
            ORDER BY uploaded_at DESC
            LIMIT {limit} OFFSET {offset}
        """
        job_config = bigquery.QueryJobConfig(query_parameters=params)
        results = self.bq.execute_query(query, job_config)
        return [self._format_row(r) for r in results]

    def update_document_status(
        self,
        document_id: str,
        status: str,
        ingestion_status: str,
        is_active: bool,
        ingestion_error: Optional[str] = None,
        rag_file_id: Optional[str] = None,
    ) -> None:
        query = f"""
            UPDATE `{self.project_id}.{self.dataset}.knowledge_documents`
            SET 
                status = @status,
                ingestion_status = @ingestion_status,
                is_active = @is_active,
                ingestion_error = @ingestion_error,
                rag_file_id = COALESCE(@rag_file_id, rag_file_id),
                updated_at = CURRENT_TIMESTAMP()
            WHERE document_id = @document_id
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("document_id", "STRING", document_id),
                bigquery.ScalarQueryParameter("status", "STRING", status),
                bigquery.ScalarQueryParameter("ingestion_status", "STRING", ingestion_status),
                bigquery.ScalarQueryParameter("is_active", "BOOL", is_active),
                bigquery.ScalarQueryParameter("ingestion_error", "STRING", ingestion_error),
                bigquery.ScalarQueryParameter("rag_file_id", "STRING", rag_file_id),
            ]
        )
        self.bq.client.query(query, job_config=job_config).result()

    def archive_prior_active_versions(
        self,
        logical_document_id: str,
        exclude_document_id: Optional[str] = None,
    ) -> None:
        """Archive any currently active versions for this logical_document_id."""
        query = f"""
            UPDATE `{self.project_id}.{self.dataset}.knowledge_documents`
            SET 
                status = 'ARCHIVED',
                is_active = FALSE,
                updated_at = CURRENT_TIMESTAMP()
            WHERE logical_document_id = @logical_document_id 
              AND is_active = TRUE
        """
        params = [
            bigquery.ScalarQueryParameter("logical_document_id", "STRING", logical_document_id)
        ]
        if exclude_document_id:
            query += " AND document_id != @exclude_document_id"
            params.append(bigquery.ScalarQueryParameter("exclude_document_id", "STRING", exclude_document_id))

        job_config = bigquery.QueryJobConfig(query_parameters=params)
        self.bq.client.query(query, job_config=job_config).result()

    def transition_active_version(
        self,
        new_document_id: str,
        logical_document_id: str,
        rag_file_id: Optional[str] = None,
    ) -> None:
        """
        Atomically archives any currently ACTIVE versions for this logical_document_id,
        and promotes the new version to ACTIVE.
        """
        self.archive_prior_active_versions(logical_document_id, exclude_document_id=new_document_id)

        # Step 2: Activate new version
        activate_query = f"""
            UPDATE `{self.project_id}.{self.dataset}.knowledge_documents`
            SET 
                status = 'ACTIVE',
                is_active = TRUE,
                ingestion_status = 'COMPLETED',
                rag_file_id = COALESCE(@rag_file_id, rag_file_id),
                updated_at = CURRENT_TIMESTAMP()
            WHERE document_id = @new_document_id
        """
        activate_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("new_document_id", "STRING", new_document_id),
                bigquery.ScalarQueryParameter("rag_file_id", "STRING", rag_file_id),
            ]
        )
        self.bq.client.query(activate_query, job_config=activate_config).result()

    def insert_audit_log(
        self,
        document_id: str,
        logical_document_id: str,
        version: str,
        action: str,
        result: str,
        user_id: str,
        details: Optional[str] = None,
    ) -> Dict[str, Any]:
        now = datetime.utcnow().isoformat()
        audit_id = f"aud_{uuid.uuid4().hex[:12]}"
        
        row = {
            "audit_id": audit_id,
            "document_id": document_id,
            "logical_document_id": logical_document_id,
            "version": version,
            "action": action,
            "result": result,
            "user_id": user_id,
            "timestamp": now,
            "details": details,
        }

        try:
            query = f"""
                INSERT INTO `{self.project_id}.{self.dataset}.knowledge_audit_log`
                (audit_id, document_id, logical_document_id, version, action, result, user_id, timestamp, details)
                VALUES
                (@audit_id, @document_id, @logical_document_id, @version, @action, @result, @user_id, CAST(@timestamp AS TIMESTAMP), @details)
            """
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("audit_id", "STRING", row["audit_id"]),
                    bigquery.ScalarQueryParameter("document_id", "STRING", row["document_id"]),
                    bigquery.ScalarQueryParameter("logical_document_id", "STRING", row["logical_document_id"]),
                    bigquery.ScalarQueryParameter("version", "STRING", row["version"]),
                    bigquery.ScalarQueryParameter("action", "STRING", row["action"]),
                    bigquery.ScalarQueryParameter("result", "STRING", row["result"]),
                    bigquery.ScalarQueryParameter("user_id", "STRING", row["user_id"]),
                    bigquery.ScalarQueryParameter("timestamp", "STRING", row["timestamp"]),
                    bigquery.ScalarQueryParameter("details", "STRING", row["details"]),
                ]
            )
            self.bq.client.query(query, job_config=job_config).result()
        except Exception as e:
            logger.error(f"Failed to insert knowledge audit log: {e}")
        return row

    def get_audit_logs_for_document(self, logical_document_id: str) -> List[Dict[str, Any]]:
        query = f"""
            SELECT *
            FROM `{self.project_id}.{self.dataset}.knowledge_audit_log`
            WHERE logical_document_id = @logical_document_id
            ORDER BY timestamp DESC
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("logical_document_id", "STRING", logical_document_id)
            ]
        )
        results = self.bq.execute_query(query, job_config)
        return [self._format_row(r) for r in results]

    def get_active_documents_by_gcs_uris(self, gcs_uris: List[str]) -> Dict[str, Dict[str, Any]]:
        if not gcs_uris:
            return {}

        query = f"""
            SELECT *
            FROM `{self.project_id}.{self.dataset}.knowledge_documents`
            WHERE gcs_uri IN UNNEST(@gcs_uris) AND is_active = TRUE
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ArrayQueryParameter("gcs_uris", "STRING", gcs_uris)
            ]
        )
        results = self.bq.execute_query(query, job_config)
        return {r["gcs_uri"]: self._format_row(r) for r in results}


knowledge_repository = KnowledgeRepository()
