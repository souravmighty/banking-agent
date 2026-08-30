from datetime import date, datetime
from typing import Any, Dict, List, Optional
import uuid
from app.config import settings
from app.repositories.knowledge_repository import KnowledgeRepository, knowledge_repository
from app.schemas.knowledge import (
    DocumentStatus,
    DocumentType,
    IngestionStatus,
    KnowledgeDocumentResponse,
    KnowledgeRetrievedContext,
    ProductType,
)
from app.services.document_storage_service import DocumentStorageService, document_storage_service
from app.services.rag_service import RAGService, rag_service
from app.utils.logger import logger
from app.utils.exceptions import CustomerIdentityException


class KnowledgeService:
    def __init__(
        self,
        repository: Optional[KnowledgeRepository] = None,
        storage_svc: Optional[DocumentStorageService] = None,
        rag_svc: Optional[RAGService] = None,
    ):
        self.repo = repository or knowledge_repository
        self.storage = storage_svc or document_storage_service
        self.rag = rag_svc or rag_service

    def upload_document(
        self,
        file_content: bytes,
        filename: str,
        logical_document_id: str,
        document_name: str,
        document_type: str,
        version: str,
        effective_from: str,
        uploaded_by: str,
        product_type: Optional[str] = None,
        product_id: Optional[str] = None,
        product_name: Optional[str] = None,
        effective_to: Optional[str] = None,
        region: str = "IN",
        access_control: Optional[List[str]] = None,
        audience: Optional[str] = None,
        content_type: Optional[str] = None,
        background_tasks: Optional[Any] = None,
    ) -> Dict[str, Any]:
        # Validate inputs
        if not logical_document_id or not document_name or not version:
            raise CustomerIdentityException(
                status_code=400,
                detail="logical_document_id, document_name, and version are required"
            )

        # Normalize and validate access_control
        if access_control is not None:
            if isinstance(access_control, str):
                access_control = [x.strip().upper() for x in access_control.split(",") if x.strip()]
            if len(access_control) == 0:
                raise CustomerIdentityException(
                    status_code=400,
                    detail="At least one valid access scope ('CUSTOMER' or 'STAFF') is required."
                )
        else:
            if audience:
                aud = str(audience).upper()
                access_control = ["CUSTOMER", "STAFF"] if aud == "ALL" else [aud]
            else:
                access_control = ["CUSTOMER", "STAFF"]

        normalized_access = []
        for ac in access_control:
            ac_upper = str(ac).strip().upper()
            if ac_upper in ("CUSTOMER", "STAFF"):
                if ac_upper not in normalized_access:
                    normalized_access.append(ac_upper)
            else:
                raise CustomerIdentityException(
                    status_code=400,
                    detail=f"Invalid access control values: '{ac}'. Supported values are 'CUSTOMER', 'STAFF'."
                )

        if not normalized_access:
            raise CustomerIdentityException(
                status_code=400,
                detail="At least one valid access scope ('CUSTOMER' or 'STAFF') is required."
            )

        # Check version uniqueness for this logical document
        if self.repo.check_version_exists(logical_document_id, version):
            raise CustomerIdentityException(
                status_code=409,
                detail=f"Version '{version}' already exists for document '{logical_document_id}'"
            )

        document_id = f"doc_{uuid.uuid4().hex[:12]}"

        # Step 1: Upload to GCS
        try:
            gcs_uri = self.storage.upload_file(
                content=file_content,
                filename=filename,
                document_type=document_type,
                logical_document_id=logical_document_id,
                version=version,
                content_type=content_type,
                product_type=product_type,
            )
        except Exception as e:
            logger.error(f"GCS storage upload failed: {e}")
            raise

        # Step 2: Register initial record in BigQuery as PROCESSING / INDEXING
        audience_str = "ALL" if len(normalized_access) > 1 else normalized_access[0]
        doc_record = {
            "document_id": document_id,
            "logical_document_id": logical_document_id,
            "document_name": document_name,
            "original_filename": filename,
            "document_type": document_type,
            "product_type": product_type,
            "product_id": product_id,
            "product_name": product_name,
            "version": version,
            "status": DocumentStatus.PROCESSING.value,
            "effective_from": effective_from,
            "effective_to": effective_to,
            "region": region,
            "audience": audience_str,
            "access_control": normalized_access,
            "gcs_uri": gcs_uri,
            "rag_corpus_name": settings.RAG_CORPUS_NAME,
            "uploaded_by": uploaded_by,
            "ingestion_status": IngestionStatus.INDEXING.value,
            "is_active": False,
        }
        self.repo.insert_document(doc_record)
        self.repo.insert_audit_log(
            document_id=document_id,
            logical_document_id=logical_document_id,
            version=version,
            action="UPLOAD_COMPLETED",
            result="SUCCESS",
            user_id=uploaded_by,
            details=f"Uploaded {filename} to {gcs_uri}. Background RAG indexing started.",
        )

        # Step 3: Trigger background RAG indexing
        if background_tasks:
            background_tasks.add_task(
                self.process_background_ingestion,
                document_id=document_id,
                gcs_uri=gcs_uri,
                logical_document_id=logical_document_id,
                version=version,
                user_id=uploaded_by,
            )
        else:
            import threading
            thread = threading.Thread(
                target=self.process_background_ingestion,
                kwargs={
                    "document_id": document_id,
                    "gcs_uri": gcs_uri,
                    "logical_document_id": logical_document_id,
                    "version": version,
                    "user_id": uploaded_by,
                },
                daemon=True,
            )
            thread.start()

        return self.repo.get_document_by_id(document_id) or doc_record

    def process_background_ingestion(
        self,
        document_id: str,
        gcs_uri: str,
        logical_document_id: str,
        version: str,
        user_id: str,
    ) -> None:
        """Executes RAG ingestion in background and promotes version upon completion."""
        try:
            logger.info(f"Starting background RAG ingestion for document {document_id} ({gcs_uri})...")
            import_res = self.rag.import_file_from_gcs(
                gcs_uri=gcs_uri,
                chunk_size=512,
                chunk_overlap=50,
            )
            rag_file_id = import_res.get("rag_file_id")

            # Atomically transition active version
            self.repo.transition_active_version(
                new_document_id=document_id,
                logical_document_id=logical_document_id,
                rag_file_id=rag_file_id,
            )

            self.repo.insert_audit_log(
                document_id=document_id,
                logical_document_id=logical_document_id,
                version=version,
                action="ACTIVATE_VERSION",
                result="SUCCESS",
                user_id=user_id,
                details="Background RAG ingestion completed and promoted to ACTIVE version.",
            )
            logger.info(f"Background RAG ingestion successfully activated document {document_id}")
        except Exception as e:
            err_msg = str(e)
            logger.error(f"Background RAG indexing failed for document {document_id}: {err_msg}")
            try:
                self.repo.update_document_status(
                    document_id=document_id,
                    status=DocumentStatus.FAILED.value,
                    ingestion_status=IngestionStatus.FAILED.value,
                    is_active=False,
                    ingestion_error=err_msg,
                )
            except Exception as ue:
                logger.error(f"Failed to update document failure status: {ue}")

            self.repo.insert_audit_log(
                document_id=document_id,
                logical_document_id=logical_document_id,
                version=version,
                action="INGESTION_FAILED",
                result="FAILURE",
                user_id=user_id,
                details=f"Background ingestion failed: {err_msg}",
            )

    def retry_ingestion(
        self,
        document_id: str,
        user_id: str,
        background_tasks: Optional[Any] = None,
    ) -> Dict[str, Any]:
        doc = self.repo.get_document_by_id(document_id)
        if not doc:
            raise CustomerIdentityException(
                status_code=404,
                detail=f"Document {document_id} not found"
            )

        if doc.get("status") not in [DocumentStatus.FAILED.value, DocumentStatus.PROCESSING.value]:
            raise CustomerIdentityException(
                status_code=400,
                detail=f"Document {document_id} is already in state '{doc.get('status')}'"
            )

        self.repo.update_document_status(
            document_id=document_id,
            status=DocumentStatus.PROCESSING.value,
            ingestion_status=IngestionStatus.INDEXING.value,
            is_active=False,
            ingestion_error=None,
        )

        self.repo.insert_audit_log(
            document_id=document_id,
            logical_document_id=doc["logical_document_id"],
            version=doc["version"],
            action="RETRY_INDEXING",
            result="QUEUED",
            user_id=user_id,
            details="Retrying RAG ingestion indexing in background.",
        )

        if background_tasks:
            background_tasks.add_task(
                self.process_background_ingestion,
                document_id=document_id,
                gcs_uri=doc["gcs_uri"],
                logical_document_id=doc["logical_document_id"],
                version=doc["version"],
                user_id=user_id,
            )
        else:
            import threading
            thread = threading.Thread(
                target=self.process_background_ingestion,
                kwargs={
                    "document_id": document_id,
                    "gcs_uri": doc["gcs_uri"],
                    "logical_document_id": doc["logical_document_id"],
                    "version": doc["version"],
                    "user_id": user_id,
                },
                daemon=True,
            )
            thread.start()

        return self.repo.get_document_by_id(document_id)

    def archive_document(self, document_id: str, user_id: str) -> Dict[str, Any]:
        doc = self.repo.get_document_by_id(document_id)
        if not doc:
            raise CustomerIdentityException(
                status_code=404,
                detail=f"Document {document_id} not found"
            )

        self.repo.update_document_status(
            document_id=document_id,
            status=DocumentStatus.ARCHIVED.value,
            ingestion_status=doc.get("ingestion_status", "COMPLETED"),
            is_active=False,
        )

        self.repo.insert_audit_log(
            document_id=document_id,
            logical_document_id=doc["logical_document_id"],
            version=doc["version"],
            action="MANUAL_ARCHIVE",
            result="SUCCESS",
            user_id=user_id,
            details="Manually archived document version.",
        )

        return self.repo.get_document_by_id(document_id)

    def retrieve_knowledge(
        self,
        query: str,
        access_scope: Optional[str] = None,
        product_type: Optional[str] = None,
        product_id: Optional[str] = None,
        document_type: Optional[str] = None,
        region: Optional[str] = "IN",
        top_k: int = 5,
    ) -> List[KnowledgeRetrievedContext]:
        # 1. Fetch from RAG Engine
        raw_results = self.rag.retrieve_contexts(query=query, top_k=top_k * 3)
        if not raw_results:
            return []

        # 2. Extract GCS URIs
        gcs_uris = [r["source_uri"] for r in raw_results if r.get("source_uri")]
        
        # 3. Lookup active documents from BigQuery
        active_docs_map = self.repo.get_active_documents_by_gcs_uris(gcs_uris)

        enriched_contexts: List[KnowledgeRetrievedContext] = []
        today_str = date.today().isoformat()

        for raw in raw_results:
            uri = raw.get("source_uri")
            doc = active_docs_map.get(uri)

            # If document is indexed in RAG but not found or not active in BigQuery registry, filter it out
            if not doc:
                continue

            # Authorization check: Document Access Control (enforced before reaching agent)
            doc_access = doc.get("access_control") or []
            if isinstance(doc_access, str):
                doc_access = [x.strip().upper() for x in doc_access.split(",") if x.strip()]
            normalized_doc_access = [str(x).upper() for x in doc_access]

            if access_scope:
                req_scope = access_scope.strip().upper()
                if req_scope not in normalized_doc_access:
                    # Never retrieve unauthorized documents
                    continue

            # Governance check: Effective Date Range
            eff_from = doc.get("effective_from")
            eff_to = doc.get("effective_to")
            if eff_from and eff_from > today_str:
                continue
            if eff_to and eff_to < today_str:
                continue

            # Metadata filters
            if product_type and doc.get("product_type") and doc.get("product_type").upper() != product_type.upper():
                continue
            if product_id and doc.get("product_id") and doc.get("product_id").upper() != product_id.upper():
                continue
            if document_type and doc.get("document_type") and doc.get("document_type").upper() != document_type.upper():
                continue
            if region and doc.get("region") and doc.get("region") not in ["GLOBAL", "ALL", region]:
                continue

            enriched_contexts.append(
                KnowledgeRetrievedContext(
                    text=raw.get("text", ""),
                    source_uri=uri,
                    document_id=doc.get("document_id"),
                    logical_document_id=doc.get("logical_document_id"),
                    document_name=doc.get("document_name"),
                    document_type=doc.get("document_type"),
                    product_type=doc.get("product_type"),
                    product_id=doc.get("product_id"),
                    product_name=doc.get("product_name"),
                    version=doc.get("version"),
                    effective_from=doc.get("effective_from"),
                    effective_to=doc.get("effective_to"),
                    access_control=normalized_doc_access,
                    distance=raw.get("distance"),
                    relevance_score=raw.get("score"),
                )
            )

            if len(enriched_contexts) >= top_k:
                break

        return enriched_contexts


knowledge_service = KnowledgeService()
