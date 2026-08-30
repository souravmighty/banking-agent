from typing import Any, Dict, List, Optional
import vertexai
from vertexai.preview import rag
from app.config import settings
from app.utils.logger import logger
from app.utils.exceptions import CustomerIdentityException


class RAGService:
    def __init__(
        self,
        project: Optional[str] = None,
        location: Optional[str] = None,
        corpus_name: Optional[str] = None,
    ):
        self.project = project or settings.GOOGLE_CLOUD_PROJECT
        self.location = location or settings.RAG_LOCATION
        self.corpus_name = corpus_name or settings.RAG_CORPUS_NAME
        self._initialized = False

    def _ensure_initialized(self):
        if not self._initialized:
            try:
                vertexai.init(project=self.project, location=self.location)
                self._initialized = True
            except Exception as e:
                logger.error(f"Failed to initialize Vertex AI RAG: {e}")
                raise CustomerIdentityException(
                    status_code=500,
                    detail=f"Failed to initialize Vertex AI RAG Service: {str(e)}"
                )

    def get_or_create_primary_corpus(self, display_name: str = "bankpilot-knowledge") -> str:
        self._ensure_initialized()
        if self.corpus_name and "ragCorpora" in self.corpus_name:
            return self.corpus_name

        try:
            corpora = list(rag.list_corpora())
            for c in corpora:
                if c.display_name == display_name:
                    self.corpus_name = c.name
                    logger.info(f"Found existing RAG corpus '{display_name}': {self.corpus_name}")
                    return self.corpus_name

            # Create new corpus if not found
            embedding_config = rag.EmbeddingModelConfig(
                publisher_model=settings.RAG_EMBEDDING_MODEL
            )
            created_corpus = rag.create_corpus(
                display_name=display_name,
                description="BankPilot Enterprise Knowledge Corpus for Products, Policies, and FAQs",
                embedding_model_config=embedding_config,
            )
            self.corpus_name = created_corpus.name
            logger.info(f"Created new RAG corpus '{display_name}': {self.corpus_name}")
            return self.corpus_name
        except Exception as e:
            logger.error(f"Failed to get/create RAG corpus: {e}")
            raise CustomerIdentityException(
                status_code=500,
                detail=f"Failed to get or create RAG corpus: {str(e)}"
            )

    def import_file_from_gcs(
        self,
        gcs_uri: str,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        corpus_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        self._ensure_initialized()
        target_corpus = corpus_name or self.get_or_create_primary_corpus()

        # Check if already indexed in corpus
        rag_file_id = None
        try:
            files = list(rag.list_files(corpus_name=target_corpus))
            for f in files:
                gcs_source = getattr(f, "gcs_source", None)
                uris = getattr(gcs_source, "uris", []) if gcs_source else []
                if gcs_uri in uris or (getattr(f, "display_name", None) and f.display_name in gcs_uri):
                    rag_file_id = f.name
                    logger.info(f"File '{gcs_uri}' is already indexed in RAG corpus '{target_corpus}' with ID '{rag_file_id}'")
                    return {
                        "status": "COMPLETED",
                        "imported_count": 1,
                        "skipped_count": 0,
                        "rag_file_id": rag_file_id,
                        "corpus_name": target_corpus,
                    }
        except Exception as ex:
            logger.warning(f"Could not check existing RAG files in corpus {target_corpus}: {ex}")

        try:
            logger.info(f"Importing GCS file '{gcs_uri}' into RAG corpus '{target_corpus}'...")
            response = rag.import_files(
                corpus_name=target_corpus,
                paths=[gcs_uri],
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                timeout=600,
            )

            imported_count = getattr(response, "imported_rag_files_count", 0)
            failed_count = getattr(response, "failed_rag_files_count", 0)
            skipped_count = getattr(response, "skipped_rag_files_count", 0)
            status_error = getattr(response, "rag_status_error", None)

            # Try to get rag_file_id by listing files in corpus
            rag_file_id = None
            try:
                files = list(rag.list_files(corpus_name=target_corpus))
                for f in files:
                    gcs_source = getattr(f, "gcs_source", None)
                    uris = getattr(gcs_source, "uris", []) if gcs_source else []
                    if gcs_uri in uris or (getattr(f, "display_name", None) and f.display_name in gcs_uri):
                        rag_file_id = f.name
                        break
            except Exception as ex:
                logger.warning(f"Could not resolve rag_file_id for {gcs_uri}: {ex}")

            if failed_count > 0 and not rag_file_id:
                err_msg = str(status_error) if status_error else f"Failed to import file into RAG (imported: {imported_count}, failed: {failed_count}, skipped: {skipped_count})"
                logger.error(f"RAG import failed for {gcs_uri}: {err_msg}")
                raise CustomerIdentityException(
                    status_code=500,
                    detail=f"RAG file ingestion failed: {err_msg}"
                )

            logger.info(f"Successfully imported {gcs_uri} into RAG corpus {target_corpus} (rag_file_id: {rag_file_id})")
            return {
                "status": "COMPLETED",
                "imported_count": imported_count or 1,
                "skipped_count": skipped_count,
                "rag_file_id": rag_file_id,
                "corpus_name": target_corpus,
            }
        except CustomerIdentityException:
            raise
        except Exception as e:
            logger.warning(f"Exception during rag.import_files for {gcs_uri}: {e}. Checking if file exists in corpus...")
            try:
                files = list(rag.list_files(corpus_name=target_corpus))
                for f in files:
                    gcs_source = getattr(f, "gcs_source", None)
                    uris = getattr(gcs_source, "uris", []) if gcs_source else []
                    if gcs_uri in uris or (getattr(f, "display_name", None) and f.display_name in gcs_uri):
                        rag_file_id = f.name
                        logger.info(f"File '{gcs_uri}' found in RAG corpus '{target_corpus}' despite error: {rag_file_id}")
                        return {
                            "status": "COMPLETED",
                            "imported_count": 1,
                            "skipped_count": 0,
                            "rag_file_id": rag_file_id,
                            "corpus_name": target_corpus,
                        }
            except Exception:
                pass
            logger.error(f"Exception importing {gcs_uri} to RAG: {e}")
            raise CustomerIdentityException(
                status_code=500,
                detail=f"Failed to import file to RAG Engine: {str(e)}"
            )

    def delete_file(self, rag_file_id: str, corpus_name: Optional[str] = None) -> bool:
        self._ensure_initialized()
        target_corpus = corpus_name or self.get_or_create_primary_corpus()
        try:
            rag.delete_file(name=rag_file_id)
            logger.info(f"Deleted RAG file {rag_file_id} from corpus {target_corpus}")
            return True
        except Exception as e:
            logger.warning(f"Could not delete RAG file {rag_file_id}: {e}")
            return False

    def retrieve_contexts(
        self,
        query: str,
        top_k: int = 5,
        corpus_name: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        self._ensure_initialized()
        target_corpus = corpus_name or self.get_or_create_primary_corpus()

        try:
            response = rag.retrieval_query(
                text=query,
                rag_corpora=[target_corpus],
                similarity_top_k=top_k,
            )

            results = []
            contexts = getattr(response.contexts, "contexts", []) if hasattr(response, "contexts") else []
            for item in contexts:
                text = getattr(item, "text", "")
                source_uri = getattr(item, "source_uri", None)
                distance = getattr(item, "distance", None)
                score = getattr(item, "score", None)

                results.append({
                    "text": text,
                    "source_uri": source_uri,
                    "distance": distance,
                    "score": score,
                })

            return results
        except Exception as e:
            logger.error(f"Failed to retrieve contexts for query '{query}': {e}")
            raise CustomerIdentityException(
                status_code=500,
                detail=f"RAG retrieval failed: {str(e)}"
            )


rag_service = RAGService()
