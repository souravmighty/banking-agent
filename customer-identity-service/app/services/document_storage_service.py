import os
import re
from typing import Tuple
from google.cloud import storage
from app.config import settings
from app.utils.logger import logger
from app.utils.exceptions import CustomerIdentityException

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md", ".html"}
MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB


class DocumentStorageService:
    def __init__(self, bucket_name: str = None, project: str = None):
        self.project = project or settings.GOOGLE_CLOUD_PROJECT
        self.bucket_name = bucket_name or settings.RAG_DOCUMENT_BUCKET
        self._client = None

    @property
    def client(self) -> storage.Client:
        if self._client is None:
            self._client = storage.Client(project=self.project)
        return self._client

    def sanitize_filename(self, filename: str) -> str:
        name = os.path.basename(filename)
        # Keep alphanumeric, underscores, hyphens, and periods
        clean_name = re.sub(r"[^a-zA-Z0-9_\-\.]", "_", name)
        return clean_name or "document.pdf"

    def build_storage_path(
        self,
        document_type: str,
        logical_document_id: str,
        version: str,
        filename: str,
        product_type: str = None,
    ) -> str:
        sanitized_filename = self.sanitize_filename(filename)
        doc_type = document_type.upper()
        
        if doc_type == "PRODUCT":
            p_type = (product_type or "OTHER").lower().replace("_", "-")
            path = f"products/{p_type}/{logical_document_id}/{version}/{sanitized_filename}"
        elif doc_type == "POLICY":
            path = f"policies/{logical_document_id}/{version}/{sanitized_filename}"
        elif doc_type == "FAQ":
            path = f"faqs/{logical_document_id}/{version}/{sanitized_filename}"
        elif doc_type == "TERMS_AND_CONDITIONS":
            path = f"terms/{logical_document_id}/{version}/{sanitized_filename}"
        elif doc_type == "SERVICE_INFORMATION":
            path = f"service_info/{logical_document_id}/{version}/{sanitized_filename}"
        else:
            path = f"general/{logical_document_id}/{version}/{sanitized_filename}"
            
        return path

    def validate_file(self, filename: str, content: bytes) -> Tuple[str, int]:
        if not filename:
            raise CustomerIdentityException(
                status_code=400,
                detail="Filename is required"
            )
            
        _, ext = os.path.splitext(filename)
        ext = ext.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise CustomerIdentityException(
                status_code=400,
                detail=f"Unsupported file format '{ext}'. Allowed formats: {', '.join(ALLOWED_EXTENSIONS)}"
            )
            
        size = len(content)
        if size == 0:
            raise CustomerIdentityException(
                status_code=400,
                detail="File content cannot be empty"
            )
            
        if size > MAX_FILE_SIZE_BYTES:
            raise CustomerIdentityException(
                status_code=400,
                detail=f"File size exceeds limit of 25MB (size: {size / (1024 * 1024):.2f}MB)"
            )
            
        return ext, size

    def upload_file(
        self,
        content: bytes,
        filename: str,
        document_type: str,
        logical_document_id: str,
        version: str,
        content_type: str = None,
        product_type: str = None,
    ) -> str:
        self.validate_file(filename, content)
        storage_path = self.build_storage_path(
            document_type=document_type,
            logical_document_id=logical_document_id,
            version=version,
            filename=filename,
            product_type=product_type,
        )

        try:
            bucket = self.client.bucket(self.bucket_name)
            blob = bucket.blob(storage_path)
            
            # Detect MIME type if not provided
            if not content_type:
                _, ext = os.path.splitext(filename)
                ext = ext.lower()
                mime_map = {
                    ".pdf": "application/pdf",
                    ".txt": "text/plain",
                    ".md": "text/markdown",
                    ".html": "text/html",
                    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                }
                content_type = mime_map.get(ext, "application/octet-stream")
                
            blob.upload_from_string(content, content_type=content_type)
            gcs_uri = f"gs://{self.bucket_name}/{storage_path}"
            logger.info(f"Uploaded knowledge document to {gcs_uri}")
            return gcs_uri
        except Exception as e:
            logger.error(f"Failed to upload document to GCS: {str(e)}")
            raise CustomerIdentityException(
                status_code=500,
                detail=f"Failed to upload document to storage: {str(e)}"
            )


document_storage_service = DocumentStorageService()
