import pytest
from unittest.mock import MagicMock
from app.services.knowledge_service import KnowledgeService
from app.services.document_storage_service import DocumentStorageService
from app.utils.exceptions import CustomerIdentityException

@pytest.fixture
def mock_storage_service():
    storage = MagicMock()
    storage.upload_file.return_value = (
        "gs://banking-agent-knowledge-docs/products/credit_card/test-card/v1.0.0/terms.pdf"
    )
    return storage

@pytest.fixture
def mock_rag_service():
    rag = MagicMock()
    rag.import_file_from_gcs.return_value = {
        "rag_file_id": "projects/123/locations/us-central1/ragCorpora/456/ragFiles/789"
    }
    rag.retrieve_contexts.return_value = [
        {
            "text": "Platinum Credit Card offers 5x reward points on dining.",
            "source_uri": "gs://banking-agent-knowledge-docs/products/credit_card/test-card/v1.0.0/terms.pdf",
            "distance": 0.12,
            "score": 0.88,
        }
    ]
    return rag

@pytest.fixture
def mock_knowledge_repo():
    repo = MagicMock()
    repo.check_version_exists.return_value = False
    repo.get_document_by_id.return_value = {
        "document_id": "doc_123",
        "document_name": "Platinum Card Terms",
        "status": "ACTIVE",
        "is_active": True,
        "ingestion_status": "COMPLETED",
    }
    return repo

@pytest.fixture
def knowledge_service(mock_storage_service, mock_rag_service, mock_knowledge_repo):
    return KnowledgeService(
        repository=mock_knowledge_repo,
        storage_svc=mock_storage_service,
        rag_svc=mock_rag_service,
    )

def test_upload_document_success(knowledge_service, mock_knowledge_repo, mock_storage_service):
    result = knowledge_service.upload_document(
        file_content=b"%PDF-1.4 Mock PDF Content",
        filename="terms.pdf",
        logical_document_id="doc-platinum-card",
        document_name="Platinum Card Terms",
        document_type="PRODUCT",
        product_type="CREDIT_CARD",
        product_id="CARD_PLATINUM_01",
        product_name="Platinum Card",
        version="v1.0.0",
        effective_from="2025-01-01",
        uploaded_by="staff_123",
    )

    assert result["document_name"] == "Platinum Card Terms"
    mock_storage_service.upload_file.assert_called_once()
    mock_knowledge_repo.insert_document.assert_called_once()
    called_doc = mock_knowledge_repo.insert_document.call_args[0][0]
    assert called_doc["status"] == "PROCESSING"
    assert called_doc["ingestion_status"] == "INDEXING"
    assert called_doc["is_active"] is False
    mock_knowledge_repo.insert_audit_log.assert_called()

def test_background_ingestion_success(knowledge_service, mock_knowledge_repo, mock_rag_service):
    knowledge_service.process_background_ingestion(
        document_id="doc_123",
        gcs_uri="gs://bucket/terms.pdf",
        logical_document_id="doc-platinum-card",
        version="v1.0.0",
        user_id="staff_123",
    )

    mock_rag_service.import_file_from_gcs.assert_called_once_with(
        gcs_uri="gs://bucket/terms.pdf",
        chunk_size=512,
        chunk_overlap=50,
    )
    mock_knowledge_repo.transition_active_version.assert_called_once()
    mock_knowledge_repo.insert_audit_log.assert_called()

def test_background_ingestion_failure(knowledge_service, mock_knowledge_repo, mock_rag_service):
    mock_rag_service.import_file_from_gcs.side_effect = Exception("Vertex RAG API Quota Exceeded")

    knowledge_service.process_background_ingestion(
        document_id="doc_123",
        gcs_uri="gs://bucket/terms.pdf",
        logical_document_id="doc-platinum-card",
        version="v1.0.0",
        user_id="staff_123",
    )

    mock_knowledge_repo.update_document_status.assert_called_once()
    kwargs = mock_knowledge_repo.update_document_status.call_args[1]
    assert kwargs["status"] == "FAILED"
    assert kwargs["ingestion_status"] == "FAILED"
    assert kwargs["is_active"] is False
    assert "Vertex RAG API Quota Exceeded" in kwargs["ingestion_error"]
    mock_knowledge_repo.insert_audit_log.assert_called()

def test_archive_document_version(knowledge_service, mock_knowledge_repo):
    existing_doc = {
        "document_id": "doc_uuid_1",
        "logical_document_id": "doc-platinum-card",
        "document_name": "Platinum Card Terms",
        "original_filename": "terms.pdf",
        "document_type": "PRODUCT",
        "product_type": "CREDIT_CARD",
        "version": "v1.0.0",
        "status": "ACTIVE",
        "effective_from": "2025-01-01",
        "region": "IN",
        "audience": "ALL",
        "gcs_uri": "gs://bucket/terms.pdf",
        "uploaded_by": "staff_123",
        "uploaded_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-01-01T00:00:00Z",
        "ingestion_status": "COMPLETED",
        "is_active": True,
    }
    mock_knowledge_repo.get_document_by_id.return_value = existing_doc

    result = knowledge_service.archive_document(
        document_id="doc_uuid_1",
        user_id="staff_admin",
    )

    assert result["document_id"] == "doc_uuid_1"
    mock_knowledge_repo.update_document_status.assert_called_once_with(
        document_id="doc_uuid_1",
        status="ARCHIVED",
        ingestion_status="COMPLETED",
        is_active=False,
    )
    mock_knowledge_repo.insert_audit_log.assert_called()

