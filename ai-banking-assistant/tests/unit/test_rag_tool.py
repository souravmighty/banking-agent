from unittest.mock import MagicMock, AsyncMock, patch
import pytest
from app.agent import root_agent
from app.tools import retrieve_product_policy_knowledge

def test_rag_tool_registered_in_root_agent():
    tool_names = [getattr(t, "__name__", getattr(t, "name", str(t))) for t in root_agent.tools]
    assert "retrieve_product_policy_knowledge" in tool_names

@pytest.mark.asyncio
async def test_retrieve_product_policy_knowledge_via_service():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "query": "What are platinum card dining perks?",
        "total_found": 1,
        "results": [
            {
                "text": "Cardholders get 5x reward points on dining and complimentary airport lounge access.",
                "document_name": "Platinum Card Terms",
                "version": "v1.0.0",
                "document_type": "PRODUCT",
                "product_type": "CREDIT_CARD",
                "source_uri": "gs://banking-agent-knowledge-docs/products/credit_card/platinum/v1.0.0/terms.pdf",
                "effective_from": "2025-01-01",
                "relevance_score": 0.92,
            }
        ],
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp

        result = await retrieve_product_policy_knowledge(
            query="What are platinum card dining perks?",
            product_type="CREDIT_CARD",
        )

        assert result["total_found"] == 1
        assert len(result["results"]) == 1
        assert "Platinum Card Terms" in result["results"][0]["document_name"]
        assert "5x reward points" in result["results"][0]["text"]
