from typing import List, Optional
from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Query, UploadFile, status
from app.dependencies import require_bank_staff
from app.repositories.knowledge_repository import knowledge_repository
from app.schemas.knowledge import (
    KnowledgeAuditLogResponse,
    KnowledgeDocumentListResponse,
    KnowledgeDocumentResponse,
    KnowledgeQueryRequest,
    KnowledgeQueryResponse,
    KnowledgeVersionResponse,
)
from app.services.knowledge_service import knowledge_service
from app.utils.logger import logger
from app.utils.exceptions import CustomerIdentityException

router = APIRouter(prefix="/knowledge", tags=["Enterprise Knowledge Management"])


@router.get("/documents", response_model=KnowledgeDocumentListResponse)
async def list_documents(
    document_type: Optional[str] = Query(None, description="Filter by document type (PRODUCT, POLICY, etc.)"),
    product_type: Optional[str] = Query(None, description="Filter by product type (CREDIT_CARD, LOAN, etc.)"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status (ACTIVE, ARCHIVED, etc.)"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    access_scope: Optional[str] = Query(None, description="Filter by access scope ('CUSTOMER', 'STAFF')"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(require_bank_staff),
):
    """List knowledge documents with optional filters (Staff only)."""
    docs = knowledge_repository.list_documents(
        document_type=document_type,
        product_type=product_type,
        status=status_filter,
        is_active=is_active,
        access_scope=access_scope,
        limit=limit,
        offset=offset,
    )
    return KnowledgeDocumentListResponse(
        documents=[KnowledgeDocumentResponse(**d) for d in docs],
        total=len(docs),
    )


@router.get("/documents/{document_id}", response_model=KnowledgeDocumentResponse)
async def get_document(
    document_id: str,
    current_user: dict = Depends(require_bank_staff),
):
    """Get single document details (Staff only)."""
    doc = knowledge_repository.get_document_by_id(document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{document_id}' not found",
        )
    return KnowledgeDocumentResponse(**doc)


@router.get("/documents/{document_id}/versions", response_model=List[KnowledgeVersionResponse])
async def get_document_versions(
    document_id: str,
    current_user: dict = Depends(require_bank_staff),
):
    """Get all versions for a document's logical ID (Staff only)."""
    doc = knowledge_repository.get_document_by_id(document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{document_id}' not found",
        )
    
    versions = knowledge_repository.get_versions_by_logical_id(doc["logical_document_id"])
    return [KnowledgeVersionResponse(**v) for v in versions]


@router.get("/documents/{document_id}/audit-logs", response_model=List[KnowledgeAuditLogResponse])
async def get_document_audit_logs(
    document_id: str,
    current_user: dict = Depends(require_bank_staff),
):
    """Get audit logs for a document's logical ID (Staff only)."""
    doc = knowledge_repository.get_document_by_id(document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{document_id}' not found",
        )
    
    logs = knowledge_repository.get_audit_logs_for_document(doc["logical_document_id"])
    return [KnowledgeAuditLogResponse(**l) for l in logs]


@router.post("/documents", response_model=KnowledgeDocumentResponse, status_code=status.HTTP_201_CREATED)
@router.post("/documents/upload", response_model=KnowledgeDocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    document_name: str = Form(...),
    logical_document_id: str = Form(...),
    document_type: str = Form(...),
    version: str = Form(...),
    effective_from: str = Form(...),
    product_type: Optional[str] = Form(None),
    product_id: Optional[str] = Form(None),
    product_name: Optional[str] = Form(None),
    effective_to: Optional[str] = Form(None),
    region: str = Form("IN"),
    access_control: Optional[str] = Form(None, description="Comma-separated or JSON list: 'CUSTOMER', 'STAFF'"),
    audience: Optional[str] = Form(None),
    current_user: dict = Depends(require_bank_staff),
):
    """
    Upload a document into Cloud Storage and kick off background Vertex AI RAG Engine indexing.
    Only authorized bank staff can perform this action.
    """
    import json
    user_email = current_user.get("email", "staff@bankpilot.com")
    content = await file.read()

    # Parse access_control list
    parsed_access = None
    if access_control:
        access_control_clean = access_control.strip()
        if access_control_clean.startswith("[") and access_control_clean.endswith("]"):
            try:
                parsed_access = json.loads(access_control_clean)
            except Exception:
                parsed_access = [x.strip() for x in access_control_clean.strip("[]").split(",") if x.strip()]
        else:
            parsed_access = [x.strip() for x in access_control_clean.split(",") if x.strip()]

    try:
        result = knowledge_service.upload_document(
            file_content=content,
            filename=file.filename or "document.pdf",
            logical_document_id=logical_document_id.strip(),
            document_name=document_name.strip(),
            document_type=document_type.strip(),
            version=version.strip(),
            effective_from=effective_from.strip(),
            uploaded_by=user_email,
            product_type=product_type.strip() if product_type else None,
            product_id=product_id.strip() if product_id else None,
            product_name=product_name.strip() if product_name else None,
            effective_to=effective_to.strip() if effective_to else None,
            region=region.strip() if region else "IN",
            access_control=parsed_access,
            audience=audience.strip() if audience else None,
            content_type=file.content_type,
            background_tasks=background_tasks,
        )
        return KnowledgeDocumentResponse(**result)
    except CustomerIdentityException as cie:
        raise HTTPException(status_code=cie.status_code, detail=cie.detail)
    except Exception as e:
        logger.error(f"Unexpected upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.post("/documents/{document_id}/retry", response_model=KnowledgeDocumentResponse)
async def retry_document_ingestion(
    document_id: str,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(require_bank_staff),
):
    """Retry failed RAG indexing for a document in background (Staff only)."""
    user_email = current_user.get("email", "staff@bankpilot.com")
    try:
        result = knowledge_service.retry_ingestion(
            document_id=document_id,
            user_id=user_email,
            background_tasks=background_tasks,
        )
        return KnowledgeDocumentResponse(**result)
    except CustomerIdentityException as cie:
        raise HTTPException(status_code=cie.status_code, detail=cie.detail)
    except Exception as e:
        logger.error(f"Unexpected retry error: {e}")
        raise HTTPException(status_code=500, detail=f"Retry failed: {str(e)}")


@router.post("/documents/{document_id}/archive", response_model=KnowledgeDocumentResponse)
async def archive_document(
    document_id: str,
    current_user: dict = Depends(require_bank_staff),
):
    """Manually archive a document version (Staff only)."""
    user_email = current_user.get("email", "staff@bankpilot.com")
    try:
        result = knowledge_service.archive_document(document_id, user_email)
        return KnowledgeDocumentResponse(**result)
    except CustomerIdentityException as cie:
        raise HTTPException(status_code=cie.status_code, detail=cie.detail)
    except Exception as e:
        logger.error(f"Unexpected archive error: {e}")
        raise HTTPException(status_code=500, detail=f"Archive failed: {str(e)}")


@router.post("/retrieve", response_model=KnowledgeQueryResponse)
async def retrieve_knowledge_contexts(
    request: KnowledgeQueryRequest,
):
    """
    Semantic retrieval endpoint queried by AI assistants and internal services.
    Retrieves active, governed knowledge chunks matching search query and filters.
    """
    try:
        contexts = knowledge_service.retrieve_knowledge(
            query=request.query,
            access_scope=request.access_scope,
            product_type=request.product_type,
            product_id=request.product_id,
            document_type=request.document_type,
            region=request.region or "IN",
            top_k=request.top_k,
        )
        return KnowledgeQueryResponse(
            query=request.query,
            results=contexts,
            total_found=len(contexts),
        )
    except Exception as e:
        logger.error(f"Error in retrieve_knowledge_contexts: {e}")
        raise HTTPException(status_code=500, detail=f"RAG retrieval failed: {str(e)}")