def test_retrieve_knowledge_filters_inactive_and_expired(knowledge_service, mock_knowledge_repo, mock_rag_service):
    # Candidate chunk from RAG
    mock_rag_service.retrieve_contexts.return_value = [
        {
            "text": "Platinum Credit Card offers 5x reward points on dining.",
            "source_uri": "gs://banking-agent-knowledge-docs/products/credit_card/test-card/v1.0.0/terms.pdf",
            "distance": 0.1,
            "score": 0.9,
        }
    ]

    # Active documents in BigQuery map
    mock_knowledge_repo.get_active_documents_by_gcs_uris.return_value = {
        "gs://banking-agent-knowledge-docs/products/credit_card/test-card/v1.0.0/terms.pdf": {
            "document_id": "doc_1",
            "logical_document_id": "doc-platinum-card",
            "document_name": "Platinum Card Terms",
            "document_type": "PRODUCT",
            "product_type": "CREDIT_CARD",
            "product_id": "CARD_PLATINUM_01",
            "product_name": "Platinum Card",
            "version": "v1.0.0",
            "status": "ACTIVE",
            "effective_from": "2020-01-01",
            "effective_to": "2030-12-31",
            "gcs_uri": "gs://banking-agent-knowledge-docs/products/credit_card/test-card/v1.0.0/terms.pdf",
            "is_active": True,
            "region": "IN",
        }
    }

    results = knowledge_service.retrieve_knowledge(
        query="What are the rewards on the platinum card?",
        top_k=5,
    )

    assert len(results) == 1
    assert results[0].text == "Platinum Credit Card offers 5x reward points on dining."
    assert results[0].document_name == "Platinum Card Terms"
    assert results[0].version == "v1.0.0"

def test_document_storage_service_validation():
    storage = DocumentStorageService(bucket_name="test-bucket")

    # Invalid extension
    with pytest.raises(CustomerIdentityException) as exc_info:
        storage.validate_file("malicious.exe", b"test executable")
    assert exc_info.value.status_code == 400
    assert "Unsupported file format" in exc_info.value.detail

    # Exceeds max size
    with pytest.raises(CustomerIdentityException) as exc_info:
        storage.validate_file("large.pdf", b"0" * (26 * 1024 * 1024))
    assert exc_info.value.status_code == 400
    assert "exceeds limit of 25MB" in exc_info.value.detail


def test_upload_document_access_control_validation(knowledge_service, mock_knowledge_repo):
    # Invalid empty access control
    with pytest.raises(CustomerIdentityException) as exc_info:
        knowledge_service.upload_document(
            file_content=b"%PDF-1.4 Mock",
            filename="terms.pdf",
            logical_document_id="doc-test",
            document_name="Test Doc",
            document_type="PRODUCT",
            version="v1.0.0",
            effective_from="2025-01-01",
            uploaded_by="staff_123",
            access_control=[],
        )
    assert exc_info.value.status_code == 400
    assert "At least one valid access scope" in exc_info.value.detail

    # Invalid scope value
    with pytest.raises(CustomerIdentityException) as exc_info:
        knowledge_service.upload_document(
            file_content=b"%PDF-1.4 Mock",
            filename="terms.pdf",
            logical_document_id="doc-test",
            document_name="Test Doc",
            document_type="PRODUCT",
            version="v1.0.0",
            effective_from="2025-01-01",
            uploaded_by="staff_123",
            access_control=["INVALID_ROLE"],
        )
    assert exc_info.value.status_code == 400
    assert "Invalid access control values" in exc_info.value.detail


def test_retrieve_knowledge_access_control_filtering(knowledge_service, mock_knowledge_repo, mock_rag_service):
    # Setup mock RAG candidate chunks from 3 different documents
    mock_rag_service.retrieve_contexts.return_value = [
        {
            "text": "Customer retail FAQ: Minimum balance requirements.",
            "source_uri": "gs://bucket/customer_faq.pdf",
            "distance": 0.1,
            "score": 0.9,
        },
        {
            "text": "Staff analytics KPI guide: Customer churn formula.",
            "source_uri": "gs://bucket/staff_kpi_guide.pdf",
            "distance": 0.12,
            "score": 0.88,
        },
        {
            "text": "Shared product overview: Platinum Card interest rate.",
            "source_uri": "gs://bucket/shared_product.pdf",
            "distance": 0.15,
            "score": 0.85,
        },
    ]

    mock_knowledge_repo.get_active_documents_by_gcs_uris.return_value = {
        "gs://bucket/customer_faq.pdf": {
            "document_id": "doc_cust_1",
            "logical_document_id": "doc-cust-faq",
            "document_name": "Customer FAQ",
            "document_type": "FAQ",
            "version": "v1.0.0",
            "status": "ACTIVE",
            "effective_from": "2020-01-01",
            "effective_to": None,
            "access_control": ["CUSTOMER"],
            "gcs_uri": "gs://bucket/customer_faq.pdf",
            "is_active": True,
            "region": "IN",
        },
        "gs://bucket/staff_kpi_guide.pdf": {
            "document_id": "doc_staff_1",
            "logical_document_id": "doc-staff-kpi",
            "document_name": "Staff KPI Guide",
            "document_type": "POLICY",
            "version": "v1.0.0",
            "status": "ACTIVE",
            "effective_from": "2020-01-01",
            "effective_to": None,
            "access_control": ["STAFF"],
            "gcs_uri": "gs://bucket/staff_kpi_guide.pdf",
            "is_active": True,
            "region": "IN",
        },
        "gs://bucket/shared_product.pdf": {
            "document_id": "doc_shared_1",
            "logical_document_id": "doc-shared-product",
            "document_name": "Platinum Card Shared Overview",
            "document_type": "PRODUCT",
            "version": "v1.0.0",
            "status": "ACTIVE",
            "effective_from": "2020-01-01",
            "effective_to": None,
            "access_control": ["CUSTOMER", "STAFF"],
            "gcs_uri": "gs://bucket/shared_product.pdf",
            "is_active": True,
            "region": "IN",
        },
    }

    # 1. Customer scope query: Must retrieve CUSTOMER-only and SHARED, but EXCLUDE STAFF-only
    customer_results = knowledge_service.retrieve_knowledge(
        query="Explain product terms and FAQs",
        access_scope="CUSTOMER",
        top_k=5,
    )
    assert len(customer_results) == 2
    customer_doc_ids = {c.document_id for c in customer_results}
    assert "doc_cust_1" in customer_doc_ids
    assert "doc_shared_1" in customer_doc_ids
    assert "doc_staff_1" not in customer_doc_ids  # Never return unauthorized staff doc to customer

    # 2. Staff scope query: Must retrieve STAFF-only and SHARED, but EXCLUDE CUSTOMER-only
    staff_results = knowledge_service.retrieve_knowledge(
        query="Explain KPI formulas and product overview",
        access_scope="STAFF",
        top_k=5,
    )
    assert len(staff_results) == 2
    staff_doc_ids = {s.document_id for s in staff_results}
    assert "doc_staff_1" in staff_doc_ids
    assert "doc_shared_1" in staff_doc_ids
    assert "doc_cust_1" not in staff_doc_ids

    # 3. No scope specified: Returns all active matches
    all_results = knowledge_service.retrieve_knowledge(
        query="All docs",
        access_scope=None,
        top_k=5,
    )
    assert len(all_results) == 3


def test_rag_service_import_existing_file(monkeypatch):
    from unittest.mock import MagicMock
    from app.services.rag_service import RAGService
    import vertexai
    from vertexai.preview import rag

    rag_service = RAGService(corpus_name="projects/123/locations/us-central1/ragCorpora/456")
    monkeypatch.setattr(vertexai, "init", MagicMock())

    # Mock file that already exists in corpus
    mock_file = MagicMock()
    mock_file.name = "rag_file_existing_123"
    mock_file.display_name = "test.pdf"
    mock_file.gcs_source = MagicMock()
    mock_file.gcs_source.uris = ["gs://bucket/test.pdf"]

    monkeypatch.setattr(rag, "list_files", MagicMock(return_value=[mock_file]))
    mock_import = MagicMock()
    monkeypatch.setattr(rag, "import_files", mock_import)

    result = rag_service.import_file_from_gcs("gs://bucket/test.pdf")
    assert result["status"] == "COMPLETED"
    assert result["rag_file_id"] == "rag_file_existing_123"
    # Should not even call import_files if already found
    mock_import.assert_not_called()


def test_rag_service_import_skipped_file(monkeypatch):
    from unittest.mock import MagicMock
    from app.services.rag_service import RAGService
    import vertexai
    from vertexai.preview import rag

    rag_service = RAGService(corpus_name="projects/123/locations/us-central1/ragCorpora/456")
    monkeypatch.setattr(vertexai, "init", MagicMock())

    # Initial check finds nothing
    mock_file = MagicMock()
    mock_file.name = "rag_file_skipped_456"
    mock_file.display_name = "test2.pdf"
    mock_file.gcs_source = MagicMock()
    mock_file.gcs_source.uris = ["gs://bucket/test2.pdf"]

    # First call returns empty, second call returns mock_file
    monkeypatch.setattr(rag, "list_files", MagicMock(side_effect=[[], [mock_file]]))

    mock_response = MagicMock()
    mock_response.imported_rag_files_count = 0
    mock_response.skipped_rag_files_count = 1
    mock_response.failed_rag_files_count = 0
    monkeypatch.setattr(rag, "import_files", MagicMock(return_value=mock_response))

    result = rag_service.import_file_from_gcs("gs://bucket/test2.pdf")
    assert result["status"] == "COMPLETED"
    assert result["rag_file_id"] == "rag_file_skipped_456"


